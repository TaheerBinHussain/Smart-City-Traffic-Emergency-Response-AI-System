#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
  SMART CITY TRAFFIC & EMERGENCY RESPONSE AI SYSTEM
  Enterprise Dashboard – Ultra Modern UI
================================================================================
Architecture: PySide6 + Matplotlib embedded
Style: Glassmorphism / Cyberpunk / Futuristic AI Dashboard

All AI modules (preprocessor, router, ann, logic, csp, search, response)
remain unchanged – only the front-end is upgraded.
================================================================================
"""

import sys
import os
import uuid
from datetime import datetime
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QFont, QFontDatabase, QIcon, QPalette, QColor, QLinearGradient
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QPushButton, QLabel, QFrame, QGridLayout, QScrollArea,
    QFileDialog, QMessageBox, QStatusBar
)

import matplotlib
matplotlib.use('Qt5Agg')  # Use Qt5Agg backend for PySide6 integration
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np

# Import your existing AI modules (make sure `modules/` folder exists)
from modules.preprocessor import InputPreprocessor
from modules.router import RequestRouter
from modules.ann_priority import ANNPriorityModule
from modules.logic_kb import LogicKnowledgeBase
from modules.csp_scheduler import CSPScheduler
from modules.search_navigation import SearchNavigationModule
from modules.final_response import FinalResponseLayer

# =============================================================================
# 1. Color Palette (CSS / QSS)
# =============================================================================
GLASS_STYLE = """
QMainWindow {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                stop:0 #0B1220, stop:1 #111827);
}

QTabWidget::pane {
    border: none;
    background: transparent;
}

QTabWidget::tab-bar {
    alignment: center;
}

QTabBar::tab {
    background: rgba(30, 41, 59, 0.6);
    color: #94A3B8;
    padding: 12px 24px;
    margin: 0px 4px;
    border-top-left-radius: 12px;
    border-top-right-radius: 12px;
    font-weight: bold;
    font-size: 13px;
    font-family: "Segoe UI", "Inter", "Helvetica Neue";
}

QTabBar::tab:selected {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #1E293B, stop:1 #0F172A);
    color: #38BDF8;
    border-bottom: 2px solid #06B6D4;
}

QTabBar::tab:hover:!selected {
    background: rgba(56, 189, 248, 0.2);
    color: #CBD5E1;
}

QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #3B82F6, stop:1 #2563EB);
    color: white;
    border: none;
    border-radius: 24px;
    padding: 10px 20px;
    font-weight: bold;
    font-size: 12px;
    font-family: "Segoe UI", "Inter";
}

QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #06B6D4, stop:1 #3B82F6);
}

QPushButton:pressed {
    background: #1E40AF;
}

QFrame#card {
    background-color: rgba(30, 41, 59, 0.65);
    border-radius: 20px;
    border: 1px solid rgba(59, 130, 246, 0.3);
}

QLabel#header_title {
    font-size: 20px;
    font-weight: bold;
    font-family: "Segoe UI", "Inter";
    color: #F8FAFC;
}

QLabel#status_badge {
    background-color: #10B981;
    border-radius: 12px;
    padding: 4px 12px;
    color: white;
    font-weight: bold;
    font-size: 10px;
}

QStatusBar {
    background-color: rgba(15, 23, 42, 0.8);
    color: #94A3B8;
    font-size: 11px;
}
"""

# =============================================================================
# 2. Matplotlib Canvas Base Class (embedded in Qt)
# =============================================================================
class MplCanvas(FigureCanvas):
    """Base canvas for embedding matplotlib figures in Qt."""
    def __init__(self, parent=None, width=10, height=8, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor='#0B1220')
        super().__init__(self.fig)
        self.setParent(parent)
        self.axes = self.fig.add_subplot(111)
        self.axes.set_facecolor('#0B1220')
        # Hide spines for a cleaner look
        for spine in self.axes.spines.values():
            spine.set_visible(False)
        self.axes.tick_params(colors='#94A3B8', which='both')
        self.axes.xaxis.label.set_color('#F8FAFC')
        self.axes.yaxis.label.set_color('#F8FAFC')
        self.fig.tight_layout(pad=2.0)

    def clear_canvas(self):
        self.axes.clear()
        self.axes.set_facecolor('#0B1220')
        for spine in self.axes.spines.values():
            spine.set_visible(False)
        self.draw()

# =============================================================================
# 3. Individual Tab Widgets (each contains an MplCanvas + optional controls)
# =============================================================================
class ControlPanel(QWidget):
    """Modern control panel with glass cards, preset buttons, and option pills."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(25, 25, 25, 25)

        # Header
        header = QLabel("REQUEST CONFIGURATION")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #38BDF8;")
        layout.addWidget(header)

        # Scrollable area for parameters
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        content = QWidget()
        self.form_layout = QGridLayout(content)
        self.form_layout.setVerticalSpacing(15)
        self.form_layout.setHorizontalSpacing(30)
        self.form_layout.setColumnStretch(0, 1)
        self.form_layout.setColumnStretch(1, 2)
        self.form_layout.setColumnStretch(2, 3)

        # Field definitions (label, current value, options, attribute name)
        self.fields = [
            ("REQUEST CATEGORY", CATEGORIES, "sel_category"),
            ("VEHICLE TYPE", VEHICLE_TYPES, "sel_vehicle"),
            ("SOURCE", VALID_LOCATIONS, "sel_source"),
            ("DESTINATION", VALID_LOCATIONS, "sel_dest"),
            ("INCIDENT SEVERITY", SEVERITIES, "sel_severity"),
            ("TRAFFIC DENSITY", DENSITIES, "sel_density"),
            ("CONTROL ZONE", VALID_ZONES, "sel_zone"),
            ("TIME SENSITIVE", ["Yes","No"], "sel_time"),
            ("PRIORITY CLAIM", ["Yes","No"], "sel_priority"),
        ]

        self.value_widgets = {}
        for row, (label, options, attr) in enumerate(self.fields):
            # Label
            lbl = QLabel(label)
            lbl.setStyleSheet("color: #CBD5E1; font-size: 12px; font-weight: bold;")
            self.form_layout.addWidget(lbl, row, 0)

            # Current value pill
            current_val = getattr(self.parent, attr)
            if isinstance(current_val, bool):
                current_val = "Yes" if current_val else "No"
            pill = QLabel(current_val)
            pill.setAlignment(Qt.AlignCenter)
            pill.setStyleSheet("""
                background-color: #1E293B;
                border: 1px solid #3B82F6;
                border-radius: 20px;
                padding: 6px 12px;
                color: #38BDF8;
                font-weight: bold;
            """)
            self.form_layout.addWidget(pill, row, 1)
            self.value_widgets[attr] = pill

            # Option buttons row
            btn_layout = QHBoxLayout()
            for opt in options:
                btn = QPushButton(opt)
                btn.setFixedHeight(28)
                btn.setStyleSheet("""
                    QPushButton {
                        background: #334155;
                        border-radius: 16px;
                        padding: 4px 12px;
                        font-size: 10px;
                    }
                    QPushButton:hover {
                        background: #3B82F6;
                    }
                """)
                btn.clicked.connect(lambda checked, a=attr, o=opt: self.parent.update_field(a, o))
                btn_layout.addWidget(btn)
            btn_layout.addStretch()
            self.form_layout.addLayout(btn_layout, row, 2)

        scroll.setWidget(content)
        layout.addWidget(scroll)

        # Preset buttons row
        preset_row = QHBoxLayout()
        preset_row.addStretch()
        emergency_btn = QPushButton("🚑  EMERGENCY PRESET")
        emergency_btn.setStyleSheet("background: #EF4444;")
        emergency_btn.clicked.connect(self.parent.preset_emergency)
        civilian_btn = QPushButton("🚗  CIVILIAN PRESET")
        civilian_btn.setStyleSheet("background: #3B82F6;")
        civilian_btn.clicked.connect(self.parent.preset_civilian)
        policy_btn = QPushButton("⚖️  POLICY PRESET")
        policy_btn.setStyleSheet("background: #8B5CF6;")
        policy_btn.clicked.connect(self.parent.preset_policy)
        preset_row.addWidget(emergency_btn)
        preset_row.addWidget(civilian_btn)
        preset_row.addWidget(policy_btn)
        preset_row.addStretch()
        layout.addLayout(preset_row)

        # Submit button
        submit_btn = QPushButton("▶  SUBMIT REQUEST")
        submit_btn.setFixedHeight(48)
        submit_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                                            stop:0 #10B981, stop:1 #059669);
                font-size: 14px;
            }
        """)
        submit_btn.clicked.connect(self.parent.submit_request)
        layout.addWidget(submit_btn)

    def update_value_display(self):
        """Refresh the pill values after a field update."""
        for attr, pill in self.value_widgets.items():
            val = getattr(self.parent, attr)
            if isinstance(val, bool):
                val = "Yes" if val else "No"
            pill.setText(str(val))

# -----------------------------------------------------------------------------
# The other tabs (CityMapTab, ANNPanel, CSPPanel, PipelinePanel, ResponsePanel)
# are implemented as MplCanvas subclasses with custom drawing functions.
# We reuse the enhanced drawing functions from the original code but upgrade
# them with neon colors, glows, and better aesthetics.
# -----------------------------------------------------------------------------

class CityMapTab(MplCanvas):
    def __init__(self, parent=None):
        super().__init__(parent, width=10, height=7)
        self.parent = parent
        self.route_path = None
        self.is_emergency = False

    def update_map(self, route_path=None, is_emergency=False):
        self.route_path = route_path
        self.is_emergency = is_emergency
        self.draw()

    def draw(self):
        self.axes.clear()
        draw_city_map_enhanced(self.axes, self.route_path, self.is_emergency)
        self.draw()

class ANNPanel(MplCanvas):
    def __init__(self, parent=None):
        super().__init__(parent, width=10, height=7)
        self.parent = parent

    def update_ann(self, ann_result=None, feature_vector=None):
        self.ann_result = ann_result
        self.feature_vector = feature_vector
        self.draw()

    def draw(self):
        self.axes.clear()
        draw_ann_enhanced(self.axes, getattr(self, 'ann_result', None),
                          getattr(self, 'feature_vector', None))
        self.draw()

class CSPPanel(MplCanvas):
    def __init__(self, parent=None):
        super().__init__(parent, width=10, height=7)
        self.parent = parent

    def update_csp(self, csp_result=None):
        self.csp_result = csp_result
        self.draw()

    def draw(self):
        self.axes.clear()
        draw_csp_enhanced(self.axes, getattr(self, 'csp_result', None))
        self.draw()

class PipelinePanel(MplCanvas):
    def __init__(self, parent=None):
        super().__init__(parent, width=10, height=5)
        self.parent = parent

    def update_pipeline(self, pipeline=None, results=None):
        self.pipeline = pipeline
        self.results = results
        self.draw()

    def draw(self):
        self.axes.clear()
        draw_pipeline_enhanced(self.axes, getattr(self, 'pipeline', None),
                               getattr(self, 'results', None))
        self.draw()

class ResponsePanel(MplCanvas):
    def __init__(self, parent=None):
        super().__init__(parent, width=10, height=8)
        self.parent = parent

    def update_response(self, final_response=None):
        self.final_response = final_response
        self.draw()

    def draw(self):
        self.axes.clear()
        draw_response_enhanced(self.axes, getattr(self, 'final_response', None))
        self.draw()

# =============================================================================
# 4. Enhanced Drawing Functions (with neon glows, better typography)
# =============================================================================
# Note: I'll only show key improvements; the full functions are long but
# structurally similar to the original, upgraded with:
# - Path effects for glow: `matplotlib.patheffects.withStroke`
# - Brighter neon colors
# - Smoother node rendering
# - Shadow effects via `SimplePatchShadow` (optional)
# For brevity, I include the core enhancements. You can replace the old drawing
# functions entirely – they are drop‑in compatible.

def draw_city_map_enhanced(ax, route_path, is_emergency):
    """Enhanced city map with neon edges and glows."""
    from matplotlib.patheffects import withStroke, withSimplePatchShadow
    ax.set_facecolor('#0B1220')
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 11)
    ax.axis('off')
    ax.set_title("CITY ROAD NETWORK", color='#38BDF8', fontsize=14,
                 fontweight='bold', pad=15, fontfamily='sans-serif')

    # (Edge drawing remains similar but with thicker, neon-colored lines)
    # Add glow effect: use a second line with alpha and larger width behind
    # This is a simplified representation; full code available in the final deliverable.
    pass

# Similarly for ANN, CSP, Pipeline, Response – all upgraded with neon styling.
# For the final answer I will provide the complete, runnable script.

# =============================================================================
# 5. Main Dashboard Window
# =============================================================================
class SmartCityDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        # AI Modules
        self.preprocessor = InputPreprocessor()
        self.router = RequestRouter()
        self.ann = ANNPriorityModule()
        self.logic_kb = LogicKnowledgeBase()
        self.csp = CSPScheduler()
        self.search = SearchNavigationModule()
        self.response_layer = FinalResponseLayer()

        # Application state
        self.last_results = None
        self.last_response = None

        # UI selection fields
        self.sel_category = "Emergency_Response_Request"
        self.sel_vehicle = "ambulance"
        self.sel_source = "Central_Junction"
        self.sel_dest = "City_Hospital"
        self.sel_severity = "Critical"
        self.sel_density = "High"
        self.sel_zone = "Central_Junction"
        self.sel_time = True
        self.sel_priority = True

        self.init_ui()
        self.apply_style()
        self.show()

    def init_ui(self):
        self.setWindowTitle("Smart City AI Dashboard – Enterprise Edition")
        self.setGeometry(100, 100, 1400, 900)

        # Central widget and main layout
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)

        # ---- Header ----
        header = QFrame()
        header.setFixedHeight(80)
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                                            stop:0 #1E293B, stop:1 #0F172A);
                border-radius: 25px;
                border: 1px solid #3B82F6;
            }
        """)
        header_layout = QHBoxLayout(header)
        title = QLabel("SMART CITY TRAFFIC & EMERGENCY RESPONSE AI SYSTEM")
        title.setObjectName("header_title")
        status_badge = QLabel("● SYSTEM ACTIVE")
        status_badge.setObjectName("status_badge")
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(status_badge)
        main_layout.addWidget(header)

        # ---- Tab Widget ----
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { background: transparent; }
        """)
        # Create tabs
        self.control_tab = ControlPanel(self)
        self.map_tab = CityMapTab(self)
        self.ann_tab = ANNPanel(self)
        self.csp_tab = CSPPanel(self)
        self.pipeline_tab = PipelinePanel(self)
        self.response_tab = ResponsePanel(self)

        self.tabs.addTab(self.control_tab, "🎮 CONTROL")
        self.tabs.addTab(self.map_tab, "🗺️ CITY MAP")
        self.tabs.addTab(self.ann_tab, "🧠 ANN")
        self.tabs.addTab(self.csp_tab, "🚦 CSP")
        self.tabs.addTab(self.pipeline_tab, "⚙️ PIPELINE")
        self.tabs.addTab(self.response_tab, "📄 RESPONSE")

        main_layout.addWidget(self.tabs)

        # ---- Footer (Status Bar) ----
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet("background: #0F172A; color: #94A3B8;")
        self.setStatusBar(self.status_bar)
        self.status_label = QLabel("● Ready")
        self.status_bar.addWidget(self.status_label)

        # Capture button in status bar
        capture_btn = QPushButton("📸 CAPTURE TAB")
        capture_btn.setFixedSize(120, 24)
        capture_btn.setStyleSheet("""
            QPushButton {
                background: #334155;
                border-radius: 12px;
                font-size: 10px;
            }
            QPushButton:hover { background: #3B82F6; }
        """)
        capture_btn.clicked.connect(self.capture_tab)
        self.status_bar.addPermanentWidget(capture_btn)

    def apply_style(self):
        self.setStyleSheet(GLASS_STYLE)

    # -----------------------------------------------------------------
    # Field update handlers
    # -----------------------------------------------------------------
    def update_field(self, attr, value):
        if attr == "sel_time":
            setattr(self, attr, value == "Yes")
        elif attr == "sel_priority":
            setattr(self, attr, value == "Yes")
        else:
            setattr(self, attr, value)
        self.control_tab.update_value_display()
        self.status_label.setText(f"● Updated {attr} → {value}")

    # -----------------------------------------------------------------
    # Presets
    # -----------------------------------------------------------------
    def preset_emergency(self):
        self.sel_category = "Emergency_Response_Request"
        self.sel_vehicle = "ambulance"
        self.sel_source = "Central_Junction"
        self.sel_dest = "City_Hospital"
        self.sel_severity = "Critical"
        self.sel_density = "High"
        self.sel_zone = "Central_Junction"
        self.sel_time = True
        self.sel_priority = True
        self.control_tab.update_value_display()
        self.status_label.setText("● Loaded Emergency Ambulance preset")

    def preset_civilian(self):
        self.sel_category = "Route_Request"
        self.sel_vehicle = "civilian_car"
        self.sel_source = "North_Station"
        self.sel_dest = "East_Market"
        self.sel_severity = "Low"
        self.sel_density = "Medium"
        self.sel_zone = "Central_Junction"
        self.sel_time = False
        self.sel_priority = False
        self.control_tab.update_value_display()
        self.status_label.setText("● Loaded Civilian Route preset")

    def preset_policy(self):
        self.sel_category = "Policy_Check"
        self.sel_vehicle = "civilian_car"
        self.sel_source = "Central_Junction"
        self.sel_dest = "City_Hospital"
        self.sel_severity = "Medium"
        self.sel_density = "Medium"
        self.sel_zone = "Central_Junction"
        self.sel_time = False
        self.sel_priority = True
        self.control_tab.update_value_display()
        self.status_label.setText("● Loaded Policy Check preset")

    # -----------------------------------------------------------------
    # AI Pipeline Execution
    # -----------------------------------------------------------------
    def submit_request(self):
        raw_data = {
            "request_id": str(uuid.uuid4())[:8].upper(),
            "request_category": self.sel_category,
            "vehicle_type": self.sel_vehicle,
            "current_location": self.sel_source,
            "destination": self.sel_dest,
            "incident_severity": self.sel_severity,
            "time_sensitivity": self.sel_time,
            "traffic_density": self.sel_density,
            "priority_claim": self.sel_priority,
            "control_zone": self.sel_zone,
            "description_note": ""
        }
        try:
            processed = self.preprocessor.process(raw_data)
            if not processed["valid"]:
                self.show_error(f"Validation Error:\n{processed['errors']}")
                return
            pipeline = self.router.route(processed)
            ann_r = self.ann.predict(processed) if "ANN" in pipeline else None
            logic_r = self.logic_kb.validate(processed, ann_r) if "Logic_KB" in pipeline else None
            csp_r = self.csp.allocate(processed, logic_r) if "CSP" in pipeline else None
            search_r = self.search.find_route(processed, csp_r) if "Search" in pipeline else None
            self.last_results = {
                "request": processed, "pipeline": pipeline,
                "ann_result": ann_r, "logic_result": logic_r,
                "csp_result": csp_r, "search_result": search_r
            }
            self.last_response = self.response_layer.generate(self.last_results)
            # Update all visual tabs
            self.map_tab.update_map(search_r["path"] if search_r and search_r.get("found") else None,
                                    processed["is_emergency_vehicle"])
            self.ann_tab.update_ann(ann_r, processed.get("ann_feature_vector"))
            self.csp_tab.update_csp(csp_r)
            self.pipeline_tab.update_pipeline(pipeline, self.last_results)
            self.response_tab.update_response(self.last_response)
            self.status_label.setText(f"● Submitted at {datetime.now().strftime('%H:%M:%S')} – Status: {self.last_response.get('status','N/A')}")
            self.tabs.setCurrentIndex(5)  # Switch to Response tab
        except Exception as e:
            self.show_error(f"Pipeline Error:\n{str(e)}")

    def show_error(self, msg):
        QMessageBox.critical(self, "Error", msg)
        self.status_label.setText("● Error occurred – check logs")

    def capture_tab(self):
        """Save current active tab as high‑res PNG."""
        current_index = self.tabs.currentIndex()
        if current_index == 0:
            canvas = None  # Control panel is not an MplCanvas
            QMessageBox.information(self, "Capture", "Cannot capture control panel directly. Switch to a visual tab (Map, ANN, etc.)")
            return
        # Get the canvas from the current tab
        tab_widget = self.tabs.widget(current_index)
        if hasattr(tab_widget, 'fig'):
            file_path, _ = QFileDialog.getSaveFileName(self, "Save Screenshot", "",
                                                       "PNG Image (*.png);;All Files (*)")
            if file_path:
                tab_widget.fig.savefig(file_path, dpi=200, bbox_inches="tight", facecolor='#0B1220')
                self.status_label.setText(f"● Screenshot saved: {os.path.basename(file_path)}")
        else:
            QMessageBox.information(self, "Capture", "This tab cannot be captured (no matplotlib figure).")

# =============================================================================
# 6. Main Entry Point
# =============================================================================
def main():
    app = QApplication(sys.argv)
    # Load custom fonts (optional)
    font_db = QFontDatabase()
    font_db.addApplicationFont(":/fonts/Inter-Regular.ttf")  # if you have it
    window = SmartCityDashboard()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()