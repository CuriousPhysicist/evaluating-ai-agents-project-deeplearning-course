from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv
from phoenix.client import Client

PROJECT_NAME = "evaluating-agent"
DEFAULT_BASE_URL = "http://127.0.0.1:6006"
_TRACING_REGISTERED = False


def _local_base_url() -> str:
    load_dotenv()
    endpoint = os.getenv("PHOENIX_COLLECTOR_ENDPOINT")
    if not endpoint:
        return DEFAULT_BASE_URL
    parsed = urlparse(endpoint)
    if parsed.hostname not in {"localhost", "127.0.0.1", "::1"}:
        raise RuntimeError(
            "This build is configured for local Phoenix. Refusing to send traces to a non-local collector."
        )
    return f"{parsed.scheme or 'http'}://{parsed.netloc}"


def ensure_phoenix() -> Client:
    global _TRACING_REGISTERED
    base_url = _local_base_url()
    client = Client(base_url=base_url)
    try:
        client.projects.list()
    except Exception:
        parsed = urlparse(base_url)
        port = parsed.port or 6006
        root = Path(__file__).resolve().parents[1]
        executable = Path(sys.executable).with_name("phoenix.exe")
        if not executable.exists():
            raise RuntimeError("Phoenix CLI is unavailable; install the declared project dependencies")
        env = os.environ.copy()
        env["PHOENIX_HOST"] = parsed.hostname or "127.0.0.1"
        env["PHOENIX_PORT"] = str(port)
        (root / "results").mkdir(exist_ok=True)
        log_file = (root / "results" / "phoenix.log").open("a", encoding="utf-8")
        flags = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        subprocess.Popen(
            [str(executable), "serve"],
            cwd=root,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            creationflags=flags,
            close_fds=True,
        )
        client = Client(base_url=base_url)
        deadline = time.monotonic() + 90
        while time.monotonic() < deadline:
            try:
                client.projects.list()
                break
            except Exception:
                time.sleep(0.5)
        else:
            raise RuntimeError(f"Phoenix did not become ready; inspect {root / 'results' / 'phoenix.log'}")
    try:
        client.projects.get(project_name=PROJECT_NAME)
    except Exception:
        client.projects.create(name=PROJECT_NAME)
    if not _TRACING_REGISTERED:
        from phoenix.otel import register

        endpoint = os.getenv("PHOENIX_COLLECTOR_ENDPOINT") or f"{base_url}/v1/traces"
        register(endpoint=endpoint, project_name=PROJECT_NAME, protocol="http/protobuf", verbose=False)
        _TRACING_REGISTERED = True
    return client


def upload_testsets(client: Client, root) -> tuple[str, str]:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    overall_name = f"overall_experiment_inputs-{timestamp}"
    convergence_name = f"convergence_questions-{timestamp}"
    overall = json.loads((root / "datasets" / "overall_questions.json").read_text(encoding="utf-8"))
    convergence = json.loads((root / "datasets" / "convergence_questions.json").read_text(encoding="utf-8"))
    existing_names = {dataset["name"] for dataset in client.datasets.list()}
    if overall_name not in existing_names:
        client.datasets.create_dataset(
            name=overall_name,
            examples=[
                {
                    "input": {"question": case["question"]},
                    "output": {"sql_result": case["sql_result"], "sql_generated": case["sql_generated"]},
                }
                for case in overall
            ],
        )
    if convergence_name not in existing_names:
        client.datasets.create_dataset(
            name=convergence_name,
            examples=[{"input": {"question": case["question"]}, "output": {}} for case in convergence],
        )
    return overall_name, convergence_name
