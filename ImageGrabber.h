#pragma once

#include <QtCore>
#include <QDebug>
#include <QThread>

#include <Spinnaker.h>
#include <SpinGenApi/SpinnakerGenApi.h>
#include <iostream>
#include <sstream>

using namespace Spinnaker;
using namespace Spinnaker::GenApi;
using namespace Spinnaker::GenICam;
using namespace std;

class ImageGrabber : public QThread
{
	Q_OBJECT

public:
	ImageGrabber(QObject * parent = 0);

	void run();
	void StopRun(); // STOP = true, break from run(), TODO: should be reset before call run() again 
	void StartRecord(int num);

signals:
	void imageUpdated(int i);

private:

	SystemPtr system;
	CameraList camList;
	CameraPtr pCam;
	ImageProcessor processor;
	gcstring deviceSerialNumber;

	bool STOP;
	bool isRecording;

	int cntIdx; // current image idx
	int tgtNum; // the number of images should be recorded
	
	void RetrieveSystemCam();
	void ReleaseSystemCam();
	int SetCameraMode(INodeMap& nodeMap, INodeMap& nodeMapTLDevice);
	int AcquireSingleImage(int imageCnt = 0);

	int PrintDeviceInfo(INodeMap& nodeMap);
	int DisableHeartbeat(INodeMap& nodeMap, INodeMap& nodeMapTLDevice);

};

