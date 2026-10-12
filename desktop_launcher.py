from __future__ import annotations

import os
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
    with LOG_FILE.open("a", encoding="utf-8") as file:
        file.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")


def _is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def _bundle_root() -> Path:
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))


def _candidate_project_roots():
    if _is_frozen():
        # Installed apps must never fall back to the original build checkout.
        yield _bundle_root() / "studio"
        return
    env_root = os.environ.get("BLACK_PIONEERS_ROOT")
    if env_root:
        yield Path(env_root).expanduser().resolve()
    launcher_root = Path(__file__).resolve().parent
    yield launcher_root
    yield from launcher_root.parents
    cwd = Path.cwd().resolve()
    yield cwd
    yield from cwd.parents


def _resolve_project_root() -> Path:
    for candidate in _candidate_project_roots():
        if (candidate / "app.py").is_file():
            return candidate
    raise FileNotFoundError("Unable to locate app.py in the application resources.")


def _resolve_port() -> int:
    port = int(os.environ.get("PORT") or os.environ.get("BLACK_PIONEERS_PORT", "8501"))
    if not 1 <= port <= 65535:
        raise ValueError("The server port must be between 1 and 65535.")
    return port


def _available_port(preferred: int) -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind(("127.0.0.1", preferred))
        except OSError:
            sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _prepare_environment() -> Path:
    if _is_frozen():
        os.environ.setdefault("BLACK_PIONEERS_DATA_DIR", str(
            Path.home() / "Library" / "Application Support" / "BlackPioneersStudio"
        ))
        ffmpeg = _bundle_root() / "bin" / "ffmpeg"
        if not ffmpeg.is_file():
            raise FileNotFoundError("The application is missing its bundled FFmpeg.")
        os.environ["IMAGEIO_FFMPEG_EXE"] = str(ffmpeg)
        os.environ["FFMPEG_BINARY"] = str(ffmpeg)
        os.environ["PATH"] = str(ffmpeg.parent) + os.pathsep + os.environ.get("PATH", "")
    else:
        import imageio_ffmpeg
        os.environ.setdefault("IMAGEIO_FFMPEG_EXE", imageio_ffmpeg.get_ffmpeg_exe())
        os.environ.setdefault("FFMPEG_BINARY", os.environ["IMAGEIO_FFMPEG_EXE"])
    return _resolve_project_root()


def _server_command(port: int) -> list[str]:
    if _is_frozen():
        return [sys.executable, "--serve", str(port)]
    return [sys.executable, str(Path(__file__).resolve()), "--serve", str(port)]


def _serve(port: int) -> int:
    project_root = _prepare_environment()
    # Set runtime paths before importing the application modules.
    from streamlit.web import bootstrap
    options = {
        "server.address": "127.0.0.1",
        "server.port": port,
        "server.headless": True,
        "server.fileWatcherType": "none",
        "server.runOnSave": False,
        "browser.gatherUsageStats": False,
        "global.developmentMode": False,
    }
    bootstrap.load_config_options(options)
    bootstrap.run(str(project_root / "app.py"), False, [], options)
    return 0


def _self_test() -> int:
    project_root = _prepare_environment()
    import runpy
    import streamlit
    import edge_tts
    import moviepy
    from black_pioneers_studio.paths import DATA_DIR, ensure_runtime_directories
    from database.connection import initialize_database
    if _is_frozen():
        static = Path(streamlit.__file__).parent / "static" / "index.html"
        if not static.is_file():
            raise FileNotFoundError("Streamlit's browser assets were not bundled.")
        if DATA_DIR == project_root or project_root in DATA_DIR.parents:
            raise ValueError("Runtime data must be stored outside the app bundle.")
    ensure_runtime_directories()
    initialize_database()
    subprocess.run([os.environ["FFMPEG_BINARY"], "-version"], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # The bundled app.py is runtime source, so validate all its imports too.
    runpy.run_path(str(project_root / "app.py"), run_name="bundle_validation")
    print(f"Bundle checks passed; runtime data: {DATA_DIR}")
    return 0


def _wait_for_http(url: str, timeout_seconds: float = 60.0,
                   process: subprocess.Popen | None = None) -> bool:
    deadline = time.monotonic() + timeout_seconds
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    while time.monotonic() < deadline:
        if process is not None and process.poll() is not None:
            return False
        try:
            with opener.open(url + "/_stcore/health", timeout=1.5) as response:
                if response.status == 200 and response.read().strip() == b"ok":
                    return True
        except Exception:
            time.sleep(0.3)
    return False


def _open_browser(url: str) -> None:
    if not webbrowser.open(url):
        subprocess.run(["open", url], check=False)


def _request_stop(_signum, _frame) -> None:
    raise KeyboardInterrupt


def main() -> int:
    if len(sys.argv) == 3 and sys.argv[1] == "--serve":
        return _serve(int(sys.argv[2]))
    if sys.argv[1:] == ["--self-test"]:
        return _self_test()
    signal.signal(signal.SIGTERM, _request_stop)
    project_root = _prepare_environment()
    port = _available_port(_resolve_port())
    url = f"http://127.0.0.1:{port}"
    _log(f"Starting server from {project_root} at {url}")
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as log:
        process = subprocess.Popen(_server_command(port), cwd=str(project_root),
                                   stdout=log, stderr=log)
        try:
            if not _wait_for_http(url, process=process):
                raise RuntimeError(f"Server did not start. See {LOG_FILE}")
            _open_browser(url)
            _log(f"Opened {url}")
            while process.poll() is None:
                time.sleep(0.5)
            return process.returncode or 0
        except KeyboardInterrupt:
            return 0
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        _log(str(exc))
        raise
