import sys
import treinamento
from PyQt5.QtWidgets import QApplication
from interface import App

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = App()
    print(f"id_to_info: {treinamento.id_to_info}")
    win.show()
    sys.exit(app.exec_())