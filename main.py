import sys
import os

os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS", "--disable-gpu")

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

sys.path.insert(0, os.path.dirname(__file__))
from ui.main_window import MainWindow


def main():
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("Rutas Perú — Dijkstra")

    ventana = MainWindow()
    ventana.show()
    ventana.showMaximized()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
