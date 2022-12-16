import os
import PySpin
import sys
import time
import base64
import numpy as np
import serial
import matplotlib.pyplot as plt
import keyboard

# NUM_IMAGES = 5  # number of images to grab

#added for swith control vars
port = 'COM3'
ser = serial.Serial(port, 9600, timeout=1)

hex_string1 = """A0 01 01 A2"""  #turn on str
some_bytes1 = bytearray.fromhex(hex_string1)
hex_string2 = """A0 01 00 A1"""  #turn off str
some_bytes2 = bytearray.fromhex(hex_string2)


#added 11/8
# img_data_array = []

#added 11/15
N = 600
img_data_array = np.zeros((N,480,640))

#added 11/9
camera_run = True





def acquire_images(cam, nodemap, nodemap_tldevice):
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
        # for i in range(NUM_IMAGES):
            try:
                image_result = cam.GetNextImage(1000)
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


                    img_data = image_result.GetNDArray()
                    # img_data_array.append(img_data)
                    # print(type(img_data))
                    img_data_array[i] = img_data
                    print(len(img_data_array))



                    plt.imshow(img_data, cmap='gray')
                    # plt.pause(0.001)
                    plt.clf()

                    if keyboard.is_pressed('ENTER'):
                        print('Program is closing...')

                        # Close figure
                        plt.close('all')
                        input('Done! Press Enter to exit...')
                        camera_run = False

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
                    # image_result.Release()
                    # print('')

                    #added
                    # with open(filename, "rb") as f:
                    #     png_encoded = base64.b64encode(f.read())
                    #
                    # encoded_b2 = "".join([format(n, '08b') for n in png_encoded])
                    # text_file = open("data.txt", "w")
                    # text_file.write(encoded_b2)
                    # text_file.close


                    i = i + 1
                    diff_time = time.time() - start_time
                    if (diff_time >= 1 and diff_time < 10):
                        ser.write(some_bytes1)
                    elif (diff_time >= 10 and diff_time < 20):
                        ser.write(some_bytes2)
                    elif (diff_time >= 20):
                        camera_run = False


            except PySpin.SpinnakerException as ex:
                print('Error: %s' % ex)
                return False
        cam.EndAcquisition()

    except PySpin.SpinnakerException as ex:
        print('Error: %s' % ex)
        return False


    #added for save to text_file
    # https://www.geeksforgeeks.org/how-to-load-and-save-3d-numpy-array-to-file-using-savetxt-and-loadtxt-functions/
    print("reached")
    array_reshaped = img_data_array.reshape(img_data_array.shape[0], -1)
    print("reached_2")
    # file = open("img_data.txt", "w+")
    # content = str(array_reshaped)
    # file.write(content)
    # file.close()
    np.savetxt("imgs_data.txt", array_reshaped)

    print(len(img_data_array))
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

def run_single_camera(cam):

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
        result &= acquire_images(cam, nodemap, nodemap_tldevice)

        # Deinitialize camera
        cam.DeInit()

    except PySpin.SpinnakerException as ex:
        print('Error: %s' % ex)
        result = False

    return result


def main():
    """
    Example entry point; please see Enumeration example for more in-depth
    comments on preparing and cleaning up the system.

    :return: True if successful, False otherwise.
    :rtype: bool
    """

    # Since this application saves images in the current folder
    # we must ensure that we have permission to write to this folder.
    # If we do not have permission, fail right away.
    try:
        test_file = open('test.txt', 'w+')
    except IOError:
        print('Unable to write to current directory. Please check permissions.')
        input('Press Enter to exit...')
        return False

    test_file.close()
    os.remove(test_file.name)

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

        result &= run_single_camera(cam)
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

if __name__ == '__main__':
    if main():
        sys.exit(0)
    else:
        sys.exit(1)
