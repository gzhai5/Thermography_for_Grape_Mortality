#pragma once

#include "ui_Viewer.h"
#include <QtWidgets/QMainWindow>

#include <iostream>
#include <QPushButton>
#include <QMessageBox>

class Viewer : public QMainWindow
{
    Q_OBJECT

public:
    Viewer(QWidget *parent = nullptr);
    ~Viewer();

private:
    Ui::ViewerClass *ui;

	//// QLabel: hold the image

	//// QPushButtons
	// 1. connect/disconnect to the thermal camera
	// 2. record a series of images
	// 3. adjust the camera focus automatically
	

	//// QLineEdits
	// 1. enter t0, t1, t2
	// 2. set saving path

	//// QTextEdit: print logging infos


};
