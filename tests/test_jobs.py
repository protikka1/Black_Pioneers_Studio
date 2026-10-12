import time
import unittest
from pathlib import Path
from threading import Event, Thread
from unittest.mock import Mock

from black_pioneers_studio.jobs import RenderJobManager


class RenderJobManagerTests(unittest.TestCase):
    def test_cleanup_waits_for_queued_and_running_jobs(self) -> None:
        manager = RenderJobManager(max_workers=1)
        release = Event()
        started = Event()
        cleanup = Mock()

        def task(_progress):
            started.set()
            release.wait(timeout=5)
            return Path("/tmp/output.mp4")

        try:
            manager.run_render_job(1, task)
            self.assertTrue(started.wait(timeout=2))
            manager.run_render_job(2, task)
            self.assertFalse(manager.clean_workspace_if_idle(cleanup))
            cleanup.assert_not_called()
        finally:
            release.set()
            manager._executor.shutdown(wait=True)
        self.assertTrue(manager.clean_workspace_if_idle(cleanup))
        cleanup.assert_called_once()

    def test_cleanup_cannot_interrupt_upload_preparation(self) -> None:
        manager = RenderJobManager(max_workers=1)
        attempted = Event()
        cleaned = Event()

        def cleanup_thread():
            attempted.set()
            manager.clean_workspace_if_idle(cleaned.set)

        with manager.prepare_workspace():
            worker = Thread(target=cleanup_thread)
            worker.start()
            self.assertTrue(attempted.wait(timeout=2))
            self.assertFalse(cleaned.wait(timeout=0.05))
        worker.join(timeout=2)
        self.assertTrue(cleaned.is_set())
        manager._executor.shutdown(wait=True)

    def test_reuses_job_for_same_request_key(self) -> None:
        manager = RenderJobManager(max_workers=1)
        calls = {"count": 0}

        def task(_progress):
            calls["count"] += 1
            return Path("/tmp/output.mp4")

        job_1 = manager.run_render_job(pioneer_id=1, task=task, request_key="abc")
        job_2 = manager.run_render_job(pioneer_id=1, task=task, request_key="abc")

        # Wait until completion by polling known status transitions.
        for _ in range(200):
            current = manager.get_job(job_1.job_id)
            if current and current.status in {"completed", "failed"}:
                break
            time.sleep(0.01)
        else:
            self.fail("Render job did not complete within timeout")
        self.assertEqual(job_1.job_id, job_2.job_id)
        self.assertEqual(calls["count"], 1)


if __name__ == "__main__":
    unittest.main()
