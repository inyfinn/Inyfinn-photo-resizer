"""Batch processing worker — QThread; ProcessPool tylko poza EXE."""

from __future__ import annotations

import os
import sys
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from pathlib import Path

from PySide6.QtCore import QObject, QThread, Signal

from inyfinn_resizer.core.job import JobResult, JobSpec, JobStatus, job_from_dict, job_to_dict
from inyfinn_resizer.core.pipeline import process_job


def _worker_process(job_dict: dict, overwrite: bool) -> dict:
    """Picklable worker dla ProcessPoolExecutor (dev)."""
    job = job_from_dict(job_dict)
    result = process_job(job, overwrite=overwrite)
    return _result_to_dict(result)


def _result_to_dict(result: JobResult) -> dict:
    return {
        "input_path": str(result.job.input_path),
        "output_path": str(result.job.output_path),
        "output_format": result.job.output_format,
        "status": result.status.value,
        "message": result.message,
        "old_bytes": result.old_bytes,
        "new_bytes": result.new_bytes,
    }


def _use_thread_pool() -> bool:
    """EXE PyInstaller — wątki zamiast procesów (stabilniejsze, wspólne _internal)."""
    return getattr(sys, "frozen", False)


class BatchWorker(QObject):
    progress = Signal(int, int, str)  # current, total, filename
    file_started = Signal(int, str)  # index, phase
    file_finished = Signal(int, str, str)  # index, status, message
    finished = Signal(list)
    error = Signal(str)
    cancelled = Signal()

    def __init__(self, jobs: list[JobSpec], parallel: bool = True, overwrite: bool = True):
        super().__init__()
        self.jobs = jobs
        self.parallel = parallel
        self.overwrite = overwrite
        self._cancelled = False

    def request_cancel(self) -> None:
        self._cancelled = True

    def run(self) -> None:
        from inyfinn_resizer.utils.frozen_stdio import ensure_stdio

        ensure_stdio()
        results: list[JobResult] = []
        total = len(self.jobs)
        if total == 0:
            self.finished.emit(results)
            return

        if self.parallel and total > 1 and not self._cancelled:
            workers = max(1, min((os.cpu_count() or 2) - 1, 4 if _use_thread_pool() else 8))
            job_dicts = [job_to_dict(j) for j in self.jobs]
            executor_cls = ThreadPoolExecutor if _use_thread_pool() else ProcessPoolExecutor
            with executor_cls(max_workers=workers) as pool:
                if _use_thread_pool():
                    futures = {
                        pool.submit(process_job, self.jobs[i], overwrite=self.overwrite): i
                        for i in range(total)
                    }
                else:
                    futures = {
                        pool.submit(_worker_process, jd, self.overwrite): i
                        for i, jd in enumerate(job_dicts)
                    }
                for idx in range(total):
                    self.file_started.emit(idx, "Oczekiwanie w kolejce")
                done = 0
                for fut in as_completed(futures):
                    if self._cancelled:
                        break
                    idx = futures[fut]
                    self.file_started.emit(idx, "Przetwarzanie…")
                    done += 1
                    try:
                        if _use_thread_pool():
                            result = fut.result()
                            data = _result_to_dict(result)
                        else:
                            data = fut.result()
                        status = data["status"]
                        msg = data["message"] or ""
                        self.file_finished.emit(idx, status, msg)
                        self.progress.emit(done, total, Path(data["input_path"]).name)
                        results.append(self._dict_to_result(data, self.jobs[idx]))
                    except Exception as e:
                        err_job = self.jobs[idx]
                        err_result = JobResult(
                            job=err_job,
                            status=JobStatus.ERROR,
                            message=str(e),
                            old_bytes=err_job.input_path.stat().st_size if err_job.input_path.is_file() else 0,
                        )
                        data = _result_to_dict(err_result)
                        self.file_finished.emit(idx, "ERROR", str(e))
                        self.progress.emit(done, total, Path(data["input_path"]).name)
                        results.append(err_result)
        else:
            for i, job in enumerate(self.jobs):
                if self._cancelled:
                    break
                self.file_started.emit(i, "Przetwarzanie…")
                self.progress.emit(i, total, job.input_path.name)
                result = process_job(job, overwrite=self.overwrite)
                data = _result_to_dict(result)
                self.file_finished.emit(i, result.status.value, result.message or "")
                results.append(result)
                self.progress.emit(i + 1, total, job.input_path.name)

        if self._cancelled:
            self.cancelled.emit()
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
        self.was_cancelled = False
        worker.moveToThread(self)

    def request_cancel(self) -> None:
        self._worker.request_cancel()

    def run(self) -> None:
        self._worker.run()
        self.was_cancelled = self._worker._cancelled
