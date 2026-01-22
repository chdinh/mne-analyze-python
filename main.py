"""
MNE Analyze Python - Main Entry Point

Uses rendercanvas.auto for the render loop (same pattern as working stc_viewer).
"""
import time
import wgpu
import numpy as np
from rendercanvas.auto import RenderCanvas, loop

from core.data import load_brain_data
from vis.renderer import BrainRenderer
from vis.camera import Camera
from vis.overlays import TraceRenderer
from vis.text import TextRenderer

# Setup window
canvas = RenderCanvas(title="MNE Analyze Python", size=(1200, 800))
adapter = wgpu.gpu.request_adapter_sync(power_preference="high-performance")
device = adapter.request_device_sync()

# Load Data
print("Loading Data...")
brain_data = load_brain_data()
print("Data Loaded.")

# Setup Renderer and Camera
renderer = BrainRenderer(device, brain_data, canvas)
camera = Camera(canvas)

# Configure context
present_context = canvas.get_context("wgpu")
render_format = "bgra8unorm"
present_context.configure(device=device, format=render_format)

# Setup Trace Overlay
trace_renderer = TraceRenderer(device, render_format)
trace_renderer.set_data(brain_data.get("traces", []))

# Setup Text Renderer
text_renderer = TextRenderer(device, render_format)

# Animation State
color_frames = brain_data.get("color_frames")
atlas_colors = brain_data.get("atlas_colors")
start_time = time.time()
render_mode = "dynamic"
show_traces = True

def draw():
    """Main render callback function."""
    try:
        current_texture = present_context.get_current_texture()
        current_view = current_texture.create_view()
        
        size = current_texture.size
        if size[1] == 0:
            return
        aspect = size[0] / size[1]
        
        elapsed = time.time() - start_time
        frame_idx = 0
        
        # Animation
        if render_mode == "dynamic" and color_frames is not None:
            frame_idx = int(elapsed * 30) % color_frames.shape[1]
            current_colors = color_frames[:, frame_idx, :]
            renderer.update_colors(current_colors)
            canvas.request_draw()
        
        # Camera
        view_matrix = camera.get_view_matrix()
        
        # 3D Render
        renderer.draw(current_view, aspect, view_matrix, camera_pos=camera.position)
        
        # 2D Overlay
        if show_traces:
            trace_renderer.draw(current_view, frame_idx)
        
        # Text Overlay
        text_renderer.draw(current_view)
        
    except Exception as e:
        print(f"Draw Error: {e}")
        import traceback
        traceback.print_exc()

def handle_event(event):
    """Global event handler."""
    global render_mode, show_traces
    camera.handle_event(event)
    
    if event["event_type"] == "key_down":
        if event["key"] == "t":
            if render_mode == "dynamic":
                render_mode = "atlas"
                print("Switched to Atlas Mode.")
                renderer.set_visualization_mode(1.0)
                if atlas_colors is not None:
                    renderer.update_colors(atlas_colors)
            else:
                render_mode = "dynamic"
                print("Switched to Dynamic Mode.")
                renderer.set_visualization_mode(0.0)
            canvas.request_draw()
        elif event["key"] == "p":
            show_traces = not show_traces
            print(f"Butterfly Plot: {show_traces}")
            canvas.request_draw()

canvas.add_event_handler(handle_event, "pointer_down", "pointer_up", "pointer_move", "wheel", "key_down")
canvas.request_draw(draw)

if __name__ == "__main__":
    print("MNE Analyze Python started.")
    print("Controls: Left Click to Orbit, Right Click to Pan, Scroll to Zoom.")
    print("Key 't': Toggle Source Animation / Atlas Colors.")
    print("Key 'p': Toggle Butterfly Plot.")
    loop.run()
