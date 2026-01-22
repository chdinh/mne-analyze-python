"""
WebGPU Viewport for the Brain Viewer.

Uses QRenderWidget from rendercanvas.qt for native Qt-WebGPU integration.
This replaces the offscreen pixel-readback approach with direct surface rendering.
"""

import time
import numpy as np
import wgpu
from PySide6 import QtCore
from PySide6.QtCore import Qt
from PySide6.QtGui import QMouseEvent, QWheelEvent
from rendercanvas.qt import QRenderWidget


class WgpuViewport(QRenderWidget):
    """
    A PySide6 widget that renders the brain using WebGPU.
    
    Uses QRenderWidget for native Qt-WebGPU integration via rendercanvas.
    """
    
    # Signal emitted when hovered region changes
    region_hovered = QtCore.Signal(str)
    
    # Signal emitted when frame changes (for slider sync)
    frame_changed = QtCore.Signal(int)  # frame index

    def __init__(self, parent=None):
        super().__init__(parent)
        self.renderer = None
        self.camera = None
        self.trace_renderer = None
        self.text_renderer = None
        
        # WebGPU resources
        self.adapter = None
        self.device = None
        self._context = None
        self._render_format = None
        self._initialized = False
        
        # Animation state
        self.brain_data = None
        self.color_frames = None
        self.atlas_colors = None
        self.start_time = time.time()
        self.render_mode = "dynamic"  # "dynamic" or "atlas"
        self.show_traces = True
        
        # Playback control
        self.is_playing = True
        self.current_frame = 0
        self.n_frames = 200  # Default, updated when data is loaded
        self.paused_time = 0.0
        
        # Enable mouse tracking for smooth interaction
        self.setMouseTracking(True)
        
        # Start render loop
        self.request_draw(self._draw_frame)

    def set_renderer(self, renderer):
        """Set the brain renderer."""
        self.renderer = renderer

    def set_camera(self, camera):
        """Set the camera for navigation."""
        self.camera = camera
    
    def set_trace_renderer(self, trace_renderer):
        """Set the trace overlay renderer."""
        self.trace_renderer = trace_renderer
    
    def set_text_renderer(self, text_renderer):
        """Set the text renderer."""
        self.text_renderer = text_renderer
    
    def set_brain_data(self, brain_data):
        """Set brain data for animation."""
        self.brain_data = brain_data
        if brain_data:
            self.color_frames = brain_data.get("color_frames")
            self.atlas_colors = brain_data.get("atlas_colors")
            self.region_names = brain_data.get("region_names", [])
            self.labels = brain_data.get("labels")
            self.vertices = brain_data.get("vertices")
            # Set number of frames for playback
            if self.color_frames is not None:
                self.n_frames = self.color_frames.shape[1]
    
    def set_visualization_mode(self, mode):
        """Set visualization mode (0.0 = dynamic, 1.0 = atlas)."""
        self.render_mode = "atlas" if mode == 1.0 else "dynamic"
    
    def set_playing(self, playing):
        """Set playback state."""
        if playing and not self.is_playing:
            # Resuming - adjust start time to continue from current frame
            self.start_time = time.time() - (self.current_frame / 30.0)
        self.is_playing = playing
    
    def seek_to_position(self, position):
        """Seek to a position (0.0 to 1.0)."""
        if self.color_frames is not None:
            self.current_frame = int(position * (self.n_frames - 1))
            self.start_time = time.time() - (self.current_frame / 30.0)
    
    def _get_hovered_region(self, mouse_x, mouse_y):
        """
        Perform simple raycasting to find the hovered brain region.
        Returns a tuple (region_name, region_id) if found, (None, -1) otherwise.
        """
        if self.vertices is None or self.labels is None or self.camera is None:
            return (None, -1)
        
        # Get widget size
        width = self.width()
        height = self.height()
        if width == 0 or height == 0:
            return (None, -1)
        
        # Convert mouse to NDC (Qt mouse coords are in logical pixels)
        # Match stc_viewer: ndc_x = (mx / l_w) * 2.0 - 1.0, ndc_y = -((my / l_h) * 2.0 - 1.0)
        ndc_x = (mouse_x / width) * 2.0 - 1.0
        ndc_y = -((mouse_y / height) * 2.0 - 1.0)  # Inverted Y
        
        import pyrr
        
        aspect = width / height
        
        # Create projection matrix
        projection = pyrr.matrix44.create_perspective_projection_matrix(45, aspect, 0.1, 1000.0)
        view = self.camera.get_view_matrix()
        model_matrix = pyrr.matrix44.create_identity()
        
        # Correction matrix - MUST match renderer exactly!
        correction = np.array([
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 0.5, 0.0],
            [0.0, 0.0, 0.5, 1.0],
        ], dtype=np.float32)
        
        # MVP construction - MUST match renderer: np.matmul(model, np.matmul(view, np.matmul(projection, correction)))
        mvp = np.matmul(model_matrix, np.matmul(view, np.matmul(projection, correction)))
        
        # Transform all vertices to clip space
        vertices_homo = np.hstack([self.vertices, np.ones((len(self.vertices), 1), dtype=np.float32)])
        clip_coords = np.dot(vertices_homo, mvp)  # Row-vector multiplication
        
        # Perspective divide
        w = clip_coords[:, 3:4].copy()
        w[w == 0] = 1e-10  # Avoid div by zero
        ndc_coords = clip_coords[:, :3] / w
        
        # Filter vertices in front of camera (ndc_z in [0, 1] after correction matrix)
        # The correction matrix maps Z from [-1,1] to [0,1]
        valid_mask = (ndc_coords[:, 2] >= 0) & (ndc_coords[:, 2] <= 1)
        
        # Calculate screen distance (only X and Y)
        screen_dist = (ndc_coords[:, 0] - ndc_x) ** 2 + (ndc_coords[:, 1] - ndc_y) ** 2
        screen_dist[~valid_mask] = np.inf
        
        # Find candidates within distance threshold
        threshold = 0.05  # NDC space threshold
        within_threshold = screen_dist < threshold ** 2
        
        if not np.any(within_threshold):
            return (None, -1)
        
        # Among candidates within threshold, pick the one closest to the camera (smallest Z = frontmost)
        candidate_indices = np.where(within_threshold)[0]
        candidate_z = ndc_coords[candidate_indices, 2]
        
        # Pick frontmost (smallest Z in NDC after correction = closest to camera)
        frontmost_local_idx = np.argmin(candidate_z)
        closest_idx = candidate_indices[frontmost_local_idx]
        
        label_id = int(self.labels[closest_idx])
        # Check for valid label (non-negative and within bounds)
        if label_id >= 0 and label_id < len(self.region_names):
            return (self.region_names[label_id], label_id)
        
        return (None, -1)

    def _ensure_initialized(self):
        """Initialize WebGPU resources on first draw."""
        if self._initialized:
            return True
            
        try:
            # Request adapter and device
            self.adapter = wgpu.gpu.request_adapter_sync(power_preference="high-performance")
            if self.adapter is None:
                print("Failed to get WebGPU adapter")
                return False
                
            self.device = self.adapter.request_device_sync()
            
            # Get the wgpu context from the canvas
            self._context = self.get_wgpu_context()
            if self._context is None:
                print("Failed to get wgpu context")
                return False
            
            # Get preferred format and configure the surface
            self._render_format = self._context.get_preferred_format(self.adapter)
            self._context.configure(
                device=self.device,
                format=self._render_format,
            )
            
            self._initialized = True
            print(f"WebGPU initialized successfully! Format: {self._render_format}")
            return True
            
        except Exception as e:
            print(f"WebGPU initialization error: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _draw_frame(self):
        """Render a frame using WebGPU."""
        if not self._ensure_initialized():
            self.request_draw(self._draw_frame)
            return
        
        try:
            # Get current texture from the swap chain
            current_texture = self._context.get_current_texture()
            if current_texture is None:
                self.request_draw(self._draw_frame)
                return
            
            current_view = current_texture.create_view()
            size = current_texture.size
            
            if size[1] == 0:
                self.request_draw(self._draw_frame)
                return
            
            aspect = size[0] / size[1]
            
            # Update animation
            frame_idx = self.current_frame
            
            if self.render_mode == "dynamic" and self.color_frames is not None and self.renderer:
                if self.is_playing:
                    # Calculate frame from elapsed time
                    elapsed = time.time() - self.start_time
                    self.current_frame = int(elapsed * 30) % self.n_frames
                    frame_idx = self.current_frame
                    
                    # Emit signal periodically (every 5 frames to reduce overhead)
                    if frame_idx % 5 == 0:
                        self.frame_changed.emit(frame_idx)
                else:
                    # Paused - use current_frame directly
                    frame_idx = self.current_frame
                
                current_colors = self.color_frames[:, frame_idx, :]
                self.renderer.update_colors(current_colors)
            
            # Render 3D content
            if self.renderer and self.camera:
                # Ensure renderer pipelines match the current texture format
                texture_format = current_texture.format
                self.renderer.ensure_format(texture_format)
                
                view_matrix = self.camera.get_view_matrix()
                self.renderer.draw(
                    target_texture_view=current_view,
                    aspect_ratio=aspect,
                    view_matrix=view_matrix,
                    camera_pos=self.camera.position,
                )
            else:
                # Clear to black if no renderer
                self._clear_to_black(current_view)
            
            # Render 2D overlays
            if self.show_traces and self.trace_renderer:
                self.trace_renderer.draw(current_view, frame_idx)
            
            if self.text_renderer:
                self.text_renderer.draw(current_view)
                
        except Exception as e:
            print(f"Render error: {e}")
            import traceback
            traceback.print_exc()
        
        # Request next frame (continuous animation)
        self.request_draw(self._draw_frame)
    
    def _clear_to_black(self, texture_view):
        """Clear the screen to black when no renderer is available."""
        encoder = self.device.create_command_encoder()
        render_pass = encoder.begin_render_pass(
            color_attachments=[{
                "view": texture_view,
                "load_op": wgpu.LoadOp.clear,
                "store_op": wgpu.StoreOp.store,
                "clear_value": (0.0, 0.0, 0.0, 1.0),
            }]
        )
        render_pass.end()
        self.device.queue.submit([encoder.finish()])

    # ─────────────────────────────────────────────────────────────────────────
    # Mouse Event Handling
    # ─────────────────────────────────────────────────────────────────────────

    def mousePressEvent(self, event: QMouseEvent):
        if self.camera:
            button = 1 if event.button() == Qt.MouseButton.LeftButton else 2
            self.camera.handle_event({
                "event_type": "pointer_down",
                "x": event.position().x(),
                "y": event.position().y(),
                "button": button,
            })
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self.camera:
            button = 1 if event.button() == Qt.MouseButton.LeftButton else 2
            self.camera.handle_event({
                "event_type": "pointer_up",
                "x": event.position().x(),
                "y": event.position().y(),
                "button": button,
            })
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.camera:
            self.camera.handle_event({
                "event_type": "pointer_move",
                "x": event.position().x(),
                "y": event.position().y(),
                "button": 0,
            })
        
        # Hover detection for region labels
        region_name, region_id = self._get_hovered_region(event.position().x(), event.position().y())
        
        # Update text renderer with region name
        if self.text_renderer:
            if region_name:
                self.text_renderer.set_text(region_name)
            else:
                self.text_renderer.set_text("")
        
        # Update brain renderer with hovered region ID for visual highlighting
        if self.renderer:
            self.renderer.set_hovered_id(region_id)
        
        # Emit signal for control panel
        self.region_hovered.emit(region_name if region_name else "None")
        
        super().mouseMoveEvent(event)

    def wheelEvent(self, event: QWheelEvent):
        if self.camera:
            self.camera.handle_event({
                "event_type": "wheel",
                "dy": -event.angleDelta().y(),
                "x": event.position().x(),
                "y": event.position().y(),
            })
        super().wheelEvent(event)

    def keyPressEvent(self, event):
        """Forward key events to parent for handling."""
        event.ignore()
