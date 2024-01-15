import sys
import os
import numpy as np
from PyQt5 import QtWidgets, QtCore
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class ExperimentParameter:
    def __init__(self):
        self.fps = 30
        self.start_experiment_time = 0
        self.start_heating_time = 1
        self.end_heating_time = 10
        self.end_experiment_time = 20

        self.interested_points_num = 1000
        self.selected_points = []
        self.threshold = 9400
        self.selected_point_radius = 5

class MplCanvas(FigureCanvas):
    def __init__(self, parent, width=5, height=4, dpi=100, modify_allowed=False, show_empty_first=False):
        self.parent = parent
        self.dpi = dpi
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super().__init__(fig)
        if modify_allowed:
            self.mpl_connect('button_press_event', self.on_click)
        if show_empty_first:
            self.display_empty()

    def display_image(self, image_data):
        self.axes.imshow(image_data, cmap='gray')  # Display as grayscale
        self.axes.axis('off')  # Turn off axis
        self.draw()

    def display_empty(self):
        # Create an empty black image
        data = np.zeros((150, 150, 3), dtype=np.uint8)
        self.axes.imshow(data)
        self.axes.axis('off')

        # Add text to the image
        self.axes.text(0.5, 0.5, 'Please select the data file\n\n to read first',
                       color='white', ha='center', va='center', transform=self.axes.transAxes)
        self.draw()

    def on_click(self, event):
        if event.inaxes == self.axes:
            x, y = int(event.xdata), int(event.ydata)
            self.parent.on_image_click(x, y)

class ThermalAnalysisApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Thermal Analysis Tool")
        self.setMinimumSize(1200, 600)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

        # Other variables
        self.data = None
        self.show_std_points = True
        self.current_folder = ""
        self.current_frame_index = 0
        self.params = ExperimentParameter()

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

        self.progress_bar = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.progress_bar.setEnabled(False)
        self.progress_bar.valueChanged.connect(self.on_frame_change)
        self.progress_info_label = QtWidgets.QLabel("0 / 0")
        self.progress_info_label.setAlignment(QtCore.Qt.AlignLeft)

        self.checkbox = QtWidgets.QCheckBox("Show Top N Sensistive Points")
        self.checkbox.setChecked(True)
        self.checkbox.setEnabled(False)
        self.checkbox.stateChanged.connect(self.toggle_std_points)

        frame_buttons_layout = QtWidgets.QHBoxLayout()
        frame_buttons_layout.setAlignment(QtCore.Qt.AlignTop)
        frame_buttons_layout.setSpacing(10)
        self.revert_button = QtWidgets.QPushButton("Revert")
        self.revert_button.clicked.connect(self.revert_point_selection)
        self.revert_button.setEnabled(False)
        frame_buttons_layout.addWidget(self.revert_button)

        self.next_button = QtWidgets.QPushButton("Next")
        self.next_button.clicked.connect(self.next_file)
        self.next_button.setEnabled(False)
        frame_buttons_layout.addWidget(self.next_button)

        self.image_canvas = MplCanvas(self, modify_allowed=True, show_empty_first=True)

        left_top_layout = QtWidgets.QVBoxLayout()
        left_top_layout.addWidget(self.image_canvas)
        left_top_layout.addWidget(self.checkbox)

        progress_layout = QtWidgets.QHBoxLayout()
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addStretch(4)
        progress_layout.addWidget(self.progress_info_label)
        progress_layout.addStretch(1)
        left_top_layout.addLayout(progress_layout)
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

        buttons_layout.addWidget(self.threshold_title)
        buttons_layout.addWidget(self.threshold_input)
        buttons_layout.addWidget(self.top_n_title)
        buttons_layout.addWidget(self.top_n_input)
        buttons_layout.addWidget(self.radius_title)
        buttons_layout.addWidget(self.radius_input)
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
            self.update_image_display()
            self.radius_input.setText(f"{value}")
            self.update_plots()

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
            file_name = selected_item.text()
            file_path = os.path.join(self.current_folder, file_name)
            self.refresh()
            self.load_image(file_path)
            self.progress_bar.setEnabled(True)
            self.checkbox.setEnabled(True)
            self.threshold_input.setReadOnly(False)
            self.threshold_input.setText(f"{self.params.threshold}")
            self.top_n_input.setReadOnly(False)
            self.top_n_input.setText(f"{self.params.interested_points_num}")
            self.radius_input.setReadOnly(False)
            self.radius_input.setText(f"{self.params.selected_point_radius}")
            self.next_button.setEnabled(True)

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
        self.revert_button.setEnabled(True)
        self.update_plots()
        self.update_image_display()

    def update_image_display(self):
        self.update_raw_image_display()
        self.update_heatmap_display()

    def update_raw_image_display(self):
        frame = self.data[self.current_frame_index]
        self.image_canvas.axes.clear()  # Clear previous image/points
        self.image_canvas.axes.imshow(frame, cmap='gray')  # Display current frame

        if self.show_std_points:
            top_points = self.find_top_sensitive_pixels(self.data, self.params.interested_points_num,
                                                        self.params.start_heating_time * self.params.fps,
                                                        self.params.end_heating_time * self.params.fps,
                                                        self.params.threshold)
            x_coords, y_coords = zip(*top_points)
            self.image_canvas.axes.plot(y_coords, x_coords, 'ro', markersize=1)  # Plot with red dots

        # Plot selected points
        if self.params.selected_points:
            selected_x_coords, selected_y_coords = zip(*self.params.selected_points)
            print(f'selected x: {selected_x_coords}, selected y: {selected_y_coords}')
            point_diameter = 2 * self.params.selected_point_radius * (72 / self.image_canvas.dpi)
            self.image_canvas.axes.plot(selected_x_coords, selected_y_coords, 'bo', markersize=point_diameter)  # Plot with blue dots

            for idx, (x, y) in enumerate(self.params.selected_points):
                self.image_canvas.axes.text(x, y, str(idx), color='orange', fontsize=8, ha='right', va='bottom')

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
            self.params.selected_points = self.params.selected_points[::-1]
            self.update_plots()
            self.update_image_display()
        else:
            self.revert_button.setEnabled(False)

    def keyPressEvent(self, event):
        modifiers = event.modifiers()
        if modifiers == QtCore.Qt.ControlModifier or modifiers == QtCore.Qt.MetaModifier:
            if event.key() == QtCore.Qt.Key_Z:
                print("Ctrl + Z pressed")
                self.revert_point_selection()
        elif event.key() == QtCore.Qt.Key_Space:
            print("Space pressed")
            self.next_file()

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

    def update_plots(self):
        if not self.params.selected_points:
            return
        
        # Extract mean and standard deviation values for selected points
        mean_curves, std_curves = self.extract_mean_val(self.params.selected_points, self.data, self.params.selected_point_radius)

        # Clear existing plots
        self.avg_plot_canvas.axes.clear()
        self.std_plot_canvas.axes.clear()

        # Plotting mean curves
        frame_indices = np.arange(len(mean_curves[0]))
        time_points = frame_indices / self.params.fps
        for i, curve in enumerate(mean_curves):
            label = f"{i+1}st selected point" if i == 0 else f"{i+1}th selected point"
            self.avg_plot_canvas.axes.plot(time_points, curve, label=label)
        self.avg_plot_canvas.axes.set_ylabel('Average Temperature')
        self.avg_plot_canvas.axes.set_title('Mean Temperature over Time')
        self.avg_plot_canvas.axes.legend()

        # Plotting standard deviation curves
        for i, curve in enumerate(std_curves):
            label = f"{i+1}st selected point" if i == 0 else f"{i+1}th selected point"
            self.std_plot_canvas.axes.plot(time_points, curve, label=label)
        self.std_plot_canvas.axes.set_ylabel('Standard Deviation')
        self.std_plot_canvas.axes.set_xlabel('Time')
        self.std_plot_canvas.axes.set_title('Standard Deviation over Time')
        self.std_plot_canvas.axes.legend()

        # Redraw the plots
        self.avg_plot_canvas.draw()
        self.std_plot_canvas.draw()

    def find_top_sensitive_pixels(self, data: np.ndarray, top_n: int, start_frame: int, end_frame: int, threshold: int) -> list:
        # Ensure the frame range is within the data bounds
        start_frame = max(0, start_frame)
        end_frame = min(data.shape[0], end_frame)

        mean_values = np.mean(data[start_frame:end_frame, :, :], axis=0)
        mask = self.mask_pixel_filter(mean_values, threshold)

        # Apply the mask and calculate the standard deviation for the masked pixels
        masked_data = data[start_frame:end_frame, :, :] * mask
        std_dev = np.std(masked_data, axis=0)

        # Flatten the std_dev array and get the indices of the top N std deviations
        flat_std_dev = std_dev.flatten()
        indices = np.argpartition(flat_std_dev, -top_n)[-top_n:]
        sorted_indices = indices[np.argsort(flat_std_dev[indices])][::-1]

        # Convert flat indices to 2D indices
        x_coords, y_coords = np.unravel_index(sorted_indices, std_dev.shape)
        return list(zip(x_coords, y_coords))
    
    # two methods apply mask to the data
    # 1. mask the pixels with mean < threshold
    # 2. mask the pixels with only the center of whole image
    @staticmethod
    def mask_pixel_filter(mean_values, threshold: int):
        mask = mean_values < threshold
        height, width = mean_values.shape
        mask[:int(height/3), :] = False
        mask[int(height*2/3):, :] = False
        mask[:, :int(width/3)] = False
        mask[:, int(width*2/3):] = False
        return mask

    
    @staticmethod
    def extract_mean_val(pixels: list, data: np.ndarray, radius: int):
        mean_curves = []
        std_curves = []
        for (x, y) in pixels:
            x_coor = int(x)
            y_coor = int(y)
            region = data[:, max(y_coor-radius, 0):min(y_coor+radius, data.shape[1]),
                            max(x_coor-radius, 0):min(x_coor+radius, data.shape[2])]
            mean_curve = np.mean(region, axis=(1, 2))
            std_curve = np.std(region, axis=(1, 2))
            mean_curves.append(mean_curve)
            std_curves.append(std_curve)
        return mean_curves, std_curves

# Main execution
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    main_window = ThermalAnalysisApp()
    main_window.show()
    sys.exit(app.exec_())
