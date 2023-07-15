import sys
import os, time
import cv2
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QLineEdit, QPushButton, QListWidget, QCheckBox, QFileDialog, QMessageBox, QProgressBar, QHBoxLayout, QGridLayout
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt
import csv

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
        self.filename = None

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
            number = int(number_str[len(number_str)-2:])
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

        # Parse filename and set labels
        try:
            cultivar_name, branch, node = self.parse_filename(os.path.basename(self.video_path))
            self.filename = os.path.basename(self.video_path)
            self.cultivar_label.setText(cultivar_name)
            self.branch_label.setText(str(branch))
            self.node_label.setText(str(node))
        except ValueError as e:
            self.show_error_message(str(e))
            return
        
        # first freeze the video playing
        self.video_paused = True

        # settings for video playback
        frame_rate = 30
        actual_frame_rate = self.num_frames / len(self.frames)
        frame_delay = int((1 / frame_rate) * 1000)

        # start playing video
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

            actual_frame_delay = int(frame_delay / actual_frame_rate)
            time.sleep(actual_frame_delay/1000)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Player")
        self.setGeometry(100, 100, 800, 600)
        self.setMinimumWidth(1350)
        self.setMinimumHeight(700)

        # Create widgets
        self.folder_lineedit = QLineEdit()
        self.browse_button = QPushButton("Browse")
        self.file_list = QListWidget()
        self.video_label = QLabel()
        self.run_pause_button = QPushButton("Run")
        self.cultivar_label = QLabel("unknown")
        self.branch_label = QLabel("unknown")
        self.node_label = QLabel("unknown")
        self.checkbox1 = QCheckBox("Primary Bud Damaged")
        self.checkbox2 = QCheckBox("Secondary Bud Damaged")
        self.checkbox3 = QCheckBox("Tertiary Bud Damaged")
        self.progress_bar = QProgressBar()
        self.add_results_button = QPushButton("Add Results")
        self.generate_csv_button = QPushButton("Generate CSV")

        # Connect signals to slots
        self.browse_button.clicked.connect(self.browse_folder)
        self.file_list.itemClicked.connect(self.load_video)
        self.run_pause_button.clicked.connect(self.toggle_playback)
        self.add_results_button.clicked.connect(self.add_results)
        self.generate_csv_button.clicked.connect(self.generate_csv)

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
        info_layout.addWidget(self.add_results_button, 8, 0)
        info_layout.addWidget(self.generate_csv_button, 8, 1)

        main_layout.addLayout(video_layout)
        main_layout.addLayout(info_layout)

        # Create central widget and set the layout
        central_widget = QWidget(self)
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # Initialize video player
        self.video_player = None
        self.csv_data = []

        # local variables
        self.folder_path = None
        self.temp_file_path = "./validate.param.temp.txt"

        # check the temp file, if exist, load it content to the csv_data
        if os.path.exists(self.temp_file_path):
            try:
                with open(self.temp_file_path, mode='r') as temp_file:
                    reader = csv.reader(temp_file)
                    self.csv_data = list(reader)
            except Exception as e:
                print("Error loading temp file: {}".format(e))

    # close GUI
    def closeEvent(self, event):
        self.clean_temp_param(self.temp_file_path)
        event.accept()

    def browse_folder(self):
        self.folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if self.folder_path:
            self.folder_lineedit.setText(self.folder_path)
            self.load_file_list(self.folder_path)

    def load_file_list(self, folder_path):
        self.file_list.clear()
        file_names = [f for f in os.listdir(folder_path) if f.endswith(".npy")]
        self.file_list.addItems(file_names)

    def load_video(self, item):
        video_path = os.path.join(self.folder_lineedit.text(), item.text())
        self.video_player = VideoPlayer(video_path, self.video_label, self.progress_bar, self.cultivar_label, self.branch_label, self.node_label, app)
        self.video_player.play_video()
        self.csv_data = []

    def update_csv_data(self):
        if self.video_player:
            filename = os.path.basename(self.video_player.video_path)
            checkbox1_state = self.checkbox1.isChecked()
            checkbox2_state = self.checkbox2.isChecked()
            checkbox3_state = self.checkbox3.isChecked()
            checkbox1_result = "damaged" if checkbox1_state else "undamaged"
            checkbox2_result = "damaged" if checkbox2_state else "undamaged"
            checkbox3_result = "damaged" if checkbox3_state else "undamaged"
            self.csv_data.append([filename, checkbox1_result, checkbox2_result, checkbox3_result])
            self.save_temp_param(self.csv_data, self.temp_file_path)

    # a backup plan for keep saving down param file
    @staticmethod
    def save_temp_param(csv_data, temp_file_path):
        try:
            with open(temp_file_path, mode='w', newline='') as temp_file:
                writer = csv.writer(temp_file)
                writer.writerows(csv_data)
        except Exception as e:
            print("Error saving temp file: {}".format(e))

    @staticmethod
    def clean_temp_param(temp_file_path):
        if os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
                print("Temp file removed successfully.")
            except Exception as e:
                print("Error removing temp file: {}".format(e))
        else:
            print("Temp file does not exist.")

    def toggle_playback(self):
        if self.video_player:
            if self.video_player.video_paused == False:
                self.video_player.video_paused = True
                self.run_pause_button.setText("Run")
            else:
                self.video_player.video_paused = False
                self.run_pause_button.setText("Pause")

    def add_results(self):
        self.update_csv_data()
        print("Results added to CSV list.")

    def generate_csv(self):
        # Open a file dialog to choose the save location for the CSV file
        default_file_name = os.path.basename(self.folder_path) + ".csv"
        save_path, _ = QFileDialog.getSaveFileName(self, "Save CSV File", default_file_name, "CSV Files (*.csv)")
        if save_path:
            try:
                # Write the CSV file
                with open(save_path, "w", newline="") as csv_file:
                    writer = csv.writer(csv_file)
                    writer.writerow(["Filename", "Checkbox 1", "Checkbox 2", "Checkbox 3"])  # Write header row
                    writer.writerows(self.csv_data)  # Write data rows

                QMessageBox.information(self, "CSV Generated", "CSV file generated successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"An error occurred while generating the CSV file:\n{str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

