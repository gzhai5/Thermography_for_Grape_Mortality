from PyQt5 import QtGui, QtCore
from PyQt5.QtWidgets import QWidget, QApplication, QLabel, QVBoxLayout, QMainWindow, QTextEdit, QPlainTextEdit, QHBoxLayout, QAction, QPushButton, QLineEdit, QFileDialog, QComboBox, QListView
from PyQt5.QtGui import QPixmap, QFont, QTextCursor
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QThread
import numpy as np
import PySpin
import os, time, sys, cv2, re
from PIL import Image, ImageDraw


# set up N for how many images we are gonna taken (30fps), and initilize a np nd array for saving img data
mode = "disconnect"   # set the initial mode to disconnect
fps = 60
image_interval = 60
frames_per_minute = 20

# set up the saving path and saved filename for the data
this_file = os.path.abspath(__file__)
Saved_Folder = "F:/"
save_file_name = ""

# set up the focus step, 100 as a default
focus_step = 100
selected_text = "default"

# set up the IRformat class, and set the default irformat = radiometric
class IRFormatType:
    LINEAR_10MK = 1
    LINEAR_100MK = 2
    RADIOMETRIC = 3
CHOSEN_IR_TYPE = IRFormatType.RADIOMETRIC
pixel_format = "Mono16"


class disconnect_thread(QThread):
    change_pixmap_signal = pyqtSignal(np.ndarray)

    def __init__(self):
        super().__init__()
        self._run_flag = True

    def run(self):
        image_data = Image.new('RGB', (130,100), color=(255,255,255))
        draw = ImageDraw.Draw(image_data)
        draw.text((20,20), "No Thread Found", fill=(0,0,0))
        image_data = np.array(image_data)
        self.change_pixmap_signal.emit(image_data)           

    def stop(self):
        self._run_flag = False
        self.wait()

class AquireImage():
    def __init__(self, change_pixmap_signal):
        self.change_pixmap_signal = change_pixmap_signal
        self.continue_recording = True

    def run_main(self, stream=True):

        # Retrieve singleton reference to system object
        system = PySpin.System.GetInstance()

        # Retrieve list of cameras from the system
        cam_list = system.GetCameras()
        num_cameras = cam_list.GetSize()
        print('Number of cameras detected: %d' % num_cameras)

        # Finish if there are no cameras
        if num_cameras == 0:
            cam_list.Clear()
            system.ReleaseInstance()
            print('Not enough cameras!')

        # Run example on each camera; here we only run the first camera
        for i, cam in enumerate(cam_list):
            print('Running example for camera %d...' % i)
            self.run_single_camera(cam, stream)
            print('Camera %d example complete... \n' % i)
            break

        del cam

        # Clear camera list before releasing system
        cam_list.Clear()

        # Release system instance
        system.ReleaseInstance()

    def run_single_camera(self, cam, stream: bool) -> None:
        try:
            result = True

            # Initialize camera
            cam.Init()

            # Retrieve GenICam nodemap
            nodemap = cam.GetNodeMap()

            # Acquire images
            result &= self.aquire_images(cam, nodemap, stream)

            # Deinitialize camera
            cam.DeInit()

        except PySpin.SpinnakerException as ex:
            print('Error when running single camera: %s' % ex)

    @staticmethod
    def flush_buffer_to_file(buffer, hour, minute):
        temp_filename = f"apple_data/temp_frames_hour{hour}_min{minute}.npy"
        np.save(temp_filename, np.array(buffer, dtype=np.uint16))
        print(f"Saved buffer to {temp_filename}")
        return []

    def acquire_images(self, cam, nodemap, stream: bool) -> None:
        sNodemap = cam.GetTLStreamNodeMap()

        # Change bufferhandling mode to NewestOnly
        node_bufferhandling_mode = PySpin.CEnumerationPtr(sNodemap.GetNode('StreamBufferHandlingMode'))
        if not PySpin.IsAvailable(node_bufferhandling_mode) or not PySpin.IsWritable(node_bufferhandling_mode):
            print('Unable to set stream buffer handling mode.. Aborting...')
            return

        # Retrieve entry node from enumeration node
        node_newestonly = node_bufferhandling_mode.GetEntryByName('NewestOnly')
        if not PySpin.IsAvailable(node_newestonly) or not PySpin.IsReadable(node_newestonly):
            print('Unable to set stream buffer handling mode.. Aborting...')
            return
        
        # Ensure pixel format = mono14 for optimal video
        node_pixel_format = PySpin.CEnumerationPtr(nodemap.GetNode('PixelFormat'))
        node_pixel_format_mono14 = PySpin.CEnumEntryPtr(node_pixel_format.GetEntryByName('Mono14'))
        node_pixel_format_mono14 = node_pixel_format_mono14.GetValue()
        node_pixel_format.SetIntValue(node_pixel_format_mono14)

        # ir format settings
        node_IRFormat = PySpin.CEnumerationPtr(nodemap.GetNode('IRFormat'))
        node_temp_radiometric = PySpin.CEnumEntryPtr(node_IRFormat.GetEntryByName('Radiometric'))
        node_radiometric = node_temp_radiometric.GetValue()
        node_IRFormat.SetIntValue(node_radiometric)

        # Retrieve integer value from entry node
        node_newestonly_mode = node_newestonly.GetValue()

        # Set integer value from entry node as new value of enumeration node
        node_bufferhandling_mode.SetIntValue(node_newestonly_mode)

        print('*** IMAGE ACQUISITION ***\n')
        try:
            node_acquisition_mode = PySpin.CEnumerationPtr(nodemap.GetNode('AcquisitionMode'))
            if not PySpin.IsAvailable(node_acquisition_mode) or not PySpin.IsWritable(node_acquisition_mode):
                print('Unable to set acquisition mode to continuous (enum retrieval). Aborting...')
                return False

            # Retrieve entry node from enumeration node
            node_acquisition_mode_continuous = node_acquisition_mode.GetEntryByName('Continuous')
            if not PySpin.IsAvailable(node_acquisition_mode_continuous) or not PySpin.IsReadable(
                    node_acquisition_mode_continuous):
                print('Unable to set acquisition mode to continuous (entry retrieval). Aborting...')
                return False

            # Retrieve integer value from entry node
            acquisition_mode_continuous = node_acquisition_mode_continuous.GetValue()

            # Set integer value from entry node as new value of enumeration node
            node_acquisition_mode.SetIntValue(acquisition_mode_continuous)

            print('Acquisition mode set to continuous...')

            #  Begin acquiring images
            #
            #  *** NOTES ***
            #  What happens when the camera begins acquiring images depends on the
            #  acquisition mode. Single frame captures only a single image, multi
            #  frame catures a set number of images, and continuous captures a
            #  continuous stream of images.
            #
            #  *** LATER ***
            #  Image acquisition must be ended when no more images are needed.
            cam.BeginAcquisition()


            # Retrieve and display images
            print('Acquiring images...')
            counter, hour, minute = 0, 0, 0
            buffer = []
            while(self.continue_recording):
                try:
                    image_result = cam.GetNextImage(1000)

                    #  Ensure image completion
                    if image_result.IsIncomplete():
                        print('Image incomplete with image status %d ...' % image_result.GetImageStatus())

                    else:                    
                        image_data = image_result.GetNDArray()

                        if not stream:
                            # compute the time
                            if counter < 60 * fps:
                                counter += 1
                            else:
                                counter = 0
                                minute += 1
                                if minute >= 60:
                                    minute = 0
                                    hour += 1

                            # keep the output video 15fps
                            if counter % 4 == 0:
                                buffer.append(image_data)

                            if len(buffer) >= frames_per_minute:
                                buffer = self.flush_buffer_to_file(buffer, hour, minute)

                        image_data_d = image_data
                        image_data_dt = cv2.normalize(image_data_d,image_data_dt,0,255,cv2.NORM_MINMAX,dtype=cv2.CV_8U)
                        self.change_pixmap_signal.emit(image_data_dt)
                                            

                    #  Release image
                    #
                    #  *** NOTES ***
                    #  Images retrieved directly from the camera (i.e. non-converted
                    #  images) need to be released in order to keep from filling the
                    #  buffer.
                    image_result.Release()

                except PySpin.SpinnakerException as ex:
                    print('Error when doing the contious reading image: %s' % ex)
                    return False

            #  End acquisition
            #
            #  *** NOTES ***
            #  Ending acquisition appropriately helps ensure that devices clean up
            #  properly and do not need to be power-cycled to maintain integrity.
            cam.EndAcquisition()

            if buffer:
                self.flush_buffer_to_file(buffer, hour, minute)

        except PySpin.SpinnakerException as ex:
            print('Error when acquiring image: %s' % ex)
            return False




class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(np.ndarray)

    def __init__(self):
        super().__init__()
        self._run_flag = True
        self.aquire_image_instance = None

    def run(self):
        self.aquire_image_instance = AquireImage(self.change_pixmap_signal)
        self.aquire_image_instance.run_main(stream=True)

    def stop(self):
        """Sets run flag to False and waits for thread to finish"""
        self.aquire_image_instance.continue_recording = False
        self._run_flag = False
        self.wait()

class VideoThread_timed(QThread):
    change_pixmap_signal = pyqtSignal(np.ndarray)

    def __init__(self):
        super().__init__()
        self._run_flag = True
        self.aquire_image_instance = None

    def run(self):
        aquire_image_instance = AquireImage(self.change_pixmap_signal)
        aquire_image_instance.run_main(stream=False)       

    def stop(self):
        """Sets run flag to False and waits for thread to finish"""
        self.aquire_image_instance.continue_recording = False
        self._run_flag = False
        self.wait()

class App(QMainWindow):
    text_update = pyqtSignal(str)

    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        self.setWindowTitle("Thermal Image Control")
        self.setMinimumWidth(1000)
        self.setMinimumHeight(700)
        self.subParametersWindow = None
        self.DAQ_window = None
        
        # create the label that holds the image
        self.image_label = QLabel(self)
        self.image_label.resize(480, 480)
        self.image_label.parent().layout().invalidate()

        # create a text label
        self.central = QWidget(self)
        self.textbox = QTextEdit(self.central)
        self.textbox.setFont(QFont("Courier", 10))
        self.textbox.setFixedWidth(970)
        self.textbox.setFixedHeight(int(970/3-100))
        self.text_update.connect(self.append_text)
        sys.stdout = self
        self.text = QPlainTextEdit()
        self.text.setReadOnly(True)


        button_path = QPushButton("Data Saving Folder", self)
        button_path.resize(280,30)
        button_path.move(680,270)
        button_path.clicked.connect(lambda: save_path())
        def save_path():
            global Saved_Folder
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            directory = QFileDialog.getExistingDirectory(self, "Select Path", Saved_Folder, options=options)
            Saved_Folder = directory
            print("Choose Download Directory:  " +Saved_Folder)

        
        

        # create buttons
        button_connect = QPushButton('Connect', self)
        button_connect.clicked.connect(self.click_connect)
        button_connect.resize(80,40)
        button_connect.move(680,30)

        button_disconnect = QPushButton('Cut', self)
        button_disconnect.clicked.connect(self.click_disconnect)
        button_disconnect.resize(80,40)
        button_disconnect.move(880,30)

        self.button_start_end = QPushButton('Start DAQ', self)
        self.button_start_end.resize(280,30)
        self.button_start_end.move(680,375)
        self.button_start_end.clicked.connect(self.start_DAQ)
                

        # create the main window
        self.vlayout = QVBoxLayout()        
        self.displays = QHBoxLayout()
        self.vlayout.addLayout(self.displays)
        self.label = QLabel(self)
        self.vlayout.addWidget(self.image_label)
        self.vlayout.addWidget(self.label)
        self.vlayout.addWidget(self.textbox)
        self.central.setLayout(self.vlayout)
        self.setCentralWidget(self.central)

        # create the menu bar
        self.mainMenu = self.menuBar()      
        exitAction = QAction('&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.triggered.connect(self.close)
        self.fileMenu = self.mainMenu.addMenu('&File')
        self.fileMenu.addAction(exitAction)
        # self.vlayout.addWidget(self.mainMenu)

        # create the video capture 
        if (mode == "TimedStream"):
            self.thread = VideoThread_timed()
            # connect its signal to the update_image slot
            self.thread.change_pixmap_signal.connect(self.update_image)
            # start the thread
            self.thread.start()
        elif (mode == "contious_stream"):
            self.thread = VideoThread()
            self.thread.change_pixmap_signal.connect(self.update_image)
            self.thread.start()
        elif (mode == "disconnect"):
            self.thread = disconnect_thread()
            self.thread.change_pixmap_signal.connect(self.update_image)
            self.thread.start()

    # Append to text display
    def append_text(self, text):
        cur = self.textbox.textCursor()     # Move cursor to end of text
        cur.movePosition(QTextCursor.End) 
        s = str(text)
        while s:
            head,sep,s = s.partition("\n")  # Split line at LF
            cur.insertText(head)            # Insert text at cursor
            if sep:                         # New line if LF
                cur.insertBlock()
        self.textbox.setTextCursor(cur)     # Update visible cursor

    def click_connect(self):
        print('-------------Connect Clicked-------------')
        global mode
        mode = "contious_stream"
        self.thread.stop()
        self.thread = VideoThread()
        self.thread.change_pixmap_signal.connect(self.update_image)
        self.thread.start()

    def click_disconnect(self):
        print('-------------Disconnect Clicked-------------')
        global mode
        mode = "disconnect"
        self.thread.stop()
        self.thread = disconnect_thread()
        self.thread.change_pixmap_signal.connect(self.update_image)
        self.thread.start()

    def start_DAQ(self):
            print('-------------DAQ Clicked-------------')
            global mode, DAQ_running_flag
            if mode != "TimedStream":
                mode = "TimedStream"
                print("Now we are going to switch mode to a DAQ mode!")
                self.button_start_end.setText("Stop DAQ")
                self.thread.stop()
                DAQ_running_flag = True
                self.thread = VideoThread_timed()
                self.thread.change_pixmap_signal.connect(self.update_image)
                self.thread.start()
            elif mode == "TimedStream":
                mode = "contious_stream"
                print("You have stopped DAQ and jumped to contious streaming mode!")
                self.button_start_end.setText("Start DAQ")
                self.thread.stop()
                DAQ_running_flag = False
                self.thread = VideoThread()
                self.thread.change_pixmap_signal.connect(self.update_image)
                self.thread.start()

    def write(self, text):
        self.text_update.emit(str(text))

    def flush(self):
        pass
    
    # Replace 'Space' with your desired key
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space:
            self.start_DAQ()

    def closeEvent(self, event):
        self.thread.stop()
        event.accept()



    @pyqtSlot(np.ndarray)
    def update_image(self, cv_img):
        """Updates the image_label with a new opencv image"""
        qt_img = self.convert_cv_qt(cv_img)
        self.image_label.setPixmap(qt_img)
    
    def convert_cv_qt(self, cv_img):
        """Convert from an opencv image to QPixmap and draw lines"""
        if len(cv_img.shape) == 2:
            rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_GRAY2RGB)
        else:
            rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)

        height, width, channels = rgb_image.shape

        if len(cv_img.shape) == 2:
            convert_to_Qt_format = QtGui.QImage(rgb_image.data, cv_img.shape[1], cv_img.shape[0], 0, QtGui.QImage.Format_RGB888)
        else:
            bytes_per_line = channels * width
            convert_to_Qt_format = QtGui.QImage(rgb_image.data, width, height, bytes_per_line, QtGui.QImage.Format_RGB888)

        p = convert_to_Qt_format.scaled(640, 480, Qt.KeepAspectRatio)
        return QPixmap.fromImage(p)


if __name__=="__main__":
    app = QApplication(sys.argv)
    a = App()
    a.show()
    sys.exit(app.exec_())

