import os, sys
import pandas as pd
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QApplication, QGridLayout, QPushButton, QVBoxLayout, QWidget, QFileDialog, QListWidget, QLabel, QComboBox, QTextEdit


class CSVToolApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('CSV and ML Toolkit')
        self.setGeometry(100, 100, 800, 600)

        grid = QGridLayout()

        # File Chooser
        self.btn_load_files = QPushButton('Load CSV Files')
        self.btn_load_files.clicked.connect(self.load_csv_files)
        grid.addWidget(self.btn_load_files, 0, 0)

        self.listbox_files = QListWidget()
        self.listbox_files.clicked.connect(self.display_csv_info)
        grid.addWidget(self.listbox_files, 1, 0)

        # Log Screen
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        grid.addWidget(self.log_text, 0, 1, 2, 1)  # Span two rows

        # ML Model Selector
        self.model_selector = QComboBox()
        self.model_selector.addItems(["Model 1", "Model 2", "Model 3"])  # Add your model names here
        grid.addWidget(self.model_selector, 2, 0)

        # CSV Info Display
        self.info_label = QLabel('CSV Info will be displayed here.')
        grid.addWidget(self.info_label, 2, 1)

        # Setting equal stretch for all rows and columns
        grid.setRowStretch(0, 1)
        grid.setRowStretch(1, 1)
        grid.setRowStretch(2, 1)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        container = QWidget()
        container.setLayout(grid)
        self.setCentralWidget(container)

    def load_csv_files(self):
        folder_path = QFileDialog.getExistingDirectory(self, 'Select Folder')
        if folder_path:
            csv_files = [f for f in os.listdir(folder_path) if f.endswith('.csv')]
            self.listbox_files.clear()
            self.listbox_files.addItems(csv_files)

    def display_csv_info(self):
        selected_file = self.listbox_files.currentItem().text()
        df = pd.read_csv(selected_file)
        print(df.head())

        true_count = len(df[df['Label'] == 'TRUE'])
        false_count = len(df[df['Label'] == 'FALSE'])
        self.info_label.setText(f"True: {true_count}, False: {false_count}")

    def log(self, message):
        self.log_text.append(f"{message}\n")

def main():
    app = QApplication(sys.argv)
    ex = CSVToolApp()
    ex.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()



