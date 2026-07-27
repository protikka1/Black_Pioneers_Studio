import unittest
from pathlib import Path

from black_pioneers_studio.jobs import RenderJobManager


class RenderJobManagerTests(unittest.TestCase):
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
