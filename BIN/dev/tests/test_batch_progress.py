"""Postęp konwersji — nie pokazuj 100% przed zakończeniem pliku."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from inyfinn_resizer.core.job import FormatOptions, JobResult, JobSpec, JobStatus
from inyfinn_resizer.workers.batch_worker import BatchWorker

FIXTURE = Path(__file__).parent / "fixtures" / "IMG_0113.jpg"


def test_single_job_progress_emits_zero_before_done():
    job = JobSpec(
        input_path=FIXTURE,
        output_path=Path(__file__).parent / "output" / "progress_probe.png",
        output_format="png",
        format_opts=FormatOptions(quality=50),
    )
    worker = BatchWorker([job], parallel=False)
    seen: list[tuple[int, int, str]] = []

    def capture(current, total, name):
        seen.append((current, total, name))

    worker.progress.connect(capture)

    with patch("inyfinn_resizer.workers.batch_worker.process_job") as proc:
        proc.return_value = JobResult(
            job=job,
            status=JobStatus.OK,
            message="",
            old_bytes=100,
            new_bytes=50,
        )
        worker.run()

    assert seen[0][0] == 0
    assert seen[-1][0] == 1
    assert seen[-1][1] == 1


def test_parallel_cancel_does_not_wait_for_queued_jobs():
    import threading
    import time

    jobs = [
        JobSpec(
            input_path=FIXTURE,
            output_path=Path(__file__).parent / "output" / f"cancel_{i}.png",
            output_format="png",
            format_opts=FormatOptions(quality=50),
        )
        for i in range(8)
    ]
    started: list[int] = []
    worker = BatchWorker(jobs, parallel=True)

    def slow_job(job, overwrite=True):
        started.append(1)
        time.sleep(0.35)
        return JobResult(job=job, status=JobStatus.OK, message="", old_bytes=100, new_bytes=50)

    with (
        patch("inyfinn_resizer.workers.batch_worker.process_job", side_effect=slow_job),
        patch("inyfinn_resizer.workers.batch_worker._use_thread_pool", return_value=True),
    ):
        thread = threading.Thread(target=worker.run)
        t0 = time.monotonic()
        thread.start()
        time.sleep(0.12)
        worker.request_cancel()
        thread.join(timeout=2.5)
        elapsed = time.monotonic() - t0

    assert not thread.is_alive()
    assert elapsed < 2.0
    assert len(started) <= 5
