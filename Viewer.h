#pragma once

#include "ui_Viewer.h"
#include <QtWidgets/QMainWindow>

#include <iostream>
#include <QtCore>
#include <QtGui>
#include <QString>
#include <QMessageBox>

#include "ImageGrabber.h"
#include "MyThread.h"

class AA
{
public:
	int num;
};
class Viewer : public QMainWindow
{
    Q_OBJECT

public:
    Viewer(QWidget *parent = nullptr);
	~Viewer();

private:
    Ui::ViewerClass *ui;
	ImageGrabber *mGrabber;

	//// QLabel: hold the image

	//// QPushButtons: 
	// 1. connect/disconnect to the thermal camera
	// 2. record a series of images
	// 3. adjust the camera focus automatically
	

	//// QLineEdits
	// 1. enter t0, t1, t2
	// 2. set saving path

	//// QTextEdit: print logging infos

public slots:
	void on_imageUpdated(int idx, QPixmap &img);


private slots:
	void on_connectButton_clicked();
	void on_testButton_clicked();
	void on_stopButton_clicked();
	void on_exitButton_clicked();

signals:
	void testSignal(int i);

};
