import sys
import os
import cv2
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QLineEdit, QPushButton, QListWidget, QCheckBox, QFileDialog, QMessageBox, QProgressBar, QHBoxLayout, QGridLayout
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt

class VideoPlayer:
    def __init__(self, video_path, video_widget, progress_bar, cultivar_label, branch_label, node_label):
        self.video_path = video_path
        self.video_widget = video_widget
        self.frames = np.load(video_path)
        self.num_frames = len(self.frames)
        self.current_frame = 0
        self.video_paused = False
        self.timer = None
        self.progress_bar = progress_bar
        self.cultivar_label = cultivar_label
        self.branch_label = branch_label
        self.node_label = node_label

    def parse_filename(self, filename):
        parts = filename.split("_")
        if len(parts) < 3:
            raise ValueError("Invalid filename format.")
        cultivar_name = parts[0]
        branch = self.validate_number(parts[1], 0, 99)
        node = self.validate_number(parts[2].split(".")[0], 0, 99)
        return cultivar_name, branch, node

    def validate_number(self, number_str, min_val, max_val):
        try:
            number = int(number_str)
            if min_val <= number <= max_val:
                return number
        except ValueError:
            pass
        raise ValueError("Invalid number format or out of range.")
    
    def show_error_message(self, error_msg):
        error_box = QMessageBox()
        error_box.setIcon(QMessageBox.Critical)
        error_box.setWindowTitle("Error")
        error_box.setText("An error occurred:")
        error_box.setInformativeText(error_msg)
        error_box.exec_()

    def play_video(self):
        try:
            cultivar_name, branch, node = self.parse_filename(os.path.basename(self.video_path))
            self.cultivar_label.setText(cultivar_name)
            self.branch_label.setText(str(branch))
            self.node_label.setText(str(node))
        except ValueError as e:
            self.show_error_message(str(e))
            return
        
        while self.current_frame < self.num_frames:
            frame = self.frames[self.current_frame]
            frame = cv2.normalize(frame, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)
            image = QImage(frame, frame.shape[1], frame.shape[0], QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(image)
            self.video_widget.setPixmap(pixmap)
            self.progress_bar.setValue(int(self.current_frame * 100 / self.num_frames))
            QApplication.processEvents()
            cv2.waitKey(1)
            
            if not self.video_paused:
                self.current_frame += 1

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Player")
        self.setGeometry(100, 100, 800, 600)

        # Create widgets
        self.folder_lineedit = QLineEdit()
        self.browse_button = QPushButton("Browse")
        self.file_list = QListWidget()
        self.video_label = QLabel()
        self.run_pause_button = QPushButton("Run")
        self.cultivar_label = QLabel("unknown")
        self.branch_label = QLabel("unknown")
        self.node_label = QLabel("unknown")
        self.checkbox1 = QCheckBox("Checkbox 1")
        self.checkbox2 = QCheckBox("Checkbox 2")
        self.checkbox3 = QCheckBox("Checkbox 3")
        self.progress_bar = QProgressBar()

        # Connect signals to slots
        self.browse_button.clicked.connect(self.browse_folder)
        self.file_list.itemClicked.connect(self.load_video)
        self.run_pause_button.clicked.connect(self.toggle_playback)

        # Create layout
        main_layout = QHBoxLayout()
        video_layout = QVBoxLayout()
        info_layout = QGridLayout()

        video_layout.addWidget(self.video_label)
        video_layout.addWidget(self.progress_bar)
        video_layout.addWidget(self.run_pause_button)

        info_layout.addWidget(QLabel("Folder Path:"), 0, 0)
        info_layout.addWidget(self.folder_lineedit, 0, 1)
        info_layout.addWidget(self.browse_button, 0, 2)
        info_layout.addWidget(QLabel("File List:"), 1, 0)
        info_layout.addWidget(self.file_list, 1, 1, 1, 2)
        info_layout.addWidget(QLabel("Cultivar:"), 2, 0)
        info_layout.addWidget(self.cultivar_label, 2, 1)
        info_layout.addWidget(QLabel("Branch:"), 3, 0)
        info_layout.addWidget(self.branch_label, 3, 1)
        info_layout.addWidget(QLabel("Node:"), 4, 0)
        info_layout.addWidget(self.node_label, 4, 1)
        info_layout.addWidget(self.checkbox1, 5, 0)
        info_layout.addWidget(self.checkbox2, 6, 0)
        info_layout.addWidget(self.checkbox3, 7, 0)

        main_layout.addLayout(video_layout)
        main_layout.addLayout(info_layout)

        # Create central widget and set the layout
        central_widget = QWidget(self)
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # Initialize video player
        self.video_player = None
        self.video_paused = False

    def browse_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder_path:
            self.folder_lineedit.setText(folder_path)
            self.load_file_list(folder_path)

    def load_file_list(self, folder_path):
        self.file_list.clear()
        file_names = [f for f in os.listdir(folder_path) if f.endswith(".npy")]
        self.file_list.addItems(file_names)

    def load_video(self, item):
        video_path = os.path.join(self.folder_lineedit.text(), item.text())
        self.video_player = VideoPlayer(video_path, self.video_label, self.progress_bar, self.cultivar_label, self.branch_label, self.node_label)
        self.video_player.play_video()

    def toggle_playback(self):
        if self.video_player:
            if self.video_paused:
                self.run_pause_button.setText("Run")
            else:
                self.run_pause_button.setText("Pause")
            self.video_paused = not self.video_paused

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

