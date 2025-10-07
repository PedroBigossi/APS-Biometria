import sys
import cv2
import os
import shutil
from PyQt5.QtWidgets import (QApplication, QLabel, QWidget, QVBoxLayout, QPushButton, QLineEdit, QComboBox, QMessageBox, QHBoxLayout, QFileDialog, QInputDialog)  # Adicionei QInputDialog aqui
from PyQt5.QtGui import QImage, QPixmap, QFont
from PyQt5.QtCore import QTimer, Qt, QPoint
from reconhecimento import process_frame, USUARIOS_DIR, NUM_FOTOS_CADASTRO
from treinamento import treinar_automaticamente

class CustomTitleBar(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setFixedHeight(40)
        self.setStyleSheet("background-color: #1e1e2e; border-top-left-radius: 10px; border-top-right-radius: 10px;")
        self.parent = parent
        self.start = QPoint(0, 0)
        self.pressing = False
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(0)
        title = QLabel("Biometria Facial Avançada")
        title.setStyleSheet("color: #cdd6f4; font-size: 14px; font-weight: bold;")
        layout.addWidget(title)
        layout.addStretch()
        self.minimize_btn = QPushButton("—")
        self.maximize_btn = QPushButton("□")
        self.close_btn = QPushButton("✕")
        for btn in (self.minimize_btn, self.maximize_btn, self.close_btn):
            btn.setFixedSize(30, 30)
            btn.setStyleSheet("""
                QPushButton {
                    color: #cdd6f4; 
                    background-color: #2a2a3c; 
                    border: none; 
                    border-radius: 5px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #3b3b4f;
                }
                QPushButton:pressed {
                    background-color: #1e1e2e;
                }
            """)
        self.close_btn.setStyleSheet(self.close_btn.styleSheet() + "QPushButton:hover { background-color: #ef4444; }")
        self.minimize_btn.clicked.connect(self.parent.showMinimized)
        self.maximize_btn.clicked.connect(self.toggle_maximize)
        self.close_btn.clicked.connect(self.parent.close)
        layout.addWidget(self.minimize_btn)
        layout.addWidget(self.maximize_btn)
        layout.addWidget(self.close_btn)
        self.setLayout(layout)

    def toggle_maximize(self):
        if self.parent.isMaximized():
            self.parent.showNormal()
            self.maximize_btn.setText("□")
        else:
            self.parent.showMaximized()
            self.maximize_btn.setText("❐")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.pressing = True
            self.start = event.globalPos() - self.parent.pos()

    def mouseMoveEvent(self, event):
        if self.pressing:
            self.parent.move(event.globalPos() - self.start)

    def mouseReleaseEvent(self, event):
        self.pressing = False

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Biometria Facial Avançada")
        self.resize(800, 650)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e2e;
                color: #cdd6f4;
                font-family: 'Arial';
            }
            QLineEdit {
                background-color: #2a2a3c;
                color: #cdd6f4;
                border: 1px solid #3b3b4f;
                border-radius: 5px;
                padding: 8px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #89b4fa;
            }
            QComboBox {
                background-color: #2a2a3c;
                color: #cdd6f4;
                border: 1px solid #3b3b4f;
                border-radius: 5px;
                padding: 8px;
                font-size: 14px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
            }
            QComboBox QAbstractItemView {
                background-color: #2a2a3c;
                color: #cdd6f4;
                selection-background-color: #89b4fa;
            }
            QPushButton {
                background-color: #89b4fa;
                color: #1e1e2e;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #b4cffa;
            }
            QPushButton:pressed {
                background-color: #6b8ed5;
            }
        """)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        self.title_bar = CustomTitleBar(self)
        main_layout.addWidget(self.title_bar)
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("background-color: #2a2a3c; border-radius: 10px;")
        self.input_nome = QLineEdit(self)
        self.input_nome.setPlaceholderText("Digite o nome")
        self.combo_nivel = QComboBox(self)
        self.combo_nivel.addItems(["1 - Nível 1", "2 - Nível 2", "3 - Nível 3"])
        self.btn_cadastrar = QPushButton("Cadastrar Usuário", self)
        self.btn_reconhecer = QPushButton("Reconhecer", self)
        self.btn_remover = QPushButton("Remover Usuário", self)  # Novo botão
        main_layout.addWidget(self.label)
        main_layout.addWidget(self.input_nome)
        main_layout.addWidget(self.combo_nivel)
        main_layout.addWidget(self.btn_cadastrar)
        main_layout.addWidget(self.btn_reconhecer)
        main_layout.addWidget(self.btn_remover)  # Adiciona o botão
        self.setLayout(main_layout)
        self.cap = cv2.VideoCapture(0)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(50)
        self.cadastrando = False
        self.reconhecendo = False
        self.count = 0
        self.nome_atual = None
        self.pasta_atual = None
        self.nivel_atual = 1
        self.id_colors = {}
        self.btn_cadastrar.clicked.connect(self.start_cadastro)
        self.btn_reconhecer.clicked.connect(self.start_reconhecimento)
        self.btn_remover.clicked.connect(self.remover_usuario)  # Conecta o novo botão

    def start_cadastro(self):
        nome = self.input_nome.text().strip()
        if not nome:
            QMessageBox.warning(self, "Erro", "Digite um nome válido!")
            return
        nivel = int(self.combo_nivel.currentText().split(" ")[0])
        self.nome_atual = nome
        self.nivel_atual = nivel
        self.pasta_atual = os.path.join(USUARIOS_DIR, nome)
        if not os.path.exists(self.pasta_atual):
            os.makedirs(self.pasta_atual)
        with open(os.path.join(self.pasta_atual, "info.txt"), "w") as f:
            f.write(str(nivel))
        self.count = 0
        self.cadastrando = True
        self.reconhecendo = False
        QMessageBox.information(self, "Info", f"Cadastro iniciado para {nome}! Para melhor precisão, capture fotos de frente, com e sem óculos, e vire levemente o rosto durante as capturas.")

    def start_reconhecimento(self):
        from treinamento import id_to_info
        if not id_to_info:
            QMessageBox.warning(self, "Erro", "Nenhum usuário cadastrado!")
            return
        self.reconhecendo = True
        self.cadastrando = False
        QMessageBox.information(self, "Info", "Reconhecimento iniciado!")

    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return
        frame, self.count, self.cadastrando = process_frame(
            frame, self.cadastrando, self.reconhecendo, self.count,
            self.pasta_atual, self.nome_atual, NUM_FOTOS_CADASTRO, self.id_colors
        )
        if self.count >= NUM_FOTOS_CADASTRO and self.cadastrando:
            self.cadastrando = False
            treinar_automaticamente()
            QMessageBox.information(self, "Info", f"Cadastro finalizado para {self.nome_atual}!")
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        bytes_per_line = ch * w
        qimg = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.label.setPixmap(QPixmap.fromImage(qimg))

    def upload_foto(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Selecionar Foto", "", "Imagens (*.png *.jpg *.jpeg)")
        if file_name:
            nome = self.input_nome.text().strip()
            if not nome:
                QMessageBox.warning(self, "Erro", "Digite um nome válido!")
                return
            nivel = int(self.combo_nivel.currentText().split(" ")[0])
            pasta_atual = os.path.join(USUARIOS_DIR, nome)
            if not os.path.exists(pasta_atual):
                os.makedirs(pasta_atual)
            with open(os.path.join(pasta_atual, "info.txt"), "w") as f:
                f.write(str(nivel))
            import shutil
            count = len(os.listdir(pasta_atual)) - 1  # Subtrai 1 por causa do info.txt
            new_path = os.path.join(pasta_atual, f"{nome}_{count + 1}.jpg")
            shutil.copy(file_name, new_path)
            QMessageBox.information(self, "Sucesso", f"Foto enviada para {nome}!")
            treinar_automaticamente()  # Re-treina após upload

    def remover_usuario(self):
        from treinamento import id_to_info
        if not id_to_info:
            QMessageBox.warning(self, "Erro", "Nenhum usuário cadastrado!")
            return
        usuarios = list(id_to_info.keys())
        nomes = [info[0] for info in id_to_info.values()]
        nome, ok = QInputDialog.getItem(self, "Remover Usuário", "Selecione o usuário para remover:", nomes, 0, False)
        if ok and nome:
            pasta = os.path.join(USUARIOS_DIR, nome)
            if os.path.exists(pasta):
                shutil.rmtree(pasta)
                treinar_automaticamente()  # Re-treina após remoção
                QMessageBox.information(self, "Sucesso", f"Usuário {nome} removido com sucesso!")
            else:
                QMessageBox.warning(self, "Erro", f"Pasta de {nome} não encontrada!")

    def closeEvent(self, event):
        self.cap.release()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = App()
    win.show()
    sys.exit(app.exec_())