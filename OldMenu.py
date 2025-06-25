# CE MENU A ETE FAIT PAR CHATGPT POUR AVOIR UNE BASE!!!

import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
from editor.editor_main import EditorWindow
from game.game_main import GameWindow
from PySide6.QtWidgets import QFileDialog
import winreg
import os

dark_style = """
    QWidget {
        background-color: #121212;
        color: #e0e0e0;
        selection-background-color: #007acc;
        selection-color: #ffffff;
    }
    QPushButton {
        background-color: #1f1f1f;
        border: 1px solid #333;
        padding: 5px;
        border-radius: 3px;
    }
    QPushButton:hover {
        background-color: #333333;
    }
    QLabel {
        color: #e0e0e0;
    }
    QListWidget {
        background-color: #1e1e1e;
        border: 1px solid #333;
        color: #e0e0e0;
    }
    QLineEdit, QTextEdit {
        background-color: #1e1e1e;
        color: #e0e0e0;
        border: 1px solid #333;
    }
"""


def associate_pyfnf_with_app():
    ext = ".pyfnf"
    prog_id = "PyFnFFile"
    app_path = sys.executable

    if getattr(sys, 'frozen', False):
        base_dir = sys._MEIPASS  # Si packagé en exe
    else:
        base_dir = os.path.abspath(os.path.dirname(__file__))

    icon_path = os.path.join(base_dir, "data", "assets", "icon.ico")
    icon_path = os.path.abspath(icon_path)

    command = f'"{app_path}" "%1"'

    try:
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"Software\\Classes\\{ext}") as ext_key:
            winreg.SetValue(ext_key, "", winreg.REG_SZ, prog_id)

        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"Software\\Classes\\{prog_id}") as prog_key:
            winreg.SetValue(prog_key, "", winreg.REG_SZ, "PyFnF Game")

            with winreg.CreateKey(prog_key, "DefaultIcon") as icon_key:
                winreg.SetValue(icon_key, "", winreg.REG_SZ, icon_path + ",0")

            with winreg.CreateKey(prog_key, r"shell\open\command") as cmd_key:
                winreg.SetValue(cmd_key, "", winreg.REG_SZ, command)

        print(f"Association {ext} créée avec succès.")
    except Exception as e:
        print(f"Erreur lors de l'association: {e}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyFNF")

        self.editor_window = None
        self.game_window = None

        layout = QVBoxLayout()

        play_button = QPushButton("🎮 Lancer le jeu")
        editor_button = QPushButton("🎼 Lancer l'éditeur")

        play_button.clicked.connect(self.launch_game)
        editor_button.clicked.connect(self.launch_editor)

        layout.addWidget(play_button)
        layout.addWidget(editor_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def launch_editor(self):
        self.editor_window = EditorWindow()
        self.editor_window.show()

    def launch_game(self):
        path, _ = QFileDialog.getOpenFileName(self, "Charger une map", "", "*.pyfnf")
        if path:
            self.game_window = GameWindow(path)
            self.game_window.show()

if __name__ == "__main__":
    associate_pyfnf_with_app()
    app = QApplication(sys.argv)
    app.setStyleSheet(dark_style)

    if len(sys.argv) > 1 and sys.argv[1].endswith(".pyfnf"):
        from game.game_main import GameWindow
        window = GameWindow(sys.argv[1])
    else:
        window = MainWindow()

    window.resize(300, 200)
    window.show()
    sys.exit(app.exec())

