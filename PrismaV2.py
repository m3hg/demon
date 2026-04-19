import json
import os
import platform
import socket
import sys
import threading
import time
import ctypes
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Set, Tuple

from PyQt6.QtCore import QThread, QTimer, Qt, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
    QColorDialog,
    QInputDialog,
)

APP_NAME = "Prisma Vision Engine v5.0.0"
ROOT = Path(__file__).resolve().parent
CFG_PATH = ROOT / "config.json"
PROFILES_PATH = ROOT / "profiles.json"


def _try_import(name: str) -> bool:
    try:
        __import__(name)
        return True
    except Exception:
        return False


HAS_PYAUTOGUI = _try_import("pyautogui")
HAS_DXCAM = _try_import("dxcam")
HAS_MSS = _try_import("mss")
HAS_VG = _try_import("vgamepad")
HAS_KB = _try_import("keyboard")
HAS_PSUTIL = _try_import("psutil")
HAS_PYDIVERT = _try_import("pydivert")

def _is_admin() -> bool:
    if os.name == "nt":
        try:
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except Exception:
            return False
    geteuid = getattr(os, "geteuid", None)
    return bool(geteuid and geteuid() == 0)


IS_ADMIN = _is_admin()


DEF_CFG = {
    "hex_color": "#FF0000",
    "tolerance": 25,
    "contour_area": 100,
    "target": 5,
    "contested_target": 3,
    "contested": False,
    "bbox_w": 120,
    "bbox_h": 120,
    "bbox_pad": 5,
    "bbox_thick": 2,
    "overlay": True,
    "hud": True,
    "show_roi": True,
    "flick_ms": 60,
    "auto_dashboard": False,
    "roi_enabled": False,
    "roi_w": 640,
    "roi_h": 360,
    "roi_thick": 2,
    "roi_color": [255, 0, 0],
    "defense": False,
    "lt_thresh": 80,
    "shuffle_boost": 15,
    "bump": 10,
    "autosync": False,
    "latency_sensitivity": 1.0,
    "jitter_dampen_px": 1.0,
    "sync_max_offset_px": 15,
    "stab_enabled": False,
    "stab_xbox_ip": "",
    "stab_public_iface": "",
    "stab_private_iface": "",
    "stab_mode": "bridge",
    "controller_port": "1",
}


# ----------------------- auth / licensing stubs -----------------------

def validate_license() -> bool:
    if check_blacklist():
        return False
    if os.getenv("PRISMA_FORCE_AUTH", "").strip().lower() in {"1", "true", "yes"}:
        return False
    lic_path = ROOT / "license.key"
    if lic_path.exists():
        try:
            key = lic_path.read_text(encoding="utf-8").strip()
            return verify_key_signature(key)
        except Exception:
            return False
    return True


def decrypt_engine() -> bool:
    return True


def verify_key_signature(_: str) -> bool:
    return bool(_ and len(_.strip()) >= 8)


def check_blacklist() -> bool:
    return False


class AuthDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("License Required")
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel("License validation failed. Continue?"))
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)


# ----------------------- config helpers -----------------------

def _load_config() -> dict:
    if not CFG_PATH.exists():
        return dict(DEF_CFG)
    try:
        data = json.loads(CFG_PATH.read_text(encoding="utf-8"))
        cfg = dict(DEF_CFG)
        cfg.update(data if isinstance(data, dict) else {})
        return cfg
    except Exception:
        return dict(DEF_CFG)


def _atomic_write_json(path: Path, data: dict):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.replace(path)


def _read_profiles() -> dict:
    if not PROFILES_PATH.exists():
        return {}
    try:
        raw = json.loads(PROFILES_PATH.read_text(encoding="utf-8"))
        return raw if isinstance(raw, dict) else {}
    except Exception:
        return {}


def _write_profiles(profiles: dict):
    _atomic_write_json(PROFILES_PATH, profiles)


# ----------------------- stabilizer primitives -----------------------

@dataclass
class StabConfig:
    poll_ms: int = 500


class NetworkUtils:
    @staticmethod
    def interface_to_ips(name: str) -> Set[str]:
        if not name:
            return set()
        return {"127.0.0.1"}


class RawSniffer:
    pass


def parse_ip_udp(_: bytes) -> Tuple[str, str, int, int]:
    return "0.0.0.0", "0.0.0.0", 0, 0


class PortPairedRTT:
    pass


class BandwidthDetector:
    pass


class TrafficShaper:
    pass


class InboundDejitter:
    pass


class JitterSmoother:
    pass


class ServerSync:
    pass


class PacketStats:
    def __init__(self):
        self.rtt_ms = 0.0
        self.jitter_ms = 0.0
        self.quality = 100.0
        self.server_count = 0
        self.tick = 0
        self.bandwidth_mbps = 0.0


class LatencyAutoTuner:
    def __init__(self):
        self.offset_px = 0
        self.rtt_ms = 0.0
        self.jitter_ms = 0.0

    def on_server_change(self, _servers: List[str]):
        pass


class StabilizerEngine:
    def __init__(
        self,
        xbox_ip: str,
        local_ips: Set[str],
        public_ip: str,
        private_ip: str,
        stats: PacketStats,
        mode: str,
    ):
        self.xbox_ip = xbox_ip
        self.local_ips = local_ips
        self.public_ip = public_ip
        self.private_ip = private_ip
        self.stats = stats
        self.mode = mode
        self.server_change_callback: Optional[Callable[[List[str]], None]] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def _loop(self):
        servers = [self.xbox_ip] if self.xbox_ip else []
        while self._running:
            self.stats.tick += 1
            self.stats.rtt_ms = 20.0 + (self.stats.tick % 7)
            self.stats.jitter_ms = 2.0 + (self.stats.tick % 3) * 0.7
            self.stats.quality = max(0.0, 100.0 - self.stats.jitter_ms * 2)
            self.stats.server_count = len(servers)
            self.stats.bandwidth_mbps = 80.0 + (self.stats.tick % 5) * 3
            if self.server_change_callback and self.stats.tick == 1:
                self.server_change_callback(servers)
            time.sleep(0.5)

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False


# ----------------------- cv / engine stubs -----------------------

class Capture:
    pass


class FPSTracker:
    pass


class Proxy:
    pass


class AutoDashboard:
    pass


class ColorManager:
    pass


class CVWorker:
    pass


class PrismaOverlay:
    pass


class Engine(QThread):
    stateChanged = pyqtSignal(str)
    fpsChanged = pyqtSignal(float)

    def __init__(self):
        super().__init__()
        self._armed = False

    def arm(self):
        self._armed = True
        self.stateChanged.emit("ARMED")

    def disarm(self):
        self._armed = False
        self.stateChanged.emit("DISARMED")


class ScreenColorPicker:
    pass


# ----------------------- style helpers -----------------------

ACCENT = "#7C4DFF"
BG_DEEP = "#111316"
BG_CARD = "#1A1E23"
FG = "#F2F5F8"
SUBTLE = "#9BA7B4"


INIT_PORTS = ["1", "2", "3", "4"]


def make_card(title: str, body: QWidget) -> QFrame:
    frame = QFrame()
    frame.setStyleSheet(f"QFrame{{background:{BG_CARD};border-radius:10px;padding:8px;}}")
    lay = QVBoxLayout(frame)
    lbl = QLabel(title)
    lbl.setStyleSheet("font-weight:700;font-size:14px;")
    lay.addWidget(lbl)
    lay.addWidget(body)
    return frame


def accent_button(text: str) -> QPushButton:
    b = QPushButton(text)
    b.setStyleSheet(f"QPushButton{{background:{ACCENT};color:white;padding:8px 12px;border-radius:8px;}}")
    return b


def ghost_button(text: str) -> QPushButton:
    b = QPushButton(text)
    b.setStyleSheet("QPushButton{background:transparent;border:1px solid #38424f;padding:8px 12px;border-radius:8px;color:#d5dde6;}")
    return b


def _mk_spin(min_v: int, max_v: int, val: int) -> QSpinBox:
    s = QSpinBox()
    s.setRange(min_v, max_v)
    s.setValue(val)
    return s


def _mk_dspin(min_v: float, max_v: float, step: float, val: float) -> QDoubleSpinBox:
    s = QDoubleSpinBox()
    s.setRange(min_v, max_v)
    s.setSingleStep(step)
    s.setValue(val)
    return s


def spin_row(label: str, widget: QWidget) -> QWidget:
    row = QWidget()
    lay = QHBoxLayout(row)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.addWidget(QLabel(label))
    lay.addStretch(1)
    lay.addWidget(widget)
    return row


def _make_scroll(inner: QWidget) -> QScrollArea:
    sc = QScrollArea()
    sc.setWidgetResizable(True)
    sc.setFrameShape(QFrame.Shape.NoFrame)
    sc.setWidget(inner)
    return sc


# ----------------------- ui atoms -----------------------

class NavButton(QPushButton):
    pass


class StatusPill(QLabel):
    pass


class TitleBar(QWidget):
    pass


class XboxSetupDialog(QDialog):
    def __init__(self, cfg: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configure Stabilizer")
        lay = QVBoxLayout(self)
        self.edit_xbox = QLineEdit(cfg.get("stab_xbox_ip", ""))
        self.edit_public = QLineEdit(cfg.get("stab_public_iface", ""))
        self.edit_private = QLineEdit(cfg.get("stab_private_iface", ""))
        self.combo_mode = QComboBox()
        self.combo_mode.addItems(["bridge", "ics"])
        self.combo_mode.setCurrentText(cfg.get("stab_mode", "bridge"))
        lay.addWidget(spin_row("Xbox IP", self.edit_xbox))
        lay.addWidget(spin_row("Public interface", self.edit_public))
        lay.addWidget(spin_row("Private interface", self.edit_private))
        lay.addWidget(spin_row("Mode", self.combo_mode))
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def values(self) -> Tuple[str, str, str, str]:
        return (
            self.edit_xbox.text().strip(),
            self.edit_public.text().strip(),
            self.edit_private.text().strip(),
            self.combo_mode.currentText().strip(),
        )


class MetricCard(QFrame):
    def __init__(self, title: str, unit: str = ""):
        super().__init__()
        self.unit = unit
        self.setStyleSheet(f"QFrame{{background:{BG_CARD};border:1px solid #2b3440;border-radius:10px;padding:8px;}}")
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel(title))
        self.value = QLabel("--")
        self.value.setStyleSheet("font-size:20px;font-weight:700;")
        lay.addWidget(self.value)

    def set_metric(self, v):
        suffix = f" {self.unit}" if self.unit else ""
        self.value.setText(f"{v}{suffix}")


# ----------------------- main window -----------------------

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(1200, 820)
        self.cfg = _load_config()
        self._autosave_timer = QTimer(self)
        self._autosave_timer.setSingleShot(True)
        self._autosave_timer.timeout.connect(self._do_autosave)

        self._eng = Engine()
        self._eng.stateChanged.connect(self._on_state)
        self._eng.fpsChanged.connect(self._on_fps)

        self._auto_tuner = LatencyAutoTuner()
        self._stab_engine: Optional[StabilizerEngine] = None
        self._stab_stats: Optional[PacketStats] = None
        self._stab_running = False

        self._build_ui()

        self._poll_timer = QTimer(self)
        self._poll_timer.timeout.connect(self._poll)
        self._poll_timer.start(500)

    def _on_server_change(self, servers: List[str]):
        self._auto_tuner.on_server_change(servers)
        if servers:
            self._stab_server_list.setText("Detected servers: " + ", ".join(servers))
        else:
            self._stab_server_list.setText("Detected servers: --")

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        main = QHBoxLayout(root)

        nav = QVBoxLayout()
        main.addLayout(nav, 0)

        self.pages = QStackedWidget()
        main.addWidget(self.pages, 1)

        page_specs = [
            ("General", self._build_general),
            ("Detection", self._build_detection),
            ("Stabilizer", self._build_stabilizer),
            ("Auto-Sync", self._build_autosync),
            ("ROI", self._build_roi),
            ("Defense", self._build_defense),
            ("Profiles", self._build_profiles),
            ("Engine", self._build_engine),
        ]

        for idx, (name, fn) in enumerate(page_specs):
            btn = NavButton(name)
            btn.clicked.connect(lambda _=False, i=idx: self.pages.setCurrentIndex(i))
            nav.addWidget(btn)
            self.pages.addWidget(fn())

        nav.addStretch(1)

    def _wire_autosave(self, *widgets):
        for w in widgets:
            if isinstance(w, QCheckBox):
                w.stateChanged.connect(self._autosave_debounced)
            elif isinstance(w, (QSpinBox, QDoubleSpinBox)):
                w.valueChanged.connect(self._autosave_debounced)
            elif isinstance(w, QLineEdit):
                w.textChanged.connect(self._autosave_debounced)
            elif isinstance(w, QComboBox):
                w.currentTextChanged.connect(self._autosave_debounced)

    def _build_general(self) -> QScrollArea:
        page = QWidget()
        lay = QVBoxLayout(page)

        body = QWidget()
        bl = QVBoxLayout(body)
        self.edit_hex_color = QLineEdit(self.cfg.get("hex_color", "#FF0000"))
        self.color_preview = QLabel("Preview")
        self.color_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.color_preview.setMinimumHeight(48)
        self.edit_hex_color.textChanged.connect(self._refresh_preview)
        self._refresh_preview(self.edit_hex_color.text())

        self.spin_tolerance = _mk_spin(0, 255, int(self.cfg.get("tolerance", 25)))
        self.spin_contour_area = _mk_spin(0, 100000, int(self.cfg.get("contour_area", 100)))
        self.spin_flick_ms = _mk_spin(0, 500, int(self.cfg.get("flick_ms", 60)))
        self.chk_auto_dashboard = QCheckBox("Auto Dashboard")
        self.chk_auto_dashboard.setChecked(bool(self.cfg.get("auto_dashboard", False)))

        bl.addWidget(spin_row("Color (hex)", self.edit_hex_color))
        bl.addWidget(self.color_preview)
        bl.addWidget(spin_row("Tolerance", self.spin_tolerance))
        bl.addWidget(spin_row("Contour Area", self.spin_contour_area))
        bl.addWidget(spin_row("Flick (ms)", self.spin_flick_ms))
        bl.addWidget(self.chk_auto_dashboard)
        lay.addWidget(make_card("General", body))
        lay.addStretch(1)

        self._wire_autosave(
            self.edit_hex_color,
            self.spin_tolerance,
            self.spin_contour_area,
            self.spin_flick_ms,
            self.chk_auto_dashboard,
        )
        return _make_scroll(page)

    def _build_detection(self) -> QScrollArea:
        page = QWidget()
        lay = QVBoxLayout(page)

        body = QWidget()
        bl = QVBoxLayout(body)
        self.spin_target = _mk_spin(1, 10, int(self.cfg.get("target", 5)))
        self.spin_contested_target = _mk_spin(1, 10, int(self.cfg.get("contested_target", 3)))
        self.chk_contested = QCheckBox("Enable contested target")
        self.chk_contested.setChecked(bool(self.cfg.get("contested", False)))
        self.spin_bbox_w = _mk_spin(10, 3840, int(self.cfg.get("bbox_w", 120)))
        self.spin_bbox_h = _mk_spin(10, 2160, int(self.cfg.get("bbox_h", 120)))
        self.spin_bbox_pad = _mk_spin(0, 200, int(self.cfg.get("bbox_pad", 5)))
        self.spin_bbox_thick = _mk_spin(1, 20, int(self.cfg.get("bbox_thick", 2)))
        self.chk_overlay = QCheckBox("Overlay")
        self.chk_overlay.setChecked(bool(self.cfg.get("overlay", True)))
        self.chk_hud = QCheckBox("HUD")
        self.chk_hud.setChecked(bool(self.cfg.get("hud", True)))
        self.chk_show_roi = QCheckBox("Show ROI")
        self.chk_show_roi.setChecked(bool(self.cfg.get("show_roi", True)))

        for row in [
            spin_row("Target", self.spin_target),
            spin_row("Contested Target", self.spin_contested_target),
            self.chk_contested,
            spin_row("BBox Width", self.spin_bbox_w),
            spin_row("BBox Height", self.spin_bbox_h),
            spin_row("BBox Padding", self.spin_bbox_pad),
            spin_row("BBox Thickness", self.spin_bbox_thick),
            self.chk_overlay,
            self.chk_hud,
            self.chk_show_roi,
        ]:
            bl.addWidget(row)

        lay.addWidget(make_card("Detection", body))
        lay.addStretch(1)

        self._wire_autosave(
            self.spin_target,
            self.spin_contested_target,
            self.chk_contested,
            self.spin_bbox_w,
            self.spin_bbox_h,
            self.spin_bbox_pad,
            self.spin_bbox_thick,
            self.chk_overlay,
            self.chk_hud,
            self.chk_show_roi,
        )
        return _make_scroll(page)

    def _refresh_preview(self, hex_color):
        color = QColor(hex_color)
        if color.isValid():
            brightness = (color.red() * 299 + color.green() * 587 + color.blue() * 114) // 1000
            text = "#000000" if brightness > 128 else "#FFFFFF"
            self.color_preview.setStyleSheet(
                f"QLabel{{background:{color.name()};color:{text};border:1px solid #2f3a46;border-radius:8px;}}"
            )
            self.color_preview.setText(color.name().upper())
        else:
            self.color_preview.setStyleSheet(
                "QLabel{background:#5a626d;color:#f0f3f6;border:1px solid #2f3a46;border-radius:8px;}"
            )
            self.color_preview.setText("Invalid Color")

    def _build_stabilizer(self) -> QScrollArea:
        page = QWidget()
        lay = QVBoxLayout(page)

        ctl = QWidget()
        cl = QVBoxLayout(ctl)
        self.chk_stab_enabled = QCheckBox("Enable Stabilizer")
        self.chk_stab_enabled.setChecked(bool(self.cfg.get("stab_enabled", False)))
        self.btn_stab_setup = ghost_button("Configure Stabilizer…")
        self.btn_stab_toggle = accent_button("Start / Stop")

        cl.addWidget(self.chk_stab_enabled)
        cl.addWidget(self.btn_stab_setup)
        cl.addWidget(self.btn_stab_toggle)

        if not HAS_PYDIVERT or not HAS_PSUTIL:
            warn = QLabel("Warning: pydivert and/or psutil not installed. Stabilizer cannot start.")
            warn.setStyleSheet("color:#ffb4b4;")
            cl.addWidget(warn)

        dash = QWidget()
        g = QGridLayout(dash)
        self._stab_metric_rtt = MetricCard("RTT", "ms")
        self._stab_metric_jitter = MetricCard("Jitter", "ms")
        self._stab_metric_quality = MetricCard("Quality", "%")
        self._stab_metric_servers = MetricCard("Servers")
        self._stab_metric_tick = MetricCard("Tick")
        self._stab_metric_bw = MetricCard("Bandwidth", "Mbps")
        cards = [
            self._stab_metric_rtt,
            self._stab_metric_jitter,
            self._stab_metric_quality,
            self._stab_metric_servers,
            self._stab_metric_tick,
            self._stab_metric_bw,
        ]
        for index, card in enumerate(cards):
            g.addWidget(card, index // 3, index % 3)

        self._stab_server_list = QLabel("Detected servers: --")
        self._stab_server_list.setWordWrap(True)

        lay.addWidget(make_card("Stabilizer Control", ctl))
        lay.addWidget(make_card("Live Dashboard", dash))
        lay.addWidget(make_card("Server List", self._stab_server_list))
        lay.addStretch(1)

        self.chk_stab_enabled.stateChanged.connect(self._toggle_stabilizer)
        self.btn_stab_setup.clicked.connect(self._open_stab_setup)
        self.btn_stab_toggle.clicked.connect(self._toggle_stabilizer)
        self._wire_autosave(self.chk_stab_enabled)
        return _make_scroll(page)

    def _build_autosync(self) -> QScrollArea:
        page = QWidget()
        lay = QVBoxLayout(page)

        body = QWidget()
        bl = QVBoxLayout(body)
        self.chk_autosync = QCheckBox("Enable Auto-Sync")
        self.chk_autosync.setChecked(bool(self.cfg.get("autosync", False)))
        self.dspin_sensitivity = _mk_dspin(0.0, 5.0, 0.1, float(self.cfg.get("latency_sensitivity", 1.0)))
        self.dspin_jitter_dampen = _mk_dspin(0.0, 5.0, 0.1, float(self.cfg.get("jitter_dampen_px", 1.0)))
        self.spin_max_offset = _mk_spin(0, 60, int(self.cfg.get("sync_max_offset_px", 15)))
        self._autosync_readout = QLabel("Offset: 0 px | RTT: 0.0 ms | Jitter: 0.0 ms")

        bl.addWidget(self.chk_autosync)
        bl.addWidget(spin_row("Latency sensitivity", self.dspin_sensitivity))
        bl.addWidget(spin_row("Jitter dampen", self.dspin_jitter_dampen))
        bl.addWidget(spin_row("Max offset", self.spin_max_offset))
        bl.addWidget(self._autosync_readout)

        lay.addWidget(make_card("Auto-Sync", body))
        lay.addStretch(1)

        self._wire_autosave(
            self.chk_autosync,
            self.dspin_sensitivity,
            self.dspin_jitter_dampen,
            self.spin_max_offset,
        )
        return _make_scroll(page)

    def _build_roi(self) -> QScrollArea:
        page = QWidget()
        lay = QVBoxLayout(page)

        body = QWidget()
        bl = QVBoxLayout(body)
        self.chk_roi_enabled = QCheckBox("Enable ROI")
        self.chk_roi_enabled.setChecked(bool(self.cfg.get("roi_enabled", False)))
        self.spin_roi_w = _mk_spin(10, 3840, int(self.cfg.get("roi_w", 640)))
        self.spin_roi_h = _mk_spin(10, 2160, int(self.cfg.get("roi_h", 360)))
        self.spin_roi_thick = _mk_spin(1, 10, int(self.cfg.get("roi_thick", 2)))
        btn_pick = ghost_button("Pick ROI Color")

        def _pick_roi_color():
            r, g, b = self.cfg.get("roi_color", [255, 0, 0])
            col = QColorDialog.getColor(QColor(r, g, b), self, "Pick ROI Color")
            if col.isValid():
                self.cfg["roi_color"] = [col.red(), col.green(), col.blue()]
                self._autosave_now()

        btn_pick.clicked.connect(_pick_roi_color)

        bl.addWidget(self.chk_roi_enabled)
        bl.addWidget(spin_row("ROI Width", self.spin_roi_w))
        bl.addWidget(spin_row("ROI Height", self.spin_roi_h))
        bl.addWidget(spin_row("ROI Thickness", self.spin_roi_thick))
        bl.addWidget(btn_pick)

        lay.addWidget(make_card("ROI", body))
        lay.addStretch(1)

        self._wire_autosave(self.chk_roi_enabled, self.spin_roi_w, self.spin_roi_h, self.spin_roi_thick)
        return _make_scroll(page)

    def _build_defense(self) -> QScrollArea:
        page = QWidget()
        lay = QVBoxLayout(page)

        body = QWidget()
        bl = QVBoxLayout(body)
        self.chk_defense = QCheckBox("Enable Defense")
        self.chk_defense.setChecked(bool(self.cfg.get("defense", False)))
        self.spin_lt_thresh = _mk_spin(0, 255, int(self.cfg.get("lt_thresh", 80)))
        self.spin_shuffle_boost = _mk_spin(0, 100, int(self.cfg.get("shuffle_boost", 15)))
        self.spin_bump = _mk_spin(0, 100, int(self.cfg.get("bump", 10)))

        bl.addWidget(self.chk_defense)
        bl.addWidget(spin_row("LT Threshold", self.spin_lt_thresh))
        bl.addWidget(spin_row("Shuffle Boost", self.spin_shuffle_boost))
        bl.addWidget(spin_row("Bump", self.spin_bump))

        lay.addWidget(make_card("Defense", body))
        lay.addStretch(1)

        self._wire_autosave(self.chk_defense, self.spin_lt_thresh, self.spin_shuffle_boost, self.spin_bump)
        return _make_scroll(page)

    def _build_profiles(self) -> QScrollArea:
        page = QWidget()
        lay = QVBoxLayout(page)

        body = QWidget()
        bl = QVBoxLayout(body)
        self.profile_list = QListWidget()
        self.btn_profile_save = accent_button("Save")
        self.btn_profile_load = ghost_button("Load")
        self.btn_profile_delete = ghost_button("Delete")
        self.btn_profile_rename = ghost_button("Rename")

        row = QWidget()
        rl = QHBoxLayout(row)
        rl.addWidget(self.btn_profile_save)
        rl.addWidget(self.btn_profile_load)
        rl.addWidget(self.btn_profile_delete)
        rl.addWidget(self.btn_profile_rename)

        bl.addWidget(self.profile_list)
        bl.addWidget(row)

        lay.addWidget(make_card("Profiles", body))
        lay.addStretch(1)

        self.btn_profile_save.clicked.connect(self._save_profile)
        self.btn_profile_load.clicked.connect(self._load_selected_profile)
        self.btn_profile_delete.clicked.connect(self._delete_selected_profile)
        self.btn_profile_rename.clicked.connect(self._rename_selected_profile)

        self._refresh_profiles()
        return _make_scroll(page)

    def _build_engine(self) -> QScrollArea:
        page = QWidget()
        lay = QVBoxLayout(page)

        body = QWidget()
        bl = QVBoxLayout(body)

        self._eng_state_lbl = QLabel("DISARMED")
        self._eng_state_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._eng_state_lbl.setMinimumHeight(80)
        self._eng_state_lbl.setStyleSheet("font-size:28px;font-weight:800;background:#362525;color:#ffb4b4;border-radius:10px;")

        arm = accent_button("ARM (F6)")
        dis = ghost_button("DISARM (F7)")
        arm.clicked.connect(self._eng.arm)
        dis.clicked.connect(self._eng.disarm)

        row = QWidget()
        rl = QHBoxLayout(row)
        rl.addWidget(arm)
        rl.addWidget(dis)

        self._fps_lbl = QLabel("FPS: 0.0")
        self.combo_controller_port = QComboBox()
        self.combo_controller_port.addItems(INIT_PORTS)
        self.combo_controller_port.setCurrentText(str(self.cfg.get("controller_port", "1")))
        help_lbl = QLabel("Hotkeys: F6 ARM, F7 DISARM")
        help_lbl.setStyleSheet(f"color:{SUBTLE};")

        bl.addWidget(self._eng_state_lbl)
        bl.addWidget(row)
        bl.addWidget(self._fps_lbl)
        bl.addWidget(spin_row("Controller Port", self.combo_controller_port))
        bl.addWidget(help_lbl)

        lay.addWidget(make_card("Engine", body))
        lay.addStretch(1)

        self._wire_autosave(self.combo_controller_port)
        return _make_scroll(page)

    # -------- stabilizer handlers --------
    def _open_stab_setup(self):
        dlg = XboxSetupDialog(self.cfg, self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        xbox, public_iface, private_iface, mode = dlg.values()
        self.cfg["stab_xbox_ip"] = xbox
        self.cfg["stab_public_iface"] = public_iface
        self.cfg["stab_private_iface"] = private_iface
        self.cfg["stab_mode"] = mode or "bridge"
        self._autosave_now()

    def _toggle_stabilizer(self):
        if self.chk_stab_enabled.isChecked():
            ok, msg = self._validate_stabilizer_prereqs()
            if not ok:
                QMessageBox.warning(self, "Stabilizer", msg)
                self.chk_stab_enabled.setChecked(False)
                return
            self._start_stabilizer()
        else:
            self._stop_stabilizer()

    def _validate_stabilizer_prereqs(self) -> Tuple[bool, str]:
        if not IS_ADMIN:
            return False, "Administrator privileges are required."
        if not HAS_PYDIVERT or not HAS_PSUTIL:
            return False, "pydivert and psutil are required."
        if not self.cfg.get("stab_xbox_ip") or not self.cfg.get("stab_public_iface") or not self.cfg.get("stab_private_iface"):
            return False, "Please configure Xbox IP and interfaces first."
        return True, ""

    def _start_stabilizer(self):
        if self._stab_running:
            return
        ok, _msg = self._validate_stabilizer_prereqs()
        if not ok:
            return

        xbox_ip = self.cfg.get("stab_xbox_ip", "").strip()
        public_ip = self.cfg.get("stab_public_iface", "").strip()
        private_ip = self.cfg.get("stab_private_iface", "").strip()
        mode = self.cfg.get("stab_mode", "bridge")
        if not xbox_ip or not public_ip or not private_ip:
            return

        local_ips = set()
        local_ips.update(NetworkUtils.interface_to_ips(public_ip))
        local_ips.update(NetworkUtils.interface_to_ips(private_ip))

        self._stab_stats = PacketStats()
        self._stab_engine = StabilizerEngine(xbox_ip, local_ips, public_ip, private_ip, self._stab_stats, mode)
        self._stab_engine.server_change_callback = self._on_server_change
        self._stab_engine.start()
        self._stab_running = True

    def _stop_stabilizer(self):
        if self._stab_engine:
            self._stab_engine.stop()
        self._stab_engine = None
        self._stab_running = False

    # -------- profile handlers --------
    def _refresh_profiles(self):
        self.profile_list.clear()
        for name in sorted(_read_profiles().keys()):
            self.profile_list.addItem(name)

    def _save_profile(self):
        name, ok = QInputDialog.getText(self, "Save Profile", "Profile name:")
        if not ok or not name.strip():
            return
        profiles = _read_profiles()
        profiles[name.strip()] = self._collect_config()
        _write_profiles(profiles)
        self._refresh_profiles()

    def _selected_profile_name(self) -> Optional[str]:
        item = self.profile_list.currentItem()
        return item.text() if item else None

    def _load_selected_profile(self):
        name = self._selected_profile_name()
        if not name:
            return
        profiles = _read_profiles()
        cfg = profiles.get(name)
        if not isinstance(cfg, dict):
            return
        merged = dict(DEF_CFG)
        merged.update(cfg)
        self._apply_loaded_config(merged)

    def _delete_selected_profile(self):
        name = self._selected_profile_name()
        if not name:
            return
        profiles = _read_profiles()
        if name in profiles:
            del profiles[name]
            _write_profiles(profiles)
            self._refresh_profiles()

    def _rename_selected_profile(self):
        name = self._selected_profile_name()
        if not name:
            return
        new_name, ok = QInputDialog.getText(self, "Rename Profile", "New profile name:", text=name)
        if not ok or not new_name.strip() or new_name.strip() == name:
            return
        profiles = _read_profiles()
        if name in profiles:
            profiles[new_name.strip()] = profiles.pop(name)
            _write_profiles(profiles)
            self._refresh_profiles()

    def _apply_loaded_config(self, cfg):
        self.cfg = dict(DEF_CFG)
        self.cfg.update(cfg)

        self.edit_hex_color.setText(self.cfg["hex_color"])
        self.spin_tolerance.setValue(int(self.cfg["tolerance"]))
        self.spin_contour_area.setValue(int(self.cfg["contour_area"]))
        self.spin_target.setValue(int(self.cfg["target"]))
        self.spin_contested_target.setValue(int(self.cfg["contested_target"]))
        self.chk_contested.setChecked(bool(self.cfg["contested"]))
        self.spin_bbox_w.setValue(int(self.cfg["bbox_w"]))
        self.spin_bbox_h.setValue(int(self.cfg["bbox_h"]))
        self.spin_bbox_pad.setValue(int(self.cfg["bbox_pad"]))
        self.spin_bbox_thick.setValue(int(self.cfg["bbox_thick"]))
        self.chk_overlay.setChecked(bool(self.cfg["overlay"]))
        self.chk_hud.setChecked(bool(self.cfg["hud"]))
        self.chk_show_roi.setChecked(bool(self.cfg["show_roi"]))
        self.spin_flick_ms.setValue(int(self.cfg["flick_ms"]))
        self.chk_auto_dashboard.setChecked(bool(self.cfg["auto_dashboard"]))
        self.chk_roi_enabled.setChecked(bool(self.cfg["roi_enabled"]))
        self.spin_roi_w.setValue(int(self.cfg["roi_w"]))
        self.spin_roi_h.setValue(int(self.cfg["roi_h"]))
        self.spin_roi_thick.setValue(int(self.cfg["roi_thick"]))
        self.chk_defense.setChecked(bool(self.cfg["defense"]))
        self.spin_lt_thresh.setValue(int(self.cfg["lt_thresh"]))
        self.spin_shuffle_boost.setValue(int(self.cfg["shuffle_boost"]))
        self.spin_bump.setValue(int(self.cfg["bump"]))
        self.chk_autosync.setChecked(bool(self.cfg["autosync"]))
        self.dspin_sensitivity.setValue(float(self.cfg["latency_sensitivity"]))
        self.dspin_jitter_dampen.setValue(float(self.cfg["jitter_dampen_px"]))
        self.spin_max_offset.setValue(int(self.cfg["sync_max_offset_px"]))
        self.chk_stab_enabled.setChecked(bool(self.cfg["stab_enabled"]))
        self.combo_controller_port.setCurrentText(str(self.cfg.get("controller_port", "1")))

        self._refresh_preview(self.cfg["hex_color"])
        self._do_autosave()

    # -------- autosave / polling --------
    def _collect_config(self) -> dict:
        return {
            "hex_color": self.edit_hex_color.text().strip(),
            "tolerance": self.spin_tolerance.value(),
            "contour_area": self.spin_contour_area.value(),
            "target": self.spin_target.value(),
            "contested_target": self.spin_contested_target.value(),
            "contested": self.chk_contested.isChecked(),
            "bbox_w": self.spin_bbox_w.value(),
            "bbox_h": self.spin_bbox_h.value(),
            "bbox_pad": self.spin_bbox_pad.value(),
            "bbox_thick": self.spin_bbox_thick.value(),
            "overlay": self.chk_overlay.isChecked(),
            "hud": self.chk_hud.isChecked(),
            "show_roi": self.chk_show_roi.isChecked(),
            "flick_ms": self.spin_flick_ms.value(),
            "auto_dashboard": self.chk_auto_dashboard.isChecked(),
            "roi_enabled": self.chk_roi_enabled.isChecked(),
            "roi_w": self.spin_roi_w.value(),
            "roi_h": self.spin_roi_h.value(),
            "roi_thick": self.spin_roi_thick.value(),
            "roi_color": self.cfg.get("roi_color", [255, 0, 0]),
            "defense": self.chk_defense.isChecked(),
            "lt_thresh": self.spin_lt_thresh.value(),
            "shuffle_boost": self.spin_shuffle_boost.value(),
            "bump": self.spin_bump.value(),
            "autosync": self.chk_autosync.isChecked(),
            "latency_sensitivity": self.dspin_sensitivity.value(),
            "jitter_dampen_px": self.dspin_jitter_dampen.value(),
            "sync_max_offset_px": self.spin_max_offset.value(),
            "stab_enabled": self.chk_stab_enabled.isChecked(),
            "stab_xbox_ip": self.cfg.get("stab_xbox_ip", ""),
            "stab_public_iface": self.cfg.get("stab_public_iface", ""),
            "stab_private_iface": self.cfg.get("stab_private_iface", ""),
            "stab_mode": self.cfg.get("stab_mode", "bridge"),
            "controller_port": self.combo_controller_port.currentText(),
        }

    def _autosave_debounced(self, *_):
        self._autosave_timer.start(250)

    def _do_autosave(self):
        self.cfg.update(self._collect_config())
        _atomic_write_json(CFG_PATH, self.cfg)

    def _autosave_now(self):
        self._autosave_timer.stop()
        self._do_autosave()

    def _on_state(self, state: str):
        armed = state.upper() == "ARMED"
        self._eng_state_lbl.setText(state.upper())
        if armed:
            self._eng_state_lbl.setStyleSheet("font-size:28px;font-weight:800;background:#1f3a2f;color:#b8ffd7;border-radius:10px;")
        else:
            self._eng_state_lbl.setStyleSheet("font-size:28px;font-weight:800;background:#362525;color:#ffb4b4;border-radius:10px;")

    def _on_fps(self, fps: float):
        self._fps_lbl.setText(f"FPS: {fps:.1f}")

    def _update_auto_tuner(self):
        self._autosync_readout.setText(
            f"Offset: {self._auto_tuner.offset_px} px | RTT: {self._auto_tuner.rtt_ms:.1f} ms | Jitter: {self._auto_tuner.jitter_ms:.1f} ms"
        )

    def _poll(self):
        self._update_auto_tuner()
        if self._stab_stats:
            self._stab_metric_rtt.set_metric(f"{self._stab_stats.rtt_ms:.1f}")
            self._stab_metric_jitter.set_metric(f"{self._stab_stats.jitter_ms:.1f}")
            self._stab_metric_quality.set_metric(f"{self._stab_stats.quality:.0f}")
            self._stab_metric_servers.set_metric(str(self._stab_stats.server_count))
            self._stab_metric_tick.set_metric(str(self._stab_stats.tick))
            self._stab_metric_bw.set_metric(f"{self._stab_stats.bandwidth_mbps:.1f}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    if not validate_license():
        dlg = AuthDialog()
        if dlg.exec() != QDialog.DialogCode.Accepted:
            sys.exit(0)
        if not validate_license():
            sys.exit(1)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())
