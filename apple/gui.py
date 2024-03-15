from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTextEdit, QFileDialog, QRadioButton, QGroupBox
from PyQt5.QtCore import Qt

class MyApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Main Layout
        mainLayout = QVBoxLayout()

        # Video Display Area
        topLayout = QHBoxLayout()
        self.videoLabel = QLabel('Video Display Area', self)
        self.videoLabel.setAlignment(Qt.AlignCenter)
        self.videoLabel.setMinimumSize(400, 300)
        self.videoLabel.setStyleSheet("QLabel { background-color : #2C2C54; }")
        topLayout.addWidget(self.videoLabel)

        # Control Panel
        controlLayout = QVBoxLayout()
        # Group Box for Radio Buttons
        modeGroupBox = QGroupBox("")
        modeGroupBox.setStyleSheet("QGroupBox { background-color: #2C2C54; color: white; font-family: Roboto; border-radius: 5px; padding: 2px; }")
        modeLayout = QVBoxLayout()

        # Radio Buttons
        self.haltRadio = QRadioButton("Halt")
        self.haltRadio.setStyleSheet("QRadioButton { background-color: #2C2C54; color: white; font-family: Roboto; }")
        self.streamRadio = QRadioButton("Stream")
        self.streamRadio.setStyleSheet("QRadioButton { background-color: #2C2C54; color: white; font-family: Roboto; }")
        self.acquisitionRadio = QRadioButton("Acquisition")
        self.acquisitionRadio.setStyleSheet("QRadioButton { background-color: #2C2C54; color: white; font-family: Roboto; }")
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

        # Command Terminal
        self.terminal = QTextEdit()
        self.terminal.setReadOnly(True)
        self.terminal.setStyleSheet("background-color: #AAABB8; color: black; font-family: Roboto; border-radius: 5px; padding: 2px;")
        mainLayout.addWidget(self.terminal)

        # Set Main Layout and Window Properties
        self.setLayout(mainLayout)
        self.setWindowTitle('Apple Tree Thermography System')
        self.setGeometry(300, 300, 600, 600) # Window size

        # Styling
        self.setStyleSheet("QWidget { background-color: #474787; }"
                           "QPushButton { background-color: #2C2C54; color: white; font-weight: bold; }")

    def selectSavePath(self):
        options = QFileDialog.Options()
        folderPath = QFileDialog.getExistingDirectory(self, "Select Directory", options=options)
        if folderPath:
            self.savePathButton.setText(folderPath)