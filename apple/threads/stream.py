from PyQt5.QtCore import QThread, pyqtSignal
import cv2
from PIL import Image
from io import BytesIO
import numpy as np
import PySpin
import keyboard
from params import CHOSEN_IR_TYPE, R, A1, A2, B, F, X, B1, B2, J1, J0, Emiss, TRefl, TAtm, TAtmC, Humidity, Dist, ExtOpticsTransmission, ExtOpticsTemp



class IRFormatType:
    LINEAR_10MK = 1
    LINEAR_100MK = 2
    RADIOMETRIC = 3

CHOSEN_IR_TYPE = IRFormatType.RADIOMETRIC
CONTINUE_RECORDING = True

class StreamingThread(QThread):
    update_image = pyqtSignal(np.ndarray)

    def __init__(self, camera):
        super(StreamingThread, self).__init__()
        self.camera = camera
        self.running = False

    def run(self):
        self.running = True
        while self.running:
            try:
                self.acquire_image()
                break
            except Exception as e:
                print("Error acquiring image: ", e)
    
    def stop(self):
        global CONTINUE_RECORDING
        CONTINUE_RECORDING = False
        self.running = False

    def acquire_image(self):
        # Retrieve singleton reference to system object
        result = True
        system = PySpin.System.GetInstance()

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
            raise Exception('Not enough cameras!')
        
        # Get 1st camera
        cam = cam_list.GetByIndex(0)
        print('Running example for camera %d...' % 1)
        result &= self.run_single_camera(cam)
        print('Camera %d example complete... \n' % 1)

        del cam
        cam_list.Clear()
        system.ReleaseInstance()
        print('Camera %d is cleared and released... \n' % 1)
        raise Exception('Camera is cleared and released... \n')

    def run_single_camera(self, cam):
        try:
            result = True

            nodemap_tldevice = cam.GetTLDeviceNodeMap()

            # Initialize camera
            cam.Init()
            print("camera initlized")

            # Retrieve GenICam nodemap
            nodemap = cam.GetNodeMap()
            print("nodmap got")

            # Acquire images
            result &= self.acquire_and_display_images(cam, nodemap, nodemap_tldevice)

            # Deinitialize camera
            cam.DeInit()

        except PySpin.SpinnakerException as ex:
            print('Error: %s' % ex)
            result = False

        return result
    
    def acquire_and_display_images(self, cam, nodemap, nodemap_tldevice):
        global CONTINUE_RECORDING

        sNodemap = cam.GetTLStreamNodeMap()

        # Change bufferhandling mode to NewestOnly
        node_bufferhandling_mode = PySpin.CEnumerationPtr(sNodemap.GetNode('StreamBufferHandlingMode'))

        node_pixel_format = PySpin.CEnumerationPtr(nodemap.GetNode('PixelFormat'))
        node_pixel_format_mono16 = PySpin.CEnumEntryPtr(node_pixel_format.GetEntryByName('Mono14'))
        pixel_format_mono16 = node_pixel_format_mono16.GetValue()
        node_pixel_format.SetIntValue(pixel_format_mono16)

        node_acquisition_framerate = PySpin.CFloatPtr(nodemap.GetNode('AcquisitionFrameRate'))
        if not PySpin.IsAvailable(node_acquisition_framerate) and not PySpin.IsReadable(node_acquisition_framerate):
            print('Unable to retrieve frame rate. Aborting...')
        else:
            framerate_to_set = node_acquisition_framerate.GetValue()
            print('Frame rate to be set to %d...' % framerate_to_set)

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
            return False

        # Retrieve entry node from enumeration node
        node_newestonly = node_bufferhandling_mode.GetEntryByName('NewestOnly')
        if not PySpin.IsAvailable(node_newestonly) or not PySpin.IsReadable(node_newestonly):
            print('Unable to set stream buffer handling mode.. Aborting...')
            return False

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

            print('Acquiring images...')

            #  Retrieve device serial number for filename
            #
            #  *** NOTES ***
            #  The device serial number is retrieved in order to keep cameras from
            #  overwriting one another. Grabbing image IDs could also accomplish
            #  this.
            device_serial_number = ''
            node_device_serial_number = PySpin.CStringPtr(nodemap_tldevice.GetNode('DeviceSerialNumber'))
            if PySpin.IsAvailable(node_device_serial_number) and PySpin.IsReadable(node_device_serial_number):
                device_serial_number = node_device_serial_number.GetValue()
                print('Device serial number retrieved as %s...' % device_serial_number)

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

            # Retrieve and display images
            print('Begin streaming')
            while(CONTINUE_RECORDING):
                try:

                    #  Retrieve next received image
                    #
                    #  *** NOTES ***
                    #  Capturing an image houses images on the camera buffer. Trying
                    #  to capture an image that does not exist will hang the camera.
                    #
                    #  *** LATER ***
                    #  Once an image from the buffer is saved and/or no longer
                    #  needed, the image must be released in order to keep the
                    #  buffer from filling up.

                    image_result = cam.GetNextImage()

                    #  Ensure image completion
                    if image_result.IsIncomplete():
                        print('Image incomplete with image status %d ...' % image_result.GetImageStatus())

                    else:

                        # Getting the image data as a np array
                        image_data = image_result.GetNDArray()
                        image_data_d = image_data
                        image_data_dt = image_data_d
                        image_data_dt = cv2.normalize(image_data_d,image_data_dt,0,255,cv2.NORM_MINMAX,dtype=cv2.CV_8U)
                        self.update_image.emit(image_data_dt)

                        # if CHOSEN_IR_TYPE == IRFormatType.LINEAR_10MK:
                        #     # Transforming the data array into a temperature array, if streaming mode is set to TemperatueLinear10mK
                        #     image_Temp_Celsius_high = (image_data * 0.01) - 273.15
                        #     print("data", np.mean(image_Temp_Celsius_high))

                        # elif CHOSEN_IR_TYPE == IRFormatType.LINEAR_100MK:
                        #     # Transforming the data array into a temperature array, if streaming mode is set to TemperatureLinear100mK
                        #     image_Temp_Celsius_low = (image_data * 0.1) - 273.15

                        # elif CHOSEN_IR_TYPE == IRFormatType.RADIOMETRIC:
                        #     # Transforming the data array into a pseudo radiance array, if streaming mode is set to Radiometric.
                        #     # and then calculating the temperature array (degrees Celsius) with the full thermography formula
                        #     image_Radiance = (image_data - J0) / J1
                        #     image_Temp = (B / np.log(R / ((image_Radiance / Emiss / Tau) - K2) + F)) - 273.15

                        # If user presses enter, close the program
                        if keyboard.is_pressed('ENTER'):
                            print('Program is closing...')
                            CONTINUE_RECORDING = False

                    #  Release image
                    #
                    #  *** NOTES ***
                    #  Images retrieved directly from the camera (i.e. non-converted
                    #  images) need to be released in order to keep from filling the
                    #  buffer.
                    image_result.Release()

                except PySpin.SpinnakerException as ex:
                    print('Error: %s' % ex)
                    return False

            #  End acquisition
            #
            #  *** NOTES ***
            #  Ending acquisition appropriately helps ensure that devices clean up
            #  properly and do not need to be power-cycled to maintain integrity.
            cam.EndAcquisition()

        except PySpin.SpinnakerException as ex:
            print('Error: %s' % ex)
            return False

        return True
