"""
MNE Analyze Python - Main Window

PySide6 main window with embedded WebGPU brain viewer.
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
        self.start_time = time.time()

        # Build UI
        self._setup_ui()
        
        # Connect signals
        self._connect_signals()

        # Load data and initialize rendering
        self._load_data()

        # Animation timer
        self.timer = QtCore.QTimer()
        self.timer.setInterval(16)  # ~60 FPS
        self.timer.timeout.connect(self._game_loop)

    def _setup_ui(self):
        """Create the UI layout."""
        # Central widget
        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QtWidgets.QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        # Viewport (main rendering area)
        self.viewport = WgpuViewport()
        self.viewport.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding
        )

        # Playback controls (bottom)
        self.playback = PlaybackControls()

        self.main_layout.addWidget(self.viewport, stretch=1)
        self.main_layout.addWidget(self.playback, stretch=0)

        # Sidebar dock
        self.dock = QtWidgets.QDockWidget("Controls", self)
        self.dock.setAllowedAreas(
            QtCore.Qt.LeftDockWidgetArea | QtCore.Qt.RightDockWidgetArea
        )
        self.controls = AppControls()
        self.dock.setWidget(self.controls)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.dock)

    def _connect_signals(self):
        """Connect UI signals to slots."""
        self.controls.mode_changed.connect(self._on_mode_changed)
        self.controls.traces_toggled.connect(self._on_traces_toggled)
        self.playback.play_toggled.connect(self._on_play_toggled)

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
        """Initialize renderers after viewport is initialized."""
        if not self.viewport.initialized:
            # Force initialization
            self.viewport.initializeWebGPU()
            self.viewport.initialized = True

        device = self.viewport.device
        if not device:
            print("Error: WebGPU device not available")
            return

        # Create renderers using viewport's device
        self.brain_renderer = BrainRenderer(device, self.brain_data, None)

        # Note: TraceRenderer and TextRenderer need the same render format
        # For offscreen we use rgba8unorm
        self.trace_renderer = TraceRenderer(device, "rgba8unorm")
        self.trace_renderer.set_data(self.brain_data.get("traces", []))

        self.text_renderer = TextRenderer(device, "rgba8unorm")

        # Camera
        self.camera = Camera(self.viewport)
        self.viewport.set_camera(self.camera)
        self.viewport.set_renderer(self.brain_renderer)

        # Start animation
        self.timer.start()
        self.viewport.update()

    def _game_loop(self):
        """Animation loop called by timer."""
        if not self.brain_renderer:
            return

        # Update animation state
        self._update_animation()

        # Trigger repaint
        self.viewport.update()

    def _update_animation(self):
        """Update animation colors for dynamic mode."""
        if self.state.visualization_mode == 0.0:  # Dynamic mode
            color_frames = self.brain_data.get("color_frames")
            if color_frames is not None:
                frame_idx = self._get_current_frame_idx()
                current_colors = color_frames[:, frame_idx, :]
                self.brain_renderer.update_colors(current_colors)

    def _get_current_frame_idx(self):
        """Get current animation frame index."""
        elapsed = time.time() - self.start_time
        color_frames = self.brain_data.get("color_frames")
        if color_frames is None:
            return 0
        total = color_frames.shape[1]
        return int(elapsed * 30) % total

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

    def _on_traces_toggled(self, enabled):
        """Handle trace overlay toggle."""
        self.state.show_traces = enabled

    def _on_play_toggled(self, playing):
        """Handle play/pause toggle."""
        self.state.is_playing = playing

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts."""
        key = event.key()

        if key == QtCore.Qt.Key_T:
            # Toggle visualization mode
            new_mode = 1 if self.state.visualization_mode == 0 else 0
            self._on_mode_changed(new_mode)
            self.controls.mode_combo.setCurrentIndex(new_mode)

        elif key == QtCore.Qt.Key_P:
            # Toggle butterfly plot
            self.state.show_traces = not self.state.show_traces
            self.controls.traces_checkbox.setChecked(self.state.show_traces)

        elif key == QtCore.Qt.Key_Space:
            # Toggle play/pause
            self.state.is_playing = not self.state.is_playing
            self.playback.play_button.setChecked(self.state.is_playing)

        else:
            super().keyPressEvent(event)
