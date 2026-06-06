#!/usr/bin/env python3
"""OmniConverter — macOS desktop app for converting documents."""

import sys
import tempfile
import threading
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal, QObject, QPointF, QRectF
from PyQt6.QtGui import (
    QFont, QPixmap, QPainter, QPen, QColor, QIcon,
    QLinearGradient, QBrush, QPainterPath, QRadialGradient,
)
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QListWidget, QFileDialog, QCheckBox,
    QTextEdit, QProgressBar, QAbstractItemView, QFrame,
)

from converter import INPUT_EXTENSIONS, OUTPUT_FORMATS, convert_file

BG = "#1e1e2e"
BG_DIM = "#181825"
FG = "#cdd6f4"
FG_DIM = "#6c7086"
ACCENT = "#89b4fa"
SUCCESS = "#a6e3a1"
ERROR = "#f38ba8"
WARN = "#fab387"
SURFACE0 = "#313244"
SURFACE1 = "#45475a"
SURFACE2 = "#585b70"
MAUVE = "#cba6f7"
TEAL = "#94e2d5"
LAVENDER = "#b4befe"


def make_app_icon(size=512):
    """Generate the OmniConverter app icon — two overlapping rounded document
    shapes with a circular arrow, in the Catppuccin palette."""
    pixmap = QPixmap(size, size)
    pixmap.fill(QColor(0, 0, 0, 0))
    p = QPainter(pixmap)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    s = size

    # Background rounded square
    bg_grad = QLinearGradient(0, 0, s, s)
    bg_grad.setColorAt(0, QColor("#1e1e2e"))
    bg_grad.setColorAt(1, QColor("#11111b"))
    bg_path = QPainterPath()
    bg_path.addRoundedRect(QRectF(0, 0, s, s), s * 0.22, s * 0.22)
    p.fillPath(bg_path, QBrush(bg_grad))

    # Subtle inner glow
    glow = QRadialGradient(s * 0.5, s * 0.35, s * 0.6)
    glow.setColorAt(0, QColor(137, 180, 250, 30))
    glow.setColorAt(1, QColor(0, 0, 0, 0))
    p.fillPath(bg_path, QBrush(glow))

    # --- Back document (PDF - mauve) ---
    doc1 = QPainterPath()
    dx1, dy1 = s * 0.18, s * 0.15
    dw1, dh1 = s * 0.38, s * 0.48
    doc1.addRoundedRect(QRectF(dx1, dy1, dw1, dh1), s * 0.03, s * 0.03)
    p.fillPath(doc1, QBrush(QColor("#cba6f7")))

    # Lines on back doc
    pen = QPen(QColor("#1e1e2e"), s * 0.015)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    p.setPen(pen)
    for i in range(4):
        ly = dy1 + dh1 * 0.22 + i * dh1 * 0.15
        lx1 = dx1 + dw1 * 0.15
        lx2 = dx1 + dw1 * (0.85 - i * 0.1)
        p.drawLine(QPointF(lx1, ly), QPointF(lx2, ly))

    # --- Front document (EPUB - accent blue) ---
    doc2 = QPainterPath()
    dx2, dy2 = s * 0.42, s * 0.32
    dw2, dh2 = s * 0.40, s * 0.50
    doc2.addRoundedRect(QRectF(dx2, dy2, dw2, dh2), s * 0.03, s * 0.03)

    doc2_grad = QLinearGradient(dx2, dy2, dx2 + dw2, dy2 + dh2)
    doc2_grad.setColorAt(0, QColor("#89b4fa"))
    doc2_grad.setColorAt(1, QColor("#74c7ec"))
    p.fillPath(doc2, QBrush(doc2_grad))

    # Lines on front doc
    pen2 = QPen(QColor("#1e1e2e"), s * 0.015)
    pen2.setCapStyle(Qt.PenCapStyle.RoundCap)
    p.setPen(pen2)
    for i in range(4):
        ly = dy2 + dh2 * 0.2 + i * dh2 * 0.15
        lx1 = dx2 + dw2 * 0.15
        lx2 = dx2 + dw2 * (0.85 - i * 0.08)
        p.drawLine(QPointF(lx1, ly), QPointF(lx2, ly))

    # --- Circular conversion arrow ---
    cx, cy = s * 0.55, s * 0.58
    radius = s * 0.18
    arrow_pen = QPen(QColor("#a6e3a1"), s * 0.035)
    arrow_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    p.setPen(arrow_pen)

    arc_rect = QRectF(cx - radius, cy - radius, radius * 2, radius * 2)
    p.drawArc(arc_rect, 30 * 16, 280 * 16)

    # Arrowhead
    import math
    angle_rad = math.radians(30)
    ax = cx + radius * math.cos(angle_rad)
    ay = cy - radius * math.sin(angle_rad)

    arrow_size = s * 0.06
    p.drawLine(QPointF(ax, ay), QPointF(ax + arrow_size, ay - arrow_size * 0.3))
    p.drawLine(QPointF(ax, ay), QPointF(ax + arrow_size * 0.1, ay - arrow_size))

    p.end()

    icon_path = Path(tempfile.gettempdir()) / "omniconverter_icon.png"
    pixmap.save(str(icon_path))
    return str(icon_path), pixmap


def make_checkmark_icon(color, size=18):
    pixmap = QPixmap(size, size)
    pixmap.fill(QColor(0, 0, 0, 0))
    painter = QPainter(pixmap)
    pen = QPen(QColor(color))
    pen.setWidth(3)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    # Draw checkmark: short stroke down-right, then long stroke up-right
    painter.drawLine(4, 9, 7, 13)
    painter.drawLine(7, 13, 14, 5)
    painter.end()
    path = Path(tempfile.gettempdir()) / "omniconverter_check.png"
    pixmap.save(str(path))
    return str(path)


def btn_style(bg, fg, font_size=12, bold=False, border=None, radius=8, pad_h=18, pad_v=7):
    weight = "bold" if bold else "normal"
    border_css = f"border: {border};" if border else "border: none;"
    if bg.startswith("#") and len(bg) == 7:
        hover_bg = bg.replace("#", "")
        r, g, b = int(hover_bg[:2], 16), int(hover_bg[2:4], 16), int(hover_bg[4:], 16)
        hover = f"#{min(255,r+25):02x}{min(255,g+25):02x}{min(255,b+25):02x}"
    else:
        hover = SURFACE1
    return (
        f"QPushButton {{ background-color: {bg}; color: {fg}; {border_css} "
        f"border-radius: {radius}px; padding: {pad_v}px {pad_h}px; "
        f"font-size: {font_size}px; font-weight: {weight}; }}"
        f"QPushButton:hover {{ background-color: {hover}; }}"
        f"QPushButton:disabled {{ background-color: {SURFACE0}; color: {FG_DIM}; border: 1px solid {SURFACE1}; }}"
    )


GLOBAL_STYLE = f"""
    QMainWindow, QWidget#central {{
        background-color: {BG};
    }}
    QLabel {{
        color: {FG};
        background: transparent;
    }}
    QFrame#card {{
        background-color: {SURFACE0};
        border: 1px solid {SURFACE1};
        border-radius: 10px;
    }}
    QListWidget {{
        background-color: {BG_DIM};
        color: {FG};
        border: 1px solid {SURFACE1};
        border-radius: 6px;
        font-family: Menlo, monospace;
        font-size: 12px;
        padding: 4px;
        outline: none;
    }}
    QListWidget::item {{
        padding: 4px 8px;
        border-radius: 4px;
    }}
    QListWidget::item:selected {{
        background-color: {ACCENT};
        color: {BG};
    }}
    QListWidget::item:hover:!selected {{
        background-color: {SURFACE1};
    }}
    QCheckBox {{
        color: {FG};
        font-size: 14px;
        spacing: 8px;
    }}
    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border: 2px solid {SURFACE2};
        border-radius: 4px;
        background-color: {BG_DIM};
    }}
    QCheckBox::indicator:hover {{
        border-color: {ACCENT};
    }}
    QCheckBox::indicator:checked {{
        background-color: {ACCENT};
        border-color: {ACCENT};
        image: url(CHECKMARK_PATH);
    }}
    QProgressBar {{
        background-color: {SURFACE0};
        border: none;
        border-radius: 4px;
        max-height: 8px;
        min-height: 8px;
    }}
    QProgressBar::chunk {{
        background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {ACCENT}, stop:1 {MAUVE});
        border-radius: 4px;
    }}
    QTextEdit {{
        background-color: {BG_DIM};
        color: {FG};
        border: 1px solid {SURFACE1};
        border-radius: 6px;
        font-family: Menlo, monospace;
        font-size: 12px;
        padding: 8px;
    }}
    QScrollBar:vertical {{
        background: transparent;
        width: 8px;
        margin: 4px 2px;
    }}
    QScrollBar::handle:vertical {{
        background: {SURFACE1};
        border-radius: 4px;
        min-height: 20px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {SURFACE2};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: transparent;
        height: 0px;
    }}
"""


class LogSignals(QObject):
    log = pyqtSignal(str, str)
    progress = pyqtSignal(int, int)
    finished = pyqtSignal()


class OmniConverterApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OmniConverter")
        self.setMinimumSize(560, 540)
        self.resize(680, 660)

        self.files = []
        self.output_dir = None
        self.format_vars = {}
        self.converting = False
        self.cancel_flag = threading.Event()

        self.signals = LogSignals()
        self.signals.log.connect(self._append_log)
        self.signals.progress.connect(self._update_progress)
        self.signals.finished.connect(self._finish_convert)

        icon_path, self.icon_pixmap = make_app_icon()
        self.setWindowIcon(QIcon(icon_path))

        check_path = make_checkmark_icon(BG_DIM)
        self.setStyleSheet(GLOBAL_STYLE.replace("CHECKMARK_PATH", check_path))
        self._build_ui()

    def _make_card(self):
        card = QFrame()
        card.setObjectName("card")
        return card

    def _make_btn(self, text, bg, fg, font_size=12, bold=False, border=None, radius=8, pad_h=18, pad_v=7):
        b = QPushButton(text)
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        b.setStyleSheet(btn_style(bg, fg, font_size, bold, border, radius, pad_h, pad_v))
        return b

    def _build_ui(self):
        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(14)

        # --- Header ---
        header_row = QHBoxLayout()
        header_row.setSpacing(14)

        icon_label = QLabel()
        icon_label.setPixmap(self.icon_pixmap.scaled(
            48, 48, Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation))
        icon_label.setFixedSize(48, 48)
        header_row.addWidget(icon_label)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        title = QLabel("OmniConverter")
        title.setFont(QFont("Helvetica Neue", 22, QFont.Weight.Bold))
        title_col.addWidget(title)

        subtitle = QLabel("Convert documents between formats")
        subtitle.setStyleSheet(f"color: {FG_DIM}; font-size: 12px;")
        title_col.addWidget(subtitle)

        header_row.addLayout(title_col)
        header_row.addStretch()
        root.addLayout(header_row)

        # ===================== INPUT FILES CARD =====================
        input_card = self._make_card()
        ic = QVBoxLayout(input_card)
        ic.setContentsMargins(16, 14, 16, 14)
        ic.setSpacing(10)

        # Header row
        row1 = QHBoxLayout()
        row1.setSpacing(8)

        section_lbl = QLabel("INPUT FILES")
        section_lbl.setStyleSheet(f"color: {LAVENDER}; font-size: 13px; font-weight: 600;")
        row1.addWidget(section_lbl)

        self.file_count_label = QLabel("0 files")
        self.file_count_label.setStyleSheet(f"color: {FG_DIM}; font-size: 12px;")
        row1.addWidget(self.file_count_label)
        row1.addStretch()

        add_btn = self._make_btn("+ Add Files", ACCENT, BG_DIM, bold=True)
        add_btn.clicked.connect(self._add_files)
        row1.addWidget(add_btn)

        remove_btn = self._make_btn("Remove", SURFACE1, FG, border=f"1px solid {SURFACE2}")
        remove_btn.clicked.connect(self._remove_selected)
        row1.addWidget(remove_btn)

        clear_btn = self._make_btn("Clear", SURFACE1, FG, border=f"1px solid {SURFACE2}")
        clear_btn.clicked.connect(self._clear_files)
        row1.addWidget(clear_btn)

        ic.addLayout(row1)

        # File list
        self.file_list = QListWidget()
        self.file_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.file_list.setFixedHeight(100)
        ic.addWidget(self.file_list)

        root.addWidget(input_card)

        hint = QLabel("Supports PDF, TXT, HTML, HTM")
        hint.setStyleSheet(f"color: {SURFACE2}; font-size: 11px; padding-left: 4px;")
        root.addWidget(hint)

        # ===================== OUTPUT DIRECTORY CARD =====================
        output_card = self._make_card()
        oc = QVBoxLayout(output_card)
        oc.setContentsMargins(16, 14, 16, 14)
        oc.setSpacing(10)

        row2 = QHBoxLayout()
        out_lbl = QLabel("OUTPUT DIRECTORY")
        out_lbl.setStyleSheet(f"color: {LAVENDER}; font-size: 13px; font-weight: 600;")
        row2.addWidget(out_lbl)
        row2.addStretch()

        browse_btn = self._make_btn("Browse", ACCENT, BG_DIM, bold=True)
        browse_btn.clicked.connect(self._choose_output)
        row2.addWidget(browse_btn)

        oc.addLayout(row2)

        self.output_path_label = QLabel("No directory selected")
        self.output_path_label.setStyleSheet(
            f"color: {FG_DIM}; font-family: Menlo; font-size: 12px; "
            f"padding: 8px 12px; background-color: {BG_DIM}; "
            f"border: 1px solid {SURFACE1}; border-radius: 6px;")
        oc.addWidget(self.output_path_label)

        root.addWidget(output_card)

        # ===================== FORMAT + ACTIONS ROW =====================
        bottom = QHBoxLayout()
        bottom.setSpacing(14)

        # --- Format card ---
        fmt_card = self._make_card()
        fc = QVBoxLayout(fmt_card)
        fc.setContentsMargins(16, 14, 16, 14)
        fc.setSpacing(12)

        fmt_lbl = QLabel("OUTPUT FORMAT")
        fmt_lbl.setStyleSheet(f"color: {LAVENDER}; font-size: 13px; font-weight: 600;")
        fc.addWidget(fmt_lbl)

        labels = {"epub": "EPUB", "pdf": "PDF"}
        for fmt in OUTPUT_FORMATS:
            cb = QCheckBox(labels[fmt])
            cb.setChecked(fmt == "epub")
            cb.setCursor(Qt.CursorShape.PointingHandCursor)
            self.format_vars[fmt] = cb
            fc.addWidget(cb)

        fc.addStretch()
        bottom.addWidget(fmt_card)

        # --- Actions area (no card, just buttons) ---
        action_box = QVBoxLayout()
        action_box.setSpacing(10)

        action_lbl = QLabel("ACTIONS")
        action_lbl.setStyleSheet(f"color: {LAVENDER}; font-size: 13px; font-weight: 600;")
        action_box.addWidget(action_lbl)

        self.convert_btn = self._make_btn(
            "Convert", ACCENT, BG_DIM, font_size=15, bold=True, radius=10, pad_h=32, pad_v=10)
        self.convert_btn.clicked.connect(self._start_convert)
        action_box.addWidget(self.convert_btn)

        self.cancel_btn = self._make_btn(
            "Cancel", "transparent", ERROR, font_size=13, border=f"2px solid {ERROR}", radius=10, pad_h=20, pad_v=8)
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self._cancel_convert)
        action_box.addWidget(self.cancel_btn)

        action_box.addStretch()
        bottom.addLayout(action_box)

        root.addLayout(bottom)

        # ===================== PROGRESS =====================
        self.progress_label = QLabel("")
        self.progress_label.setStyleSheet(f"color: {ACCENT}; font-size: 11px;")
        self.progress_label.hide()
        root.addWidget(self.progress_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setValue(0)
        self.progress_bar.hide()
        root.addWidget(self.progress_bar)

        # ===================== LOG =====================
        log_header = QHBoxLayout()
        log_lbl = QLabel("LOG")
        log_lbl.setStyleSheet(f"color: {LAVENDER}; font-size: 13px; font-weight: 600;")
        log_header.addWidget(log_lbl)
        log_header.addStretch()

        clear_log_btn = QPushButton("Clear")
        clear_log_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_log_btn.setStyleSheet(
            f"QPushButton {{ background: transparent; color: {FG_DIM}; border: none; font-size: 11px; padding: 4px 8px; }}"
            f"QPushButton:hover {{ color: {FG}; }}")
        clear_log_btn.clicked.connect(self._clear_log)
        log_header.addWidget(clear_log_btn)

        root.addLayout(log_header)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(80)
        root.addWidget(self.log_text, stretch=1)

    # --- Actions ---

    def _add_files(self):
        ext_filter = " ".join(f"*{e}" for e in INPUT_EXTENSIONS)
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Select files to convert", "",
            f"Supported files ({ext_filter});;All files (*)",
        )
        for p in paths:
            path = Path(p)
            if path not in self.files:
                self.files.append(path)
                self.file_list.addItem(path.name)
        self._update_file_count()

    def _remove_selected(self):
        for item in reversed(self.file_list.selectedItems()):
            idx = self.file_list.row(item)
            self.file_list.takeItem(idx)
            del self.files[idx]
        self._update_file_count()

    def _clear_files(self):
        self.files.clear()
        self.file_list.clear()
        self._update_file_count()

    def _update_file_count(self):
        n = len(self.files)
        self.file_count_label.setText(f"{n} file{'s' if n != 1 else ''}" if n else "0 files")

    def _choose_output(self):
        path = QFileDialog.getExistingDirectory(self, "Choose output directory")
        if path:
            self.output_dir = Path(path)
            display = str(self.output_dir)
            if len(display) > 50:
                display = "..." + display[-47:]
            self.output_path_label.setText(display)
            self.output_path_label.setStyleSheet(
                f"color: {TEAL}; font-family: Menlo; font-size: 12px; "
                f"padding: 8px 12px; background-color: {BG_DIM}; "
                f"border: 1px solid {SURFACE1}; border-radius: 6px;")

    def _append_log(self, msg, tag):
        color_map = {
            "success": SUCCESS, "error": ERROR,
            "info": ACCENT, "warn": WARN, "dim": FG_DIM,
        }
        color = color_map.get(tag, FG)
        self.log_text.append(f'<span style="color:{color};">{msg}</span>')

    def _clear_log(self):
        self.log_text.clear()

    def _update_progress(self, current, total):
        if total == 0:
            self.progress_label.hide()
            self.progress_bar.hide()
            self.progress_bar.setValue(0)
            return
        self.progress_label.setText(f"Converting {current} of {total}...")
        self.progress_label.show()
        self.progress_bar.show()
        self.progress_bar.setValue(int(100 * current / total))

    def _start_convert(self):
        if self.converting:
            return
        if not self.files:
            self.signals.log.emit("No files selected.", "error")
            return
        if not self.output_dir:
            self.signals.log.emit("No output directory selected.", "error")
            return

        formats = [fmt for fmt, cb in self.format_vars.items() if cb.isChecked()]
        if not formats:
            self.signals.log.emit("No output format selected.", "error")
            return

        self.converting = True
        self.cancel_flag.clear()
        self.convert_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)

        fmt_str = ", ".join(f.upper() for f in formats)
        self.signals.log.emit(f"Converting {len(self.files)} file(s) → {fmt_str}", "info")

        thread = threading.Thread(
            target=self._convert_worker,
            args=(list(self.files), self.output_dir, formats),
            daemon=True,
        )
        thread.start()

    def _cancel_convert(self):
        if self.converting:
            self.cancel_flag.set()
            self.signals.log.emit("Cancelling...", "warn")

    def _convert_worker(self, files, output_dir, formats):
        output_dir.mkdir(parents=True, exist_ok=True)
        total = len(files) * len(formats)
        done = 0
        success_count = 0
        fail_count = 0

        for filepath in files:
            if self.cancel_flag.is_set():
                break
            self.signals.log.emit(f"  {filepath.name}", "dim")
            results = convert_file(filepath, output_dir, formats)

            for fmt, result in results:
                if self.cancel_flag.is_set():
                    break
                done += 1
                self.signals.progress.emit(done, total)

                if result.startswith(("Error:", "Read error:", "Unsupported")):
                    self.signals.log.emit(f"    {fmt.upper()}: {result}", "error")
                    fail_count += 1
                else:
                    name = Path(result).name
                    self.signals.log.emit(f"    {fmt.upper()}: {name}", "success")
                    success_count += 1

        if self.cancel_flag.is_set():
            self.signals.log.emit(
                f"Cancelled. {success_count} completed before stop.", "warn")
        else:
            summary = f"Done — {success_count} succeeded"
            if fail_count:
                summary += f", {fail_count} failed"
            self.signals.log.emit(summary, "info")

        self.signals.finished.emit()

    def _finish_convert(self):
        self.converting = False
        self.cancel_flag.clear()
        self.convert_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.signals.progress.emit(0, 0)


def main():
    app = QApplication(sys.argv)
    icon_path, _ = make_app_icon()
    app.setWindowIcon(QIcon(icon_path))
    window = OmniConverterApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
