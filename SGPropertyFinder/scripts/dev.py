"""Run the FastAPI backend and Vite frontend together."""

from __future__ import annotations

import argparse
import os
import shutil
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"
ENV_FILE = ROOT / ".env"
ENV_EXAMPLE = ROOT / ".env.example"


def wait_for(
    url: str,
    timeout_seconds: int = 60,
    process: subprocess.Popen[bytes] | None = None,
) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if process is not None and process.poll() is not None:
            return False
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if response.status < 500:
                    return True
        except (urllib.error.URLError, TimeoutError, OSError):
            pass
        time.sleep(0.75)
    return False


def oneMapCredentialsConfigured() -> bool:
    """Return whether OneMap credentials exist in the environment or `.env`."""
    values: dict[str, str] = {}
    if ENV_FILE.exists():
        for raw_line in ENV_FILE.read_text(encoding="utf-8-sig").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            if line.startswith("export "):
                line = line[len("export ") :]
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip('"').strip("'")
    email = os.environ.get("ONEMAP_EMAIL") or values.get("ONEMAP_EMAIL")
    password = os.environ.get("ONEMAP_PASSWORD") or values.get("ONEMAP_PASSWORD")
    return bool(email and password)


def terminate(process: subprocess.Popen[bytes] | None) -> None:
    if process is None or process.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            capture_output=True,
            check=False,
        )
    else:
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        except ProcessLookupError:
            pass


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the SG Property Finder dev stack")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--backend-only", action="store_true")
    group.add_argument("--frontend-only", action="store_true")
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()

    if not ENV_FILE.exists():
        if ENV_EXAMPLE.exists():
            shutil.copyfile(ENV_EXAMPLE, ENV_FILE)
            print("Created .env from .env.example. Fill in ONEMAP_EMAIL/ONEMAP_PASSWORD.")
        else:
            print("Missing .env. Copy .env.example to .env and add OneMap credentials.")
            return 1

    if not args.frontend_only and not oneMapCredentialsConfigured():
        print("OneMap credentials are missing; the backend cannot start.")
        print(f"Set ONEMAP_EMAIL and ONEMAP_PASSWORD in {ENV_FILE},")
        print("then run `make dev` again. A free OneMap account works.")
        return 1

    backend_process: subprocess.Popen[bytes] | None = None
    frontend_process: subprocess.Popen[bytes] | None = None

    try:
        if not args.frontend_only:
            print("Starting FastAPI on http://127.0.0.1:8000 ...")
            backend_process = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "uvicorn",
                    "main:app",
                    "--reload",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    "8000",
                ],
                cwd=BACKEND,
                start_new_session=os.name != "nt",
            )
            if not wait_for(
                "http://127.0.0.1:8000/api/v1/health", 90, backend_process
            ):
                print("Backend did not become healthy. Check the backend output above.")
                return 1
            print("Backend ready: http://127.0.0.1:8000/docs")

        if not args.backend_only:
            npm = shutil.which("npm.cmd") if os.name == "nt" else shutil.which("npm")
            if npm is None:
                print("npm was not found. Install Node.js, then run `npm install` in frontend/.")
                return 1
            print("Starting Vite on http://127.0.0.1:5173 ...")
            frontend_process = subprocess.Popen(
                [npm, "run", "dev", "--", "--host", "127.0.0.1", "--port", "5173"],
                cwd=FRONTEND,
                start_new_session=os.name != "nt",
            )
            if not wait_for(
                "http://127.0.0.1:5173/", 90, frontend_process
            ):
                print("Frontend did not start. Check the Vite output above.")
                return 1
            print("Frontend ready: http://127.0.0.1:5173")
            if not args.no_browser:
                webbrowser.open("http://127.0.0.1:5173")

        print("Press Ctrl+C to stop both servers.")
        while True:
            if backend_process is not None and backend_process.poll() is not None:
                print("Backend exited. Stopping frontend.")
                return backend_process.returncode or 1
            if frontend_process is not None and frontend_process.poll() is not None:
                print("Frontend exited. Stopping backend.")
                return frontend_process.returncode or 1
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nStopping servers...")
        return 0
    finally:
        terminate(frontend_process)
        terminate(backend_process)


if __name__ == "__main__":
    raise SystemExit(main())
