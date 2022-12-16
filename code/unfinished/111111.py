from PyQt5.QtWidgets import * 
from PyQt5 import QtCore, QtGui
from PyQt5.QtGui import * 
from PyQt5.QtCore import * 
import sys
  
  
class Window(QMainWindow):
  
    def __init__(self):
        super().__init__()
  
        # setting title
        self.setWindowTitle("Python ")
  
        # setting geometry
        self.setGeometry(100, 100, 500, 400)
  
        # calling method
        self.UiComponents()
        self.setFixedWidth(1000)
        self.setFixedHeight(800)
  
        # showing all the widgets
        self.show()
  
  
  
    # method for components
    def UiComponents(self):
  
        # creating a QLineEdit object
        line_edit = QLineEdit("GeeksforGeeks", self)
  
        # setting geometry
        line_edit.setGeometry(80, 80, 150, 40)
  
        # creating a label
        label = QLabel("GfG", self)
  
        # setting geometry to the label
        label.setGeometry(80, 150, 120, 60)
  
        # setting word wrap property of label
        label.setWordWrap(True)
  
        # adding action to the line edit when enter key is pressed
        line_edit.returnPressed.connect(lambda: do_action())
  
        # method to do action
        def do_action():
  
            # getting text from the line edit
            value = line_edit.text()
            print(value)
  
            # setting text to the label
            label.setText(value)
  
  
  
  
# create pyqt5 app
App = QApplication(sys.argv)
  
# create the instance of our Window
window = Window()
  
# start the app
sys.exit(App.exec())