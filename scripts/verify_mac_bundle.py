"""Test the packaged app without the developer environment or Homebrew on PATH."""
from __future__ import annotations
import os
from pathlib import Path
import socket
import subprocess
import sys
from tempfile import TemporaryDirectory
import time
import urllib.request


def verify(executable: Path) -> None:
    executable = executable.resolve()
    with TemporaryDirectory(prefix="black-pioneers-bundle-test-") as folder:
        root = Path(folder)
        env = dict(os.environ)
        for key in ("PYTHONPATH", "PYTHONHOME", "VIRTUAL_ENV", "BLACK_PIONEERS_ROOT",
                    "IMAGEIO_FFMPEG_EXE", "FFMPEG_BINARY", "DYLD_LIBRARY_PATH"):
            env.pop(key, None)
        env["PATH"] = "/usr/bin:/bin:/usr/sbin:/sbin"
        env["BLACK_PIONEERS_DATA_DIR"] = str(root / "data")
        subprocess.run([str(executable), "--self-test"], cwd=root, env=env,
                       check=True, timeout=120)
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        with (root / "server.log").open("w+") as log:
            process = subprocess.Popen([str(executable), "--serve", str(port)],
                                       cwd=root, env=env, stdout=log, stderr=log)
            try:
                opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
                deadline = time.monotonic() + 60
                while time.monotonic() < deadline:
                    if process.poll() is not None:
                        break
                    try:
                        with opener.open(f"http://127.0.0.1:{port}/_stcore/health", timeout=2) as reply:
                            if reply.status == 200 and reply.read().strip() == b"ok":
                                with opener.open(f"http://127.0.0.1:{port}/", timeout=2) as page:
                                    assert b"<html" in page.read().lower(), "Missing browser page"
                                print("Packaged server and browser assets passed with Homebrew/Python removed from PATH.")
                                return
                    except OSError:
                        pass
                    time.sleep(0.2)
                log.seek(0)
                raise RuntimeError("Packaged server did not start:\n" + log.read())
            finally:
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()


if __name__ == "__main__":
    supplied = Path(sys.argv[1])
    executable = (supplied / "Contents" / "MacOS" / "Black Pioneers Studio"
                  if supplied.suffix == ".app" else supplied)
    verify(executable)
