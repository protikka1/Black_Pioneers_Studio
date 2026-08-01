from __future__ import annotations

import os
import shutil
import signal
import socket
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

LOG_FILE = Path.home() / "Library" / "Logs" / "BlackPioneersStudio.log"


def _log(message: str) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with LOG_FILE.open("a", encoding="utf-8") as file:
        file.write(f"[{timestamp}] {message}\n")


def _candidate_project_roots():
    env_root = os.environ.get("BLACK_PIONEERS_ROOT")
    if env_root:
        yield Path(env_root).expanduser().resolve()

    launcher_root = Path(__file__).resolve().parent
    yield launcher_root
    yield from launcher_root.parents

    cwd = Path.cwd().resolve()
    yield cwd
    yield from cwd.parents


def _resolve_port() -> int:
    return int(os.environ.get("PORT") or os.environ.get("BLACK_PIONEERS_PORT", "8501"))


def _resolve_project_root() -> Path:
    for candidate in _candidate_project_roots():
        if (candidate / "app.py").exists():
            return candidate

    raise FileNotFoundError(
        "Unable to locate app.py. Set BLACK_PIONEERS_ROOT to the project root."
    )


def _resolve_streamlit_bin(project_root: Path) -> str:
    venv_streamlit = project_root / ".venv" / "bin" / "streamlit"
    if venv_streamlit.exists():
        return str(venv_streamlit)

    sibling_streamlit = Path(sys.executable).with_name("streamlit")
    if sibling_streamlit.exists():
        return str(sibling_streamlit)

    system_streamlit = shutil.which("streamlit")
    if system_streamlit:
        return system_streamlit

    raise FileNotFoundError(
        "Streamlit executable not found. Install dependencies in .venv first."
    )


def _wait_for_http(url: str, timeout_seconds: float = 30.0) -> bool:
    start = time.time()
    while time.time() - start < timeout_seconds:
        try:
            with urllib.request.urlopen(url, timeout=1.5) as response:
                if response.status < 500:
                    return True
        except Exception:
            time.sleep(0.3)
    return False


def _is_port_open(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.75)
        return sock.connect_ex((host, port)) == 0


def _open_browser(url: str) -> None:
    opened = webbrowser.open(url)
    if opened:
        return

    # Fallback for bundled app environments where webbrowser may not resolve handlers.
    subprocess.run(["open", url], check=False)


def main() -> int:
    project_root = _resolve_project_root()
    app_file = project_root / "app.py"
    _log(f"Launcher starting from root={project_root}")

    if not app_file.exists():
        print(f"app.py not found in {project_root}")
        return 1

    if shutil.which("ffmpeg") is None:
        print("ffmpeg is not installed or not on PATH.")
        return 1

    try:
        streamlit_bin = _resolve_streamlit_bin(project_root)
    except FileNotFoundError as exc:
        print(str(exc))
        return 1

    port = _resolve_port()
    url = f"http://127.0.0.1:{port}"

    if _is_port_open("127.0.0.1", port):
        _log(f"Detected existing server on {url}; opening browser only")
        _open_browser(url)
        # Keep the process alive briefly so macOS launcher/Dock sees a valid app lifecycle.
        time.sleep(1.5)
        return 0

    cmd = [
        streamlit_bin,
        "run",
        str(app_file),
        "--server.address",
        "127.0.0.1",
        "--server.port",
        str(port),
        "--server.headless",
        "true",
    ]

    process = subprocess.Popen(
        cmd,
        cwd=str(project_root),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        if not _wait_for_http(url):
            print("Streamlit did not start in time. Check your environment.")
            _log("Streamlit did not start in time")
            process.terminate()
            return 1

        _open_browser(url)
        _log(f"Opened browser at {url}")
        print(f"Black Pioneers Studio is running at {url}")
        print("Press Ctrl+C to stop.")

        while process.poll() is None:
            time.sleep(0.5)

        return process.returncode or 0

    except KeyboardInterrupt:
        pass
    except Exception as exc:
        _log(f"Unexpected launcher error: {exc}")
        raise
    finally:
        if process.poll() is None:
            process.send_signal(signal.SIGTERM)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
