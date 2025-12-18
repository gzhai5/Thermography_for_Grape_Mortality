import sys
import argparse
from PyQt5.QtWidgets import QApplication
from gui import MyApp


if __name__ == '__main__':
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run the MyApp application.")
    parser.add_argument('--mode', type=str, help='Mode to run MyApp in: halt, stream, acquire', default='default_mode')
    args = parser.parse_args()

    app = QApplication(sys.argv)
    ex = MyApp(mode=args.mode)
    ex.show()
    sys.exit(app.exec_())