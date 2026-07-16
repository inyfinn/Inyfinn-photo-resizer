"""5 prób weryfikacji ścieżki instalacji aktualizacji (bez nadpisywania BIN/)."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def _ok(name: str, cond: bool, detail: str = "") -> None:
    status = "PASS" if cond else "FAIL"
    print(f"[{status}] {name}" + (f" — {detail}" if detail else ""))
    if not cond:
        raise SystemExit(1)


def probe_1_no_shutil_gettempdir() -> None:
    import ast

    path = ROOT / "src" / "inyfinn_resizer" / "utils" / "update_apply.py"
    src = path.read_text(encoding="utf-8")
    _ok("1a source imports tempfile", "import tempfile" in src)
    _ok("1b source uses tempfile.gettempdir", "tempfile.gettempdir()" in src)
    tree = ast.parse(src)
    bad_calls = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr == "gettempdir":
            if isinstance(node.value, ast.Name) and node.value.id == "shutil":
                bad_calls.append(node.lineno)
    _ok("1c AST: brak wywołania shutil.gettempdir", not bad_calls, str(bad_calls))
    _ok("1d helper _temp_dir istnieje", "def _temp_dir" in src)


def probe_2_write_script() -> Path:
    from inyfinn_resizer.utils.update_apply import write_apply_script

    tmp = Path(tempfile.mkdtemp(prefix="inyfinn-upd-test-"))
    zip_path = tmp / "pkg.zip"
    zip_path.write_bytes(b"PK\x03\x04dummy")
    install_root = tmp / "install"
    install_root.mkdir()
    launcher = install_root / "InyfinnPhotoResizer.exe"
    launcher.write_bytes(b"MZ")
    pkg = tmp / "cache" / "1.0.99"
    script = write_apply_script(
        zip_path=zip_path,
        install_root=install_root,
        version="1.0.99-test",
        launcher=launcher,
        package_dir=pkg,
    )
    temp_dir = Path(tempfile.gettempdir()).resolve()
    _ok("2a script exists", script.is_file(), str(script))
    _ok("2b script in TEMP", script.resolve().parent == temp_dir, str(script.parent))
    raw = script.read_bytes()
    _ok("2c UTF-8 BOM present", raw.startswith(b"\xef\xbb\xbf"))
    text = raw.decode("utf-8-sig")
    _ok("2d script body non-empty", len(text) > 200, f"len={len(text)}")
    return script


def probe_3_powershell_parses(script: Path) -> None:
    # -Command parses/loads without executing install body if we only check syntax via Tokenizer
    cmd = [
        "powershell.exe",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-Command",
        f"$e=$null; [void][System.Management.Automation.Language.Parser]::ParseFile('{script}', [ref]$null, [ref]$e); if($e){{$e|ForEach-Object{{$_.Message}}; exit 1}} else {{'PARSE_OK'}}",
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    _ok("3a PowerShell parse exit 0", r.returncode == 0, (r.stdout + r.stderr)[:300])
    _ok("3b PARSE_OK in stdout", "PARSE_OK" in (r.stdout or ""), r.stdout[:200])


def probe_4_launch_like_app(script: Path) -> None:
    """Symuluje UpdateManager._launch_installer (DEVNULL + CREATE_NO_WINDOW)."""
    # Zamień treść na bezpieczny skrypt testowy (nie instaluj nic)
    probe_ps1 = Path(tempfile.gettempdir()) / "inyfinn-apply-update-probe.ps1"
    probe_ps1.write_text(
        "Add-Content -Path (Join-Path $env:TEMP 'inyfinn-update-probe.ok') -Value (Get-Date -Format o)\n",
        encoding="utf-8-sig",
    )
    marker = Path(tempfile.gettempdir()) / "inyfinn-update-probe.ok"
    marker.unlink(missing_ok=True)

    creationflags = subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP
    proc = subprocess.Popen(
        [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-STA",
            "-File",
            str(probe_ps1),
        ],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=creationflags,
        close_fds=True,
    )
    _ok("4a Popen returned pid", proc.pid > 0, f"pid={proc.pid}")
    deadline = time.time() + 10
    while time.time() < deadline and not marker.is_file():
        time.sleep(0.1)
    _ok("4b marker file created by PS", marker.is_file(), str(marker))
    probe_ps1.unlink(missing_ok=True)
    marker.unlink(missing_ok=True)


def probe_5_launcher_spec_paths() -> None:
    """Bug 2: SPECPATH to katalog .spec → ROOT=parent → launcher.py istnieje."""
    for label, spec_dir in [
        ("BIN/dev/installer", ROOT / "installer"),
        ("dev/installer", ROOT.parent.parent / "dev" / "installer"),
    ]:
        if not spec_dir.is_dir():
            print(f"[SKIP] 5 {label} — brak katalogu")
            continue
        root = spec_dir.resolve().parent
        launcher = root / "launcher" / "launcher.py"
        wrong = spec_dir / "launcher" / "launcher.py"
        _ok(f"5a {label} LAUNCHER exists", launcher.is_file(), str(launcher))
        _ok(f"5b {label} NOT under installer/", not wrong.is_file(), str(wrong))


def main() -> int:
    print("=== verify_update_install: 5 prób ===")
    probe_1_no_shutil_gettempdir()
    script = probe_2_write_script()
    try:
        probe_3_powershell_parses(script)
        probe_4_launch_like_app(script)
        probe_5_launcher_spec_paths()
    finally:
        script.unlink(missing_ok=True)
    print("=== ALL PROBES PASSED ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
