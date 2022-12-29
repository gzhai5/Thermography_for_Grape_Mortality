#include "Viewer.h"

Viewer::Viewer(QWidget *parent)
    : QMainWindow(parent)
{
    ui->setupUi(this);
	setWindowTitle(tr("Active Thermography System"));
	resize(1080, 720);

	/* Init */
	ui->label->setText(QString::number(100));
	ui->imageLabel->resize(480, 360);
	ui->imageLabel->setStyleSheet("QLabel { background-color : white; color : black; }");
	
	/* QThread: imageGrabber */
	// connect function should be in child class
	mGrabber = new ImageGrabber(this);
	//connect(mGrabber, SIGNAL(imageUpdated(int)), this, SLOT(on_ImageUpdated(int))); // optional
	connect(this, SIGNAL(testSignal(int)), this, SLOT(on_imageUpdated(int)));

	/* QPushButton Connect Functions */
	//these functions are autoconnected, so comment them out; 
	// o.w. the slot functions will run twice
	//connect(ui->connectButton, SIGNAL(clicked()), this, SLOT(on_connectButton_clicked()));
	//connect(ui->testButton, SIGNAL(clicked()), this, SLOT(on_testButton_clicked()));
	//connect(ui->stopButton, SIGNAL(clicked()), this, SLOT(on_stopButton_clicked()));
	//connect(ui->exitButton, SIGNAL(clicked()), this, SLOT(on_exitButton_clicked()));

}

Viewer::~Viewer()
{
	delete ui;
	delete mGrabber;
}

void Viewer::on_imageUpdated(int idx, QPixmap &img)
{
	ui->label->setText(QString::number(idx));

}

void Viewer::on_connectButton_clicked()
{
	// start the thread
	qDebug() << endl << "*** Start Thread ***";
	ui->label->setText(QString::number(9999));
	mGrabber->start();
}


void Viewer::on_testButton_clicked()
{
	qDebug() << endl << "*** Start Record ***";
	mGrabber->StartRecord(10);
}

void Viewer::on_stopButton_clicked()
{
	mGrabber->StopRun();
}


void Viewer::on_exitButton_clicked()
{
	QApplication::exit();
}
