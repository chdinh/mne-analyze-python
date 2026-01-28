from PySide6 import QtWidgets, QtCore, QtGui
import os


class SubjectConfigItem(QtWidgets.QWidget):
    """
    Row item for configuring a specific subject file (Recording, Surface, Atlas).
    """
    file_selected = QtCore.Signal(str) # Emits path
    
    # Class variable to persist directory across instances
    last_directory = os.path.expanduser("~")

    def __init__(self, label_text, file_filter="All Files (*.*)", parent=None):
        super().__init__(parent)
        self.file_filter = file_filter
        
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.lbl_type = QtWidgets.QLabel(f"{label_text}:")
        self.lbl_type.setFixedWidth(80)
        
        self.lbl_value = QtWidgets.QLabel("None")
        self.lbl_value.setStyleSheet("color: gray; font-style: italic;")
        self.lbl_value.setWordWrap(True)
        
        self.btn_select = QtWidgets.QPushButton()
        self.btn_select.setIcon(self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_DirOpenIcon))
        self.btn_select.setFlat(True)
        self.btn_select.setToolTip("Browse...")
        self.btn_select.clicked.connect(self._on_select)
        
        layout.addWidget(self.lbl_type)
        layout.addWidget(self.lbl_value, stretch=1)
        layout.addWidget(self.btn_select)
        
    def _on_select(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Select File", SubjectConfigItem.last_directory, self.file_filter
        )
        if path:
            SubjectConfigItem.last_directory = os.path.dirname(path)
            self.set_value(path)
            self.file_selected.emit(path)
            
    def set_value(self, path):
        filename = os.path.basename(path)
        self.lbl_value.setText(filename)
        self.lbl_value.setStyleSheet("color: white;")
        self.lbl_value.setToolTip(path)

class SubjectConfigWidget(QtWidgets.QGroupBox):
    """
    Group box for configuring subject files.
    """
    recording_changed = QtCore.Signal(str)
    surface_changed = QtCore.Signal(str)
    atlas_changed = QtCore.Signal(str)

    def __init__(self, parent=None):
        super().__init__("Subject Configuration", parent)
        layout = QtWidgets.QVBoxLayout(self)
        
        # Recording
        self.item_recording = SubjectConfigItem("Recording", "Raw FIF (*_raw.fif);;All Files (*)")
        self.item_recording.file_selected.connect(self.recording_changed.emit)
        
        # Surface
        self.item_surface = SubjectConfigItem("Surface", "Geometry Files (*.gii *.obj *.stl *.ply)")
        self.item_surface.file_selected.connect(self.surface_changed.emit)
        
        # Atlas
        self.item_atlas = SubjectConfigItem("Atlas", "Label Files (*.nii *.nii.gz *.mgz *.label)")
        self.item_atlas.file_selected.connect(self.atlas_changed.emit)
        
        layout.addWidget(self.item_recording)
        layout.addWidget(self.item_surface)
        layout.addWidget(self.item_atlas)

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
        self.model.setNameFilters(["*_raw.fif"])
        self.model.setNameFilterDisables(False)
        
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
    
    # Forward subject signals
    recording_changed = QtCore.Signal(str)
    surface_changed = QtCore.Signal(str)
    atlas_changed = QtCore.Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QtWidgets.QVBoxLayout(self)
        
        # Section 0: Subject Config
        self.subject_config = SubjectConfigWidget()
        self.subject_config.recording_changed.connect(self.recording_changed.emit)
        self.subject_config.surface_changed.connect(self.surface_changed.emit)
        self.subject_config.atlas_changed.connect(self.atlas_changed.emit)
        
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
        
        # Section 3: Browser (Removed)
        # self.browser = FileBrowserWidget(start_path=os.path.expanduser("~"))
        
        self.layout.addWidget(self.subject_config)
        self.layout.addWidget(grp_vis)
        self.layout.addWidget(self.lbl_region)
        self.layout.addStretch(1)
        
    def set_hovered_region(self, name):
        self.lbl_region.setText(f"Hovered: {name}")

