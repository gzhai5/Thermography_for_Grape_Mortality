import logging
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTextEdit, QFileDialog, QRadioButton, QGroupBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from threads.stream import StreamingThread

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class MyApp(QWidget):
    def __init__(self):
        super().__init__()
        self.stream_thread = StreamingThread(0)
        self.stream_thread.update_image.connect(self.update_image_display)
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
        self.haltRadio.setChecked(True)
        self.haltRadio.setStyleSheet("QRadioButton { background-color: #2C2C54; color: white; font-size: 30px; font-weight: semi-bold;}")
        self.streamRadio = QRadioButton("Stream")
        self.streamRadio.setStyleSheet("QRadioButton { background-color: #2C2C54; color: white; font-size: 30px; font-weight: semi-bold;}")
        self.streamRadio.toggled.connect(self.toggle_stream)
        self.acquisitionRadio = QRadioButton("Acquisition")
        self.acquisitionRadio.setStyleSheet("QRadioButton { background-color: #2C2C54; color: white; font-size: 30px; font-weight: semi-bold;}")
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
            logging.info(f'Save path selected: {folderPath}')

    def toggle_stream(self):
        if self.streamRadio.isChecked():
            logging.info('Stream mode selected')
            self.stream_thread.start()
        else:
            logging.info('Stream mode deselected')
            self.stream_thread.stop()

    def update_image_display(self, image):
        # Convert the image to QPixmap and display it
        qimage = QImage(image.data, image.shape[1], image.shape[0], QImage.Format_RGB888).rgbSwapped()
        pixmap = QPixmap.fromImage(qimage)
        self.videoLabel.setPixmap(pixmap.scaled(self.videoLabel.size(), Qt.KeepAspectRatio))