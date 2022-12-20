#include "Viewer.h"

Viewer::Viewer(QWidget *parent)
    : QMainWindow(parent)
{
    ui->setupUi(this);
	setWindowTitle(tr("Active Thermography System"));
	resize(1080, 720);


}

Viewer::~Viewer()
{
	delete ui;
}
