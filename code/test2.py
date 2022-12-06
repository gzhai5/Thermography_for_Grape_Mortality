#import necessay modules
from PyQt5 import QtGui
from PyQt5.QtWidgets import QWidget, QApplication, QLabel, QVBoxLayout
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QTimer, QPoint, pyqtSignal, QCoreApplication
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QLabel
from PyQt5.QtWidgets import QWidget, QAction, QVBoxLayout, QHBoxLayout
from PyQt5.QtGui import QFont, QPainter, QImage, QTextCursor
import sys, cv2, os, time, threading, PySpin
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QThread
import numpy as np
from PIL import Image
import base64, serial, keyboard
import matplotlib.pyplot as plt
import matplotlib.image
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QMainWindow, QLabel, QGridLayout, QWidget
from PyQt5.QtWidgets import QPushButton, QPlainTextEdit
import PyQt5.QtWidgets as qtw
from PyQt5.QtCore import QSize   
from PyQt5.QtCore import QProcess
try:
    import Queue as Queue
except:
    import queue as Queue

# switch initilization
port = 'COM3'
ser = serial.Serial(port, 9600, timeout=1)
hex_string1 = """A0 01 01 A2"""  #turn on str
some_bytes1 = bytearray.fromhex(hex_string1)
hex_string2 = """A0 01 00 A1"""  #turn off str
some_bytes2 = bytearray.fromhex(hex_string2)

# set up N for how many images we are gonna taken (30fps), and initilize a np nd array for saving img data
t0,t1,t2 = 1,10,20
fps = 30
N = t2*fps
img_data_array = np.zeros((N,480,640))

#set a var for knowing when to run camera
camera_run = True
one_time = True

# vars for gui image streaming
IMG_SIZE    = 640,480          # 640,480 or 1280,720 or 1920,1080
IMG_FORMAT  = QImage.Format_RGB888
DISP_SCALE  = 2                # Scaling factor for display image
DISP_MSEC   = 50                # Delay between display cycles
CAP_API     = cv2.CAP_ANY       # API: CAP_ANY or CAP_DSHOW etc...
EXPOSURE    = 0                 # Zero for automatic exposure
TEXT_FONT   = QFont("Courier", 10)

camera_num  = 1                 # Default camera (first in list)
image_queue = Queue.Queue()     # Queue to hold images
capturing   = True              # Flag to indicate capturing

#define fcn to acquire img
def acquire_images(cam, nodemap, nodemap_tldevice, queue):
    print('*** IMAGE ACQUISITION ***\n')
    try:
        result = True
        node_acquisition_mode = PySpin.CEnumerationPtr(nodemap.GetNode('AcquisitionMode'))
        if not PySpin.IsAvailable(node_acquisition_mode) or not PySpin.IsWritable(node_acquisition_mode):
            print('Unable to set acquisition mode to continuous (enum retrieval). Aborting...')
            return False
        node_acquisition_mode_continuous = node_acquisition_mode.GetEntryByName('Continuous')
        if not PySpin.IsAvailable(node_acquisition_mode_continuous) or not PySpin.IsReadable(node_acquisition_mode_continuous):
            print('Unable to set acquisition mode to continuous (entry retrieval). Aborting...')
            return False
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
        processor = PySpin.ImageProcessor()
        processor.SetColorProcessing(PySpin.HQ_LINEAR)


        #added 11/9
        start_time = time.time()
        camera_run = True
        i = 0
        while (camera_run):
            try:
                image_result = cam.GetNextImage(1000) #here, img_result is an img ptr
                if image_result.IsIncomplete():
                    print('Image incomplete with image status %d ...' % image_result.GetImageStatus())

                else:
                    #added:
                    received_time = int(time.time()*10**6)

                    width = image_result.GetWidth()
                    height = image_result.GetHeight()
                    print('Grabbed Image %d, width = %d, height = %d' % (i, width, height))


                    #image_converted = processor.Convert(image_result, PySpin.PixelFormat_Mono8)
                    image_converted = image_result



                    ##########################################


                    img_data = image_result.GetNDArray() #here retuns a ndarray img_data from img ptr
                    # print(type(img_data))
                    img_data_array[i] = img_data
                    print(len(img_data_array))



                    # new test
                    img_data_rgb = cv2.cvtColor(img_data, cv2.COLOR_GRAY2RGB)
                    if one_time == True:
                        x = img_data_rgb
                        y = img_data

                    if img_data_rgb is not None and queue.qsize() < 2:
                        queue.put(img_data_rgb)
                    else:
                        time.sleep(DISP_MSEC / 1000.0)


                    #plot continous plots as a video in single threading, problem: it will pause 0.001s each img, causing the calculation of time wrong
                    # plt.imshow(img_data, cmap='gray')
                    # plt.pause(0.001)
                    # plt.clf()

                    # if keyboard.is_pressed('ENTER'):
                    #     print('Program is closing...')

                    #     # Close figure
                    #     plt.close('all')
                    #     input('Done! Press Enter to exit...')
                    #     camera_run = False

                    # Create a unique filename
                    # if device_serial_number:
                    #     #filename = 'Acquisition-%s-%d.png' % (device_serial_number, i)
                    #     filename = '%s-%d.raw' % (device_serial_number, received_time)
                    # else:  # if serial number is empty
                    #     #filename = 'Acquisition-%d.png' % i
                    #     filename = 'Acquistion-%d-%d.raw' % (i, received_time)


                    #  Save image
                    #
                    #  *** NOTES ***
                    #  The standard practice of the examples is to use device
                    #  serial numbers to keep images of one device from
                    #  overwriting those of another.


                    #added for switch control
                    # input_val = int(input("Press 1 for turn on the switch\nPress 0 for turn off the switch\n"))
                    # if (input_val == 1):
                    #     ser.write(some_bytes1)
                    #     print('Icon On!')
                    # elif (input_val == 0):
                    #     ser.write(some_bytes2)
                    #     print('Icon OFF!')
                    # else:
                    #     print("you have pressed the wrong button!!!")


                    # image_converted.Save(filename)
                    # print('Image saved at %s' % filename)
                    image_result.Release()
                    # print('')

                    #added
                    # with open(filename, "rb") as f:
                    #     png_encoded = base64.b64encode(f.read())
                    #
                    # encoded_b2 = "".join([format(n, '08b') for n in png_encoded])
                    # text_file = open("data.txt", "w")
                    # text_file.write(encoded_b2)
                    # text_file.close

                    # different time acting on switch on/off
                    i = i + 1
                    diff_time = time.time() - start_time
                    if (diff_time >= t0 and diff_time < t1):
                        ser.write(some_bytes1)
                    elif (diff_time >= t1 and diff_time < t2):
                        ser.write(some_bytes2)
                    elif (diff_time >= t2):
                        camera_run = False


            except PySpin.SpinnakerException as ex:
                print('Error: %s' % ex)
                return False
        cam.EndAcquisition()

    except PySpin.SpinnakerException as ex:
        print('Error: %s' % ex)
        return False


    # Save to text_file, problem: text file will be too big
    # https://www.geeksforgeeks.org/how-to-load-and-save-3d-numpy-array-to-file-using-savetxt-and-loadtxt-functions/
    # array_reshaped = img_data_array.reshape(img_data_array.shape[0], -1) #reshape the 3d array into 2d
    # np.savetxt("imgs_data.txt", array_reshaped)

    # Save to npy file
    np.save('img_data.npy',img_data_array)

    print(len(img_data_array))

    print(img_data_array[10].shape)
    matplotlib.image.imsave('name.png', img_data_array[10])
    # cv2.imwrite("test.png", img_data_array[10])
    result_11111 = cv2.normalize(img_data_array[10], dst=None, alpha=0, beta=255,norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8U)
    cv2.imwrite("test.png", result_11111)
    # cv2.imwrite("x.png", x)
    # cv2.imwrite("y.png", y)

    # fourcc = cv2.VideoWriter_fourcc(*'MP42')
    # video = cv2.VideoWriter('test.mp4', fourcc, float(30), (480, 640))
    # for i in range(150):
    #     img = img_data_array[i]
    #     video.write(img)
    # video.release()

    return result

def print_device_info(nodemap):
    """
    This function prints the device information of the camera from the transport
    layer; please see NodeMapInfo example for more in-depth comments on printing
    device information from the nodemap.

    :param nodemap: Transport layer device nodemap.
    :type nodemap: INodeMap
    :returns: True if successful, False otherwise.
    :rtype: bool
    """

    print('*** DEVICE INFORMATION ***\n')

    try:
        result = True
        node_device_information = PySpin.CCategoryPtr(nodemap.GetNode('DeviceInformation'))

        if PySpin.IsAvailable(node_device_information) and PySpin.IsReadable(node_device_information):
            features = node_device_information.GetFeatures()
            for feature in features:
                node_feature = PySpin.CValuePtr(feature)
                print('%s: %s' % (node_feature.GetName(),
                                  node_feature.ToString() if PySpin.IsReadable(node_feature) else 'Node not readable'))

        else:
            print('Device control information not available.')

    except PySpin.SpinnakerException as ex:
        print('Error: %s' % ex)
        return False
    return result

def run_single_camera(cam, queue):
    try:
        result = True
        # Retrieve TL device nodemap and print device information
        nodemap_tldevice = cam.GetTLDeviceNodeMap()
        result &= print_device_info(nodemap_tldevice)
        # Initialize camera
        cam.Init()
        # Retrieve GenICam nodemap
        nodemap = cam.GetNodeMap()
        # Acquire images
        result &= acquire_images(cam, nodemap, nodemap_tldevice, queue)
        # Deinitialize camera
        cam.DeInit()
    except PySpin.SpinnakerException as ex:
        print('Error: %s' % ex)
        result = False
    return result

def camera_work(queue):
    result = True

    # Retrieve singleton reference to system object
    system = PySpin.System.GetInstance()

    # Get current library version
    version = system.GetLibraryVersion()
    print('Library version: %d.%d.%d.%d' % (version.major, version.minor, version.type, version.build))

    # Retrieve list of cameras from the system
    cam_list = system.GetCameras()

    num_cameras = cam_list.GetSize()

    print('Number of cameras detected: %d' % num_cameras)

    # Finish if there are no cameras
    if num_cameras == 0:

        # Clear camera list before releasing system
        cam_list.Clear()

        # Release system instance
        system.ReleaseInstance()

        print('Not enough cameras!')
        input('Done! Press Enter to exit...')
        return False

    # Run example on each camera
    for i, cam in enumerate(cam_list):

        print('Running example for camera %d...' % i)

        result &= run_single_camera(cam, queue)
        print('Camera %d example complete... \n' % i)

    # Release reference to camera
    # NOTE: Unlike the C++ examples, we cannot rely on pointer objects being automatically
    # cleaned up when going out of scope.
    # The usage of del is preferred to assigning the variable to None.
    del cam

    # Clear camera list before releasing system
    cam_list.Clear()

    # Release system instance
    system.ReleaseInstance()

    input('Done! Press Enter to exit...')
    return result

def grab_images(cam_num, queue):
    cap = cv2.VideoCapture(cam_num-1 + CAP_API)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, IMG_SIZE[0])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, IMG_SIZE[1])
    if EXPOSURE:
        cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0)
        cap.set(cv2.CAP_PROP_EXPOSURE, EXPOSURE)
    else:
        cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)
    while capturing:
        if cap.grab():
            retval, image = cap.retrieve(0)
            # print(type(image))
            # print(image.shape)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            print(type(gray))
            print(gray.shape)
            image = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)
            print(type(image))
            print(image.shape)
            # image = np.mean(image, axis=2)
            # print(image.shape)
            # image = np.stack((image,)*3, axis=-1)
            # print(image.shape)
            if image is not None and queue.qsize() < 2:
                queue.put(image)
            else:
                time.sleep(DISP_MSEC / 1000.0)
        else:
            print("Error: can't grab camera image")
            break
    cap.release()

class ImageWidget(QWidget):
    def __init__(self, parent=None):
        super(ImageWidget, self).__init__(parent)
        self.image = None

    def setImage(self, image):
        self.image = image
        self.setMinimumSize(image.size())
        self.update()

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
        if self.image:
            qp.drawImage(QPoint(0, 0), self.image)
        qp.end()

# Main window
class MyWindow(QMainWindow):
    text_update = pyqtSignal(str)

    # Create main window
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)

        self.central = QWidget(self)
        self.textbox = QTextEdit(self.central)
        self.textbox.setFont(TEXT_FONT)
        # self.textbox.setMinimumSize(300, 100)
        self.textbox.setFixedWidth(870)
        self.textbox.setFixedHeight(870/3)
        self.text_update.connect(self.append_text)
        sys.stdout = self
        print("Camera number %u" % camera_num)
        print("Image size %u x %u" % IMG_SIZE)
        if DISP_SCALE > 1:
            print("Display scale %u:1" % DISP_SCALE)

           
        self.setWindowTitle("Thermal Image Control")
        self.setFixedWidth(900)
        self.setFixedHeight(600)
        self.text = QPlainTextEdit()
        self.text.setReadOnly(True) 

        button_run = QPushButton('RUN', self)
        button_run.clicked.connect(self.click_run)
        button_run.resize(150,80)
        button_run.move(380,200) 

        button_stop = QPushButton('Stop', self)
        button_stop.clicked.connect(self.click_stop)
        button_stop.resize(150,80)
        button_stop.move(580,200)

        # set boxes for typing in time, and the last one is for data saving_path
        box_t0 = qtw.QLineEdit('t0', self)
        box_t0.setAlignment(QtCore.Qt.AlignCenter)    # set the text in middle
        box_t0.resize(100,30)
        box_t0.move(380,50)
        box_t0.returnPressed.connect(lambda: save_t0())
        def save_t0():
            t0 = int(box_t0.text())
            print(t0)

        box_t1 = qtw.QLineEdit('t1', self)
        box_t1.setAlignment(QtCore.Qt.AlignCenter)
        box_t1.resize(100,30)
        box_t1.move(500,50)
        box_t1.returnPressed.connect(lambda: save_t1())
        def save_t1():
            t1 = int(box_t1.text())
            print(t1)

        box_t2 = qtw.QLineEdit('t2', self)
        box_t2.setAlignment(QtCore.Qt.AlignCenter)
        box_t2.resize(100,30)
        box_t2.move(620,50)
        box_t2.returnPressed.connect(lambda: save_t2())
        def save_t2():
            t2 = int(box_t2.text())
            print(t2)

        box_path = qtw.QLineEdit('Data Saving Path', self)
        box_path.setAlignment(QtCore.Qt.AlignCenter)
        box_path.resize(340,30)
        box_path.move(380,120)
        box_path.returnPressed.connect(lambda: save_path())
        def save_path():
            saving_path = box_path.text()
            print(saving_path)


        self.vlayout = QVBoxLayout()        # Window layout
        self.displays = QHBoxLayout()
        self.disp = ImageWidget(self)    
        self.displays.addWidget(self.disp)
        self.vlayout.addLayout(self.displays)
        self.label = QLabel(self)
        self.vlayout.addWidget(self.label)
        self.vlayout.addWidget(self.textbox)
        self.central.setLayout(self.vlayout)
        self.setCentralWidget(self.central)

        self.mainMenu = self.menuBar()      # Menu bar
        exitAction = QAction('&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.triggered.connect(self.close)
        self.fileMenu = self.mainMenu.addMenu('&File')
        self.fileMenu.addAction(exitAction)

    # Start image capture & display
    def start(self):
        self.timer = QTimer(self)           # Timer to trigger display
        self.timer.timeout.connect(lambda: 
                    self.show_image(image_queue, self.disp, DISP_SCALE))
        self.timer.start(DISP_MSEC)         
        self.capture_thread = threading.Thread(target=camera_work, 
                    args=(image_queue,))
        self.capture_thread.start()         # Thread to grab images

    # Fetch camera image from queue, and display it
    def show_image(self, imageq, display, scale):
        if not imageq.empty():
            image = imageq.get()
            if image is not None and len(image) > 0:
                img = image
                # img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB) 
                self.display_image(img, display, scale)

    # Display an image, reduce size if required
    def display_image(self, img, display, scale=1):
        disp_size = img.shape[1]//scale, img.shape[0]//scale
        disp_bpl = disp_size[0] * 3
        if scale > 1:
            img = cv2.resize(img, disp_size, 
                             interpolation=cv2.INTER_CUBIC)
        qimg = QImage(img.data, disp_size[0], disp_size[1], 
                      disp_bpl, IMG_FORMAT)
        display.setImage(qimg)

    # Handle sys.stdout.write: update text display
    def write(self, text):
        self.text_update.emit(str(text))
    def flush(self):
        pass

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

    # Window is closing: stop video capture
    def closeEvent(self, event):
        global capturing
        capturing = False
        self.capture_thread.join()

    def message(self, s):
        self.text.appendPlainText(s)

    def click_run(self):
        print('run clicked')
        sys.exit()

    def process_finished(self):
        self.message("Process finished.")
        self.p = None


    def click_stop(self):
        print('stop clicked')
        global camera_run
        camera_run = False
        self.capture_thread.join()

# def main():
#     camera_work(image_queue)
#     print("here!!")
#     print(image_queue.qsize())

# if __name__ == '__main__':
#     if main():
#         sys.exit(0)
#     else:
#         sys.exit(1)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        try:
            camera_num = int(sys.argv[1])
        except:
            camera_num = 0
    if camera_num < 1:
        print("Invalid camera number '%s'" % sys.argv[1])
    else:
        app = QApplication(sys.argv)
        win = MyWindow()
        win.show()
        win.start()
        sys.exit(app.exec_())


