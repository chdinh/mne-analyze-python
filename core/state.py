from dataclasses import dataclass

@dataclass
class AppState:
    """
    Holds the runtime state of the application.
    Independent of UI or Rendering backend.
    """
    # Visualization Settings
    visualization_mode: float = 0.0  # 0.0 = Electric Source, 1.0 = Atlas Regions
    show_traces: bool = True
    
    # Interaction State
    hovered_region_id: float = -1.0
    selected_region_id: float = -1.0
    hovered_region_name: str = ""
    
    # Animation State
    current_time: float = 0.0
    is_playing: bool = True
    time_speed: float = 1.0
