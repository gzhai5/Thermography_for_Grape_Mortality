import sys
from PyQt5.QtWidgets import QApplication, QPushButton, QWidget
from PyQt5.QtMultimedia import QSound
from PyQt5.QtCore import Qt

class SoundButtonApp(QWidget):
    def __init__(self):
        super().__init__()

        # Set up the window
        self.setWindowTitle("Sound Button")
        self.setGeometry(100, 100, 200, 100)

        # Create a button
        self.button = QPushButton("Play Sound", self)
        self.button.clicked.connect(self.play_sound)
        self.button.resize(100, 30)
        self.button.move(50, 35)

        # Load Sound
        self.sound = QSound("./static/success_sound.wav")

    def play_sound(self):
        self.sound.play()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_S:
            self.play_sound()

def main():
    app = QApplication(sys.argv)
    ex = SoundButtonApp()
    ex.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
