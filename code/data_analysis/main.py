import sys
from PyQt5 import QtWidgets
from app_window import ThermalAnalysisApp

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    main_window = ThermalAnalysisApp()
    main_window.show()
    sys.exit(app.exec_())