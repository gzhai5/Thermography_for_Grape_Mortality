import sys
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QMainWindow, QLabel, QGridLayout, QWidget
from PyQt5.QtWidgets import QPushButton, QPlainTextEdit
import PyQt5.QtWidgets as qtw
from PyQt5.QtCore import QSize   
from PyQt5.QtCore import QProcess 

global t0,t1,t2

class MainWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)

        self.p = None
        self.setMinimumSize(QSize(900, 600))    
        self.setWindowTitle("Thermal Image Control")
        self.text = QPlainTextEdit()
        self.text.setReadOnly(True) 

        button_run = QPushButton('RUN', self)
        button_run.clicked.connect(self.clickMethod_1)
        button_run.resize(150,80)
        button_run.move(680, 360) 

        button_stop = QPushButton('Stop', self)
        button_stop.clicked.connect(self.clickMethod_2)
        button_stop.resize(150,80)
        button_stop.move(680, 450)        
        

        # set boxes for typing in time
        box_t0 = qtw.QLineEdit('t0', self)
        box_t0.resize(100,30)
        box_t0.move(80,120)
        box_t0.returnPressed.connect(lambda: save_t0())
        def save_t0():
            t0 = box_t0.text()
            print(t0)

        box_t1 = qtw.QLineEdit('t1', self)
        box_t1.resize(100,20)
        box_t1.move(200,120)

        box_t2 = qtw.QLineEdit('t2', self)
        box_t2.resize(100,20)
        box_t2.move(320,120)
    

    def message(self, s):
        self.text.appendPlainText(s)

    def clickMethod_1(self):
        print('run clicked')
        if self.p is None:  # No process running.
            self.message("Executing process")
            self.p = QProcess()  # Keep a reference to the QProcess (e.g. on self) while it's running.
            self.p.finished.connect(self.process_finished)  # Clean up once complete.
            self.p.start("python3", ['helloworld.py'])

    def process_finished(self):
        self.message("Process finished.")
        self.p = None


    def clickMethod_2(self):
        print('stop clicked')
        print(t0)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    mainWin = MainWindow()
    mainWin.show()
    sys.exit( app.exec_() )



