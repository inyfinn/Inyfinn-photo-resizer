"""Persystencja ustawień użytkownika (QSettings)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from PySide6.QtCore import QSettings

from dataclasses import replace

from inyfinn_resizer.core.job import BatchSettings
from inyfinn_resizer.core.size_presets import PRESET_ORIGINAL, PRESET_LONG_1200, PRESET_SHORT_1200, PRESET_BOX_1200, apply_size_preset
from inyfinn_resizer.core.presets import settings_to_dict

if TYPE_CHECKING:
    from inyfinn_resizer.app.main_window import MainWindow


def _settings() -> QSettings:
    return QSettings("Inyfinn", "PhotoResizer")


def load_theme() -> str:
    theme = _settings().value("ui/theme", "light")
    return theme if theme in ("light", "dark") else "light"


def save_theme(theme: str) -> None:
    _settings().setValue("ui/theme", theme)


def save_results_table_header(header) -> None:
    _settings().setValue("ui/results_table_header", header.saveState())


def restore_results_table_header(header) -> bool:
    raw = _settings().value("ui/results_table_header")
    if raw is None:
        return False
    try:
        return bool(header.restoreState(raw))
    except (TypeError, ValueError):
        return False


def save_results_dialog_geometry(dialog) -> None:
    _settings().setValue("ui/results_dialog_size", [dialog.width(), dialog.height()])


def restore_results_dialog_geometry(dialog) -> bool:
    raw = _settings().value("ui/results_dialog_size")
    if not raw:
        return False
    try:
        w, h = int(raw[0]), int(raw[1])
        dialog.resize(max(w, 400), max(h, 300))
        return True
    except (TypeError, ValueError, IndexError):
        return False


def save_geometry(window: MainWindow) -> None:
    s = _settings()
    if splitter := window._main_splitter:
        s.setValue("ui/splitter", splitter.sizes())


def restore_geometry(window: MainWindow) -> bool:
    s = _settings()
    sizes = s.value("ui/splitter")
    if sizes and window._main_splitter:
        try:
            parsed = [int(x) for x in sizes]
            if len(parsed) == 2:
                right = max(500, parsed[1])
                left = max(400, parsed[0])
                window._main_splitter.setSizes([left, right])
            else:
                window._main_splitter.setSizes(parsed)
        except (TypeError, ValueError):
            pass
    return bool(sizes)


def snapshot_from_window(window: MainWindow) -> dict[str, Any]:
    fmt = window.format_combo.first_selected()
    window._format_opts.quality = window.quality_slider.value()
    window._format_opts.png_max_colors = window.png_colors_slider.value()
    window._format_opts.png_colors_auto = window.png_colors_auto_cb.isChecked()
    window._resize = replace(
        window._resize,
        scale_percent=float(window.scale_slider.value()),
        min_longest_enabled=window.min_longest_cb.isChecked(),
        min_longest_px=window._min_longest_px_value(),
    )
    data = settings_to_dict(
        fmt,
        window._format_opts,
        window._resize,
        window._transforms,
        window._metadata,
        window._rename,
        window._batch,
    )
    data["ui"] = {
        "theme": window._theme,
        "output_dir": window.output_dir_edit.text(),
        "output_enabled": window.output_enabled_cb.isChecked(),
        "segregate": window.segregate_cb.isChecked(),
        "wiz_sequence": window.wiz_sequence_cb.isChecked(),
        "size_preset": window._current_size_preset_id(),
        "preserve_structure": window.preserve_cb.isChecked(),
        "keep_dates": window.keep_dates_cb.isChecked(),
        "overwrite_ask": window.overwrite_cb.isChecked(),
        "parallel": window.parallel_cb.isChecked(),
        "preview": window.preview_cb.isChecked(),
        "sort_mode": window.sort_combo.currentIndex(),
        "formats": window.format_combo.selected_formats(),
        "remove_background": window.remove_bg_cb.isChecked(),
        "bg_model": window.bg_model_combo.currentData() or "birefnet-general-lite",
    }
    return data


def restore_to_window(window: MainWindow, data: dict[str, Any]) -> None:
    from inyfinn_resizer.core.presets import apply_preset

    applied = apply_preset(data)
    window._format_opts = applied["format_opts"]
    window._resize = applied["resize"]
    window._transforms = applied["transforms"]
    window._metadata = applied["metadata"]
    window._rename = applied["rename"]
    batch = data.get("batch") or {}
    if batch:
        window._batch = BatchSettings(**{k: v for k, v in batch.items() if hasattr(BatchSettings, k)})

    ui = data.get("ui") or {}
    window._programmatic_settings = True
    try:
        window.quality_slider.setValue(window._format_opts.quality)
        window.quality_label.setText(str(window._format_opts.quality))
        window.png_colors_auto_cb.setChecked(window._format_opts.png_colors_auto)
        window.png_colors_slider.setValue(window._format_opts.png_max_colors)
        window.png_colors_slider.setEnabled(not window._format_opts.png_colors_auto)
        window.png_colors_label.setText(str(window._format_opts.png_max_colors))
        window.scale_slider.setValue(int(round(window._resize.scale_percent)))
        window.scale_label.setText(f"{int(round(window._resize.scale_percent))}%")
        window.min_longest_cb.setChecked(window._resize.min_longest_enabled)
        window.min_longest_edit.setText(str(window._resize.min_longest_px))
        if "output_enabled" in ui:
            window.output_enabled_cb.setChecked(bool(ui["output_enabled"]))
        window._on_output_enabled_toggled(window.output_enabled_cb.isChecked())
        fmts = ui.get("formats") or [applied["output_format"]]
        window.format_combo.set_selected(fmts)
        if "output_dir" in ui:
            window.output_dir_edit.setText(ui["output_dir"])
        if "segregate" in ui:
            window.segregate_cb.setChecked(bool(ui["segregate"]))
        if "wiz_sequence" in ui:
            window.wiz_sequence_cb.setChecked(bool(ui["wiz_sequence"]))
        if "size_preset" in ui:
            sp = ui["size_preset"]
            if isinstance(sp, str):
                pid = sp
            else:
                pid = {
                    0: PRESET_ORIGINAL,
                    1: PRESET_LONG_1200,
                    2: PRESET_SHORT_1200,
                    3: PRESET_SHORT_1200,
                    4: PRESET_BOX_1200,
                }.get(int(sp), PRESET_ORIGINAL)
            window._reload_size_combo(select_id=pid)
            payload = window._custom_preset_payloads.get(pid)
            window._resize, window._transforms = apply_size_preset(pid, custom_payload=payload)
            window._last_size_preset_id = pid
        if "preserve_structure" in ui:
            window.preserve_cb.setChecked(bool(ui["preserve_structure"]))
        if "keep_dates" in ui:
            window.keep_dates_cb.setChecked(bool(ui["keep_dates"]))
        if "overwrite_ask" in ui:
            window.overwrite_cb.setChecked(bool(ui["overwrite_ask"]))
        if "parallel" in ui:
            window.parallel_cb.setChecked(bool(ui["parallel"]))
        if "preview" in ui:
            window.preview_cb.setChecked(bool(ui["preview"]))
        if "sort_mode" in ui:
            window.sort_combo.setCurrentIndex(int(ui["sort_mode"]))
        if "remove_background" in ui:
            window._transforms.remove_background = bool(ui["remove_background"])
        if "bg_model" in ui:
            window._transforms.bg_model = str(ui["bg_model"])
        window._sync_remove_bg_ui()
    finally:
        window._programmatic_settings = False
    window._update_advanced_summary()
    if window._format_opts.png_colors_auto:
        window._sync_png_colors_from_quality()


def save_session(window: MainWindow) -> None:
    s = _settings()
    s.setValue("session", snapshot_from_window(window))


def load_session(window: MainWindow) -> bool:
    raw = _settings().value("session")
    if not raw:
        return False
    if isinstance(raw, dict):
        restore_to_window(window, raw)
        return True
    return False


def persist_all(window: MainWindow) -> None:
    save_geometry(window)
    save_session(window)
    save_theme(window._theme)
