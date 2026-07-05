"""Batch processing worker — runs in QThread, uses ProcessPoolExecutor."""

from __future__ import annotations

import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from PySide6.QtCore import QObject, QThread, Signal

from inyfinn_resizer.core.job import JobResult, JobSpec, JobStatus
from inyfinn_resizer.core.pipeline import process_job


def _worker_process(job_dict: dict, overwrite: bool) -> dict:
    """Picklable worker for multiprocessing."""
    job = JobSpec(
        input_path=Path(job_dict["input_path"]),
        output_path=Path(job_dict["output_path"]),
        output_format=job_dict["output_format"],
    )
    from inyfinn_resizer.core.job import FormatOptions
    job.format_opts = FormatOptions(**job_dict.get("format_opts", {}))
    result = process_job(job, overwrite=overwrite)
    return {
        "input_path": str(result.job.input_path),
        "output_path": str(result.job.output_path),
        "status": result.status.value,
        "message": result.message,
        "old_bytes": result.old_bytes,
        "new_bytes": result.new_bytes,
    }


class BatchWorker(QObject):
    progress = Signal(int, int, str)  # current, total, filename
    file_done = Signal(dict)
    finished = Signal(list)
    error = Signal(str)

    def __init__(self, jobs: list[JobSpec], parallel: bool = True, overwrite: bool = True):
        super().__init__()
        self.jobs = jobs
        self.parallel = parallel
        self.overwrite = overwrite

    def run(self) -> None:
        results: list[JobResult] = []
        total = len(self.jobs)
        if total == 0:
            self.finished.emit(results)
            return

        job_dicts = [
            {
                "input_path": str(j.input_path),
                "output_path": str(j.output_path),
                "output_format": j.output_format,
                "format_opts": {
                    "quality": j.format_opts.quality,
                    "lossless": j.format_opts.lossless,
                    "progressive": j.format_opts.progressive,
                    "optimize": j.format_opts.optimize,
                    "keep_metadata": j.format_opts.keep_metadata,
                    "target_kb": j.format_opts.target_kb,
                    "target_tolerance": j.format_opts.target_tolerance,
                },
            }
            for j in self.jobs
        ]

        if self.parallel and total > 1:
            workers = max(1, (os.cpu_count() or 2) - 1)
            with ProcessPoolExecutor(max_workers=workers) as pool:
                futures = {
                    pool.submit(_worker_process, jd, self.overwrite): i
                    for i, jd in enumerate(job_dicts)
                }
                done = 0
                for fut in as_completed(futures):
                    idx = futures[fut]
                    done += 1
                    try:
                        data = fut.result()
                        self.progress.emit(done, total, Path(data["input_path"]).name)
                        self.file_done.emit(data)
                        results.append(self._dict_to_result(data, self.jobs[idx]))
                    except Exception as e:
                        self.error.emit(str(e))
        else:
            for i, job in enumerate(self.jobs):
                self.progress.emit(i + 1, total, job.input_path.name)
                result = process_job(job, overwrite=self.overwrite)
                data = {
                    "input_path": str(result.job.input_path),
                    "output_path": str(result.job.output_path),
                    "status": result.status.value,
                    "message": result.message,
                    "old_bytes": result.old_bytes,
                    "new_bytes": result.new_bytes,
                }
                self.file_done.emit(data)
                results.append(result)

        self.finished.emit(results)

    @staticmethod
    def _dict_to_result(data: dict, job: JobSpec) -> JobResult:
        return JobResult(
            job=job,
            status=JobStatus(data["status"]),
            message=data["message"],
            old_bytes=data["old_bytes"],
            new_bytes=data["new_bytes"],
        )


class BatchThread(QThread):
    def __init__(self, worker: BatchWorker):
        super().__init__()
        self._worker = worker
        worker.moveToThread(self)

    def run(self) -> None:
        self._worker.run()
