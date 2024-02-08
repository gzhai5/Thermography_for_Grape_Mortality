from PyQt5 import QtGui, QtCore
from PyQt5.QtWidgets import QWidget, QApplication, QLabel, QVBoxLayout, QMainWindow, QTextEdit, QPlainTextEdit, QHBoxLayout, QAction, QPushButton, QLineEdit, QFileDialog, QComboBox, QListView
from PyQt5.QtGui import QPixmap, QFont, QTextCursor
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QThread
from PyQt5.QtMultimedia import QSound
import numpy as np
import PySpin
import os, time, sys, cv2, re, configparser
from PIL import Image, ImageDraw


# set up N for how many images we are gonna taken (30fps), and initilize a np nd array for saving img data
mode = "disconnect"   # set the initial mode to disconnect
t0, t1, t2 = 1, 10, 20
fps = 30
image_interval = 60
N = t2*fps
img_data_array = np.zeros((N,480,640), dtype=np.uint16)

# set up the saving path and saved filename for the data
this_file = os.path.abspath(__file__)
Saved_Folder = "F:/"

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
            node_pixel_format_mono8 = PySpin.CEnumEntryPtr(node_pixel_format.GetEntryByName('Mono16'))
            node_pixel_format_mono8 = node_pixel_format_mono8.GetValue()
            node_pixel_format.SetIntValue(node_pixel_format_mono8)

            CalibrationQueryJ1_node = PySpin.CFloatPtr(nodemap.GetNode('J1'))    # Gain
            J1 = CalibrationQueryJ1_node.GetValue()
            # print('Gain =', J1)

            CalibrationQueryJ0_node = PySpin.CIntegerPtr(nodemap.GetNode('J0'))   # Offset
            J0 = CalibrationQueryJ0_node.GetValue()
            # print('Offset =', J0)

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

                index = 0
                while(self._run_flag):
                    try:
                        image_result = cam.GetNextImage(1000)
                        if image_result.IsIncomplete():
                            print("image incomplete")
                        else:                    
                            image_data = image_result.GetNDArray()
                            index += 1

                            # save the image data into .raw files
                            if index % image_interval == 0:
                                index = 0
                                filename = "img_" + str(int(time.time())) + ".raw"
                                with open(filename, "wb") as f:
                                    f.write(image_data.tobytes())
                                pass


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
        self.finish_sound = QSound("./static/success_sound.wav")

    def play_sound(self):
        self.finish_sound.play()

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
            node_pixel_format_mono8 = PySpin.CEnumEntryPtr(node_pixel_format.GetEntryByName('Mono16'))
            node_pixel_format_mono8 = node_pixel_format_mono8.GetValue()
            node_pixel_format.SetIntValue(node_pixel_format_mono8)

            CalibrationQueryJ1_node = PySpin.CFloatPtr(nodemap.GetNode('J1'))    # Gain
            J1 = CalibrationQueryJ1_node.GetValue()
            # print('Gain =', J1)

            CalibrationQueryJ0_node = PySpin.CIntegerPtr(nodemap.GetNode('J0'))   # Offset
            J0 = CalibrationQueryJ0_node.GetValue()
            # print('Offset =', J0)

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

        # set boxes for typing in time, and the last one is for data saving_path
        label_t0 = QLabel('t0', self)
        label_t0.move(680, 190)
        box_t0 = QLineEdit(str(t0), self)
        box_t0.setAlignment(QtCore.Qt.AlignCenter)    # set the text in middle
        box_t0.resize(40,30)
        box_t0.move(700,190)
        box_t0.returnPressed.connect(lambda: save_t0())
        def save_t0():
            if re.match("^\d+$", box_t0.text()):
                global t0
                t0 = int(box_t0.text())
                print("You have set t0 to  " + str(t0) + "  !")
            else:
                print("wrong input! Want int")

        label_t1 = QLabel('t1', self)
        label_t1.move(780, 190)
        box_t1 = QLineEdit(str(t1), self)
        box_t1.setAlignment(QtCore.Qt.AlignCenter)
        box_t1.resize(40,30)
        box_t1.move(800,190)
        box_t1.returnPressed.connect(lambda: save_t1())
        def save_t1():
            if re.match("^\d+$", box_t1.text()):
                global t1
                t1 = int(box_t1.text())
                print("You have set t1 to  " + str(t1) + "  !")
            else:
                print("wrong input! Want int")

        label_t2 = QLabel('t2', self)
        label_t2.move(880, 190)
        box_t2 = QLineEdit(str(t2), self)
        box_t2.setAlignment(QtCore.Qt.AlignCenter)
        box_t2.resize(40,30)
        box_t2.move(900,190)
        box_t2.returnPressed.connect(lambda: save_t2())
        def save_t2():
            if re.match("^\d+$", box_t2.text()):
                global t2
                t2 = int(box_t2.text())
                print("You have set t2 to  " + str(t2) + "  !")
            else:
                print("wrong input! Want int")

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

        label_cultivar = QLabel('Cultivar', self)
        label_cultivar.move(680,305)
        box_cultivar = QLineEdit(cultivar, self)
        box_cultivar.setAlignment(QtCore.Qt.AlignCenter)
        box_cultivar.resize(70,30)
        box_cultivar.move(750,305)
        box_cultivar.returnPressed.connect(lambda: save_cultivar())
        def save_cultivar():
            global cultivar
            cultivar = box_cultivar.text()
            box_path.setText(cultivar + "_" + branch + "_" + node + ".npy")
            print("You have set cultivar to  " + cultivar + "  !")

        label_branch = QLabel('Branch', self)
        label_branch.move(680,340)
        box_branch = QLineEdit(str(branch_num), self)
        box_branch.setAlignment(QtCore.Qt.AlignCenter)
        box_branch.resize(70,30)
        box_branch.move(750,340)
        box_branch.returnPressed.connect(lambda: save_branch())
        def save_branch():
            if re.match("^\d+$", box_branch.text()):
                if int(box_branch.text()) < 0 or int(box_branch.text()) > 99:
                    print("wrong input for branch number! Want int between 0 and 99.")
                    return
                global branch_num, branch
                branch_num = int(box_branch.text())
                if branch_num < 10:
                    branch = "B0" + str(branch_num)
                else:
                    branch = "B" + str(branch_num)
                box_path.setText(cultivar + "_" + branch + "_" + node + ".npy")
                print("You have set branch to  " + str(branch) + "  !")
            else:
                print("wrong input! Want int")

        label_node = QLabel('Node', self)
        label_node.move(840, 340)
        box_node = QLineEdit(str(node_num), self)
        box_node.setAlignment(QtCore.Qt.AlignCenter)
        box_node.resize(70,30)
        box_node.move(885,340)
        box_node.returnPressed.connect(lambda: save_node())
        def save_node():
            if re.match("^\d+$", box_node.text()):
                if int(box_node.text()) < 0 or int(box_node.text()) > 99:
                    print("wrong input for node number! Want int between 0 and 99.")
                    return
                global node_num, node
                node_num = int(box_node.text())
                if node_num < 10:
                    node = "N0" + str(node_num)
                else:
                    node = "N" + str(node_num)
                box_path.setText(cultivar + "_" + branch + "_" + node + ".npy")
                print("You have set node to  " + str(node) + "  !")
            else:
                print("wrong input! Want int")

        # create buttons
        button_connect = QPushButton('Connect', self)
        button_connect.clicked.connect(self.click_connect)
        button_connect.resize(80,40)
        button_connect.move(680,30)

        button_disconnect = QPushButton('Cut', self)
        button_disconnect.clicked.connect(self.click_disconnect)
        button_disconnect.resize(80,40)
        button_disconnect.move(880,30)

        button_autofocus = QPushButton('Auto', self)
        button_autofocus.clicked.connect(self.click_autofocus)
        button_autofocus.setFocusPolicy(Qt.NoFocus)
        button_autofocus.resize(80,40)
        button_autofocus.move(680,80)

        button_focusplus = QPushButton('+', self)
        button_focusplus.clicked.connect(self.click_focusplus)
        button_focusplus.resize(80,40)
        button_focusplus.move(780,80)

        button_focusminus = QPushButton('-', self)
        button_focusminus.clicked.connect(self.click_focusminus)
        button_focusminus.resize(80,40)
        button_focusminus.move(880,80)

        combo_box_autofocus_method = QComboBox(self)
        options = ["Coarse", "Fine"]
        combo_box_autofocus_method.addItems(options)
        combo_box_autofocus_method.setCurrentIndex(0)
        combo_box_autofocus_method.currentIndexChanged.connect(self.autofocus_method)
        combo_box_autofocus_method.resize(90,40)
        combo_box_autofocus_method.move(680,135)

        # combo_box_pixelformat_method = QComboBox(self)
        # options_pf = ["Mono8", "Mono16"]
        # combo_box_pixelformat_method.addItems(options_pf)
        # combo_box_pixelformat_method.setCurrentIndex(0)
        # combo_box_pixelformat_method.currentIndexChanged.connect(lambda: imageformat_method)
        # combo_box_pixelformat_method.resize(90,40)
        # combo_box_pixelformat_method.move(780,380)
        # def imageformat_method(self, index):
        #     global pixel_format
        #     if index == 0:
        #         pixel_format = "Mono8"
        #         print("You have choose the image format as Mono8!")
        #     elif index == 1:
        #         pixel_format = "Mono16"
        #         print("You have choose the image format as Mono16!")

        box_focus_step = QLineEdit('Focus Step', self)
        box_focus_step.setAlignment(QtCore.Qt.AlignCenter)
        box_focus_step.resize(90,40)
        box_focus_step.move(875,135)
        box_focus_step.returnPressed.connect(lambda: save_focus_step())
        def save_focus_step():
            if re.match("^\d+$", box_focus_step.text()):
                global focus_step
                focus_step = int(box_focus_step.text())
                print("You have set focus step to  " + str(focus_step) + "  !")
            else:
                print("wrong input! Want int")

        button_parameter = QPushButton('Set Parameters', self)
        button_parameter.resize(280,30)
        button_parameter.move(680,410)
        button_parameter.clicked.connect(lambda: click_button_parameter())
        def click_button_parameter():
            if self.subParametersWindow is None:
                self.subParametersWindow = SubParameterGUI()
            self.subParametersWindow.show()

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

    def start_DAQ(self):
            print('-------------DAQ Clicked-------------')
            if (port_exist == False):
                print("USB not inserted, cannot go to timed version!")
            else:
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
    
    # Replace 'Space' with your desired key
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space:
            self.start_DAQ()
        elif event.key() == Qt.Key_A:
            self.click_autofocus()

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
        cv2.line(rgb_image, (center_x, 0), (center_x, height), line_color, thickness)
        # Drawing horizontal line
        cv2.line(rgb_image, (0, center_y), (width, center_y), line_color, thickness)

        if len(cv_img.shape) == 2:
            convert_to_Qt_format = QtGui.QImage(rgb_image.data, cv_img.shape[1], cv_img.shape[0], 0, QtGui.QImage.Format_RGB888)
        else:
            bytes_per_line = channels * width
            convert_to_Qt_format = QtGui.QImage(rgb_image.data, width, height, bytes_per_line, QtGui.QImage.Format_RGB888)

        p = convert_to_Qt_format.scaled(640, 480, Qt.KeepAspectRatio)
        return QPixmap.fromImage(p)


class SubParameterGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Camera Parameter Setting")
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.setMinimumWidth(365)
        self.setMinimumHeight(290)

        # create boxs for saving object parameters
        box_emiss = QLineEdit('Emiss', self)
        box_emiss.setAlignment(QtCore.Qt.AlignCenter)
        box_emiss.resize(70,30)
        box_emiss.move(20,20)
        box_emiss.returnPressed.connect(lambda: save_emiss())
        def save_emiss():
            if re.match("^\d+(\.\d+)?$", box_emiss.text()):
                global Emiss
                Emiss = float(box_emiss.text())
                print("You have set Emiss to  " + str(Emiss) + "  !")
            else:
                print("wrong input! Want float")

        box_trefl = QLineEdit('TRefl', self)
        box_trefl.setAlignment(QtCore.Qt.AlignCenter)
        box_trefl.resize(70,30)
        box_trefl.move(20,60)
        box_trefl.returnPressed.connect(lambda: save_trefl())
        def save_trefl():
            if re.match("^\d+(\.\d+)?$", box_trefl.text()):
                global TRefl
                TRefl = float(box_trefl.text())
                print("You have set TRefl to  " + str(TRefl) + "  !")
            else:
                print("wrong input! Want float")

        box_tatm = QLineEdit('TAtm', self)
        box_tatm.setAlignment(QtCore.Qt.AlignCenter)
        box_tatm.resize(70,30)
        box_tatm.move(20,100)
        box_tatm.returnPressed.connect(lambda: save_tatm())
        def save_tatm():
            if re.match("^\d+(\.\d+)?$", box_tatm.text()):
                global TAtm
                TAtm = float(box_tatm.text())
                print("You have set TAtm to  " + str(TAtm) + "  !")
                global TAtmC
                TAtmC = TAtm - 273.15
                print("You have also set TAtm to  " + str(TAtmC) + "  !")
                print("Because normally TAtmC = TAtm - 273.15 by formula, but you can still change TatmC in its box")
                global ExtOpticsTemp
                ExtOpticsTemp = TAtm
                print("You have also set ExtOpticsTemp to  " + str(ExtOpticsTemp) + "  !")
                print("Because normally ExtOpticsTemp = TAtm by formula, but you can still change ExtOpticsTemp in its box")
            else:
                print("wrong input! Want float")

        box_tatmc = QLineEdit('TAtmC', self)
        box_tatmc.setAlignment(QtCore.Qt.AlignCenter)
        box_tatmc.resize(70,30)
        box_tatmc.move(20,140)
        box_tatmc.returnPressed.connect(lambda: save_tatmc())
        def save_tatmc():
            if re.match("^\d+(\.\d+)?$", box_tatmc.text()):
                global TAtmC
                TAtmC = float(box_tatmc.text())
                print("You have set TAtmC to  " + str(TAtmC) + "  !")
            else:
                print("wrong input! Want float")

        box_humidity = QLineEdit('Humidity', self)
        box_humidity.setAlignment(QtCore.Qt.AlignCenter)
        box_humidity.resize(70,30)
        box_humidity.move(20,180)
        box_humidity.returnPressed.connect(lambda: save_humidity())
        def save_humidity():
            if re.match("^\d+(\.\d+)?$", box_humidity.text()):
                global Humidity
                Humidity = float(box_humidity.text())
                print("You have set Humidity to  " + str(Humidity) + "  !")
            else:
                print("wrong input! Want float")

        box_dist = QLineEdit('Dist', self)
        box_dist.setAlignment(QtCore.Qt.AlignCenter)
        box_dist.resize(70,30)
        box_dist.move(20,220)
        box_dist.returnPressed.connect(lambda: save_dist())
        def save_dist():
            if re.match("^\d+(\.\d+)?$", box_dist.text()):
                global Dist
                Dist = float(box_dist.text())
                print("You have set Dist to  " + str(Dist) + "  !")
            else:
                print("wrong input! Want float")

        box_extOpticsTransmission = QLineEdit('ExtOpticsTransmission', self)
        box_extOpticsTransmission.setAlignment(QtCore.Qt.AlignCenter)
        box_extOpticsTransmission.resize(150,30)
        box_extOpticsTransmission.move(180,20)
        box_extOpticsTransmission.returnPressed.connect(lambda: save_extOpticsTransmission())
        def save_extOpticsTransmission():
            if re.match("^\d+(\.\d+)?$", box_extOpticsTransmission.text()):
                global ExtOpticsTransmission
                ExtOpticsTransmission = int(box_extOpticsTransmission.text())
                print("You have set ExtOpticsTransmission to  " + str(ExtOpticsTransmission) + "  !")
            else:
                print("wrong input! Want float")

        box_extOpticsTemp = QLineEdit('ExtOpticsTemp', self)
        box_extOpticsTemp.setAlignment(QtCore.Qt.AlignCenter)
        box_extOpticsTemp.resize(150,30)
        box_extOpticsTemp.move(180,60)
        box_extOpticsTemp.returnPressed.connect(lambda: save_extOpticsTemp())
        def save_extOpticsTemp():
            if re.match("^\d+(\.\d+)?$", box_extOpticsTemp.text()):
                global ExtOpticsTemp
                ExtOpticsTemp = float(box_extOpticsTemp.text())
                print("You have set ExtOpticsTemp to  " + str(ExtOpticsTemp) + "  !")
            else:
                print("wrong input! Want float")

        box_node_num_upper_limit = QLineEdit('Node UpperLimit', self)
        box_node_num_upper_limit.setAlignment(QtCore.Qt.AlignCenter)
        box_node_num_upper_limit.resize(150,30)
        box_node_num_upper_limit.move(180,100)
        box_node_num_upper_limit.returnPressed.connect(lambda: save_node_num_upper_limit())
        def save_node_num_upper_limit():
            if re.match("^\d+$", box_node_num_upper_limit.text()):
                global node_num_upper_limit
                node_num_upper_limit = int(box_node_num_upper_limit.text())
                print("You have set the upper limit of node number to  " + str(node_num_upper_limit) + "  !")
            else:
                print("wrong input! Want Int")        

if __name__=="__main__":
    app = QApplication(sys.argv)
    a = App()
    a.show()
    sys.exit(app.exec_())

