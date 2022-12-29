#include <QtWidgets/QApplication>

#include "Viewer.h"
#include"ImageGrabber.h"

#include <QtCore>
#include <QDebug>

int main(int argc, char *argv[])
{

	// Retrieve singleton reference to system object
	

	QApplication a(argc, argv);

	Viewer mViewer;
	mViewer.show();


    return a.exec();
}
