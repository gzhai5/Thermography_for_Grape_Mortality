from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np

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
        self.axes.text(0.5, 0.5, 'Please select \n\nthe data file\n\n to read first',
                       color='white', ha='center', va='center', transform=self.axes.transAxes)
        self.draw()

    def on_click(self, event):
        if event.inaxes == self.axes:
            x, y = int(event.xdata), int(event.ydata)
            self.parent.on_image_click(x, y)