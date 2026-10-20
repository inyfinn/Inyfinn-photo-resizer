"""Zapis plików jawnie (2.6.8, S82): które nazwy są zajęte, co powiedzieć userowi i jak je rozdzielić.

Czysta logika bez widżetów (testy bez okna). Dopisek w nazwie pliku to w rdzeniu nadal ``_conv`` (``unique_conv_path``);
w tekstach dla usera mówimy „z dopiskiem” (S83).
"""

from __future__ import annotations

import re
from dataclasses import replace
from pathlib import Path

from inyfinn_resizer.core.job import JobSpec
from inyfinn_resizer.core.pipeline import unique_conv_path

SUFFIX = "suffix"
OVERWRITE = "overwrite"

_ASK_TAIL = "Gdy plik o tej nazwie już istnieje, zapytam: nadpisać czy zapisać obok z dopiskiem."


def nbsp(text: str) -> str:
    """Twarda spacja po jednoliterowych wyrazach (a, i, o, u, w, z) — S72: żadna linia nie kończy się na „w” czy „z”."""
    return re.sub(r"(?<![\w])([aiouwzAIOUWZ]) ", "\\1\u00a0", text)


def _same_dir(a: Path, b: Path) -> bool:
    try:
        return a.resolve() == b.resolve()
    except OSError:
        return a == b


def simple_save_info(folder: Path | None, queue: list[Path]) -> str:
    """Linijka pod polem „Folder” w trybie prostym: gdzie zapisze i co z zajętymi nazwami."""
    if folder is None:
        return nbsp(f"Zapis obok oryginałów. {_ASK_TAIL}")
    if queue and all(_same_dir(folder, p.parent) for p in queue):
        return nbsp(f"To ten sam folder co zdjęcia. {_ASK_TAIL}")
    return nbsp(f"Zapis do folderu „{folder.name or folder}”. {_ASK_TAIL}")


def advanced_save_info(output_on: bool, ask_overwrite: bool) -> str:
    """Linijka w karcie „Zapis plików” trybu zaawansowanego."""
    if not output_on:
        return nbsp(f"Zapis obok oryginałów. {_ASK_TAIL}")
    if ask_overwrite:
        return nbsp(f"Zapis do folderu wyjściowego. {_ASK_TAIL}")
    return nbsp("Zapis do folderu wyjściowego. Pliki o tych samych nazwach zostaną nadpisane bez pytania.")


def conflicting_indices(jobs: list[JobSpec]) -> list[int]:
    """Zadania, których cel już leży na dysku albo który wcześniejsze zadanie z tej samej partii zajmuje."""
    seen: set[Path] = set()
    found: list[int] = []
    for i, job in enumerate(jobs):
        if job.output_path.exists() or job.output_path in seen:
            found.append(i)
        seen.add(job.output_path)
    return found


def same_as_source(jobs: list[JobSpec], indices: list[int]) -> bool:
    """Każdy zajęty cel leży w folderze swojego zdjęcia źródłowego (nadpisanie zastąpi oryginały)."""
    return bool(indices) and all(_same_dir(jobs[i].output_path.parent, jobs[i].input_path.parent) for i in indices)


def with_suffix_names(jobs: list[JobSpec], indices: list[int]) -> list[JobSpec]:
    """Zajęte cele dostają wolną nazwę z dopiskiem (``unique_conv_path``); nazwy nie powtarzają się także w partii."""
    taken = {job.output_path for job in jobs}
    pick = set(indices)
    result: list[JobSpec] = []
    for i, job in enumerate(jobs):
        if i in pick:
            target = job.output_path
            free = unique_conv_path(target)
            n = 2
            while free in taken or free.exists():
                free = target.with_name(f"{target.stem}_conv{n}{target.suffix}")
                n += 1
            taken.add(free)
            job = replace(job, output_path=free)
        result.append(job)
    return result
