"""Isolate packaged Flet integration tests from normal user application data."""

from __future__ import annotations

import os
import shutil
import socket
from pathlib import Path

import flet.testing.flet_test_app as flet_test_app_module
from flet.testing.remote_tester import RemoteTester

_RUNTIME = Path(__file__).resolve().parent / ".runtime"
shutil.rmtree(_RUNTIME, ignore_errors=True)
_RUNTIME.mkdir(parents=True)
os.environ["TFT_BUILDER_DATA_DIR"] = str(_RUNTIME)


def _closed_probe_port() -> int:
    """Return a free port without leaking Flet 1.0.1's temporary probe socket."""

    with socket.socket() as probe:
        probe.bind(("", 0))
        return probe.getsockname()[1]


# Flet 1.0.1's get_free_tcp_port() leaves its probe socket open. Patch only the
# test-host module reference so ResourceWarning remains strict everywhere else.
flet_test_app_module.get_free_tcp_port = _closed_probe_port


_original_cleanup_connection = RemoteTester._cleanup_connection


def _close_remote_writer_before_cleanup(self: RemoteTester) -> None:
    """Close Flet 1.0.1's remote writer before cleanup drops its last reference."""

    writer = self._writer
    if writer is not None:
        writer.close()
    _original_cleanup_connection(self)


# Flet 1.0.1 clears a disconnected RemoteTester writer without closing it first,
# which surfaces as a strict ResourceWarning on Windows. Keep this compatibility
# shim inside the integration-test host and remove it when the upstream cleanup
# closes the writer itself.
RemoteTester._cleanup_connection = _close_remote_writer_before_cleanup
