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
t0, t1, t2 = 1, 10, 20
fps = 1

# set up the saving path and saved filename for the data
this_file = os.path.abspath(__file__)
Saved_Folder = "F:/"
save_file_name = ""

# set up object parameters, it could be changed in GUI
Emiss = 0.97
TRefl = 293.15
TAtm = 293.15
TAtmC = TAtm - 273.15
Humidity = 0.55
Dist = 2
ExtOpticsTransmission = 1
ExtOpticsTemp = TAtm

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
        """Sets run flag to False and waits for thread to finish"""
        self._run_flag = False
        self.wait()

class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(np.ndarray)

    def __init__(self):
        super().__init__()
        self._run_flag = True

    def run(self):
        system = PySpin.System.GetInstance()
        cam_list = system.GetCameras()
        if (cam_list.GetSize() == 0):
            cam_list.Clear()
            system.ReleaseInstance()
            print("No Camera Found!")
            input('Done! Press Enter to Exit...')
        for i, cam in enumerate(cam_list):
            nodemap_tldevice = cam.GetTLDeviceNodeMap()
            cam.Init()
            nodemap = cam.GetNodeMap()
            global _run_flag
            sNodemap = cam.GetTLStreamNodeMap()
            node_bufferhandling_mode = PySpin.CEnumerationPtr(sNodemap.GetNode('StreamBufferHandlingMode'))
            # ensure the pixel format = mono8 for streaming
            node_pixel_format = PySpin.CEnumerationPtr(nodemap.GetNode('PixelFormat'))
            node_pixel_format_mono8 = PySpin.CEnumEntryPtr(node_pixel_format.GetEntryByName('Mono14'))
            node_pixel_format_mono8 = node_pixel_format_mono8.GetValue()
            node_pixel_format.SetIntValue(node_pixel_format_mono8)

            # test ir format settings
            node_IRFormat = PySpin.CEnumerationPtr(nodemap.GetNode('IRFormat'))
            node_temp_radiometric = PySpin.CEnumEntryPtr(node_IRFormat.GetEntryByName('Radiometric'))
            node_radiometric = node_temp_radiometric.GetValue()
            node_IRFormat.SetIntValue(node_radiometric)


            if not PySpin.IsAvailable(node_bufferhandling_mode) or not PySpin.IsWritable(node_bufferhandling_mode):
                print('Unable to set stream buffer handling mode.. Aborting...')
                break
            node_newestonly = node_bufferhandling_mode.GetEntryByName('NewestOnly')
            if not PySpin.IsAvailable(node_newestonly) or not PySpin.IsReadable(node_newestonly):
                print('Unable to set stream buffer handling mode.. Aborting...')
                break
            node_newestonly_mode = node_newestonly.GetValue()
            node_bufferhandling_mode.SetIntValue(node_newestonly_mode)

            print('*** IMAGE ACQUISITION ***\n')
            try:
                node_acquisition_mode = PySpin.CEnumerationPtr(nodemap.GetNode('AcquisitionMode'))
                if not PySpin.IsAvailable(node_acquisition_mode) or not PySpin.IsWritable(node_acquisition_mode):
                    print('Unable to set acquisition mode to continuous (enum retrieval). Aborting...')
                    break
                node_acquisition_mode_continuous = node_acquisition_mode.GetEntryByName('Continuous')
                if not PySpin.IsAvailable(node_acquisition_mode_continuous) or not PySpin.IsReadable(node_acquisition_mode_continuous):
                    print('Unable to set acquisition mode to continuous (entry retrieval). Aborting...')
                    break

                acquisition_mode_continuous = node_acquisition_mode_continuous.GetValue()
                node_acquisition_mode.SetIntValue(acquisition_mode_continuous)
                print('Acquisition mode set to continuous...')

                cam.BeginAcquisition()
                print('Acquiring images...')
                device_serial_number = ''
                node_device_serial_number = PySpin.CStringPtr(nodemap_tldevice.GetNode('DeviceSerialNumber'))
                if PySpin.IsAvailable(node_device_serial_number) and PySpin.IsReadable(node_device_serial_number):
                    device_serial_number = node_device_serial_number.GetValue()
                    print('Device serial number retrieved as %s...' % device_serial_number)

                while(self._run_flag):
                    try:
                        image_result = cam.GetNextImage(1000)
                        if image_result.IsIncomplete():
                            print("")
                            # print('Image incomplete with image status %d ...' % image_result.GetImageStatus())
                        else:                    
                            image_data = image_result.GetNDArray()
                            image_data_d = image_data
                            image_data_dt = image_data_d
                            image_data_dt = cv2.normalize(image_data_d,image_data_dt,0,255,cv2.NORM_MINMAX,dtype=cv2.CV_8U)
                            self.change_pixmap_signal.emit(image_data_dt)                       
                        image_result.Release()

                    except PySpin.SpinnakerException as ex:
                        print('Error: %s' % ex)
                        break
                cam.EndAcquisition()

            except PySpin.SpinnakerException as ex:
                print('Error: %s' % ex)
                break
            cam.DeInit()
        del cam
        cam_list.Clear()
        try:
            system.ReleaseInstance()
        except Exception as e:
            print('an release error occurred', e)           

    def stop(self):
        """Sets run flag to False and waits for thread to finish"""
        self._run_flag = False
        self.wait()

class VideoThread_timed(QThread):
    change_pixmap_signal = pyqtSignal(np.ndarray)

    def __init__(self):
        super().__init__()
        self._run_flag = True

    def run(self):
        system = PySpin.System.GetInstance()
        cam_list = system.GetCameras()
        if (cam_list.GetSize() == 0):
            cam_list.Clear()
            system.ReleaseInstance()
            print("No Camera Found!")
            input('Done! Press Enter to Exit...')
        for i, cam in enumerate(cam_list):
            nodemap_tldevice = cam.GetTLDeviceNodeMap()
            cam.Init()
            nodemap = cam.GetNodeMap()
            global _run_flag
            sNodemap = cam.GetTLStreamNodeMap()
            node_bufferhandling_mode = PySpin.CEnumerationPtr(sNodemap.GetNode('StreamBufferHandlingMode'))
            # ensure the pixel format = mono8 for streaming
            node_pixel_format = PySpin.CEnumerationPtr(nodemap.GetNode('PixelFormat'))
            node_pixel_format_mono14 = PySpin.CEnumEntryPtr(node_pixel_format.GetEntryByName('Mono16'))
            node_pixel_format_mono14 = node_pixel_format_mono14.GetValue()
            node_pixel_format.SetIntValue(node_pixel_format_mono14)

            # test ir format settings
            node_IRFormat = PySpin.CEnumerationPtr(nodemap.GetNode('IRFormat'))
            # node_temp_radiometric = PySpin.CEnumEntryPtr(node_IRFormat.GetEntryByName('Radiometric'))
            # node_radiometric = node_temp_radiometric.GetValue()
            
            node_temp_linear_high = PySpin.CEnumEntryPtr(node_IRFormat.GetEntryByName('TemperatureLinear10mK'))
            node_temp_high = node_temp_linear_high.GetValue()
            node_IRFormat.SetIntValue(node_temp_high)


            if not PySpin.IsAvailable(node_bufferhandling_mode) or not PySpin.IsWritable(node_bufferhandling_mode):
                print('Unable to set stream buffer handling mode.. Aborting...')
                break
            node_newestonly = node_bufferhandling_mode.GetEntryByName('NewestOnly')
            if not PySpin.IsAvailable(node_newestonly) or not PySpin.IsReadable(node_newestonly):
                print('Unable to set stream buffer handling mode.. Aborting...')
                break
            node_newestonly_mode = node_newestonly.GetValue()
            node_bufferhandling_mode.SetIntValue(node_newestonly_mode)

            print('*** IMAGE ACQUISITION ***\n')
            try:
                node_acquisition_mode = PySpin.CEnumerationPtr(nodemap.GetNode('AcquisitionMode'))
                if not PySpin.IsAvailable(node_acquisition_mode) or not PySpin.IsWritable(node_acquisition_mode):
                    print('Unable to set acquisition mode to continuous (enum retrieval). Aborting...')
                    break
                node_acquisition_mode_continuous = node_acquisition_mode.GetEntryByName('Continuous')
                if not PySpin.IsAvailable(node_acquisition_mode_continuous) or not PySpin.IsReadable(node_acquisition_mode_continuous):
                    print('Unable to set acquisition mode to continuous (entry retrieval). Aborting...')
                    break

                acquisition_mode_continuous = node_acquisition_mode_continuous.GetValue()
                node_acquisition_mode.SetIntValue(acquisition_mode_continuous)
                print('Acquisition mode set to continuous...')

                cam.BeginAcquisition()
                print('Acquiring images...')
                device_serial_number = ''
                node_device_serial_number = PySpin.CStringPtr(nodemap_tldevice.GetNode('DeviceSerialNumber'))
                print("get here 217")
                if PySpin.IsAvailable(node_device_serial_number) and PySpin.IsReadable(node_device_serial_number):
                    device_serial_number = node_device_serial_number.GetValue()
                    print('Device serial number retrieved as %s...' % device_serial_number)


                index = 0
                frames_per_min = 30 * 60
                buffer = []

                while(self._run_flag):
                    print('index:', index)
                    try:
                        image_result = cam.GetNextImage(1000)
                        if image_result.IsIncomplete():
                            print("image incomplete")
                        else:                    
                            image_data = image_result.GetNDArray()
                            print("image_data shape:", image_data.shape)
                            print("image_data type:", image_data.dtype)
                            image_Temp_Celsius_high = (image_data * 0.01) - 273.15
                            index += 1


                            # convert raw image data into tempature value
                            print("image val:", np.mean(image_Temp_Celsius_high))

                            # Save every 60th frame into buffer so reduce the outputfps to 15
                            if index % 60 == 0:
                                buffer.append(image_data)

                            # Flush buffer to file when it reaches buffer size
                            if len(buffer) >= frames_per_min:
                                minute_index = index // (frames_per_min * 2)
                                temp_filename = f"data_apple_test/frames_minute_{minute_index}.npy"
                                np.save(temp_filename, np.array(buffer, dtype=np.uint16))
                                print(f"Saved buffer to {temp_filename}")
                                buffer = []


                            image_data_d = image_data
                            image_data_dt = image_data_d
                            image_data_dt = cv2.normalize(image_data_d,image_data_dt,0,255,cv2.NORM_MINMAX,dtype=cv2.CV_8U)
                            self.change_pixmap_signal.emit(image_data_dt)                       
                        image_result.Release()

                    except PySpin.SpinnakerException as ex:
                        print('Error when doing daq: %s' % ex)
                        break
                cam.EndAcquisition()

                # Flush any remaining frames in the buffer
                if buffer:
                    minute_index = index // (frames_per_min * 2)
                    temp_filename = f"data_apple_test/frames_minute_{minute_index}.npy"
                    np.save(temp_filename, np.array(buffer, dtype=np.uint16))
                    print(f"Final save of buffer to {temp_filename}")

            except PySpin.SpinnakerException as ex:
                print('Error: %s' % ex)
                break

        
            cam.DeInit()
        del cam
        cam_list.Clear()
        try:
            system.ReleaseInstance()
        except Exception as e:
            print('an release error occurred', e)          

    def stop(self):
        """Sets run flag to False and waits for thread to finish"""
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

        # for the data saving path and also saved filename
        box_path = QLineEdit(save_file_name, self)
        box_path.setAlignment(QtCore.Qt.AlignCenter)
        box_path.resize(280,30)
        box_path.move(680,230)
        box_path.returnPressed.connect(lambda: save_file())
        def save_file():
            global save_file_name
            save_file_name = box_path.text() + ".npy"
            print("You have choosen " + save_file_name + " as the saved npy filename")

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
                print("Now we are going to switch mode to a timed streaming mode!")
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

        # Draw lines on the image
        height, width, channels = rgb_image.shape
        center_x, center_y = width // 2, height // 2

        # Color for the lines (red in this case), adjust as needed
        line_color = (255, 0, 0)  # Red color in BGR
        thickness = 2  # Line thickness

        # Drawing vertical line
        # cv2.line(rgb_image, (center_x, 0), (center_x, height), line_color, thickness)
        # Drawing horizontal line
        # cv2.line(rgb_image, (0, center_y), (width, center_y), line_color, thickness)

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

