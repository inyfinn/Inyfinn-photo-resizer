"""CLI for headless batch conversion."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from inyfinn_resizer.core.job import FormatOptions, JobSpec
from inyfinn_resizer.core.pipeline import build_output_path, process_job
from inyfinn_resizer.core.presets import apply_preset, load_preset


def _collect_inputs(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    return sorted(p for p in path.rglob("*") if p.is_file() and p.suffix.lower() in {
        ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tif", ".tiff", ".webp", ".avif", ".heic",
    })


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="inyfinn-resizer", description="Batch image converter CLI")
    sub = parser.add_subparsers(dest="command")

    conv = sub.add_parser("convert", help="Convert images")
    conv.add_argument("--input", "-i", required=True, help="Input file or folder")
    conv.add_argument("--output", "-o", required=True, help="Output folder")
    conv.add_argument("--format", "-f", default="webp", help="Output format (webp, jpeg, png, avif...)")
    conv.add_argument("--quality", "-q", type=int, default=85, help="Quality 0-100")
    conv.add_argument("--preset", "-p", help="JSON preset file")
    conv.add_argument("--target-kb", type=float, help="Target file size KB")
    conv.add_argument("--overwrite", action="store_true", help="Overwrite existing files")

    args = parser.parse_args(argv)
    if args.command != "convert":
        parser.print_help()
        return 2

    inp = Path(args.input)
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    fmt_opts = FormatOptions(quality=args.quality)
    output_format = args.format
    if args.preset:
        applied = apply_preset(load_preset(Path(args.preset)))
        fmt_opts = applied["format_opts"]
        output_format = applied["output_format"]

    if args.target_kb:
        fmt_opts.target_kb = args.target_kb

    errors = 0
    for src in _collect_inputs(inp):
        dst = build_output_path(src, out_dir, output_format, preserve_structure=False)
        job = JobSpec(input_path=src, output_path=dst, output_format=output_format, format_opts=fmt_opts)
        result = process_job(job, overwrite=args.overwrite)
        status = result.status.value
        print(f"{src.name}: {status} {result.old_kb:.1f} KB -> {result.new_kb:.1f} KB ({result.ratio_pct:.0f}%)")
        if result.status.value == "ERROR":
            errors += 1
            print(f"  {result.message}", file=sys.stderr)

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
