"""Build one pinned TFT Set package from Riot Data Dragon and CommunityDragon.

This is a developer-only acquisition tool. The application runtime never imports it and never
uses the network. A source configuration selects one exact Riot/CDragon revision and contains
only the small explicit exceptions that cannot be derived safely from upstream Set metadata.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlparse

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


def _fnv1a_32(value: str) -> str:
    """Return Riot's lowercase 32-bit FNV-1a BIN-field hash as eight hex digits."""

    result = 0x811C9DC5
    for byte in value.casefold().encode("utf-8"):
        result = ((result ^ byte) * 0x01000193) & 0xFFFFFFFF
    return f"{result:08x}"


def _effect_variable(effect: dict, name: str, overrides: dict[str, float]) -> float | None:
    """Resolve one tooltip variable from readable or hashed CommunityDragon effect keys."""

    for key, value in overrides.items():
        if key.casefold() == name.casefold():
            return float(value)
    variables = effect.get("variables") or {}
    for key, value in variables.items():
        if key.casefold() == name.casefold():
            return float(value)
    value = variables.get("{" + _fnv1a_32(name) + "}")
    return None if value is None else float(value)


def _format_trait_number(value: float) -> str:
    """Hide binary floating-point noise while preserving meaningful decimal trait values."""

    rounded = round(value, 4)
    if abs(rounded - round(rounded)) < 1e-4:
        return str(round(rounded))
    return f"{rounded:.4f}".rstrip("0").rstrip(".")


_STAT_ICON_LABELS = {
    "en_US": {
        "scaleAD": "AD",
        "scaleAP": "AP",
        "scaleAS": "Attack Speed",
        "scaleHealth": "Health",
        "scaleArmor": "Armor",
        "scaleMR": "Magic Resist",
        "scaleManaRegen": "Mana Regen",
        "scaleDR": "Durability",
    },
    "de_DE": {
        "scaleAD": "Angriffsschaden",
        "scaleAP": "F\u00e4higkeitsst\u00e4rke",
        "scaleAS": "Angriffstempo",
        "scaleHealth": "Leben",
        "scaleArmor": "R\u00fcstung",
        "scaleMR": "Magieresistenz",
        "scaleManaRegen": "Manaregeneration",
        "scaleDR": "Durchhalteverm\u00f6gen",
    },
}


def _plain_trait_text(value: str, locale: str) -> str:
    """Convert Riot tooltip markup to stable plain text suitable for locale JSON and the GUI."""

    labels = _STAT_ICON_LABELS.get(locale, _STAT_ICON_LABELS["en_US"])
    value = re.sub(r"<br\s*/?>", "\n", value, flags=re.IGNORECASE)
    combined_resists = {
        "en_US": "Armor and Magic Resist",
        "de_DE": "R\u00fcstung und Magieresistenz",
    }.get(locale, "Armor and Magic Resist")
    value = value.replace("%i:scaleArmor%%i:scaleMR%", f" {combined_resists} ")
    value = re.sub(
        r"%i:([^%]+)%",
        lambda match: " " + labels.get(match.group(1), match.group(1)) + " ",
        value,
    )
    value = re.sub(r"<[^>]+>", "", value)
    value = html.unescape(value).replace("\xa0", " ")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in value.splitlines()]
    return "\n".join(line for line in lines if line).strip()


def _render_trait_template(
    template: str,
    effect: dict,
    *,
    count: int | None,
    overrides: dict[str, float] | None = None,
    locale: str = "en_US",
) -> str:
    """Resolve Riot ``@Variable@`` tooltip expressions without a runtime markup interpreter."""

    override_values = overrides or {}

    def replace(match: re.Match[str]) -> str:
        expression = match.group(1)
        parts = expression.split("*", 1)
        name = parts[0]
        if name == "MinUnits":
            if count is None:
                raise ValueError("trait tooltip MinUnits has no breakpoint count")
            value = float(count)
        else:
            resolved = _effect_variable(effect, name, override_values)
            if resolved is None:
                raise ValueError(f"unresolved Trait tooltip variable {name!r}")
            value = resolved
        if len(parts) == 2:
            value *= float(parts[1])
        return _format_trait_number(value)

    return _plain_trait_text(re.sub(r"@([^@]+)@", replace, template), locale)


def _render_item_description(item: dict, *, locale: str) -> str:
    """Resolve Item tooltip variables and strip source markup before locale packaging."""

    description = item.get("desc") or ""
    if not description:
        return ""
    return _render_trait_template(
        description,
        {"variables": item.get("effects") or {}},
        count=None,
        locale=locale,
    )


def _trait_display_texts(
    trait: dict,
    breakpoints: list[dict],
    variable_overrides: dict[str, dict[str, float]],
    *,
    locale: str = "en_US",
) -> tuple[str, dict[int, str]]:
    """Render one localized Trait summary and its informative breakpoint-specific effects."""

    description = trait.get("desc") or ""
    rows = re.findall(r"<row>(.*?)</row>", description, flags=re.IGNORECASE | re.DOTALL)
    effects = trait.get("effects") or []

    # Preamble variables can be invariant across breakpoints. Resolve each
    # from the first source effect that carries it so summaries stay compact and non-repetitive.
    summary_template = description.split("<row>", 1)[0] if rows else description
    summary_effect: dict = {"variables": {}}
    for expression in re.findall(r"@([^@]+)@", summary_template):
        name = expression.split("*", 1)[0]
        if name == "MinUnits":
            continue
        for effect in effects:
            value = _effect_variable(effect, name, {})
            if value is not None:
                summary_effect["variables"][name] = value
                break
    summary = (
        _render_trait_template(summary_template, summary_effect, count=None, locale=locale)
        if summary_template
        else ""
    )

    # Duplicate minUnits occur for special stateful traits such as Rival. Matching by source
    # order and keeping the last row for a count mirrors the source breakpoint selection logic.
    rows_by_count: dict[int, tuple[str, dict]] = {}
    for row, effect in zip(rows, effects, strict=False):
        source_count = int(effect.get("minUnits") or 0)
        if source_count >= 1:
            rows_by_count[source_count] = (row, effect)

    rendered_breakpoints: dict[int, str] = {}
    for breakpoint in breakpoints:
        count = int(breakpoint["count"])
        row_and_effect = rows_by_count.get(count)
        if row_and_effect is None:
            continue
        row, effect = row_and_effect
        overrides = variable_overrides.get(str(count), {})
        rendered = _render_trait_template(
            row, effect, count=count, overrides=overrides, locale=locale
        )
        rendered = re.sub(rf"^\(\s*{count}\s*\)\s*", "", rendered).strip()
        if rendered:
            rendered_breakpoints[count] = rendered
    if not summary and rendered_breakpoints:
        summary = next(iter(rendered_breakpoints.values()))
    return summary, rendered_breakpoints


def _trait_variable_overrides(
    config: dict, trait_name: str, breakpoint_counts: set[str] | None = None
) -> dict[str, dict[str, float]]:
    """Return one reviewed Trait override map and validate its provenance metadata."""

    record = config.get("trait_variable_overrides_by_name", {}).get(trait_name)
    if record is None:
        return {}
    override_source_id = record.get("source")
    if override_source_id not in config.get("trait_variable_override_sources", {}):
        raise ValueError(
            f"Trait variable override for {trait_name!r} has unknown source: {override_source_id!r}"
        )
    reason = record.get("reason")
    if not isinstance(reason, str) or not reason.strip():
        raise ValueError(f"Trait variable override for {trait_name!r} requires a reason")
    values = record.get("breakpoints")
    if not isinstance(values, dict):
        raise ValueError(f"Trait variable override for {trait_name!r} requires breakpoint values")
    if breakpoint_counts is not None:
        unknown_counts = sorted(set(values) - breakpoint_counts)
        if unknown_counts:
            raise ValueError(
                f"Trait variable overrides for {trait_name!r} reference unknown breakpoints: "
                + ", ".join(unknown_counts)
            )
    return values


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
    """Index Data Dragon records by their stable public ID instead of archive path keys."""

    data = payload.get("data")
    if not isinstance(data, dict):
        raise ValueError("Data Dragon payload has no data object")
    records: dict[str, dict] = {}
    for archive_key, record in data.items():
        record_id = record.get("id") if isinstance(record, dict) else None
        if not isinstance(record_id, str) or not record_id:
            raise ValueError(f"Data Dragon record {archive_key!r} has no stable id")
        if record_id in records:
            raise ValueError(f"Data Dragon contains duplicate record id {record_id!r}")
        records[record_id] = record
    return records


def _dd_asset_url(version: str, record: dict) -> tuple[str, str]:
    """Return one pinned individual Data Dragon asset URL for an image record."""

    image = record.get("image") or {}
    group = image.get("group")
    full = image.get("full")
    if not group or not full:
        raise ValueError(f"Data Dragon record {record.get('id')!r} has no full image metadata")
    source_key = f"{group}/{full}"
    suffix = hashlib.sha256(source_key.encode("utf-8")).hexdigest()[:12]
    source_id = f"ddragon_asset_{_slug(group)}_{_slug(full)}_{suffix}"
    url = (
        f"https://ddragon.leagueoflegends.com/cdn/{version}/img/"
        f"{quote(str(group), safe='')}/{quote(str(full), safe='')}"
    )
    return source_id, url


def _append_source_once(sources: list[dict], record: dict) -> None:
    """Add one provenance source while rejecting ID collisions with different content."""

    existing = next((value for value in sources if value["id"] == record["id"]), None)
    if existing is None:
        sources.append(record)
    elif existing != record:
        raise ValueError(f"source id {record['id']!r} resolves to inconsistent metadata")


def _dd_full_asset(
    client: httpx.Client,
    cache_dir: Path,
    spec_dir: Path,
    sources: list[dict],
    version: str,
    record: dict,
    target: str,
) -> None:
    """Copy one pinned individual Data Dragon PNG into the local Set source spec."""

    source_id, url = _dd_asset_url(version, record)
    downloaded = _download(client, cache_dir, source_id, url, MAX_IMAGE_BYTES)
    payload = downloaded.read_bytes()
    if payload[:8] != PNG_SIGNATURE:
        raise ValueError(f"Data Dragon asset is not a PNG: {url}")
    _append_source_once(sources, _source_record(source_id, url, version, None, downloaded))

    destination = spec_dir / target
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(payload)


def _cdragon_game_asset_url(version: str, game_path: str) -> tuple[str, str]:
    """Return a pinned CommunityDragon PNG URL for one exported game texture path."""

    normalized = game_path.replace("\\", "/").casefold()
    if not normalized.startswith("assets/"):
        raise ValueError(f"CommunityDragon game asset path must start with assets/: {game_path!r}")
    if normalized.endswith(".tex"):
        normalized = normalized[:-4] + ".png"
    if not normalized.endswith(".png"):
        raise ValueError(f"CommunityDragon game asset is not an exported PNG path: {game_path!r}")
    suffix = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:12]
    source_id = f"cdragon_asset_{_slug(Path(normalized).name)}_{suffix}"
    url = f"https://raw.communitydragon.org/{version}/game/{quote(normalized, safe='/')}"
    return source_id, url


def _cdragon_game_asset(
    client: httpx.Client,
    cache_dir: Path,
    spec_dir: Path,
    sources: list[dict],
    version: str,
    game_path: str,
    target: str,
) -> None:
    """Copy one pinned exported CommunityDragon game PNG into the local Set source spec."""

    source_id, url = _cdragon_game_asset_url(version, game_path)
    downloaded = _download(client, cache_dir, source_id, url, MAX_IMAGE_BYTES)
    payload = downloaded.read_bytes()
    if payload[:8] != PNG_SIGNATURE:
        raise ValueError(f"CommunityDragon asset is not a PNG: {url}")
    _append_source_once(sources, _source_record(source_id, url, version, None, downloaded))

    destination = spec_dir / target
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(payload)


def _trait_name_map(set_data: dict) -> tuple[dict[str, dict], dict[str, str]]:
    traits = set_data.get("traits") or []
    by_api = {trait["apiName"]: trait for trait in traits}
    by_name = {trait["name"]: trait["apiName"] for trait in traits}
    if len(by_api) != len(traits) or len(by_name) != len(traits):
        raise ValueError("Trait IDs and localized names must be unique in the source Set")
    return by_api, by_name


def _retained_item_categories(
    source_set: dict, all_items: dict[str, dict], policy: dict
) -> dict[str, str]:
    """Select the reviewed user-facing Set item inventory from broad upstream records.

    CommunityDragon intentionally exposes many engine objects, aliases, Wisps and temporary
    rewards through the Set item list. The runtime package keeps only the stable item families
    that a player can identify as actual Set item references. Source-specific identifiers stay
    in the declarative Set configuration instead of leaking into application code.
    """

    declared = set(source_set.get("items") or [])
    missing = sorted(source_id for source_id in declared if source_id not in all_items)
    if missing:
        raise ValueError("Set item records are missing from CommunityDragon: " + ", ".join(missing))

    excluded = set(policy.get("exclude_ids", []))
    explicit = {
        source_id: category
        for category, source_ids in policy.get("explicit_ids", {}).items()
        for source_id in source_ids
    }
    unknown_explicit = sorted(set(explicit) - declared)
    if unknown_explicit:
        raise ValueError(
            "explicit retained Item IDs are missing from the Set: " + ", ".join(unknown_explicit)
        )
    unknown_excluded = sorted(excluded - declared)
    if unknown_excluded:
        raise ValueError(
            "explicit excluded Item IDs are missing from the Set: " + ", ".join(unknown_excluded)
        )

    component_prefix = policy["component_prefix"]
    craftable_prefix = policy["craftable_prefix"]
    emblem_prefix = policy["emblem_prefix"]
    artifact_prefixes = tuple(policy["artifact_prefixes"])
    radiant_prefix = policy["radiant_prefix"]
    radiant_tag = policy["radiant_tag"]

    retained: dict[str, str] = {}
    for source_id in sorted(declared):
        if source_id in excluded:
            continue
        item = all_items[source_id]
        tags = set(item.get("tags") or [])
        if source_id in explicit:
            retained[source_id] = explicit[source_id]
        elif source_id.startswith(component_prefix) and "component" in tags:
            retained[source_id] = "COMPONENT"
        elif source_id.startswith(emblem_prefix):
            retained[source_id] = "EMBLEM"
        elif source_id.startswith(artifact_prefixes):
            retained[source_id] = "ARTIFACT"
        elif source_id.startswith(radiant_prefix) and radiant_tag in tags:
            retained[source_id] = "RADIANT"
        elif source_id.startswith(craftable_prefix) and item.get("composition"):
            retained[source_id] = "CRAFTABLE"

    # A retained recipe must never point back into the discarded alias/internal inventory.
    for source_id in sorted(retained):
        for component in all_items[source_id].get("composition") or []:
            if component not in retained:
                raise ValueError(
                    f"retained Item {source_id!r} references non-retained component {component!r}"
                )
    return retained


def _require_item_category_counts(
    categories: dict[str, str], expected_counts: dict[str, int]
) -> None:
    """Fail acquisition when the reviewed current-item boundary drifts upstream."""

    actual: dict[str, int] = {}
    for category in categories.values():
        actual[category] = actual.get(category, 0) + 1
    if actual != expected_counts:
        raise ValueError(
            f"retained Item category counts differ: expected {expected_counts}; got {actual}"
        )


def _require_expected_count(label: str, actual: int, expected: int | None) -> None:
    """Turn silent upstream roster drift into an explicit review failure."""

    if expected is not None and actual != expected:
        raise ValueError(f"expected {expected} {label}; got {actual}")


def _variant_records(group: dict, raw_champions: dict[str, dict]) -> list[dict]:
    """Resolve one explicit variant group and report every missing source ID together."""

    missing = [source_id for source_id in group["source_ids"] if source_id not in raw_champions]
    if missing:
        raise ValueError(
            f"variant group {group['target_id']!r} references missing Champion source IDs: "
            + ", ".join(missing)
        )
    records = [raw_champions[source_id] for source_id in group["source_ids"]]
    costs = {record["cost"] for record in records}
    if len(costs) != 1:
        raise ValueError(f"variant group {group['target_id']!r} has inconsistent Champion costs")
    if group["image_source_id"] not in group["source_ids"]:
        raise ValueError(
            f"variant group {group['target_id']!r} image_source_id must be one of source_ids"
        )
    return records


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

    with httpx.Client(
        timeout=REQUEST_TIMEOUT, headers={"User-Agent": "tft-team-builder-set-import/0.7"}
    ) as client:
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
                    _source_record(f"ddragon_{kind}_{locale}", url, ddragon_version, locale, path)
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
    item_categories = _retained_item_categories(source_set, all_items, config["item_retention"])
    _require_item_category_counts(item_categories, config["expected_items_by_category"])

    excluded = config.get("exclude_champions", {})
    variant_groups = config.get("variant_groups", [])
    variant_source_ids = {
        source_id for group in variant_groups for source_id in group["source_ids"]
    }
    raw_champions = {champion["apiName"]: champion for champion in source_set["champions"]}
    _require_expected_count(
        "raw Champion records", len(raw_champions), config.get("expected_source_champions")
    )
    _require_expected_count(
        "Trait records", len(source_set["traits"]), config.get("expected_traits")
    )

    missing_exclusions = sorted(set(excluded) - raw_champions.keys())
    if missing_exclusions:
        raise ValueError(
            "excluded Champion source IDs are missing upstream: " + ", ".join(missing_exclusions)
        )
    overlap = sorted(set(excluded) & variant_source_ids)
    if overlap:
        raise ValueError(
            "Champion source IDs cannot be both excluded and variant members: " + ", ".join(overlap)
        )
    if len(variant_source_ids) != sum(len(group["source_ids"]) for group in variant_groups):
        raise ValueError("Champion source IDs may belong to only one variant group")
    for group in variant_groups:
        _variant_records(group, raw_champions)

    champion_candidates = [
        champion for champion in source_set["champions"] if champion["apiName"] not in excluded
    ]

    champion_rows: list[dict] = []
    dynamic_rows: list[dict] = []
    inventory: list[dict] = []
    assets: dict[str, str] = {}
    variant_choice_sources: dict[str, dict[str, str]] = {}
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
            {
                "kind": "CHAMPION",
                "source_id": source_id,
                "status": "INCLUDED",
                "target_id": source_id,
            }
        )

    for group in variant_groups:
        variants = _variant_records(group, raw_champions)
        trait_sets = [set(trait_ids(champion)) for champion in variants]
        base_traits = set.intersection(*trait_sets)
        choice_traits = sorted(set.union(*trait_sets) - base_traits)
        target_id = group["target_id"]

        # Each visual source variant must represent either the base form or exactly one dynamic
        # Trait choice. This keeps the source mapping reviewable and makes portrait switching
        # deterministic without encoding Lux-specific rules in runtime code.
        choice_sources: dict[str, str] = {}
        for variant in variants:
            selected = set(trait_ids(variant)) - base_traits
            if not selected:
                continue
            if len(selected) != 1:
                raise ValueError(
                    f"variant source {variant['apiName']!r} must add exactly one choice Trait"
                )
            trait_id = next(iter(selected))
            if trait_id in choice_sources:
                raise ValueError(
                    f"variant group {target_id!r} has multiple source records for Trait {trait_id!r}"
                )
            choice_sources[trait_id] = variant["apiName"]
        if set(choice_sources) != set(choice_traits):
            raise ValueError(
                f"variant group {target_id!r} cannot map every choice to one source image"
            )
        variant_choice_sources[target_id] = choice_sources
        choice_images = {
            trait_id: (f"assets/champions/variants/{_slug(target_id)}--{_slug(trait_id)}.png")
            for trait_id in choice_traits
        }

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
                "choice_points": {
                    trait_id: group.get("choice_points", 1) for trait_id in choice_traits
                },
                "choice_images": choice_images,
            }
        )
        for source_id in group["source_ids"]:
            inventory.append(
                {
                    "kind": "CHAMPION",
                    "source_id": source_id,
                    "status": "INCLUDED",
                    "target_id": target_id,
                }
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
                "choice_images": {},
            }
        )

    _require_expected_count(
        "logical Champions", len(champion_rows), config.get("expected_logical_champions")
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

        known_counts = {str(value["count"]) for value in breakpoints}
        variable_overrides = _trait_variable_overrides(config, trait["name"], known_counts)
        _summary, breakpoint_texts = _trait_display_texts(
            localized_traits[default_locale][source_id],
            breakpoints,
            variable_overrides,
            locale=default_locale,
        )
        for breakpoint in breakpoints:
            count = int(breakpoint["count"])
            if count in breakpoint_texts:
                breakpoint["description_key"] = (
                    f"trait.{_slug(source_id)}.breakpoint.{count}.description"
                )

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
    retained_item_ids = set(item_categories)
    for source_id in sorted(set(source_set.get("items") or []) - retained_item_ids):
        inventory.append(
            {
                "kind": "ITEM",
                "source_id": source_id,
                "status": "EXCLUDED",
                "reason": "outside reviewed user-facing item reference boundary",
            }
        )

    for index, source_id in enumerate(sorted(retained_item_ids)):
        item = all_items[source_id]
        item_rows.append(
            {
                "id": source_id,
                "name_key": f"item.{_slug(source_id)}.name",
                "description_key": f"item.{_slug(source_id)}.description",
                "icon": f"assets/items/{_slug(source_id)}.png",
                "category": item_categories[source_id],
                "composition": item.get("composition") or [],
                "associated_traits": [
                    value for value in item.get("associatedTraits") or [] if value in traits_by_api
                ],
                "display_order": index * 10 + 10,
                "tags": [_slug(str(tag)) for tag in item.get("tags") or [] if str(tag).strip()],
            }
        )
        inventory.append(
            {"kind": "ITEM", "source_id": source_id, "status": "INCLUDED", "target_id": source_id}
        )

    locale_catalogs: dict[str, dict[str, str]] = {}
    for locale in locales:
        set_name_key = f"set.{_slug(config['set_id'])}.name"
        display_name = config.get("localized_display_names", {}).get(locale, config["display_name"])
        catalog = {set_name_key: display_name}
        source_champs = {
            champion["apiName"]: champion for champion in localized_sets[locale]["champions"]
        }
        source_items = {item["apiName"]: item for item in cdragon[locale].get("items", [])}
        for row in champion_rows:
            group = next(
                (value for value in variant_groups if value["target_id"] == row["id"]), None
            )
            source_id = group["image_source_id"] if group else row["id"]
            name = source_champs[source_id].get("name") or source_champs[source_id]["apiName"]
            if group:
                name = group.get("localized_names", {}).get(
                    locale, group.get("display_name", "Lux")
                )
            catalog[row["name_key"]] = name
        for row in trait_rows:
            trait = localized_traits[locale][row["id"]]
            dd = ddragon[f"trait:{locale}"].get(row["id"], {})
            catalog[row["name_key"]] = dd.get("name") or trait.get("name") or row["id"]
            source_trait_name = traits_by_api[row["id"]]["name"]
            variable_overrides = _trait_variable_overrides(config, source_trait_name)
            summary, breakpoint_texts = _trait_display_texts(
                trait, row["breakpoints"], variable_overrides, locale=locale
            )
            catalog[row["description_key"]] = summary or "No source description available."
            for breakpoint in row["breakpoints"]:
                description_key = breakpoint.get("description_key")
                if description_key is not None:
                    catalog[description_key] = breakpoint_texts[int(breakpoint["count"])]
        for row in item_rows:
            item = source_items.get(row["id"]) or all_items[row["id"]]
            dd = ddragon[f"item:{locale}"].get(row["id"], {})
            catalog[row["name_key"]] = dd.get("name") or item.get("name") or row["id"]
            description = _render_item_description(item, locale=locale)
            catalog[row["description_key"]] = description or "No source description available."
        locale_catalogs[locale] = catalog

    planner_rows = planner_payload.get(mutator) or []
    planner_by_character = {row.get("character_id"): row for row in planner_rows}
    planner_ids: dict[str, str] = {}
    for champion in champion_rows:
        group = next(
            (value for value in variant_groups if value["target_id"] == champion["id"]), None
        )
        source_id = group["image_source_id"] if group else champion["id"]
        planner = planner_by_character.get(source_id)
        if planner and planner.get("team_planner_code") is not None:
            planner_ids[champion["id"]] = format(int(planner["team_planner_code"]), "03x")

    spec_dir.mkdir(parents=True, exist_ok=True)
    with httpx.Client(
        timeout=REQUEST_TIMEOUT, headers={"User-Agent": "tft-team-builder-set-import/0.7"}
    ) as client:
        for champion in champion_rows:
            group = next(
                (value for value in variant_groups if value["target_id"] == champion["id"]), None
            )
            source_id = group["image_source_id"] if group else champion["id"]
            dd_record = ddragon[f"champion:{default_locale}"].get(source_id)
            if dd_record is None:
                raise ValueError(f"Data Dragon has no Champion image record for {source_id!r}")
            _dd_full_asset(
                client,
                cache_dir,
                spec_dir,
                sources,
                config["ddragon_version"],
                dd_record,
                champion["image"],
            )
            assets[champion["image"]] = champion["image"]

            choice_sources = variant_choice_sources.get(champion["id"], {})
            if choice_sources:
                dynamic_rule = next(
                    rule for rule in dynamic_rows if rule["champion_id"] == champion["id"]
                )
                for trait_id, variant_source_id in sorted(choice_sources.items()):
                    variant_record = raw_champions[variant_source_id]
                    variant_image = variant_record.get("squareIcon")
                    if not variant_image:
                        raise ValueError(
                            f"CommunityDragon has no squareIcon for Champion variant "
                            f"{variant_source_id!r}"
                        )
                    target = dynamic_rule["choice_images"][trait_id]
                    _cdragon_game_asset(
                        client,
                        cache_dir,
                        spec_dir,
                        sources,
                        config["cdragon_version"],
                        variant_image,
                        target,
                    )
                    assets[target] = target

        for trait in trait_rows:
            dd_record = ddragon[f"trait:{default_locale}"].get(trait["id"])
            if dd_record is None:
                raise ValueError(f"Data Dragon has no Trait image record for {trait['id']!r}")
            _dd_full_asset(
                client,
                cache_dir,
                spec_dir,
                sources,
                config["ddragon_version"],
                dd_record,
                trait["icon"],
            )
            assets[trait["icon"]] = trait["icon"]

        for item in item_rows:
            dd_record = ddragon[f"item:{default_locale}"].get(item["id"])
            if dd_record is None:
                raise ValueError(f"Data Dragon has no Item image record for {item['id']!r}")
            _dd_full_asset(
                client,
                cache_dir,
                spec_dir,
                sources,
                config["ddragon_version"],
                dd_record,
                item["icon"],
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
            "review_file": "data/review.json" if config.get("review") is not None else None,
            "review_report_file": "SET_REVIEW.md",
            "locales_dir": "locales",
            "assets_dir": "assets",
            "team_planner_supported": len(planner_ids) == len(champion_rows),
        },
        "champions": champion_rows,
        "items": item_rows,
        "traits": trait_rows,
        "dynamic_traits": dynamic_rows,
        "team_planner": {
            "codec": "riot_v2_12bit" if planner_ids else None,
            "champion_ids": planner_ids,
        },
        "source_inventory": inventory,
        "review": config.get("review"),
        "sources": sources,
        "locales": locale_catalogs,
        "assets": assets,
    }
    (spec_dir / "set_spec.json").write_bytes(canonical_json_bytes(spec))


def _prepare_source_lock(
    config_path: Path, spec_dir: Path, refresh: bool
) -> tuple[Path, bytes | None]:
    """Validate an existing source lock or prepare bytes to commit after a successful build."""

    spec = _json(spec_dir / "set_spec.json")
    current = {record["id"]: record for record in spec["sources"]}
    lock_path = config_path.with_name("source_lock.json")
    if lock_path.is_file() and not refresh:
        locked = _json(lock_path)
        expected = {record["id"]: record for record in locked["sources"]}
        if set(expected) != set(current):
            raise ValueError(
                "source inventory differs from source_lock.json; review with --refresh-lock"
            )
        changed = [
            source_id
            for source_id in sorted(current)
            if expected[source_id]["sha256"] != current[source_id]["sha256"]
        ]
        if changed:
            raise ValueError(
                "downloaded source hashes differ from source_lock.json: " + ", ".join(changed)
            )
        return lock_path, None

    payload = {
        "set_id": spec["manifest"]["set_id"],
        "revision": spec["manifest"]["revision"],
        "sources": [current[source_id] for source_id in sorted(current)],
    }
    return lock_path, canonical_json_bytes(payload)


def _commit_source_lock(lock_path: Path, payload: bytes | None) -> None:
    """Atomically publish a prepared source lock after the runtime package is valid."""

    if payload is None:
        return
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        prefix=f".{lock_path.name}.", suffix=".tmp", dir=lock_path.parent, delete=False
    ) as handle:
        temporary = Path(handle.name)
        handle.write(payload)
        handle.flush()
    try:
        temporary.replace(lock_path)
    finally:
        temporary.unlink(missing_ok=True)
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
        lock_path, lock_payload = _prepare_source_lock(args.config, spec_dir, args.refresh_lock)
        build_set_from_local_spec(spec_dir, args.output, overwrite=args.overwrite)
        _commit_source_lock(lock_path, lock_payload)
    print(f"Built validated Set package: {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
