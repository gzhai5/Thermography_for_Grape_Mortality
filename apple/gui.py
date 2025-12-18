import logging
import cv2
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTextEdit, QFileDialog, QRadioButton, QGroupBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage
from threads.stream import StreamingThread
from threads.acquisition import AcquisitionThread
from threads.halt import HaltingThread

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

folder_path = './stored_data/'

class MyApp(QWidget):
    def __init__(self, mode="halt"):
        super().__init__()
        self.mode = mode
        self.active_thread = None
        # # Initialize Matplotlib figure and canvas
        # self.figure = plt.figure()
        # self.canvas = FigureCanvas(self.figure)
        # self.plot_data = []
        self.initUI()

    def initUI(self):
        logging.info('Initializing UI')
        # Main Layout
        mainLayout = QVBoxLayout()
        self.setMinimumSize(1200, 800)

        # Video Display Area
        topLayout = QHBoxLayout()
        self.videoLabel = QLabel('Video Display Area', self)
        self.videoLabel.setAlignment(Qt.AlignCenter)
        self.videoLabel.setMinimumSize(400, 300)
        self.videoLabel.setStyleSheet("QLabel { background-color : #2C2C54; color: white;}")
        topLayout.addWidget(self.videoLabel)

        # Control Panel
        controlLayout = QVBoxLayout()
        # Group Box for Radio Buttons
        modeGroupBox = QGroupBox("")
        modeGroupBox.setTitle("Please select the mode:")
        modeGroupBox.setStyleSheet("QGroupBox { background-color: #2C2C54; color: white; border-radius: 5px; padding: 2px; }")
        modeLayout = QVBoxLayout()
        # Radio Buttons
        self.haltRadio = QRadioButton("Halt")
        self.haltRadio.setChecked(True) if (self.mode != "halt") and (self.mode != "acquire") else None
        self.haltRadio.toggled.connect(self.toggle_halt)
        self.toggle_halt() if self.haltRadio.isChecked() else None
        self.haltRadio.setStyleSheet("QRadioButton { background-color: #2C2C54; color: white; font-size: 30px; font-weight: semi-bold;}")
        self.streamRadio = QRadioButton("Stream")
        self.streamRadio.setStyleSheet("QRadioButton { background-color: #2C2C54; color: white; font-size: 30px; font-weight: semi-bold;}")
        self.streamRadio.setChecked(True) if self.mode == "stream" else None
        self.streamRadio.toggled.connect(self.toggle_stream)
        self.toggle_stream() if self.streamRadio.isChecked() else None
        self.acquisitionRadio = QRadioButton("Acquisition")
        self.acquisitionRadio.setChecked(True) if self.mode == "acquire" else None
        self.acquisitionRadio.toggled.connect(self.toggle_acquisition)
        self.acquisitionRadio.setStyleSheet("QRadioButton { background-color: #2C2C54; color: white; font-size: 30px; font-weight: semi-bold;}")
        self.toggle_acquisition() if self.acquisitionRadio.isChecked() else None
        modeLayout.addWidget(self.haltRadio)
        modeLayout.addWidget(self.streamRadio)
        modeLayout.addWidget(self.acquisitionRadio)
        modeGroupBox.setLayout(modeLayout)
        controlLayout.addWidget(modeGroupBox)
        # Save Path Button
        self.savePathButton = QPushButton('Select Save Path')
        self.savePathButton.clicked.connect(self.selectSavePath)
        controlLayout.addWidget(self.savePathButton)
        topLayout.addLayout(controlLayout)

        mainLayout.addLayout(topLayout)

        # Plot area
        botLayout = QHBoxLayout()
        self.plotLabel = QLabel('Plot Area', self)
        self.plotLabel.setAlignment(Qt.AlignCenter)
        self.plotLabel.setMinimumSize(400, 300)
        self.plotLabel.setStyleSheet("QLabel { background-color : #2C2C54; color: white; }")
        # self.plotLabel.setParent(None)
        botLayout.addWidget(self.plotLabel)

        # Lab Logo
        self.labLogo = QLabel(self)
        pixmap = QPixmap('./static/logo.png')
        self.labLogo.setPixmap(pixmap)
        self.labLogo.setAlignment(Qt.AlignCenter)
        self.labLogo.setScaledContents(False)
        self.labLogo.setMinimumSize(270, 91)
        botLayout.addWidget(self.labLogo)

        mainLayout.addLayout(botLayout)

        # Set Main Layout and Window Properties
        self.setLayout(mainLayout)
        self.setWindowTitle('Apple Tree Thermography System')
        self.setGeometry(300, 300, 600, 600) # Window size

        # Styling
        self.setStyleSheet("QWidget { background-color: #474787; }"
                           "QPushButton { background-color: #2C2C54; color: white; font-weight: bold; }")
        logging.info('UI Initialized')

    def selectSavePath(self):
        options = QFileDialog.Options()
        folderPath = QFileDialog.getExistingDirectory(self, "Select Directory", options=options)
        if folderPath:
            self.savePathButton.setText(folderPath)
            global folder_path
            folder_path = folderPath
            logging.info(f'Save path selected: {folderPath}')

    def toggle_stream(self):
        if self.streamRadio.isChecked():
            self.active_thread.stop() if self.active_thread else None
            self.active_thread = StreamingThread(0)
            self.active_thread.update_image.connect(self.update_image_display)
            self.active_thread.start()
            logging.info('Stream mode selected')
        else:
            self.active_thread.stop() if self.active_thread else None
            self.active_thread = None
            logging.info('Stream mode deselected')

    def toggle_halt(self):
        if self.haltRadio.isChecked():
            self.active_thread.stop() if self.active_thread else None
            self.active_thread = HaltingThread()
            self.active_thread.change_pixmap_signal.connect(self.update_image_display)
            self.active_thread.start()
            logging.info("Halt mode slected")
        else:
            self.active_thread.stop() if self.active_thread else None
            self.active_thread = None
            logging.info("Halt mode stopped")

    def toggle_acquisition(self):
        if self.acquisitionRadio.isChecked():
            self.active_thread.stop() if self.active_thread else None
            self.active_thread = AcquisitionThread(0, file_path=folder_path)
            self.active_thread.update_image.connect(self.update_image_display)
            self.active_thread.start()
            logging.info("Acquisition Mode selected")
        else:
            self.active_thread.stop() if self.active_thread else None
            self.active_thread = None
            logging.info("Acquisition mode Stopped")

    def update_image_display(self, image, mean_value=None):
        # Convert the image to QPixmap and display it
        qt_img = self.convert_cv_qt(image)
        self.videoLabel.setPixmap(qt_img)

        # Update the plot with the new mean value
        # self.update_plot(mean_value)

    def update_plot(self, mean_value):
        # Add the new mean value to the data and redraw the plot
        self.plot_data.append(mean_value)
        self.figure.clear()
        plt.plot(self.plot_data, '-o')  # Plotting the data
        plt.ylabel('Mean Value')
        plt.xlabel('Frame')
        self.canvas.draw()

    def convert_cv_qt(self, cv_img):
        if (len(cv_img.shape) == 2):
            rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_GRAY2RGB)
        else:
            rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)

        height, width, channel = rgb_image.shape

        if len(cv_img.shape) == 2:
            convert_to_qt_format = QImage(rgb_image.data, cv_img.shape[1], cv_img.shape[0], 0, QImage.Format_RGB888)
        else:
            bytes_per_line = channel * width
            convert_to_qt_format = QImage(rgb_image.data, width, height, bytes_per_line, QImage.Format_RGB888)
        p = convert_to_qt_format.scaled(620, 330, Qt.KeepAspectRatio)
        return QPixmap.fromImage(p)