from PyQt5 import QtGui, QtCore
from PyQt5.QtWidgets import QWidget, QApplication, QLabel, QVBoxLayout, QMainWindow, QTextEdit, QPlainTextEdit, QHBoxLayout, QAction, QPushButton, QLineEdit, QFileDialog, QComboBox, QListView
from PyQt5.QtGui import QPixmap, QFont, QTextCursor
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QThread
import numpy as np
import PySpin, serial, pyfirmata
import os, keyboard, time, base64, sys, cv2, re, configparser
from PIL import Image, ImageDraw
from skimage import img_as_ubyte


# switch initilization
port = 'COM4'
relay_pin = 12
port_exist = True
try:
    board = pyfirmata.Arduino('COM4')
except IOError:
    print("USB port not Found")
    port_exist = False
    time.sleep(3)

# set up N for how many images we are gonna taken (30fps), and initilize a np nd array for saving img data
mode = "disconnect"   # set the initial mode to disconnect
t0, t1, t2 = 1, 10, 20
fps = 30
N = t2*fps
img_data_array = np.zeros((N,480,640))

# set up the saving path and saved filename for the data
Saved_Folder = "C:/Users/Alfoul/Desktop/Thermography_for_Grape_Mortality/code/SavedData/"
cultivar = "unknown"
branch_num = 1
if branch_num < 10:
    branch = "B0" + str(branch_num)
else:
    branch = "B" + str(branch_num)
node_num = 1
if node_num < 10:
    node = "N0" + str(node_num)
else:
    node = "N" + str(node_num)
save_file_name = cultivar + "_" + branch + "_" + node + "_" + ".npy"

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

            # ensure the pixel format = mono16
            node_pixel_format = PySpin.CEnumerationPtr(nodemap.GetNode('PixelFormat'))
            node_pixel_format_mono16 = PySpin.CEnumEntryPtr(node_pixel_format.GetEntryByName(pixel_format))
            pixel_format_mono16 = node_pixel_format_mono16.GetValue()
            node_pixel_format.SetIntValue(pixel_format_mono16)

            # # handle different options of IRformattype
            if CHOSEN_IR_TYPE == IRFormatType.LINEAR_10MK:
                # This section is to be activated only to set the streaming mode to TemperatureLinear10mK
                node_IRFormat = PySpin.CEnumerationPtr(nodemap.GetNode('IRFormat'))
                node_temp_linear_high = PySpin.CEnumEntryPtr(node_IRFormat.GetEntryByName('TemperatureLinear10mK'))
                node_temp_high = node_temp_linear_high.GetValue()
                node_IRFormat.SetIntValue(node_temp_high)
            elif CHOSEN_IR_TYPE == IRFormatType.LINEAR_100MK:
                # This section is to be activated only to set the streaming mode to TemperatureLinear100mK
                node_IRFormat = PySpin.CEnumerationPtr(nodemap.GetNode('IRFormat'))
                node_temp_linear_low = PySpin.CEnumEntryPtr(node_IRFormat.GetEntryByName('TemperatureLinear100mK'))
                node_temp_low = node_temp_linear_low.GetValue()
                node_IRFormat.SetIntValue(node_temp_low)
            elif CHOSEN_IR_TYPE == IRFormatType.RADIOMETRIC:
                # This section is to be activated only to set the streaming mode to Radiometric
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

                # Retrieve Calibration details
                CalibrationQueryR_node = PySpin.CFloatPtr(nodemap.GetNode('R'))
                R = CalibrationQueryR_node.GetValue()
                print('R =', R)

                CalibrationQueryB_node = PySpin.CFloatPtr(nodemap.GetNode('B'))
                B = CalibrationQueryB_node.GetValue()
                print('B =', B)

                CalibrationQueryF_node = PySpin.CFloatPtr(nodemap.GetNode('F'))
                F = CalibrationQueryF_node.GetValue()
                print('F =', F)

                CalibrationQueryX_node = PySpin.CFloatPtr(nodemap.GetNode('X'))
                X = CalibrationQueryX_node.GetValue()
                print('X =', X)

                CalibrationQueryA1_node = PySpin.CFloatPtr(nodemap.GetNode('alpha1'))
                A1 = CalibrationQueryA1_node.GetValue()
                print('alpha1 =', A1)

                CalibrationQueryA2_node = PySpin.CFloatPtr(nodemap.GetNode('alpha2'))
                A2 = CalibrationQueryA2_node.GetValue()
                print('alpha2 =', A2)

                CalibrationQueryB1_node = PySpin.CFloatPtr(nodemap.GetNode('beta1'))
                B1 = CalibrationQueryB1_node.GetValue()
                print('beta1 =', B1)

                CalibrationQueryB2_node = PySpin.CFloatPtr(nodemap.GetNode('beta2'))
                B2 = CalibrationQueryB2_node.GetValue()
                print('beta2 =', B2)

                CalibrationQueryJ1_node = PySpin.CFloatPtr(nodemap.GetNode('J1'))    # Gain
                J1 = CalibrationQueryJ1_node.GetValue()
                print('Gain =', J1)

                CalibrationQueryJ0_node = PySpin.CIntegerPtr(nodemap.GetNode('J0'))   # Offset
                J0 = CalibrationQueryJ0_node.GetValue()
                print('Offset =', J0)

                if CHOSEN_IR_TYPE == IRFormatType.RADIOMETRIC:
                    H2O = Humidity * np.exp(1.5587 + 0.06939 * TAtmC - 0.00027816 * TAtmC * TAtmC + 0.00000068455 * TAtmC * TAtmC * TAtmC)
                    print('H20 =', H2O)
                    Tau = X * np.exp(-np.sqrt(Dist) * (A1 + B1 * np.sqrt(H2O))) + (1 - X) * np.exp(-np.sqrt(Dist) * (A2 + B2 * np.sqrt(H2O)))
                    print('tau =', Tau)
                    # Pseudo radiance of the reflected environment
                    r1 = ((1 - Emiss) / Emiss) * (R / (np.exp(B / TRefl) - F))
                    print('r1 =', r1)
                    # Pseudo radiance of the atmosphere
                    r2 = ((1 - Tau) / (Emiss * Tau)) * (R / (np.exp(B / TAtm) - F))
                    print('r2 =', r2)
                    # Pseudo radiance of the external optics
                    r3 = ((1 - ExtOpticsTransmission) / (Emiss * Tau * ExtOpticsTransmission)) * (R / (np.exp(B / ExtOpticsTemp) - F))
                    print('r3 =', r3)
                    K2 = r1 + r2 + r3
                    print('K2 =', K2)

                # about to run
                global branch_num, node_num, branch, node, save_file_name
                print("Now we have t0 =  " + str(t0) + "  , t1 =  " + str(t1) + "  t2 =  " + str(t2))
                print("going to conduct data acquisition on " + cultivar + " cultivar of branch (" + branch + ") and node (" + node + ")")

                # save down parameters in .cfg in the same directory of where image data saved
                config = configparser.ConfigParser()
                config['PARAMETERS'] = {'TRefl': str(TRefl),
                                        'Emiss': str(Emiss),
                                        'TAtm': str(TAtm),
                                        'TAtmC': str(TAtmC),
                                        'Humidity': str(Humidity),
                                        'Dist': str(Dist),
                                        'ExtOpticsTransmission': str(ExtOpticsTransmission),
                                        'ExtOpticsTemp': str(ExtOpticsTemp)}
                save_param_name = os.path.splitext(save_file_name)[0] + ".cfg"
                with open (os.path.join(Saved_Folder, save_param_name),'w') as configfile:
                    config.write(configfile)
                print("Parameter Saved")
                time.sleep(1)

                # record start time, construct image_data_array
                start_time = time.time()
                i = 0
                global N, img_data_array
                N = t2*fps
                img_data_array = np.zeros((N,480,640))

                while(self._run_flag):
                    try:
                        image_result = cam.GetNextImage(1000)
                        if image_result.IsIncomplete():
                            print("")
                            # print('Image incomplete with image status %d ...' % image_result.GetImageStatus())
                        else:                   
                            image_data = image_result.GetNDArray()

                            # depending on different irformattype
                            if CHOSEN_IR_TYPE == IRFormatType.LINEAR_10MK:
                                image_Temp_Celsius_high = (image_data * 0.01) - 273.15
                            elif CHOSEN_IR_TYPE == IRFormatType.LINEAR_100MK:
                                image_Temp_Celsius_low = (image_data * 0.1) - 273.15
                            elif CHOSEN_IR_TYPE == IRFormatType.RADIOMETRIC:
                                image_Radiance = (image_data - J0) / J1
                                image_Temp = (B / np.log(R / ((image_Radiance / Emiss / Tau) - K2) + F)) - 273.15

                            # TODO: 
                            # Issue: if pixel format is mono16, then we will receive the image_data in uint16 and after the calculation,
                            # the image_Temp would be float64, this format needs to be rounded to be pass through cv2, and also cannot be viewed
                            # Solution: we record the estimate range for pixel value that could be view in mono8 is from [26,232],
                            # and the pixel value for image_data in mono16 is [8409,9246],
                            # We used a linear conversion and get k = 0.24612,b=-2043.6. With this conversion, we could view the video somehow
                            # Another soln might be changing cv2 package into matlab package
                            # print(image_data.dtype,np.min(image_data),np.max(image_data))

                            # image_Temp_conv = (image_data*0.24612-2043.6)*1.4
                            # image_Temp_conv = np.round(image_Temp_conv).astype(np.uint8)
                            # self.change_pixmap_signal.emit(image_Temp_conv)

                            # image_data_norm = cv2.normalize(image_data,image_data,0,255,cv2.NORM_MINMAX,dtype=cv2.CV_8U)
                            image_Temp_norm = cv2.normalize(image_Radiance,image_Radiance,0,255,cv2.NORM_MINMAX,dtype=cv2.CV_8U)
                            self.change_pixmap_signal.emit(image_Temp_norm)


                        image_result.Release()
                        if (i < N):
                            img_data_array[i] = image_data
                            # print("Now, You have passed  " + str(i) + "  images!")
                            i = i + 1
                        if (i == N):
                            print("Now, You have passed  " + str(i) + "  images!")
                            print("DAQ finished!")

                            # # save the image content array to a npy file
                            np.save(os.path.join(Saved_Folder, save_file_name),img_data_array)   
                            print("------------Image Contents Saved------------")
                            print("Data saved into   " + save_file_name)

                            # update branch and node indexs for the next
                            if node_num == 99:
                                node_num = 0
                                branch_num += 1
                            else:
                                node_num += 1
                            if branch_num < 10:
                                branch = "B0" + str(branch_num)
                            else:
                                branch = "B" + str(branch_num)
                            if node_num < 10:
                                node = "N0" + str(node_num)
                            else:
                                node = "N" + str(node_num)
                            save_file_name = cultivar + "_" + branch + "_" + node + "_" + ".npy"

                            i = N + 1
                        diff_time = time.time() - start_time
                        if (diff_time >= t0 and diff_time < t1):
                            # ser.write(some_bytes1)
                             board.digital[relay_pin].write(1)
                        elif (diff_time >= t1 and diff_time < t2):
                            # ser.write(some_bytes2)
                             board.digital[relay_pin].write(0)
                        

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

        # create buttons
        button_DAQ = QPushButton('DAQ', self)
        button_DAQ.clicked.connect(self.open_DAQ_window)
        button_DAQ.resize(80,40)
        button_DAQ.move(880,30)

        button_connect = QPushButton('Connect', self)
        button_connect.clicked.connect(self.click_connect)
        button_connect.resize(80,40)
        button_connect.move(680,30)

        button_disconnect = QPushButton('Cut', self)
        button_disconnect.clicked.connect(self.click_disconnect)
        button_disconnect.resize(80,40)
        button_disconnect.move(780,30)

        button_autofocus = QPushButton('Auto', self)
        button_autofocus.clicked.connect(self.click_autofocus)
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
        combo_box_autofocus_method.move(680,140)

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
        box_focus_step.move(880,140)
        box_focus_step.returnPressed.connect(lambda: save_focus_step())
        def save_focus_step():
            if re.match("^\d+$", box_focus_step.text()):
                global focus_step
                focus_step = int(box_focus_step.text())
                print("You have set focus step to  " + str(focus_step) + "  !")
            else:
                print("wrong input! Want int")

        button_parameter = QPushButton('Set Parameters', self)
        button_parameter.resize(280,35)
        button_parameter.move(680,255)
        button_parameter.clicked.connect(lambda: click_button_parameter())
        def click_button_parameter():
            if self.subParametersWindow is None:
                self.subParametersWindow = SubParameterGUI()
            self.subParametersWindow.show()

        button_start_end = QPushButton('Start DAQ', self)
        button_start_end.resize(280,40)
        button_start_end.move(680,300)
        button_start_end.clicked.connect(lambda: start_DAQ())
        def start_DAQ():
            print('-------------DAQ Clicked-------------')
            if (port_exist == False):
                print("USB not inserted, cannot go to timed version!")
            else:
                global mode
                if mode != "TimedStream":
                    mode = "TimedStream"
                    print("Now we are going to switch mode to a timed streaming mode!")
                    button_start_end.setText("Stop DAQ")
                    self.thread.stop()
                    self.thread = VideoThread_timed()
                    self.thread.change_pixmap_signal.connect(self.update_image)
                    self.thread.start()
                elif mode == "TimedStream":
                    mode = "contious_stream"
                    print("You have stopped DAQ and jumped to contious streaming mode!")
                    button_start_end.setText("Start DAQ")
                    self.thread.stop()
                    self.thread = VideoThread()
                    self.thread.change_pixmap_signal.connect(self.update_image)
                    self.thread.start()               

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

    def open_DAQ_window(self):
        if self.DAQ_window is None:    
            self.DAQ_window = DAQ_GUI()
        self.DAQ_window.show()

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
        if len(cv_img.shape) == 2:
            rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_GRAY2RGB)
            convert_to_Qt_format = QtGui.QImage(rgb_image.data,cv_img.shape[1],cv_img.shape[0],0,QtGui.QImage.Format_RGB888)
        else:
            rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            convert_to_Qt_format = QtGui.QImage(rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
        p = convert_to_Qt_format.scaled(640, 480, Qt.KeepAspectRatio)
        return QPixmap.fromImage(p)

class DAQ_GUI(QWidget):  
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Data Acquistion Setting")
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.setMinimumWidth(360)
        self.setMinimumHeight(410)

        # set boxes for typing in time, and the last one is for data saving_path
        label_t0 = QLabel('t0', self)
        label_t0.move(20, 20)
        box_t0 = QLineEdit(str(t0), self)
        box_t0.setAlignment(QtCore.Qt.AlignCenter)    # set the text in middle
        box_t0.resize(40,30)
        box_t0.move(40,20)
        box_t0.returnPressed.connect(lambda: save_t0())
        def save_t0():
            if re.match("^\d+$", box_t0.text()):
                global t0
                t0 = int(box_t0.text())
                print("You have set t0 to  " + str(t0) + "  !")
            else:
                print("wrong input! Want int")

        label_t1 = QLabel('t1', self)
        label_t1.move(120, 20)
        box_t1 = QLineEdit(str(t1), self)
        box_t1.setAlignment(QtCore.Qt.AlignCenter)
        box_t1.resize(40,30)
        box_t1.move(140,20)
        box_t1.returnPressed.connect(lambda: save_t1())
        def save_t1():
            if re.match("^\d+$", box_t1.text()):
                global t1
                t1 = int(box_t1.text())
                print("You have set t1 to  " + str(t1) + "  !")
            else:
                print("wrong input! Want int")

        label_t2 = QLabel('t2', self)
        label_t2.move(220, 20)
        box_t2 = QLineEdit(str(t2), self)
        box_t2.setAlignment(QtCore.Qt.AlignCenter)
        box_t2.resize(40,30)
        box_t2.move(240,20)
        box_t2.returnPressed.connect(lambda: save_t2())
        def save_t2():
            if re.match("^\d+$", box_t2.text()):
                global t2
                t2 = int(box_t2.text())
                print("You have set t2 to  " + str(t2) + "  !")
            else:
                print("wrong input! Want int")

        # for the data saving path and also saved filename
        label_filename = QLabel('Data Name', self)
        label_filename.move(120, 60)
        box_path = QLineEdit(save_file_name, self)
        box_path.setAlignment(QtCore.Qt.AlignCenter)
        box_path.resize(280,30)
        box_path.move(20,90)
        box_path.returnPressed.connect(lambda: save_file())
        def save_file():
            global save_file_name
            save_file_name = box_path.text() + ".npy"
            print("You have choosen " + save_file_name + " as the saved npy filename")

        button_path = QPushButton("Data Saving Folder", self)
        button_path.resize(280,30)
        button_path.move(20,120)
        button_path.clicked.connect(lambda: save_path())
        def save_path():
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            directory = QFileDialog.getExistingDirectory(self, "QFileDialog..getExistingDirectory()", "", options=options)
            global Saved_Folder
            Saved_Folder = directory
            print("Choose Download Directory:  " +Saved_Folder)

        label_cultivar = QLabel('Cultivar', self)
        label_cultivar.move(30,160)
        box_cultivar = QLineEdit(cultivar, self)
        box_cultivar.setAlignment(QtCore.Qt.AlignCenter)
        box_cultivar.resize(70,30)
        box_cultivar.move(100,160)
        box_cultivar.returnPressed.connect(lambda: save_cultivar())
        def save_cultivar():
            global cultivar
            cultivar = box_cultivar.text()
            box_path.setText(cultivar + "_" + branch + "_" + node + "_" + ".npy")
            print("You have set cultivar to  " + cultivar + "  !")

        label_branch = QLabel('Branch', self)
        label_branch.move(30,200)
        box_branch = QLineEdit(str(branch_num), self)
        box_branch.setAlignment(QtCore.Qt.AlignCenter)
        box_branch.resize(70,30)
        box_branch.move(100,200)
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
                box_path.setText(cultivar + "_" + branch + "_" + node + "_" + ".npy")
                print("You have set branch to  " + str(branch) + "  !")
            else:
                print("wrong input! Want int")

        label_node = QLabel('Node', self)
        label_node.move(30, 240)
        box_node = QLineEdit(str(node_num), self)
        box_node.setAlignment(QtCore.Qt.AlignCenter)
        box_node.resize(70,30)
        box_node.move(100,240)
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
                box_path.setText(cultivar + "_" + branch + "_" + node + "_" + ".npy")
                print("You have set node to  " + str(node) + "  !")
            else:
                print("wrong input! Want int")

        # while True:
        #     box_cultivar.setText(cultivar)
        #     box_branch.setText(str(branch_num))
        #     box_node.setText(str(node_num))
        #     box_path.setText(save_file_name)     


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

if __name__=="__main__":
    app = QApplication(sys.argv)
    a = App()
    a.show()
    sys.exit(app.exec_())

