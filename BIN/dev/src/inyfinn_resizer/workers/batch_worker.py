"""Batch processing worker — QThread; ProcessPool tylko poza EXE."""

from __future__ import annotations

import os
import sys
from concurrent.futures import (
    FIRST_COMPLETED,
    ProcessPoolExecutor,
    ThreadPoolExecutor,
    wait,
)
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
            self._run_parallel(results, total)
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

    def _submit_job(self, pool, index: int):
        if _use_thread_pool():
            return pool.submit(process_job, self.jobs[index], overwrite=self.overwrite)
        return pool.submit(_worker_process, job_to_dict(self.jobs[index]), self.overwrite)

    def _consume_future(self, fut, index: int) -> JobResult:
        try:
            raw = fut.result()
            data = raw if isinstance(raw, dict) else _result_to_dict(raw)
            status = data["status"]
            msg = data["message"] or ""
            self.file_finished.emit(index, status, msg)
            return self._dict_to_result(data, self.jobs[index])
        except Exception as exc:
            err_job = self.jobs[index]
            err_result = JobResult(
                job=err_job,
                status=JobStatus.ERROR,
                message=str(exc),
                old_bytes=err_job.input_path.stat().st_size if err_job.input_path.is_file() else 0,
            )
            self.file_finished.emit(index, "ERROR", str(exc))
            return err_result

    def _run_parallel(self, results: list[JobResult], total: int) -> None:
        """W locie tylko max_workers zadań — cancel nie czeka na całą kolejkę."""
        workers = max(1, min((os.cpu_count() or 2) - 1, 4 if _use_thread_pool() else 8))
        executor_cls = ThreadPoolExecutor if _use_thread_pool() else ProcessPoolExecutor
        pool = executor_cls(max_workers=workers)
        in_flight: dict = {}
        next_i = 0
        done = 0
        try:
            while next_i < total and len(in_flight) < workers and not self._cancelled:
                self.file_started.emit(next_i, "Przetwarzanie…")
                in_flight[self._submit_job(pool, next_i)] = next_i
                next_i += 1

            while in_flight and not self._cancelled:
                finished, _ = wait(
                    list(in_flight.keys()),
                    timeout=0.2,
                    return_when=FIRST_COMPLETED,
                )
                if not finished:
                    continue
                for fut in finished:
                    idx = in_flight.pop(fut)
                    if fut.cancelled():
                        continue
                    done += 1
                    result = self._consume_future(fut, idx)
                    results.append(result)
                    self.progress.emit(done, total, self.jobs[idx].input_path.name)
                    if not self._cancelled and next_i < total:
                        self.file_started.emit(next_i, "Przetwarzanie…")
                        in_flight[self._submit_job(pool, next_i)] = next_i
                        next_i += 1
        finally:
            pool.shutdown(wait=False, cancel_futures=True)

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
