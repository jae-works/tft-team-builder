"""Build one pinned TFT Set package from Riot Data Dragon and CommunityDragon.

This is a developer-only acquisition tool. The application runtime never imports it and never
uses the network. A source configuration selects one exact Riot/CDragon revision and contains
only the small explicit exceptions that cannot be derived safely from upstream Set metadata.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx

from tft_builder.constants import SET_SCHEMA_VERSION, SOURCE_SPEC_SCHEMA_VERSION
from tft_builder.json_utils import canonical_json_bytes
from tft_builder.set_builder import build_set_from_local_spec

MAX_JSON_BYTES = 64 * 1024 * 1024
MAX_IMAGE_BYTES = 8 * 1024 * 1024
REQUEST_TIMEOUT = httpx.Timeout(30.0, connect=15.0)
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.casefold()).strip("_")
    if not slug:
        raise ValueError(f"cannot create stable ID from {value!r}")
    return slug


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _cache_path(cache_dir: Path, source_id: str, url: str) -> Path:
    suffix = Path(urlparse(url).path).suffix or ".bin"
    return cache_dir / f"{_slug(source_id)}-{hashlib.sha256(url.encode()).hexdigest()[:16]}{suffix}"


def _download(client: httpx.Client, cache_dir: Path, source_id: str, url: str, limit: int) -> Path:
    """Download one exact source URL with a bounded stream and immutable URL-keyed cache."""

    if urlparse(url).scheme != "https":
        raise ValueError(f"source URL must use HTTPS: {url}")
    cache_dir.mkdir(parents=True, exist_ok=True)
    target = _cache_path(cache_dir, source_id, url)
    if target.is_file() and target.stat().st_size > 0:
        return target

    last_error: Exception | None = None
    for _attempt in range(3):
        temporary = target.with_suffix(target.suffix + ".part")
        temporary.unlink(missing_ok=True)
        try:
            with client.stream("GET", url, follow_redirects=True) as response:
                response.raise_for_status()
                total = 0
                with temporary.open("wb") as output:
                    for chunk in response.iter_bytes(64 * 1024):
                        total += len(chunk)
                        if total > limit:
                            raise ValueError(f"download exceeds {limit} byte limit: {url}")
                        output.write(chunk)
            if total == 0:
                raise ValueError(f"downloaded empty source: {url}")
            temporary.replace(target)
            return target
        except (httpx.HTTPError, OSError, ValueError) as error:
            last_error = error
            temporary.unlink(missing_ok=True)
    raise RuntimeError(f"failed to download {url}: {last_error}") from last_error


def _source_record(source_id: str, url: str, revision: str, locale: str | None, path: Path) -> dict:
    return {
        "id": source_id,
        "url": url,
        "revision": revision,
        "locale": locale,
        "sha256": _sha256(path),
        "byte_length": path.stat().st_size,
    }


def _set_data(payload: dict, mutator: str) -> dict:
    matches = [entry for entry in payload.get("setData", []) if entry.get("mutator") == mutator]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one setData entry for {mutator!r}; got {len(matches)}")
    return matches[0]


def _dd_data(payload: dict) -> dict[str, dict]:
    data = payload.get("data")
    if not isinstance(data, dict):
        raise ValueError("Data Dragon payload has no data object")
    return data


def _cdragon_asset_url(revision: str, path: str) -> str:
    normalized = path.replace("\\", "/").lower().removeprefix("/").replace(".tex", ".png")
    return f"https://raw.communitydragon.org/{revision}/game/{normalized}"


def _dd_asset_url(version: str, record: dict) -> str | None:
    image = record.get("image") or {}
    group = image.get("group")
    filename = image.get("full")
    if not group or not filename:
        return None
    return f"https://ddragon.leagueoflegends.com/cdn/{version}/img/{group}/{filename}"


def _asset(
    client: httpx.Client,
    cache_dir: Path,
    spec_dir: Path,
    sources: list[dict],
    source_id: str,
    revision: str,
    locale: str | None,
    url: str,
    target: str,
) -> None:
    downloaded = _download(client, cache_dir, source_id, url, MAX_IMAGE_BYTES)
    if downloaded.read_bytes()[:8] != PNG_SIGNATURE:
        raise ValueError(f"asset is not a PNG: {url}")
    destination = spec_dir / target
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(downloaded, destination)
    sources.append(_source_record(source_id, url, revision, locale, downloaded))


def _trait_name_map(set_data: dict) -> tuple[dict[str, dict], dict[str, str]]:
    traits = set_data.get("traits") or []
    by_api = {trait["apiName"]: trait for trait in traits}
    by_name = {trait["name"]: trait["apiName"] for trait in traits}
    if len(by_api) != len(traits) or len(by_name) != len(traits):
        raise ValueError("Trait IDs and localized names must be unique in the source Set")
    return by_api, by_name


def _category(item: dict) -> str:
    tags = {str(tag).casefold() for tag in item.get("tags") or []}
    api = str(item.get("apiName", "")).casefold()
    if "component" in tags or "component" in api:
        return "COMPONENT"
    if "radiant" in tags or "radiant" in api:
        return "RADIANT"
    if "artifact" in tags or "ornn" in api:
        return "ARTIFACT"
    if "support" in tags or "support" in api:
        return "SUPPORT"
    if item.get("associatedTraits") or "emblem" in api:
        return "EMBLEM"
    if (
        "consumable" in tags
        or "consumable" in api
        or "potion" in api
        or "booster" in api
    ):
        return "CONSUMABLE"
    if item.get("composition"):
        return "CRAFTABLE"
    return "OTHER"



def _collect_set_item_ids(source_set: dict, all_items: dict[str, dict]) -> set[str]:
    """Return every Set-declared item plus every recursively referenced component."""

    item_ids = set(source_set.get("items") or [])
    pending = list(item_ids)
    while pending:
        current = pending.pop()
        item = all_items.get(current)
        if item is None:
            raise ValueError(f"Set item {current!r} is missing from CommunityDragon items")
        for component in item.get("composition") or []:
            if component not in item_ids:
                item_ids.add(component)
                pending.append(component)
    return item_ids


def _require_item_categories(item_rows: list[dict], required_categories: list[str]) -> None:
    """Fail acquisition when an expected current-Set item family disappears upstream."""

    present = {row["category"] for row in item_rows}
    missing = sorted(set(required_categories) - present)
    if missing:
        raise ValueError("Set item inventory is missing required categories: " + ", ".join(missing))

def _localized_record(payload: dict, mutator: str, kind: str) -> dict[str, dict]:
    data = _set_data(payload, mutator)
    return {entry["apiName"]: entry for entry in data[kind]}


def _load_remote_sources(config: dict, cache_dir: Path) -> tuple[dict, dict, dict, list[dict]]:
    cdragon_version = config["cdragon_version"]
    ddragon_version = config["ddragon_version"]
    mutator = config["mutator"]
    locales = config["locales"]
    sources: list[dict] = []
    cdragon: dict[str, dict] = {}
    ddragon: dict[str, dict[str, dict]] = {}

    with httpx.Client(timeout=REQUEST_TIMEOUT, headers={"User-Agent": "tft-team-builder-set-import/0.7"}) as client:
        for locale in locales:
            cd_locale = locale.casefold()
            url = f"https://raw.communitydragon.org/{cdragon_version}/cdragon/tft/{cd_locale}.json"
            path = _download(client, cache_dir, f"cdragon_{locale}", url, MAX_JSON_BYTES)
            cdragon[locale] = _json(path)
            _set_data(cdragon[locale], mutator)
            sources.append(_source_record(f"cdragon_{locale}", url, cdragon_version, locale, path))

            for kind in ("champion", "item", "trait"):
                url = (
                    f"https://ddragon.leagueoflegends.com/cdn/{ddragon_version}/data/"
                    f"{locale}/tft-{kind}.json"
                )
                path = _download(client, cache_dir, f"ddragon_{kind}_{locale}", url, MAX_JSON_BYTES)
                ddragon[f"{kind}:{locale}"] = _dd_data(_json(path))
                sources.append(
                    _source_record(
                        f"ddragon_{kind}_{locale}", url, ddragon_version, locale, path
                    )
                )

        planner_url = (
            f"https://raw.communitydragon.org/{cdragon_version}/plugins/rcp-be-lol-game-data/"
            "global/default/v1/tftchampions-teamplanner.json"
        )
        planner_path = _download(client, cache_dir, "team_planner", planner_url, MAX_JSON_BYTES)
        planner = _json(planner_path)
        sources.append(
            _source_record("team_planner", planner_url, cdragon_version, None, planner_path)
        )

        return cdragon, ddragon, planner, sources


def _build_spec(config: dict, cache_dir: Path, spec_dir: Path) -> None:
    mutator = config["mutator"]
    default_locale = config["default_locale"]
    locales = config["locales"]
    cdragon, ddragon, planner_payload, sources = _load_remote_sources(config, cache_dir)
    source_set = _set_data(cdragon[default_locale], mutator)
    traits_by_api, trait_api_by_name = _trait_name_map(source_set)
    localized_sets = {locale: _set_data(cdragon[locale], mutator) for locale in locales}
    localized_traits = {
        locale: _localized_record(cdragon[locale], mutator, "traits") for locale in locales
    }

    all_items = {item["apiName"]: item for item in cdragon[default_locale].get("items", [])}
    item_ids = _collect_set_item_ids(source_set, all_items)

    excluded = config.get("exclude_champions", {})
    variant_groups = config.get("variant_groups", [])
    variant_source_ids = {source_id for group in variant_groups for source_id in group["source_ids"]}
    raw_champions = {champion["apiName"]: champion for champion in source_set["champions"]}
    champion_candidates = [
        champion for champion in source_set["champions"] if champion["apiName"] not in excluded
    ]

    champion_rows: list[dict] = []
    dynamic_rows: list[dict] = []
    inventory: list[dict] = []
    assets: dict[str, str] = {}
    adjustments = config.get("champion_adjustments", {})

    def trait_ids(champion: dict) -> list[str]:
        try:
            return [trait_api_by_name[name] for name in champion.get("traits") or []]
        except KeyError as error:
            raise ValueError(
                f"Champion {champion['apiName']} references unknown localized Trait {error.args[0]!r}"
            ) from error

    for source_id, reason in excluded.items():
        inventory.append(
            {"kind": "CHAMPION", "source_id": source_id, "status": "EXCLUDED", "reason": reason}
        )

    for champion in champion_candidates:
        source_id = champion["apiName"]
        if source_id in variant_source_ids:
            continue
        row = {
            "id": source_id,
            "name_key": f"champion.{_slug(source_id)}.name",
            "cost": champion["cost"],
            "traits": trait_ids(champion),
            "trait_points": {},
            "board_slots": 1,
            "image": f"assets/champions/{_slug(source_id)}.png",
            "display_order": len(champion_rows) * 10 + 10,
            "search_aliases": [],
        }
        adjustment = dict(adjustments.get(source_id, {}))
        points_by_name = adjustment.pop("trait_points_by_name", {})
        if points_by_name:
            adjustment["trait_points"] = {
                trait_api_by_name[name]: points for name, points in points_by_name.items()
            }
        row.update(adjustment)
        champion_rows.append(row)
        inventory.append(
            {"kind": "CHAMPION", "source_id": source_id, "status": "INCLUDED", "target_id": source_id}
        )

    for group in variant_groups:
        variants = [raw_champions[source_id] for source_id in group["source_ids"]]
        trait_sets = [set(trait_ids(champion)) for champion in variants]
        base_traits = set.intersection(*trait_sets)
        choice_traits = sorted(set.union(*trait_sets) - base_traits)
        target_id = group["target_id"]
        champion_rows.append(
            {
                "id": target_id,
                "name_key": f"champion.{_slug(target_id)}.name",
                "cost": variants[0]["cost"],
                "traits": sorted(base_traits),
                "trait_points": {},
                "board_slots": 1,
                "image": f"assets/champions/{_slug(target_id)}.png",
                "display_order": len(champion_rows) * 10 + 10,
                "search_aliases": group.get("search_aliases", []),
            }
        )
        dynamic_rows.append(
            {
                "champion_id": target_id,
                "selection_rule": group["selection_rule"],
                "choices": choice_traits,
                "selection_scope": group.get("selection_scope", "PER_INSTANCE"),
                "exact_count": group.get("exact_count"),
                "choice_points": {trait_id: group.get("choice_points", 1) for trait_id in choice_traits},
            }
        )
        for source_id in group["source_ids"]:
            inventory.append(
                {"kind": "CHAMPION", "source_id": source_id, "status": "INCLUDED", "target_id": target_id}
            )

    for rule in config.get("dynamic_traits", []):
        choices = [trait_api_by_name[name] for name in rule["choice_trait_names"]]
        dynamic_rows.append(
            {
                "champion_id": rule["champion_id"],
                "selection_rule": rule["selection_rule"],
                "choices": choices,
                "selection_scope": rule.get("selection_scope", "PER_CHAMPION"),
                "exact_count": rule.get("exact_count"),
                "choice_points": {trait_id: rule.get("choice_points", 1) for trait_id in choices},
            }
        )


    trait_adjustments = {}
    for trait_name, adjustment in config.get("trait_adjustments_by_name", {}).items():
        if trait_name not in trait_api_by_name:
            raise ValueError(f"Trait adjustment references unknown Trait name: {trait_name}")
        trait_adjustments[trait_api_by_name[trait_name]] = adjustment

    trait_rows = []
    for index, trait in enumerate(source_set["traits"]):
        source_id = trait["apiName"]
        adjustment = trait_adjustments.get(source_id, {})
        breakpoints_by_count: dict[int, dict] = {}
        for effect in trait.get("effects") or []:
            count = int(effect.get("minUnits") or 0)
            if count >= 1:
                breakpoints_by_count[count] = {
                    "count": count,
                    "style": f"tier_{int(effect.get('style') or 1)}",
                }
        breakpoints = adjustment.get("breakpoints") or [
            breakpoints_by_count[count] for count in sorted(breakpoints_by_count)
        ]
        if not breakpoints:
            breakpoints = [{"count": 1, "style": "tier_1"}]
        derived_requirements = {
            trait_api_by_name[name]: count
            for name, count in adjustment.get("derived_requirements_by_name", {}).items()
        }
        trait_rows.append(
            {
                "id": source_id,
                "name_key": f"trait.{_slug(source_id)}.name",
                "description_key": f"trait.{_slug(source_id)}.description",
                "icon": f"assets/traits/{_slug(source_id)}.png",
                "display_order": index * 10 + 10,
                "breakpoints": breakpoints,
                "counting_mode": "UNIQUE_CHAMPION",
                "activation_mode": adjustment.get("activation_mode", "AT_LEAST"),
                "derived_requirements": derived_requirements,
            }
        )
        inventory.append(
            {"kind": "TRAIT", "source_id": source_id, "status": "INCLUDED", "target_id": source_id}
        )

    item_rows = []
    for index, source_id in enumerate(sorted(item_ids)):
        item = all_items[source_id]
        item_rows.append(
            {
                "id": source_id,
                "name_key": f"item.{_slug(source_id)}.name",
                "description_key": f"item.{_slug(source_id)}.description",
                "icon": f"assets/items/{_slug(source_id)}.png",
                "category": _category(item),
                "composition": item.get("composition") or [],
                "associated_traits": [value for value in item.get("associatedTraits") or [] if value in traits_by_api],
                "display_order": index * 10 + 10,
                "tags": [_slug(str(tag)) for tag in item.get("tags") or [] if str(tag).strip()],
            }
        )
        inventory.append(
            {"kind": "ITEM", "source_id": source_id, "status": "INCLUDED", "target_id": source_id}
        )

    _require_item_categories(item_rows, config.get("required_item_categories", []))

    locale_catalogs: dict[str, dict[str, str]] = {}
    for locale in locales:
        set_name_key = f"set.{_slug(config["set_id"])}.name"
        catalog = {set_name_key: localized_sets[locale].get("name") or config["display_name"]}
        source_champs = {champion["apiName"]: champion for champion in localized_sets[locale]["champions"]}
        source_items = {item["apiName"]: item for item in cdragon[locale].get("items", [])}
        for row in champion_rows:
            group = next((value for value in variant_groups if value["target_id"] == row["id"]), None)
            source_id = group["image_source_id"] if group else row["id"]
            name = source_champs[source_id].get("name") or source_champs[source_id]["apiName"]
            if group:
                name = group.get("localized_names", {}).get(locale, group.get("display_name", "Lux"))
            catalog[row["name_key"]] = name
        for row in trait_rows:
            trait = localized_traits[locale][row["id"]]
            dd = ddragon[f"trait:{locale}"].get(row["id"], {})
            catalog[row["name_key"]] = dd.get("name") or trait.get("name") or row["id"]
            catalog[row["description_key"]] = trait.get("desc") or "No source description available."
        for row in item_rows:
            item = source_items.get(row["id"]) or all_items[row["id"]]
            dd = ddragon[f"item:{locale}"].get(row["id"], {})
            catalog[row["name_key"]] = dd.get("name") or item.get("name") or row["id"]
            catalog[row["description_key"]] = item.get("desc") or "No source description available."
        locale_catalogs[locale] = catalog

    planner_rows = planner_payload.get(mutator) or []
    planner_by_character = {row.get("character_id"): row for row in planner_rows}
    planner_ids: dict[str, str] = {}
    for champion in champion_rows:
        group = next((value for value in variant_groups if value["target_id"] == champion["id"]), None)
        source_id = group["image_source_id"] if group else champion["id"]
        planner = planner_by_character.get(source_id)
        if planner and planner.get("team_planner_code") is not None:
            planner_ids[champion["id"]] = format(int(planner["team_planner_code"]), "03x")

    spec_dir.mkdir(parents=True, exist_ok=True)
    with httpx.Client(timeout=REQUEST_TIMEOUT, headers={"User-Agent": "tft-team-builder-set-import/0.7"}) as client:
        for champion in champion_rows:
            group = next((value for value in variant_groups if value["target_id"] == champion["id"]), None)
            source_id = group["image_source_id"] if group else champion["id"]
            c_record = raw_champions[source_id]
            dd_record = ddragon[f"champion:{default_locale}"].get(source_id, {})
            url = _dd_asset_url(config["ddragon_version"], dd_record) or _cdragon_asset_url(
                config["cdragon_version"], c_record.get("squareIcon") or c_record.get("icon")
            )
            revision = (
                config["ddragon_version"]
                if "ddragon.leagueoflegends.com" in url
                else config["cdragon_version"]
            )
            _asset(
                client, cache_dir, spec_dir, sources, f"champion_asset_{source_id}",
                revision, None, url, champion["image"]
            )
            assets[champion["image"]] = champion["image"]

        for trait in trait_rows:
            source = traits_by_api[trait["id"]]
            dd_record = ddragon[f"trait:{default_locale}"].get(trait["id"], {})
            url = _dd_asset_url(config["ddragon_version"], dd_record) or _cdragon_asset_url(
                config["cdragon_version"], source["icon"]
            )
            revision = (
                config["ddragon_version"]
                if "ddragon.leagueoflegends.com" in url
                else config["cdragon_version"]
            )
            _asset(
                client, cache_dir, spec_dir, sources, f"trait_asset_{trait['id']}",
                revision, None, url, trait["icon"]
            )
            assets[trait["icon"]] = trait["icon"]

        for item in item_rows:
            source = all_items[item["id"]]
            dd_record = ddragon[f"item:{default_locale}"].get(item["id"], {})
            url = _dd_asset_url(config["ddragon_version"], dd_record) or _cdragon_asset_url(
                config["cdragon_version"], source["icon"]
            )
            revision = (
                config["ddragon_version"]
                if "ddragon.leagueoflegends.com" in url
                else config["cdragon_version"]
            )
            _asset(
                client, cache_dir, spec_dir, sources, f"item_asset_{item['id']}",
                revision, None, url, item["icon"]
            )
            assets[item["icon"]] = item["icon"]

    spec = {
        "schema_version": SOURCE_SPEC_SCHEMA_VERSION,
        "manifest": {
            "schema_version": SET_SCHEMA_VERSION,
            "set_id": config["set_id"],
            "display_name_key": f"set.{_slug(config['set_id'])}.name",
            "revision": config["revision"],
            "default_locale": default_locale,
            "supported_locales": locales,
            "champions_file": "data/champions.json",
            "items_file": "data/items.json",
            "traits_file": "data/traits.json",
            "dynamic_traits_file": "data/dynamic_traits.json",
            "team_planner_file": "data/team_planner.json",
            "source_inventory_file": "reports/source_inventory.json",
            "overview_file": "SET_OVERVIEW.md",
            "source_manifest_file": "source_manifest.json",
            "locales_dir": "locales",
            "assets_dir": "assets",
            "team_planner_supported": len(planner_ids) == len(champion_rows),
        },
        "champions": champion_rows,
        "items": item_rows,
        "traits": trait_rows,
        "dynamic_traits": dynamic_rows,
        "team_planner": {"codec": "riot_v2_12bit" if planner_ids else None, "champion_ids": planner_ids},
        "source_inventory": inventory,
        "sources": sources,
        "locales": locale_catalogs,
        "assets": assets,
    }
    (spec_dir / "set_spec.json").write_bytes(canonical_json_bytes(spec))


def _check_or_write_lock(config_path: Path, spec_dir: Path, refresh: bool) -> None:
    """Pin every downloaded payload and asset by SHA-256 after the first reviewed import."""

    spec = _json(spec_dir / "set_spec.json")
    current = {record["id"]: record for record in spec["sources"]}
    lock_path = config_path.with_name("source_lock.json")
    if lock_path.is_file() and not refresh:
        locked = _json(lock_path)
        expected = {record["id"]: record for record in locked["sources"]}
        if set(expected) != set(current):
            raise ValueError("source inventory differs from source_lock.json; review with --refresh-lock")
        changed = [
            source_id
            for source_id in sorted(current)
            if expected[source_id]["sha256"] != current[source_id]["sha256"]
        ]
        if changed:
            raise ValueError(
                "downloaded source hashes differ from source_lock.json: " + ", ".join(changed)
            )
        return

    payload = {
        "set_id": spec["manifest"]["set_id"],
        "revision": spec["manifest"]["revision"],
        "sources": [current[source_id] for source_id in sorted(current)],
    }
    lock_path.write_bytes(canonical_json_bytes(payload))
    print(f"Wrote source lock: {lock_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--cache-dir", type=Path, default=Path(".cache/set_import"))
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--refresh-lock", action="store_true")
    args = parser.parse_args()

    config = _json(args.config)
    with tempfile.TemporaryDirectory(prefix=f"{config['set_id']}-source-") as temporary:
        spec_dir = Path(temporary)
        _build_spec(config, args.cache_dir, spec_dir)
        _check_or_write_lock(args.config, spec_dir, args.refresh_lock)
        build_set_from_local_spec(spec_dir, args.output, overwrite=args.overwrite)
    print(f"Built validated Set package: {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
