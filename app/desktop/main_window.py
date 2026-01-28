"""
MNE Analyze Python - Main Window

PySide6 main window with embedded WebGPU brain viewer using QRenderWidget.
"""

import time
import wgpu
from PySide6 import QtWidgets, QtCore, QtGui

from core.data import load_brain_data
from core.state import AppState
from vis.renderer import BrainRenderer
from vis.overlays import TraceRenderer
from vis.camera import Camera
from vis.text import TextRenderer
from .viewport import WgpuViewport
from .widgets import AppControls, PlaybackControls
from .channel_browser import ChannelBrowser


class MainWindow(QtWidgets.QMainWindow):
    """
    Main application window for MNE Analyze Python.
    
    Contains the WebGPU viewport for brain rendering and Qt controls
    for visualization options and playback.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("MNE Analyze Python")
        self.resize(1200, 800)

        # Core State
        self.state = AppState()
        self.brain_data = None
        self.brain_renderer = None
        self.trace_renderer = None
        self.text_renderer = None
        self.camera = None
        self.channel_browser = None

        # Build UI
        self._setup_ui()
        
        # Connect signals
        self._connect_signals()

        # Load data and initialize rendering
        self._load_data()

    def _setup_ui(self):
        """Create the UI layout."""
        # Central widget
        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QtWidgets.QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        # Tab Widget
        self.tabs = QtWidgets.QTabWidget()
        self.main_layout.addWidget(self.tabs)

        # --- Tab 1: Brain View ---
        self.brain_container = QtWidgets.QWidget()
        self.brain_layout = QtWidgets.QVBoxLayout(self.brain_container)
        self.brain_layout.setContentsMargins(0, 0, 0, 0)

        # Viewport (main rendering area) - using QRenderWidget
        self.viewport = WgpuViewport()
        self.viewport.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding
        )
        self.viewport.setMinimumSize(400, 300)

        # Playback controls (bottom of brain view)
        self.playback = PlaybackControls()

        self.brain_layout.addWidget(self.viewport, stretch=1)
        self.brain_layout.addWidget(self.playback, stretch=0)

        self.tabs.addTab(self.brain_container, "Brain View")

        # --- Tab 2: Raw Browser ---
        self.channel_browser = ChannelBrowser()
        self.tabs.addTab(self.channel_browser, "Raw Browser")

        # Sidebar dock (Controls) - Moved to LEFT
        self.dock = QtWidgets.QDockWidget("Controls", self)
        self.dock.setAllowedAreas(
            QtCore.Qt.LeftDockWidgetArea | QtCore.Qt.RightDockWidgetArea
        )
        self.controls = AppControls()
        self.dock.setWidget(self.controls)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.dock)

    def _connect_signals(self):
        """Connect UI signals to slots."""
        self.controls.mode_changed.connect(self._on_mode_changed)
        self.controls.traces_toggled.connect(self._on_traces_toggled)
        self.playback.play_toggled.connect(self._on_play_toggled)
        self.playback.time_changed.connect(self._on_time_changed)
        self.viewport.region_hovered.connect(self.controls.set_hovered_region)
        self.viewport.frame_changed.connect(self._on_frame_changed)
        
        # Connect File Browser

        # Connect Subject Configuration
        self.controls.recording_changed.connect(self._load_recording)
        self.controls.surface_changed.connect(self._load_surface)
        self.controls.atlas_changed.connect(self._load_atlas)

    def _load_data(self):
        """Load brain data (blocking for now)."""
        print("Loading Data...")
        self.brain_data = load_brain_data()
        print("Data Loaded.")

    def showEvent(self, event):
        """Initialize rendering after window is shown."""
        super().showEvent(event)
        if self.brain_renderer is None:
            # Delay initialization until viewport is ready
            QtCore.QTimer.singleShot(100, self._init_rendering)

    def _init_rendering(self):
        """Initialize renderers after viewport has initialized WebGPU."""
        # Wait for viewport to initialize WebGPU
        if not self.viewport._initialized:
            # Force initialization by triggering a draw
            self.viewport._ensure_initialized()
        
        device = self.viewport.device
        if not device:
            print("Error: WebGPU device not available, retrying...")
            QtCore.QTimer.singleShot(200, self._init_rendering)
            return

        print("Initializing renderers...")
        
        # Create renderers using viewport's device
        self.brain_renderer = BrainRenderer(device, self.brain_data, None)

        # Get render format from viewport
        render_format = self.viewport._render_format or "bgra8unorm"
        
        # Create overlay renderers
        self.trace_renderer = TraceRenderer(device, render_format)
        self.trace_renderer.set_data(self.brain_data.get("traces", []))

        self.text_renderer = TextRenderer(device, render_format)

        # Camera (no canvas reference needed - viewport handles redraws)
        self.camera = Camera(None)
        
        # Connect everything to the viewport
        self.viewport.set_camera(self.camera)
        self.viewport.set_renderer(self.brain_renderer)
        self.viewport.set_trace_renderer(self.trace_renderer)
        self.viewport.set_text_renderer(self.text_renderer)
        self.viewport.set_brain_data(self.brain_data)
        
        # Set slider range based on number of frames
        if self.viewport.n_frames > 1:
            self.playback.slider.setRange(0, 100)
        
        print("Renderers initialized successfully!")

    def _on_file_selected(self, path):
        """Handle file selection from sidebar."""
        if path.endswith('.fif') or path.endswith('.fif.gz'):
             self.channel_browser.load_raw(path)
             # Switch to browser tab (index 1)
             self.tabs.setCurrentIndex(1)

    def _load_recording(self, path):
        """Load recording from subject config."""
        print(f"Subject Config: Loading recording {path}")
        self.channel_browser.load_raw(path)
        # Update renderer if needed or just browser
        self.tabs.setCurrentIndex(1)

    def _load_surface(self, path):
        """Load surface from subject config."""
        print(f"Subject Config: Loading surface {path}")
        # Placeholder: This would trigger a brain data reload
        # self.brain_data = load_brain_data(surface_path=path)
        # self.brain_renderer.update_data(self.brain_data)

    def _load_atlas(self, path):
        """Load atlas from subject config."""
        print(f"Subject Config: Loading atlas {path}")
        # Placeholder: This would trigger an atlas reload
        # self.brain_data.load_atlas(path)
        # self.brain_renderer.update_colors(...)

    # ─────────────────────────────────────────────────────────────────────────
    # UI Event Handlers
    # ─────────────────────────────────────────────────────────────────────────

    def _on_mode_changed(self, mode):
        """Handle visualization mode toggle."""
        self.state.visualization_mode = float(mode)
        if self.brain_renderer:
            self.brain_renderer.set_visualization_mode(self.state.visualization_mode)
            if mode == 1:  # Atlas mode
                atlas = self.brain_data.get("atlas_colors")
                if atlas is not None:
                    self.brain_renderer.update_colors(atlas)
        
        # Update viewport mode
        self.viewport.set_visualization_mode(self.state.visualization_mode)

    def _on_traces_toggled(self, enabled):
        """Handle trace overlay toggle."""
        self.state.show_traces = enabled
        self.viewport.show_traces = enabled

    def _on_play_toggled(self, playing):
        """Handle play/pause toggle."""
        self.state.is_playing = playing
        self.viewport.set_playing(playing)
    
    def _on_time_changed(self, position):
        """Handle timeline slider change."""
        self.viewport.seek_to_position(position)
    
    def _on_frame_changed(self, frame_idx):
        """Handle frame change from viewport (update slider)."""
        if self.viewport.n_frames > 1:
            # Block signals to prevent feedback loop
            self.playback.slider.blockSignals(True)
            slider_val = int((frame_idx / (self.viewport.n_frames - 1)) * 100)
            self.playback.slider.setValue(slider_val)
            self.playback.slider.blockSignals(False)

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts."""
        key = event.key()

        if key == QtCore.Qt.Key_T:
            # Toggle visualization mode
            new_mode = 1 if self.state.visualization_mode == 0 else 0
            self._on_mode_changed(new_mode)
            if new_mode == 0:
                self.controls.radio_electric.setChecked(True)
            else:
                self.controls.radio_atlas.setChecked(True)

        elif key == QtCore.Qt.Key_P:
            # Toggle butterfly plot
            self.state.show_traces = not self.state.show_traces
            self.controls.check_traces.setChecked(self.state.show_traces)
            self.viewport.show_traces = self.state.show_traces

        elif key == QtCore.Qt.Key_Space:
            # Toggle play/pause
            self.state.is_playing = not self.state.is_playing
            self.playback.btn_play.setChecked(self.state.is_playing)

        else:
            super().keyPressEvent(event)
