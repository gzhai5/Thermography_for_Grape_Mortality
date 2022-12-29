#include "ImageGrabber.h"

ImageGrabber::ImageGrabber(QObject *parent) :
	QThread(parent),STOP(false),isRecording(false), cntIdx(0)
{
	connect(this, SIGNAL(imageUpdated(int)), parent, SLOT(on_imageUpdated(int)));

	// Set default image processor color processing method
	processor.SetColorProcessing(HQ_LINEAR);
}

void ImageGrabber::StopRun()
{
	QMutex mutex; 
	mutex.lock();
	STOP = true;
	mutex.unlock();
}

void ImageGrabber::StartRecord(int num)
{
	
	tgtNum = num; // Set target number of images recorded
	cntIdx = 0; // Init current image idx to be 0

	// Set mode to be recording
	QMutex mutex; 
	mutex.lock();
	isRecording = true;
	mutex.unlock();
}


void ImageGrabber::run()
{

	qDebug() << " mGrabber is running";
	this->sleep(1);
	
	/**** Init System, Check Camera Number ****/
	RetrieveSystemCam();
	const unsigned int numCameras = camList.GetSize();
	qDebug() << "Number of cameras detected: " << camList.GetSize();
	// Finish if there are no cameras or more than one camera, currently just consider single camera
	if (numCameras != 1)
	{
		qDebug() << "Not enough cameras or Too many cameras ";
		ReleaseSystemCam();
		return;
	}


	/**** Run Camera ****/
	// Get camera pointer
	pCam = camList.GetByIndex(0); 

	// Init camera
	int result;
	try
	{
		// Retrieve TL device nodemap and print device information
		INodeMap& nodeMapTLDevice = pCam->GetTLDeviceNodeMap();
		result = PrintDeviceInfo(nodeMapTLDevice);

		// Initialize camera
		pCam->Init();

		// Retrieve GenICam nodemap
		INodeMap& nodeMap = pCam->GetNodeMap();

		// Set camera mode to be continuous
		result = result | SetCameraMode(nodeMap, nodeMapTLDevice);

		// Check whether initialization success
		if (result != 0)
		{
			qDebug() << "Camera Init Failed";
			return;
		}
	}
	catch(Spinnaker::Exception& e)
	{
		cout << "Error: " << e.what() << endl;
		return;
	}
	
	/**** Acquire Images ****/
	while (result == 0)
	{
		try
		{
			// Check State
			QMutex mutex;  // prevent other threads from changing the "Stop" value
			mutex.lock();
			if (this->STOP)
			{
				// End acquisition
				pCam->EndAcquisition();
				// End while loop
				break;
			}
			mutex.unlock();

			result = AcquireSingleImage(cntIdx);

			mutex.lock();
			if (this->isRecording && cntIdx < tgtNum)
			{
				cntIdx += 1;
				if (cntIdx == 10)
				{
					this->isRecording = false;
					cntIdx = 0;
					qDebug() << endl << "*** Record Finished ***"<< endl;
				}
			}
			mutex.unlock();

		}
		catch (Spinnaker::Exception& e)
		{
			cout << "Error: " << e.what() << endl;
			return;
		}

	}

	// Deinitialize camera
	pCam->DeInit();
	ReleaseSystemCam();

}



void ImageGrabber::RetrieveSystemCam()
{
	qDebug() << "Init system and camera list...";

	// Retrieve singleton reference to system object
	system = System::GetInstance();
	// Retrieve list of cameras from the system
	camList = system->GetCameras();
	// Create shared pointer to camera
	pCam = nullptr;
}


void ImageGrabber::ReleaseSystemCam()
{
	qDebug() << "Exit...";

	// Release reference to the camera
	pCam = nullptr;
	// Clear camera list before releasing system
	camList.Clear();
	// Release system
	system->ReleaseInstance();

	qDebug() << "Camera list cleared, System released.";
}


int ImageGrabber::SetCameraMode(INodeMap& nodeMap, INodeMap& nodeMapTLDevice)
{
	int result = 0;
	try
	{

		//
		// Set acquisition mode to continuous
		//

		// Retrieve enumeration node from nodemap
		CEnumerationPtr ptrAcquisitionMode = nodeMap.GetNode("AcquisitionMode");
		if (!IsAvailable(ptrAcquisitionMode) || !IsWritable(ptrAcquisitionMode))
		{
			qDebug() << "Unable to set acquisition mode to continuous (enum retrieval). Aborting..." << endl << endl;
			return -1;
		}

		// Retrieve entry node from enumeration node
		CEnumEntryPtr ptrAcquisitionModeContinuous = ptrAcquisitionMode->GetEntryByName("Continuous");
		if (!IsAvailable(ptrAcquisitionModeContinuous) || !IsReadable(ptrAcquisitionModeContinuous))
		{
			qDebug() << "Unable to set acquisition mode to continuous (entry retrieval). Aborting..." << endl << endl;
			return -1;
		}

		// Retrieve integer value from entry node
		const int64_t acquisitionModeContinuous = ptrAcquisitionModeContinuous->GetValue();

		// Set integer value from entry node as new value of enumeration node
		ptrAcquisitionMode->SetIntValue(acquisitionModeContinuous);

		qDebug() << "Acquisition mode set to continuous..." << endl;

#ifdef _DEBUG
		qDebug() << endl << endl << "*** DEBUG ***" << endl << endl;

		// If using a GEV camera and debugging, should disable heartbeat first to prevent further issues
		if (DisableHeartbeat(nodeMap, nodeMapTLDevice) != 0)
		{
			return -1;
		}

		qDebug() << endl << endl << "*** END OF DEBUG ***" << endl << endl;
#endif

		//
		// Retrieve device serial number for filename
		//
		// *** NOTES ***
		// The device serial number is retrieved in order to keep cameras from
		// overwriting one another. Grabbing image IDs could also accomplish
		// this.
		//
		CStringPtr ptrStringSerial = nodeMapTLDevice.GetNode("DeviceSerialNumber");
		if (IsAvailable(ptrStringSerial) && IsReadable(ptrStringSerial))
		{
			deviceSerialNumber = ptrStringSerial->GetValue();

			qDebug() << "Device serial number retrieved as " << deviceSerialNumber << "..." << endl;
		}
		qDebug() << endl;


		//
		// Begin acquiring images
		//
		// *** LATER ***
		// Image acquisition must be ended when no more images are needed.
		//
		pCam->BeginAcquisition();
		qDebug() << "***  Acquiring Images ***" << endl;

	}
	catch (Spinnaker::Exception& e)
	{
		qDebug() << "Error: " << e.what() << endl;
		result = -1;
	}
	
	return result;
}


int ImageGrabber::AcquireSingleImage(int imageCnt)
{
	int result = 0;
	try
	{
		//
		// Retrieve next received image
		//
		// *** NOTES ***
		// Capturing an image houses images on the camera buffer. Trying
		// to capture an image that does not exist will hang the camera.
		//
		// *** LATER ***
		// Once an image from the buffer is saved and/or no longer
		// needed, the image must be released in order to keep the
		// buffer from filling up.
		//
		ImagePtr pResultImage = pCam->GetNextImage(1000);

		//
		// Ensure image completion
		//
		// *** NOTES ***
		// Images can easily be checked for completion. This should be
		// done whenever a complete image is expected or required.
		// Further, check image status for a little more insight into
		// why an image is incomplete.
		//
		if (pResultImage->IsIncomplete())
		{
			// Retrieve and print the image status description
			qDebug() << "Image incomplete: " << Image::GetImageStatusDescription(pResultImage->GetImageStatus())
				<< "..." << endl
				<< endl;
		}
		else
		{
			//
			// Print image information; height and width recorded in pixels
			//
			// *** NOTES ***
			// Images have quite a bit of available metadata including
			// things such as CRC, image status, and offset values, to
			// name a few.
			//
			const size_t width = pResultImage->GetWidth();

			const size_t height = pResultImage->GetHeight();

			qDebug() << "Grabbed image " << imageCnt << ", width = " << width << ", height = " << height;

			//
			// Convert image to mono 8
			//
			// *** NOTES ***
			// Images can be converted between pixel formats by using
			// the appropriate enumeration value. Unlike the original
			// image, the converted one does not need to be released as
			// it does not affect the camera buffer.
			//
			// When converting images, color processing algorithm is an
			// optional parameter.
			//
			ImagePtr convertedImage = processor.Convert(pResultImage, PixelFormat_Mono8);

			//
			// Save image
			//
			// *** NOTES ***
			// The standard practice of the examples is to use device
			// serial numbers to keep images of one device from
			// overwriting those of another.
			//
			if (isRecording)
			{
				// Create a unique filename
				ostringstream filename;

				filename << "Acquisition-";
				if (!deviceSerialNumber.empty())
				{
					filename << deviceSerialNumber.c_str() << "-";
				}
				filename << imageCnt << ".jpg";

				// Save image
				convertedImage->Save(filename.str().c_str());

				cout << "Image saved at " << filename.str() << endl;
			}

		}

		//
		// Release image
		//
		// *** NOTES ***
		// Images retrieved directly from the camera (i.e. non-converted
		// images) need to be released in order to keep from filling the
		// buffer.
		//
		pResultImage->Release();

		cout << endl;
	}
	catch (Spinnaker::Exception& e)
	{
		cout << "Error: " << e.what() << endl;
		result = -1;
	}

	return result;

}


// This function prints the device information of the camera from the transport
// layer; please see NodeMapInfo example for more in-depth comments on printing
// device information from the nodemap.
int ImageGrabber::PrintDeviceInfo(INodeMap& nodeMap)
{
	int result = 0;
	qDebug() << endl << "*** DEVICE INFORMATION ***" << endl << endl;

	try
	{
		FeatureList_t features;
		const CCategoryPtr category = nodeMap.GetNode("DeviceInformation");
		if (IsAvailable(category) && IsReadable(category))
		{
			category->GetFeatures(features);

			for (auto it = features.begin(); it != features.end(); ++it)
			{
				const CNodePtr pfeatureNode = *it;
				qDebug() << pfeatureNode->GetName() << " : ";
				CValuePtr pValue = static_cast<CValuePtr>(pfeatureNode);
				qDebug() << (IsReadable(pValue) ? pValue->ToString() : "Node not readable");
				qDebug() << endl;
			}
		}
		else
		{
			qDebug() << "Device control information not available." << endl;
		}
	}
	catch (Spinnaker::Exception& e)
	{
		qDebug() << "Error: " << e.what() << endl;
		result = -1;
	}

	return result;
}


#ifdef _DEBUG
// Disables heartbeat on GEV cameras so debugging does not incur timeout errors
int ImageGrabber::DisableHeartbeat(INodeMap& nodeMap, INodeMap& nodeMapTLDevice)
{
	qDebug() << "Checking device type to see if we need to disable the camera's heartbeat..." << endl << endl;

	//
	// Write to boolean node controlling the camera's heartbeat
	//
	// *** NOTES ***
	// This applies only to GEV cameras and only applies when in DEBUG mode.
	// GEV cameras have a heartbeat built in, but when debugging applications the
	// camera may time out due to its heartbeat. Disabling the heartbeat prevents
	// this timeout from occurring, enabling us to continue with any necessary debugging.
	// This procedure does not affect other types of cameras and will prematurely exit
	// if it determines the device in question is not a GEV camera.
	//
	// *** LATER ***
	// Since we only disable the heartbeat on GEV cameras during debug mode, it is better
	// to power cycle the camera after debugging. A power cycle will reset the camera
	// to its default settings.
	//
	CEnumerationPtr ptrDeviceType = nodeMapTLDevice.GetNode("DeviceType");
	if (!IsAvailable(ptrDeviceType) || !IsReadable(ptrDeviceType))
	{
		qDebug() << "Error with reading the device's type. Aborting..." << endl << endl;
		return -1;
	}
	else
	{
		if (ptrDeviceType->GetIntValue() == DeviceType_GigEVision)
		{
			qDebug() << "Working with a GigE camera. Attempting to disable heartbeat before continuing..." << endl << endl;
			CBooleanPtr ptrDeviceHeartbeat = nodeMap.GetNode("GevGVCPHeartbeatDisable");
			if (!IsAvailable(ptrDeviceHeartbeat) || !IsWritable(ptrDeviceHeartbeat))
			{
				qDebug() << "Unable to disable heartbeat on camera. Continuing with execution as this may be non-fatal..."
					<< endl
					<< endl;
			}
			else
			{
				ptrDeviceHeartbeat->SetValue(true);
				qDebug() << "WARNING: Heartbeat on GigE camera disabled for the rest of Debug Mode." << endl;
				qDebug() << "         Power cycle camera when done debugging to re-enable the heartbeat..." << endl << endl;
			}
		}
		else
		{
			qDebug() << "Camera does not use GigE interface. Resuming normal execution..." << endl << endl;
		}
	}
	return 0;
}
#endif
