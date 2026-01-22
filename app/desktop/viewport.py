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
    
    def set_visualization_mode(self, mode):
        """Set visualization mode (0.0 = dynamic, 1.0 = atlas)."""
        self.render_mode = "atlas" if mode == 1.0 else "dynamic"
    
    def _get_hovered_region(self, mouse_x, mouse_y):
        """
        Perform simple raycasting to find the hovered brain region.
        Returns the region name if found, None otherwise.
        """
        if self.vertices is None or self.labels is None or self.camera is None:
            return None
        
        # Get widget size
        width = self.width()
        height = self.height()
        if width == 0 or height == 0:
            return None
        
        # Convert mouse to NDC
        ndc_x = (2.0 * mouse_x / width) - 1.0
        ndc_y = 1.0 - (2.0 * mouse_y / height)
        
        # Simple projected vertex picking (find closest vertex in screen space)
        import pyrr
        
        aspect = width / height
        projection = pyrr.matrix44.create_perspective_projection_matrix(45, aspect, 0.1, 1000.0)
        view = self.camera.get_view_matrix()
        mvp = projection @ view
        
        # Transform all vertices to clip space
        vertices_homo = np.hstack([self.vertices, np.ones((len(self.vertices), 1), dtype=np.float32)])
        clip_coords = (mvp @ vertices_homo.T).T
        
        # Perspective divide
        w = clip_coords[:, 3:4]
        w[w == 0] = 1e-10  # Avoid div by zero
        ndc_coords = clip_coords[:, :3] / w
        
        # Filter vertices in front of camera (ndc_z in [-1, 1])
        valid_mask = (ndc_coords[:, 2] >= -1) & (ndc_coords[:, 2] <= 1)
        
        # Calculate screen distance
        screen_dist = (ndc_coords[:, 0] - ndc_x) ** 2 + (ndc_coords[:, 1] - ndc_y) ** 2
        screen_dist[~valid_mask] = np.inf
        
        closest_idx = np.argmin(screen_dist)
        min_dist = screen_dist[closest_idx]
        
        # Threshold for "hovering" (in NDC space, roughly 20 pixels for 800px width)
        threshold = 0.05
        if min_dist < threshold ** 2:
            label_id = int(self.labels[closest_idx])
            if 0 <= label_id < len(self.region_names):
                return self.region_names[label_id]
        
        return None

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
            elapsed = time.time() - self.start_time
            frame_idx = 0
            
            if self.render_mode == "dynamic" and self.color_frames is not None and self.renderer:
                frame_idx = int(elapsed * 30) % self.color_frames.shape[1]
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
        region = self._get_hovered_region(event.position().x(), event.position().y())
        if self.text_renderer:
            if region:
                self.text_renderer.set_text(region)
            else:
                self.text_renderer.set_text("MNE Analyze")
        
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
