from PyQt5.QtCore import QThread, pyqtSignal
from PIL import Image, ImageDraw
import numpy as np

class HaltingThread(QThread):
    change_pixmap_signal = pyqtSignal(np.ndarray)

    def __init__(self):
        super(HaltingThread, self).__init__()
        self.running = False

    def run(self):
        self.running = True
        while self.running:
            image_data = Image.new('RGB', (130,100), color=(44,44,84))
            draw = ImageDraw.Draw(image_data)
            draw.text((20,20), "No Thread Found", fill=(0,0,0))
            image_data = np.array(image_data)
            self.change_pixmap_signal.emit(image_data)           

    def stop(self):
        self.running = False