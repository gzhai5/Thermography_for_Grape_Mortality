from PyQt5 import QtGui, QtCore
from PyQt5.QtWidgets import QWidget, QApplication, QLabel, QVBoxLayout, QMainWindow, QTextEdit, QPlainTextEdit, QHBoxLayout, QAction, QPushButton, QLineEdit, QFileDialog, QComboBox, QListView
from PyQt5.QtGui import QPixmap, QFont, QTextCursor
import sys
import cv2
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QThread
import numpy as np
import os, PySpin, keyboard, time, base64, serial
from PIL import Image, ImageDraw


# switch initilization
port = 'COM3'
port_exist = True
try:
    ser = serial.Serial(port, 9600, timeout=1)
except serial.serialutil.SerialException:
    print("USB port not Found")
    port_exist = False
    time.sleep(3)
hex_string1 = """A0 01 01 A2"""  #turn on str
some_bytes1 = bytearray.fromhex(hex_string1)
hex_string2 = """A0 01 00 A1"""  #turn off str
some_bytes2 = bytearray.fromhex(hex_string2)

# set up N for how many images we are gonna taken (30fps), and initilize a np nd array for saving img data
mode = "disconnect"   # set the initial mode to disconnect
t0, t1, t2 = 1, 10, 20
fps = 30
N = t2*fps
img_data_array = np.zeros((N,480,640))

# set up the saving path and saved filename for the data
Saved_Folder = "C:/Users/Alfoul/Desktop/Thermography_for_Grape_Mortality/code/SavedData/"
save_file_name = "img_data.npy"

# set up the focus step, 100 as a default
focus_step = 100
selected_text = "default"

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
                            print('Image incomplete with image status %d ...' % image_result.GetImageStatus())
                        else:                    
                            image_data = image_result.GetNDArray()
                            self.change_pixmap_signal.emit(image_data)                       
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
        system.ReleaseInstance()            

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
        print("Library version: ....")
        cam_list = system.GetCameras()
        if (cam_list.GetSize() == 0):
            cam_list.Clear()
            system.ReleaseInstance()
            print("No Camera Found!")
            time.sleep(5)
            sys.exit(app.exec_())
        for i, cam in enumerate(cam_list):
            nodemap_tldevice = cam.GetTLDeviceNodeMap()
            cam.Init()
            nodemap = cam.GetNodeMap()
            global _run_flag
            sNodemap = cam.GetTLStreamNodeMap()
            node_bufferhandling_mode = PySpin.CEnumerationPtr(sNodemap.GetNode('StreamBufferHandlingMode'))
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

                print("Now we have t0 =  " + str(t0) + "  , t1 =  " + str(t1) + "  t2 =  " + str(t2))
                time.sleep(5)
                start_time = time.time()
                i = 0
                global N, img_data_array
                N = t2*fps
                img_data_array = np.zeros((N,480,640))

                while(self._run_flag):
                    try:
                        image_result = cam.GetNextImage(1000)
                        if image_result.IsIncomplete():
                            print('Image incomplete with image status %d ...' % image_result.GetImageStatus())
                        else:                    
                            image_data = image_result.GetNDArray()
                            self.change_pixmap_signal.emit(image_data)                      
                        image_result.Release()
                        if (i < N):
                            img_data_array[i] = image_data
                            print("Now, You have passed  " + str(i) + "  images!")
                            i = i + 1
                        if (i == N):
                            print("Now, You have passed  " + str(i) + "  images!")
                            print("DAQ finished!")

                            # # save the image content array to a npy file
                            np.save(os.path.join(Saved_Folder, save_file_name),img_data_array)   
                            print("------------Image Contents Saved------------")

                            i = N + 1
                        diff_time = time.time() - start_time
                        if (diff_time >= t0 and diff_time < t1):
                            ser.write(some_bytes1)
                        elif (diff_time >= t1 and diff_time < t2):
                            ser.write(some_bytes2)

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
        system.ReleaseInstance()            

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

        # create buttons
        button_DAQ = QPushButton('DAQ', self)
        button_DAQ.clicked.connect(self.click_DAQ)
        button_DAQ.resize(80,40)
        button_DAQ.move(880,220)

        button_connect = QPushButton('Connect', self)
        button_connect.clicked.connect(self.click_connect)
        button_connect.resize(80,40)
        button_connect.move(680,220)

        button_disconnect = QPushButton('Cut', self)
        button_disconnect.clicked.connect(self.click_disconnect)
        button_disconnect.resize(80,40)
        button_disconnect.move(780,220)

        button_autofocus = QPushButton('Auto', self)
        button_autofocus.clicked.connect(self.click_autofocus)
        button_autofocus.resize(80,40)
        button_autofocus.move(680,280)

        button_focusplus = QPushButton('+', self)
        button_focusplus.clicked.connect(self.click_focusplus)
        button_focusplus.resize(80,40)
        button_focusplus.move(780,280)

        button_focusminus = QPushButton('-', self)
        button_focusminus.clicked.connect(self.click_focusminus)
        button_focusminus.resize(80,40)
        button_focusminus.move(880,280)

        combo_box_autofocus_method = QComboBox(self)
        options = ["Coarse", "Fine"]
        combo_box_autofocus_method.addItems(options)
        combo_box_autofocus_method.setCurrentIndex(0)
        combo_box_autofocus_method.currentIndexChanged.connect(self.autofocus_method)
        combo_box_autofocus_method.resize(90,40)
        combo_box_autofocus_method.move(720,350)

        box_focus_step = QLineEdit('Focus Step', self)
        box_focus_step.setAlignment(QtCore.Qt.AlignCenter)
        box_focus_step.resize(90,40)
        box_focus_step.move(830,350)
        box_focus_step.returnPressed.connect(lambda: save_focus_step())
        def save_focus_step():
            global focus_step
            focus_step = int(box_focus_step.text())
            print("You have set focus step to  " + str(focus_step) + "  !")

        # set boxes for typing in time, and the last one is for data saving_path
        box_t0 = QLineEdit('t0', self)
        box_t0.setAlignment(QtCore.Qt.AlignCenter)    # set the text in middle
        box_t0.resize(80,30)
        box_t0.move(680,50)
        box_t0.returnPressed.connect(lambda: save_t0())
        def save_t0():
            global t0
            t0 = int(box_t0.text())
            print("You have set t0 to  " + str(t0) + "  !")

        box_t1 = QLineEdit('t1', self)
        box_t1.setAlignment(QtCore.Qt.AlignCenter)
        box_t1.resize(80,30)
        box_t1.move(780,50)
        box_t1.returnPressed.connect(lambda: save_t1())
        def save_t1():
            global t1
            t1 = int(box_t1.text())
            print("You have set t1 to  " + str(t1) + "  !")

        box_t2 = QLineEdit('t2', self)
        box_t2.setAlignment(QtCore.Qt.AlignCenter)
        box_t2.resize(80,30)
        box_t2.move(880,50)
        box_t2.returnPressed.connect(lambda: save_t2())
        def save_t2():
            global t2
            t2 = int(box_t2.text())
            print("You have set t2 to  " + str(t2) + "  !")

        box_path = QLineEdit('Data Saving Name', self)
        box_path.setAlignment(QtCore.Qt.AlignCenter)
        box_path.resize(280,30)
        box_path.move(680,160)
        box_path.returnPressed.connect(lambda: save_file())
        def save_file():
            global save_file_name
            save_file_name = box_path.text() + ".npy"
            print("You have choosen " + save_file_name + " as the saved npy filename")

        button_path = QPushButton("Browse", self)
        button_path.resize(280,30)
        button_path.move(680,120)
        button_path.clicked.connect(self.save_path)

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

    def save_path(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        directory = QFileDialog.getExistingDirectory(self, "QFileDialog..getExistingDirectory()", "", options=options)
        global Saved_Folder
        Saved_Folder = directory
        print("Choose Download Directory:  " +Saved_Folder)

    def click_DAQ(self):
        print('-------------DAQ Clicked-------------')
        if (port_exist == False):
            print("USB not inserted, cannot go to timed version!")
        else:
            global mode
            mode = "TimedStream"
            print("Now we are going to switch mode to a timed streaming mode!")
            self.thread.stop()
            self.thread = VideoThread_timed()
            self.thread.change_pixmap_signal.connect(self.update_image)
            self.thread.start()

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

    def click_autofocus(self):
        print('-------------Autofocus Clicked-------------')
        system = PySpin.System.GetInstance()
        camera = system.GetCameras()[0]
        # camera.Init()
        nodemap = camera.GetNodeMap()
        node_autofocus = PySpin.CCommandPtr(nodemap.GetNode('AutoFocus'))
        node_autofocus.Execute()
        # camera.DeInit()

    def click_focusplus(self):
        print("-------------Plus " + str(focus_step) + " Focus-------------")
        system = PySpin.System.GetInstance()
        camera = system.GetCameras()[0]
        nodemap = camera.GetNodeMap()
        node_focus_pos = PySpin.CIntegerPtr(nodemap.GetNode('FocusPos'))
        focus_pos_curr = node_focus_pos.GetValue()
        node_focus_pos.SetValue(focus_pos_curr + focus_step)

    def click_focusminus(self):
        print("-------------Minus " + str(focus_step) + " Focus-------------")
        system = PySpin.System.GetInstance()
        camera = system.GetCameras()[0]
        nodemap = camera.GetNodeMap()
        node_focus_pos = PySpin.CIntegerPtr(nodemap.GetNode('FocusPos'))
        focus_pos_curr = node_focus_pos.GetValue()
        node_focus_pos.SetValue(focus_pos_curr - focus_step)

    def autofocus_method(self, index):
        if index == 0:
            print("You have choose the autofoucs method as Coarse!")
            system = PySpin.System.GetInstance()
            camera = system.GetCameras()[0]
            nodemap = camera.GetNodeMap()
            node_autofocus_method = PySpin.CEnumerationPtr(nodemap.GetNode('AutoFocusMethod'))
            node_autofocus_method_coarse = node_autofocus_method.GetEntryByName('Coarse')
            node_autofocus_method.SetIntValue(node_autofocus_method_coarse.GetValue())
        elif index == 1:
            print("You have choose the autofoucs method as Fine!")
            system = PySpin.System.GetInstance()
            camera = system.GetCameras()[0]
            nodemap = camera.GetNodeMap()
            node_autofocus_method = PySpin.CEnumerationPtr(nodemap.GetNode('AutoFocusMethod'))
            node_autofocus_method_fine = node_autofocus_method.GetEntryByName('Fine')
            node_autofocus_method.SetIntValue(node_autofocus_method_fine.GetValue())

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
        """Convert from an opencv image to QPixmap"""
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QtGui.QImage(rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
        p = convert_to_Qt_format.scaled(640, 480, Qt.KeepAspectRatio)
        return QPixmap.fromImage(p)
    
if __name__=="__main__":
    app = QApplication(sys.argv)
    a = App()
    a.show()
    sys.exit(app.exec_())

