# MNE Analyze Python

**High-Performance 3D Brain Visualization & Analysis**

MNE Analyze Python is a cutting-edge desktop application designed for the visualization and analysis of MNE-Python source estimation data. Built on **PySide6** for a modern, responsive user interface and **wgpu-py** (WebGPU) for next-generation hardware-accelerated 3D rendering, it offers a distinct performance advantage over traditional OpenGL-based viewers.

This tool is specifically engineered for researchers and clinicians working with MEG/EEG data who need to visualize cortical activity in real-time, explore raw signal recordings, and inspect source time courses with high fidelity.

---

## Key Features

### 🧠 High-Performance 3D Rendering
- **WebGPU Powered**: Utilizes the latest graphics API standards via `wgpu-py` to render high-resolution cortical surfaces efficiently.
- **Dynamic Visualization**: Real-time rendering of "Electric" source activity superimposed on the brain surface.
- **Atlas Support**: Toggle between dynamic source activation and static Atlas region visualization (e.g., Desikan-Killiany).
- **Butterfly Traces**: Overlay global signal traces directly on the 3D view for temporal context.

### 🗂️ Comprehensive Subject Management
- **Subject Configuration Panel**: A dedicated sidebar allows you to easily manage and switch between files for a specific subject:
  - **Raw Recordings**: Load `.fif` files to inspect sensor-level data.
  - **Surfaces**: Import cortical surface geometries (`.gii`, `.obj`, etc.).
  - **Atlases**: Load parcellation labels/annotations.
  - **Source Estimates (STC)**: Independently load Left Hemisphere (`-lh.stc`) and Right Hemisphere (`-rh.stc`) source time courses.

### 📈 integrated Data Browsers
- **Raw Data Browser**: A fully integrated, interaction-rich plot for exploring raw MEG/EEG sensor data. Features include zooming, panning, and time-locking with the 3D view.
- **Source Traces Browser**: A dedicated tab for visualizing source-level time courses (butterfly plots), automatically synchronized when you load an STC file.

### ⏯️ Playback & Control
- **Time-Locked Playback**: Scrub through time or play back the neural activity.
- **Interactive Navigation**: Intuitive camera controls for the 3D view.
- **Keyboard Shortcuts**: Rapidly toggle modes (T), traces (P), or playback (Space).

---

## Prerequisites

Before installing, ensure your system meets the following requirements:

- **Operating System**: macOS 12+, Windows 10/11, or modern Linux distribution.
- **Python**: Version 3.10 or higher.
- **Graphics Hardware**: A GPU compatible with **WebGPU**, **Vulkan**, **Metal**, or **DirectX 12**.
  - *Note: This application relies on `wgpu-py` which accesses the GPU directly. Older integrated graphics requiring legacy OpenGL drivers may not work.*

---

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/mne-analyze-python.git
cd mne-analyze-python
```

### 2. Set Up a Virtual Environment (Recommended)
It is highly recommended to use a virtual environment to manage dependencies.

**Using `venv`:**
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

**Using `uv` (Faster):**
```bash
pip install uv
uv venv
source .venv/bin/activate
```

### 3. Install Dependencies
Install the package in editable mode to ensure all dependencies (including MNE, PySide6, and wgpu) are installed correctly.

```bash
pip install -e .
```

---

## Running the Application

Once installed, you can launch the application directly from the root directory:

```bash
python main.py
```

---

## User Guide

### 1. The Workspace
The application window is divided into three main areas:
- **Left Sidebar (Controls)**: Manage Visualization settings (`Electric` vs `Atlas`) and **Subject Configuration**.
- **Central View**: The main 3D Brain Viewport.
- **Tabs**: Switch between the **Brain View**, **Raw Browser** (sensor data), and **Source Traces** (source data).

### 2. Loading Data
Use the **Subject Configuration** section in the top-left to load your files:
- Click the **Folder Icon** next to **Recording** to open a `.fif` file. This populate the "Raw Browser".
- Click the **Folder Icon** next to **Source (LH)** or **Source (RH)** to load source estimates. This will populate the "Source Traces" tab and the 3D view.

### 3. Navigation & Interaction
- **3D View**: Click and drag to rotate. Scroll to zoom. Right-click and drag to pan.
- **Keyboard Shortcuts**:
  - `Space`: Play / Pause animation.
  - `T`: Toggle between Source Activation view and Atlas Region view.
  - `P`: Toggle "Butterfly Traces" overlay on the 3D view.

---

## Troubleshooting

- **"WebGPU device not available"**: Ensure your GPU drivers are up to date and support Vulkan (Windows/Linux) or Metal (macOS).
- **Performance Issues**: If rendering is slow, check if the application is using your dedicated GPU instead of integrated graphics (common on laptops).

---

## License

MIT License. See `LICENSE` for details.
