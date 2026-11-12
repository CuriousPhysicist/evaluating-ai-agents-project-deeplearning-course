from __future__ import annotations

import os
import socket
import subprocess
import sys
import tempfile
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

import pytest
from opentelemetry import trace
from phoenix.client import Client

from agent_evals.recording import ensure_phoenix


@dataclass(frozen=True)
class IsolatedPhoenix:
    client: Client
    base_url: str
    project_name: str
    database_path: Path


def _available_ports() -> tuple[int, int]:
    listeners: list[socket.socket] = []
    try:
        for _ in range(2):
            listener = socket.socket()
            listener.bind(("127.0.0.1", 0))
            listeners.append(listener)
        return int(listeners[0].getsockname()[1]), int(listeners[1].getsockname()[1])
    finally:
        for listener in listeners:
            listener.close()


def _cleanup_temporary_directory(directory: tempfile.TemporaryDirectory[str]) -> None:
    last_error: PermissionError | None = None
    for _ in range(20):
        try:
            directory.cleanup()
            return
        except PermissionError as error:
            last_error = error
            time.sleep(0.25)
    if last_error is not None:
        raise last_error


@pytest.fixture(scope="session")
def isolated_phoenix() -> IsolatedPhoenix:
    port, grpc_port = _available_ports()
    temporary_directory = tempfile.TemporaryDirectory(prefix="agent-evals-phoenix-")
    root = Path(temporary_directory.name)
    database_path = root / "phoenix.db"
    base_url = f"http://127.0.0.1:{port}"
    project_name = f"agent-evals-test-{uuid.uuid4().hex}"

    safe_environment_keys = {
        "APPDATA",
        "COMSPEC",
        "HOME",
        "HOMEDRIVE",
        "HOMEPATH",
        "LOCALAPPDATA",
        "PATH",
        "SYSTEMROOT",
        "TEMP",
        "TMP",
        "USERPROFILE",
        "VIRTUAL_ENV",
        "WINDIR",
    }
    environment = {
        key: value
        for key, value in os.environ.items()
        if key.upper() in safe_environment_keys
    }
    environment.update(
        {
            "PHOENIX_HOST": "127.0.0.1",
            "PHOENIX_PORT": str(port),
            "PHOENIX_GRPC_PORT": str(grpc_port),
            "PHOENIX_WORKING_DIR": str(root),
            "PHOENIX_SQL_DATABASE_URL": f"sqlite:///{database_path.as_posix()}",
            "PHOENIX_ALLOW_EXTERNAL_RESOURCES": "false",
            "PHOENIX_DISABLE_MODEL_COST_AUTO_UPDATE": "true",
        }
    )
    for key in ("OPENAI_API_KEY", "PHOENIX_API_KEY", "PHOENIX_COLLECTOR_ENDPOINT", "OTEL_EXPORTER_OTLP_ENDPOINT"):
        environment.pop(key, None)

    log_path = root / "phoenix.log"
    log_file = log_path.open("w", encoding="utf-8")
    process: subprocess.Popen | None = None
    tracing_registered = False

    def server_log() -> str:
        log_file.flush()
        return log_path.read_text(encoding="utf-8", errors="replace")[-5000:]

    try:
        process = subprocess.Popen(
            [sys.executable, "-m", "phoenix.server.main", "serve"],
            cwd=root,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=log_file,
            stderr=subprocess.STDOUT,
        )
        client = Client(base_url=base_url)
        deadline = time.monotonic() + 90
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError(f"Isolated Phoenix server exited during startup:\n{server_log()}")
            try:
                client.projects.list()
                break
            except Exception:
                time.sleep(0.5)
        else:
            raise RuntimeError(f"Isolated Phoenix server did not become ready:\n{server_log()}")

        client = ensure_phoenix(base_url=base_url, project_name=project_name)
        tracing_registered = True
        yield IsolatedPhoenix(client, base_url, project_name, database_path)
    finally:
        try:
            if tracing_registered:
                if not trace.get_tracer_provider().force_flush(timeout_millis=10_000):
                    raise RuntimeError("Phoenix trace exporter did not flush before server shutdown")
                trace.get_tracer_provider().shutdown()
        finally:
            if process is not None and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=10)
            try:
                log_file.close()
            finally:
                _cleanup_temporary_directory(temporary_directory)
