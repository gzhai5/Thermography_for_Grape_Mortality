import time
import pandas as pd
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtMultimedia import QSound
from mpl_canvas import MplCanvas
from experiment_params import ExperimentParameter
from data_process import find_top_sensitive_pixels, extract_mean_val
import os
import numpy as np


class ThermalAnalysisApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Thermal Analysis Tool")
        self.setMinimumSize(1200, 600)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

        # Other variables
        self.data = None
        self.previous_avg_plots = []
        self.previous_std_plots = []
        self.filename = ""
        self.show_std_points = True
        self.show_heatmap_flag = False
        self.multi_plot_mode = False
        self.label = True
        self.current_folder = ""
        self.current_frame_index = 0
        self.params = ExperimentParameter()
        self.csv_path = 'roi_data_ries_2.csv'

        # Main layout
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        grid_layout = QtWidgets.QGridLayout(central_widget)
        grid_layout.setColumnStretch(0, 1)
        grid_layout.setColumnStretch(1, 1)
        grid_layout.setColumnStretch(2, 1)
        grid_layout.setRowStretch(0, 1)
        grid_layout.setRowStretch(1, 1)

        # Top left: Image display
        left_top_layout = QtWidgets.QVBoxLayout()
        self.image_canvas = MplCanvas(self, modify_allowed=True, show_empty_first=True)
        left_top_layout.addWidget(self.image_canvas)

        self.progress_bar = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.progress_bar.setEnabled(False)
        self.progress_bar.setMinimumWidth(330)
        self.progress_bar.valueChanged.connect(self.on_frame_change)
        self.progress_info_label = QtWidgets.QLabel("0 / 0")
        self.progress_info_label.setAlignment(QtCore.Qt.AlignLeft)
        progress_layout = QtWidgets.QHBoxLayout()
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.progress_info_label)
        left_top_layout.addLayout(progress_layout)

        self.checkbox_layout = QtWidgets.QHBoxLayout()
        self.checkbox1 = QtWidgets.QCheckBox("Show Top N Sensistive Points")
        self.checkbox1.setChecked(True)
        self.checkbox1.setEnabled(False)
        self.checkbox1.stateChanged.connect(self.toggle_std_points)
        self.checkbox_layout.addWidget(self.checkbox1)
        self.checkbox2 = QtWidgets.QCheckBox("Show Std Heatmap")
        self.checkbox2.setChecked(False)
        self.checkbox2.setEnabled(False)
        self.checkbox2.stateChanged.connect(self.show_heatmap)
        self.checkbox_layout.addWidget(self.checkbox2)
        self.checkbox3 = QtWidgets.QCheckBox("Multi-Plot Enabled")
        self.checkbox3.setChecked(False)
        self.checkbox3.setEnabled(False)
        self.checkbox3.stateChanged.connect(self.multi_plot_enable)
        self.checkbox_layout.addWidget(self.checkbox3)
        left_top_layout.addLayout(self.checkbox_layout)

        frame_buttons_layout = QtWidgets.QHBoxLayout()
        frame_buttons_layout.setAlignment(QtCore.Qt.AlignLeft)
        frame_buttons_layout.setSpacing(10)
        self.revert_button = QtWidgets.QPushButton("Revert")
        self.revert_button.clicked.connect(self.revert_point_selection)
        self.revert_button.setEnabled(False)
        self.next_button = QtWidgets.QPushButton("Next")
        self.next_button.clicked.connect(self.next_file)
        self.next_button.setEnabled(False)
        frame_buttons_layout.addWidget(self.revert_button)
        frame_buttons_layout.addWidget(self.next_button)
        left_top_layout.addLayout(frame_buttons_layout)

        grid_layout.addLayout(left_top_layout, 0, 0)


        # Bottom left: heatmap for mean and std
        self.heatmap_canvas = MplCanvas(self, show_empty_first=True)
        grid_layout.addWidget(self.heatmap_canvas, 1, 0)

        # Top and Bottom Right: Plotting areas
        self.avg_plot_canvas = MplCanvas(self)
        self.std_plot_canvas = MplCanvas(self)
        grid_layout.addWidget(self.avg_plot_canvas, 0, 2)
        grid_layout.addWidget(self.std_plot_canvas, 1, 2)

        # Middle: Control board
        self.open_button = QtWidgets.QPushButton("Open Folder")
        self.open_button.clicked.connect(self.open_folder)
        self.npy_list_widget = QtWidgets.QListWidget()
        self.npy_list_widget.itemSelectionChanged.connect(self.on_file_selection)
        folder_layout = QtWidgets.QVBoxLayout()
        control_layout = QtWidgets.QHBoxLayout()
        folder_layout.addWidget(self.open_button)
        folder_layout.addWidget(self.npy_list_widget)
        control_layout.addLayout(folder_layout)

        buttons_layout = QtWidgets.QVBoxLayout()
        buttons_layout.setAlignment(QtCore.Qt.AlignTop)
        buttons_layout.setSpacing(10)
        self.threshold_title = QtWidgets.QLabel("Threshold:")
        self.threshold_input = QtWidgets.QLineEdit()
        self.threshold_input.setText("0")
        self.threshold_input.setReadOnly(True)
        self.threshold_input.textChanged.connect(self.on_threshold_change)

        self.top_n_title = QtWidgets.QLabel("Top N:")
        self.top_n_input = QtWidgets.QLineEdit()
        self.top_n_input.setText("0")
        self.top_n_input.setReadOnly(True)
        self.top_n_input.textChanged.connect(self.on_top_n_change)

        self.radius_title = QtWidgets.QLabel("Radius:")
        self.radius_input = QtWidgets.QLineEdit()
        self.radius_input.setText("0")
        self.radius_input.setReadOnly(True)
        self.radius_input.textChanged.connect(self.radius_change)

        self.label_checkbox = QtWidgets.QCheckBox("Alive?")
        self.label_checkbox.setChecked(True)
        self.label_checkbox.setEnabled(False)
        self.label_checkbox.stateChanged.connect(self.label_checkbox_change)

        self.save_button = QtWidgets.QPushButton("Save")
        self.save_button.setEnabled(False)
        self.save_button.clicked.connect(self.save_roi_data)

        buttons_layout.addWidget(self.threshold_title)
        buttons_layout.addWidget(self.threshold_input)
        buttons_layout.addWidget(self.top_n_title)
        buttons_layout.addWidget(self.top_n_input)
        buttons_layout.addWidget(self.radius_title)
        buttons_layout.addWidget(self.radius_input)
        buttons_layout.addWidget(self.label_checkbox)
        buttons_layout.addWidget(self.save_button)
        buttons_layout.setSpacing(20)
        control_layout.addLayout(buttons_layout)
        grid_layout.addLayout(control_layout, 0, 1, 2, 1)

    def refresh(self):
        self.params = ExperimentParameter()
        self.progress_bar.setValue(0)
        self.progress_info_label.setText("0 / 0")


    def on_threshold_change(self, value: int):
        if value:
            self.current_threshold = int(value)
            self.params.threshold = int(value)
            self.update_image_display()
            self.threshold_input.setText(f"{value}")

    def on_top_n_change(self, value: int):
        if value:
            self.current_top_n = int(value)
            self.params.interested_points_num = int(value)
            self.update_image_display()
            self.top_n_input.setText(f"{value}")

    def radius_change(self, value: int):
        if value:
            self.current_radius = int(value)
            self.params.selected_point_radius = int(value)
            self.update_raw_image_display(select_point_changed=True)
            self.radius_input.setText(f"{value}")
            self.update_plots()

    def save_roi_data(self):
        # Initialize the list to store all the data
        all_data = []

        if len(self.params.selected_points) != 1:
            print("Error: More than one point or no point selected")
            return
        
        x_coor = int(self.params.selected_points[0][0])
        y_coor = int(self.params.selected_points[0][1])

        # Extract the ROI
        region = self.data[:, 
                            max(y_coor - self.params.selected_point_radius, 0):min(y_coor + self.params.selected_point_radius + 1, self.data.shape[1]),
                            max(x_coor - self.params.selected_point_radius, 0):min(x_coor + self.params.selected_point_radius + 1, self.data.shape[2])]

        # Iterate through each frame
        for frame in range(region.shape[0]):
            # Extract the 7x7 region for the current frame and reshape to 7x7x1
            frame_data = region[frame, :, :].reshape(region.shape[1], region.shape[2], 1)
            all_data.append(frame_data)

        # Read the local csv file or create a new one
        if os.path.exists(self.csv_path):
            existing_data = pd.read_csv(self.csv_path)
        else:
            column_names = ['filename', 'Label', 'Breed'] + [f'Frame_{i+1}' for i in range(region.shape[0])]
            existing_data = pd.DataFrame(columns=column_names)

        # Add the new data to the DataFrame
        new_data = [self.filename, self.label, self.get_breed(self.filename)]
        for frame_data in all_data:
            new_data.append(frame_data)
        existing_data.loc[len(existing_data)] = new_data
        
        # Save the updated DataFrame to the csv file
        existing_data.to_csv(self.csv_path, index=False)
        self.play_sound()

    def open_folder(self):
        # Open folder dialog
        folder_path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder_path:
            self.current_folder = folder_path
            self.load_npy_files(folder_path)
            self.refresh()

    def load_npy_files(self, folder_path):
        # List .npy files in the folder
        self.npy_list_widget.clear()
        for file_name in os.listdir(folder_path):
            if file_name.endswith('.npy'):
                self.npy_list_widget.addItem(file_name)

    def on_file_selection(self):
        # Load selected .npy file and display first frame
        selected_item = self.npy_list_widget.currentItem()
        if selected_item:
            self.filename = selected_item.text()
            file_path = os.path.join(self.current_folder, self.filename)
            self.refresh()
            self.load_image(file_path)
            self.progress_bar.setEnabled(True)
            self.checkbox1.setEnabled(True)
            self.checkbox2.setEnabled(True)
            self.checkbox3.setEnabled(True)
            self.threshold_input.setReadOnly(False)
            self.threshold_input.setText(f"{self.params.threshold}")
            self.top_n_input.setReadOnly(False)
            self.top_n_input.setText(f"{self.params.interested_points_num}")
            self.radius_input.setReadOnly(False)
            self.radius_input.setText(f"{self.params.selected_point_radius}")
            self.next_button.setEnabled(True)
            self.label_checkbox.setEnabled(True)

    def load_image(self, file_path):
        # Load and display image from .npy file
        self.data = np.load(file_path)
        self.max_frames = self.data.shape[0]
        self.progress_bar.setMaximum(self.max_frames - 1)
        self.current_frame_index = 0
        self.update_image_display()
        total_frames = self.data.shape[0]
        self.progress_info_label.setText(f"0 / {total_frames}")

    def on_image_click(self, x, y):
        self.params.selected_points.append((x, y))
        self.save_button.setEnabled(True)
        self.revert_button.setEnabled(True)
        self.update_plots()
        self.update_raw_image_display(select_point_changed=True)

    def update_image_display(self):
        self.update_raw_image_display()
        self.update_heatmap_display() if self.show_heatmap_flag else self.heatmap_canvas.axes.clear()

    def update_raw_image_display(self, select_point_changed=False):
        frame = self.data[self.current_frame_index]
        self.image_canvas.axes.clear()  # Clear previous image/points
        self.image_canvas.axes.imshow(frame, cmap='hot')  # Display current frame

        if self.show_std_points:
            top_points = find_top_sensitive_pixels(self.data, self.params.interested_points_num,
                                                        self.params.start_heating_time * self.params.fps,
                                                        self.params.end_heating_time * self.params.fps,
                                                        self.params.threshold)
            x_coords, y_coords = zip(*top_points)
            self.image_canvas.axes.plot(y_coords, x_coords, 'ro', markersize=1)  # Plot with red dots

        # Plot selected points
        if select_point_changed and self.params.selected_points:
            selected_x_coords, selected_y_coords = zip(*self.params.selected_points)
            point_edge_length = 2 * self.params.selected_point_radius * (72 / self.image_canvas.dpi)
            self.image_canvas.axes.plot(selected_x_coords, selected_y_coords, 'bs', markersize=point_edge_length)  # Plot with blue dots

            for idx, (x, y) in enumerate(self.params.selected_points):
                self.image_canvas.axes.text(x, y, str(idx+1), color='orange', fontsize=8, ha='right', va='bottom')

        self.image_canvas.axes.axis('off')
        self.image_canvas.axes.set_title(f"Frame {self.current_frame_index} of the Raw Video Data")
        self.image_canvas.draw()

    # show the std heatmap of the selected data
    def update_heatmap_display(self):
        self.heatmap_canvas.axes.clear()

        start_frame = max(0, self.params.start_heating_time * self.params.fps)
        end_frame = min(self.data.shape[0], self.params.end_heating_time * self.params.fps)

        mean_values = np.mean(self.data[start_frame:end_frame, :, :], axis=0)
        mask = mean_values < self.params.threshold
        masked_data = self.data[start_frame:end_frame, :, :] * mask
        std_dev = np.std(masked_data, axis=0)

        self.heatmap_canvas.axes.imshow(std_dev, cmap='hot', interpolation='nearest')
        self.heatmap_canvas.axes.set_title('Standard Deviation Heatmap')
        self.heatmap_canvas.axes.axis('off')
        self.heatmap_canvas.draw()


    def on_frame_change(self, frame_index):
        # Handle frame change from progress bar
        self.current_frame_index = frame_index
        self.update_image_display()
        # Update frame info label
        total_frames = self.data.shape[0]
        self.progress_info_label.setText(f"{frame_index} / {total_frames}")

    def revert_point_selection(self):
        # Revert the order of selected points
        if self.params.selected_points:
            self.params.selected_points = self.params.selected_points[:-1]
            self.update_plots()
            self.update_raw_image_display(select_point_changed=True)
        else:
            self.revert_button.setEnabled(False)
            self.save_button.setEnabled(False)

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Z:
            print("Ctrl + Z pressed")
            self.revert_point_selection()
        elif event.key() == QtCore.Qt.Key_Space:
            print("Space pressed")
            self.next_file()
        elif event.key() == QtCore.Qt.Key_A:
            print("A pressed")
            self.label = not self.label
            self.label_checkbox.setChecked(self.label)
        elif event.key() == QtCore.Qt.Key_S:
            print("S pressed")
            self.save_roi_data()

    def play_sound(self):
        finish_sound = QSound("../static/signal.wav")
        finish_sound.play()

    def next_file(self):
        # Load next .npy file
        current_index = self.npy_list_widget.currentRow()
        if current_index < self.npy_list_widget.count() - 1:
            self.npy_list_widget.setCurrentRow(current_index + 1)
            self.on_file_selection()
        else:
            self.next_button.setEnabled(False)

    def toggle_std_points(self, state):
        # Toggle displaying top N std points
        self.show_std_points = (state == QtCore.Qt.Checked)
        self.update_image_display()

    def show_heatmap(self, state):
        # Toggle displaying heatmap
        self.show_heatmap_flag = (state == QtCore.Qt.Checked)
        self.update_image_display()

    def multi_plot_enable(self, state):
        # Toggle multi-plot mode
        self.multi_plot_mode = (state == QtCore.Qt.Checked)

    def label_checkbox_change(self, state):
        # Toggle label checkbox
        self.label = (state == QtCore.Qt.Checked)

    def update_plots(self):
        if not self.params.selected_points:
            return
        
        # Extract mean and standard deviation values for selected points
        mean_curves, std_curves = extract_mean_val(self.params.selected_points, self.data, self.params.selected_point_radius)
        
        # Prepare new plot data
        frame_indices = np.arange(len(mean_curves[0]))
        time_points = frame_indices / self.params.fps
        print(self.filename)
        new_avg_plot_data = [(time_points, curve, f"{i+1}st selected pt in {self.filename}" if i == 0 else f"{i+1}th selected pt in {self.filename}") for i, curve in enumerate(mean_curves)]
        new_std_plot_data = [(time_points, curve, f"{i+1}st selected pt in {self.filename}" if i == 0 else f"{i+1}th selected pt in {self.filename}") for i, curve in enumerate(std_curves)]

        # Clear existing plots
        self.avg_plot_canvas.axes.clear()
        self.std_plot_canvas.axes.clear()

        # Check multi plot mode
        if self.multi_plot_mode:
            # Append new data to previous data
            self.previous_avg_plots.extend(new_avg_plot_data)
            self.previous_std_plots.extend(new_std_plot_data)
        else:
            # Clear previous data
            self.previous_avg_plots = new_avg_plot_data
            self.previous_std_plots = new_std_plot_data
            # Clear existing plots
            self.avg_plot_canvas.axes.clear()
            self.std_plot_canvas.axes.clear()

        # Plotting mean curves
        for time_points, curve, label in self.previous_avg_plots:
            self.avg_plot_canvas.axes.plot(time_points, curve, label=label)
        self.avg_plot_canvas.axes.set_ylabel('Average Temperature')
        self.avg_plot_canvas.axes.set_title('Mean Temperature over Time')
        self.avg_plot_canvas.axes.legend()

        # Plotting standard deviation curves
        for time_points, curve, label in self.previous_std_plots:
            self.std_plot_canvas.axes.plot(time_points, curve, label=label)
        self.std_plot_canvas.axes.set_ylabel('Standard Deviation')
        self.std_plot_canvas.axes.set_xlabel('Time')
        self.std_plot_canvas.axes.set_title('Standard Deviation over Time')
        self.std_plot_canvas.axes.legend()

        # Redraw the plots
        self.avg_plot_canvas.draw()
        self.std_plot_canvas.draw()

    @staticmethod
    def get_breed(filename: str):
        return filename.split('_')[0]