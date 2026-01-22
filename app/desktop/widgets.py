from PySide6 import QtWidgets, QtCore, QtGui
import os

class FileBrowserWidget(QtWidgets.QWidget):
    """
    Displays the file system to select recording directories/files.
    """
    file_selected = QtCore.Signal(str) # Path

    def __init__(self, start_path=".", parent=None):
        super().__init__(parent)
        self.layout = QtWidgets.QVBoxLayout(self)
        
        # Model
        self.model = QtWidgets.QFileSystemModel()
        self.model.setRootPath(start_path)
        self.model.setFilter(QtCore.QDir.AllDirs | QtCore.QDir.Files | QtCore.QDir.NoDotAndDotDot)
        # Filters for STC files etc if needed
        # self.model.setNameFilters(["*.stc", "*.label"])
        
        # View
        self.tree = QtWidgets.QTreeView()
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(start_path))
        self.tree.setAnimated(False)
        self.tree.setIndentation(20)
        self.tree.setSortingEnabled(True)
        self.tree.setColumnWidth(0, 200)
        
        self.tree.clicked.connect(self._on_click)
        
        self.layout.addWidget(QtWidgets.QLabel("Recordings Browser"))
        self.layout.addWidget(self.tree)
        
    def _on_click(self, index):
        path = self.model.filePath(index)
        self.file_selected.emit(path)

class PlaybackControls(QtWidgets.QWidget):
    """
    Timeline slider and Play/Pause button.
    """
    time_changed = QtCore.Signal(float)
    play_toggled = QtCore.Signal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QHBoxLayout(self)
        
        self.btn_play = QtWidgets.QPushButton("Pause")
        self.btn_play.setCheckable(True)
        self.btn_play.setChecked(True) # Playing by default
        self.btn_play.clicked.connect(self._on_play)
        
        self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider.setRange(0, 100) # Percentage or Frames
        self.slider.valueChanged.connect(self._on_slider)
        
        layout.addWidget(self.btn_play)
        layout.addWidget(self.slider)
        
    def _on_play(self, checked):
        self.btn_play.setText("Pause" if checked else "Play")
        self.play_toggled.emit(checked)
        
    def _on_slider(self, val):
        # Normalized 0..1
        self.time_changed.emit(val / 100.0)

class AppControls(QtWidgets.QWidget):
    """
    Main Sidebar Widget combining FileBrowser and Global Settings.
    """
    mode_changed = QtCore.Signal(int) # 0=Electric, 1=Atlas
    traces_toggled = QtCore.Signal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QtWidgets.QVBoxLayout(self)
        
        # Section 1: Visibility
        grp_vis = QtWidgets.QGroupBox("Visualization")
        v_layout = QtWidgets.QVBoxLayout()
        
        self.check_traces = QtWidgets.QCheckBox("Show Butterfly Traces")
        self.check_traces.setChecked(True)
        self.check_traces.toggled.connect(self.traces_toggled.emit)
        
        self.radio_electric = QtWidgets.QRadioButton("Electric Source (Dynamic)")
        self.radio_electric.setChecked(True)
        self.radio_electric.toggled.connect(lambda c: self.mode_changed.emit(0) if c else None)
        
        self.radio_atlas = QtWidgets.QRadioButton("Atlas Regions (Static)")
        self.radio_atlas.toggled.connect(lambda c: self.mode_changed.emit(1) if c else None)
        
        v_layout.addWidget(self.check_traces)
        v_layout.addWidget(self.radio_electric)
        v_layout.addWidget(self.radio_atlas)
        grp_vis.setLayout(v_layout)
        
        # Section 2: Info
        self.lbl_region = QtWidgets.QLabel("Hovered: None")
        self.lbl_region.setStyleSheet("font-weight: bold; color: yellow;") # Dark mode friendly?
        
        # Section 3: Browser
        self.browser = FileBrowserWidget(start_path=os.path.expanduser("~"))
        
        self.layout.addWidget(grp_vis)
        self.layout.addWidget(self.lbl_region)
        self.layout.addWidget(self.browser, stretch=1)
        
    def set_hovered_region(self, name):
        self.lbl_region.setText(f"Hovered: {name}")

