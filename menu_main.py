import json
import os
import zipfile
import shutil

from PySide6.QtWidgets import (
    QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QApplication,
    QSlider, QCheckBox, QStackedWidget, QFileDialog, QComboBox, QMessageBox
)
from PySide6.QtGui import QFont, QCursor, QKeySequence
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, Signal, QEvent
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput, QSoundEffect
from PySide6.QtCore import QUrl
from editor.editor_main import EditorWindow
import sys
from game.game_main import GameWindow
from PySide6.QtGui import QMovie
from PySide6.QtCore import QObject
from PySide6.QtCore import QPropertyAnimation, QRect
from PySide6.QtGui import QFontDatabase, QFont
from pypresence import Presence
import time
import threading
import winreg

rpc = None

app = QApplication([])

font_path = os.path.join("data", "assets", "Quicksand-Bold.ttf")
font_id = QFontDatabase.addApplicationFont(font_path)
if font_id == -1:
    print("Erreur : la police n'a pas pu être chargée")
else:
    families = QFontDatabase.applicationFontFamilies(font_id)
    if families:
        font_family = families[0]
        app.setFont(QFont(font_family))

CONFIG_PATH = "config.json"

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
        transition: all 0.3s ease;
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
    
    QComboBox {
    background-color: #222;
    border: 1px solid #00e676;
    border-radius: 6px;
    padding: 5px 10px;
    color: #00e676;
    min-height: 28px;
    font-size: 16px;
}

QComboBox:hover {
    background-color: #00e676;
    color: #121212;
}

QComboBox::drop-down {
    border-left: 1px solid #00e676;
    width: 25px;
    background: #00e676;
}

QComboBox::down-arrow {
    image: url(:/data/assets/dropicon.png);
    width: 12px;
    height: 12px;
}

QComboBox QAbstractItemView {
    background-color: #222;
    border: 1px solid #00e676;
    selection-background-color: #00b359;
    color: #e0e0e0;
    font-size: 14px;
} 

* {
  font-family: "Quicksand";
}
  
"""


rpc = None
start_time = time.time()

def start_rich_presence():
    def run():
        global rpc
        try:
            rpc = Presence("1387098477997195364")
            rpc.connect()
            update_status("menu")
            print("[RichPresence] Connecté")
        except Exception as e:
            print(f"[RichPresence] Erreur : {e}")
    threading.Thread(target=run, daemon=True).start()

def update_status(state):
    global rpc, start_time
    if not rpc:
        print("[RichPresence] Pas connecté")
        return
    try:
        print(f"[RichPresence] Mise à jour status : {state}")
        if state == "menu":
            rpc.update(
                state="Focusing on the game!",
                details="Playing PyFNF 1.5",
                large_image="logo",
                large_text="PyFNF",
                start=start_time
            )
        elif state == "editor":
            rpc.update(
                state="In the editor",
                details="Creating a map",
                large_image="logo",
                large_text="PyFNF Editor",
                start=start_time
            )
        elif state == "game":
            rpc.update(
                state="Playing a map",
                details="Tapping Arrows",
                large_image="logo",
                large_text="PyFNF Game",
                start=start_time
            )
    except Exception as e:
        print(f"[RichPresence] update_status error : {e}")

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


def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    return {}

def save_config(config):
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=4)

class AnimatedLabel(QLabel):
    def __init__(self, text):
        super().__init__(text)
        self.setFont(QFont("Arial", 48, QFont.Bold))
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("color: #00e676;")
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(2000)
        self.anim.setStartValue(0)
        self.anim.setEndValue(1)
        self.anim.setEasingCurve(QEasingCurve.OutBounce)
        self.anim.start()

class MenuButton(QPushButton):
    def __init__(self, text, sound_effects=None):
        super().__init__(text)
        self.setFixedSize(200, 50)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setStyleSheet("""
            QPushButton {
                background-color: #222;
                color: #00e676;
                border-radius: 10px;
                border: 2px solid #00e676;
                font-size: 18px;
                font-weight: bold;
                transition: all 0.3s ease;
            }
            QPushButton:hover {
                background-color: #00e676;
                color: #111;
                transform: scale(1.05);
                box-shadow: 0 0 8px #00ff88;
            }
            QPushButton:pressed {
                background-color: #00b359;
                transform: scale(0.95);
            }
        """)
        self.sound_effects = sound_effects or {}
        self.installEventFilter(self)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Enter:
            if 'hover' in self.sound_effects:
                self.sound_effects['hover'].play()
        elif event.type() == QEvent.MouseButtonPress:
            if 'click' in self.sound_effects:
                self.sound_effects['click'].play()
        return super().eventFilter(obj, event)

class MenuWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyFNF - Menu")
        self.setFixedSize(1000, 800)

        self.bg_label = QLabel(self)
        self.bg_label.setGeometry(0, 0, 800, 600)

        gif_path = os.path.join(os.path.dirname(__file__), "data", "assets", "menu_background.gif")
        self.movie = QMovie(gif_path)
        self.bg_label.setMovie(self.movie)
        self.movie.start()
        self.bg_label.lower()  # en arrière-plan
        if not self.movie.isValid():
            print("Erreur: GIF non chargé !")

class TutorialPopup(QMessageBox):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tutoriel PyFNF")
        self.setText(
            "Bienvenue dans PyFNF !\n\n"
            "- Utilise les flèches pour jouer.\n"
            "- Essaie de suivre le rythme.\n"
            "- Tu peux modifier les touches dans les options.\n"
            "- Amuse-toi bien !"
        )
        self.setStandardButtons(QMessageBox.Ok)

class CreditsPopup(QMessageBox):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Crédits")
        self.setText(
            "PyFNF\n\n"
            "Développeur: Bowser-2077\n"
            "Musique: Pixabay, MyInstants\n"
            "Graphismes: Some websites with images (vecteezy, freepik)\n"
            "\nThanks for playing!"
        )
        self.setStandardButtons(QMessageBox.Ok)

class OptionsMenu(QWidget):
    volume_changed = Signal(int)
    fullscreen_toggled = Signal(bool)
    difficulty_changed = Signal(str)
    effects_toggled = Signal(bool)
    theme_changed = Signal(str)
    notespeed_changed = Signal(int)
    language_changed = Signal(str)
    keybinding_changed = Signal(str, int)  # action, key code

    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.setStyleSheet("""
            QWidget {
                background-color: #121212;
                color: #e0e0e0;
                font-family: Arial, sans-serif;
            }
            QSlider::groove:horizontal {
                border: 1px solid #444; height: 8px;
                background: #222; border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #00e676; border: 1px solid #00b359;
                width: 18px; height: 18px; margin: -5px 0;
                border-radius: 9px;
            }
            QSlider::handle:horizontal:hover {
                background: #00ff88; border: 1px solid #00cc66;
            }
            QComboBox {
                background-color: #222; border: 1px solid #00e676;
                border-radius: 6px; padding: 5px 10px;
                color: #00e676; min-height: 28px; font-size: 16px;
            }
            QComboBox:hover { background-color: #00e676; color: #121212; }
            QComboBox QAbstractItemView {
                background-color: #222; border: 1px solid #00e676;
                selection-background-color: #00b359; color: #e0e0e0;
            }
            QCheckBox {
                spacing: 8px; font-size: 16px;
            }
            QCheckBox::indicator {
                width: 18px; height: 18px;
                border: 1px solid #00e676;
                border-radius: 4px;
                background: #222;
            }
            QCheckBox::indicator:hover { border: 1px solid #00ff88; }
            QCheckBox::indicator:checked {
                background-color: #00e676;
                border: 1px solid #00b359;
            }
            QCheckBox::indicator:checked:hover {
                background-color: #00ff88;
                border: 1px solid #00cc66;
            }
        """)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        title = QLabel("Options")
        title.setFont(QFont("Arial", 32, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #00e676;")
        layout.addWidget(title)

        # Volume
        vol_layout = QHBoxLayout()
        vol_layout.addWidget(QLabel("Volume", styleSheet="font-size:16px"))
        self.vol_slider = QSlider(Qt.Horizontal)
        self.vol_slider.setRange(0, 100)
        self.vol_slider.setValue(self.config.get("volume", 50))
        self.vol_slider.valueChanged.connect(self.handle_volume)
        vol_layout.addWidget(self.vol_slider)
        layout.addLayout(vol_layout)

        # Fullscreen
        self.fullscreen_checkbox = QCheckBox("Plein écran")
        self.fullscreen_checkbox.setChecked(self.config.get("fullscreen", False))
        self.fullscreen_checkbox.toggled.connect(self.handle_fullscreen)
        layout.addWidget(self.fullscreen_checkbox)

        # Difficulty
        diff_layout = QHBoxLayout()
        diff_layout.addWidget(QLabel("Difficulté", styleSheet="font-size:16px"))
        self.diff_combo = QComboBox()
        self.diff_combo.addItems(["Easy", "Normal", "Hard"])
        self.diff_combo.setCurrentText(self.config.get("difficulty", "Normal"))
        self.diff_combo.currentTextChanged.connect(self.handle_difficulty)
        diff_layout.addWidget(self.diff_combo)
        layout.addLayout(diff_layout)

        # Visual effects
        self.effects_checkbox = QCheckBox("Effets visuels")
        self.effects_checkbox.setChecked(self.config.get("effects", True))
        self.effects_checkbox.toggled.connect(self.handle_effects)
        layout.addWidget(self.effects_checkbox)

        # Theme
        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel("Thème", styleSheet="font-size:16px"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light"])
        self.theme_combo.setCurrentText(self.config.get("theme", "Dark"))
        self.theme_combo.currentTextChanged.connect(self.handle_theme)
        theme_layout.addWidget(self.theme_combo)
        layout.addLayout(theme_layout)

        # Note speed
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("Vitesse des notes", styleSheet="font-size:16px"))
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(100, 800)
        self.speed_slider.setValue(self.config.get("notespeed", 300))
        self.speed_slider.valueChanged.connect(self.handle_speed)
        speed_layout.addWidget(self.speed_slider)
        layout.addLayout(speed_layout)

        # Language
        lang_layout = QHBoxLayout()
        lang_layout.addWidget(QLabel("Langue", styleSheet="font-size:16px"))
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["fr", "en"])
        self.lang_combo.setCurrentText(self.config.get("language", "fr"))
        self.lang_combo.currentTextChanged.connect(self.handle_language)
        lang_layout.addWidget(self.lang_combo)
        layout.addLayout(lang_layout)

        # Personnalisation des touches
        keybind_title = QLabel("Personnalisation des touches")
        keybind_title.setFont(QFont("Arial", 20, QFont.Bold))
        keybind_title.setStyleSheet("color: #00e676; margin-top: 15px;")
        layout.addWidget(keybind_title)

        self.keybind_buttons = {}
        actions = {
            "Gauche": "left",
            "Droite": "right",
            "Haut": "up",
            "Bas": "down"
        }

        for name, key in actions.items():
            key_name = self.get_key_name(self.config.get(f"key_{key}", None))
            btn = QPushButton(f"{name}: {key_name}")
            btn.setFixedHeight(35)
            btn.clicked.connect(lambda checked, a=key, b=btn: self.rebind_key(a, b))
            layout.addWidget(btn)
            self.keybind_buttons[key] = btn

        # Bouton crédits
        self.credits_btn = MenuButton("Crédits")
        self.credits_btn.clicked.connect(lambda: CreditsPopup().exec())
        layout.addWidget(self.credits_btn, alignment=Qt.AlignCenter)

        # Back button
        self.back_btn = MenuButton("Retour")
        layout.addWidget(self.back_btn, alignment=Qt.AlignCenter)

        self.setLayout(layout)

    def get_key_name(self, key_code):
        if key_code is None:
            return "Non défini"
        return QKeySequence(key_code).toString()

    def rebind_key(self, action, btn):
        btn.setText(f"{action}: appuyez sur une touche...")

        # Installer temporairement un eventFilter sur la fenêtre pour capter la touche
        def key_press(event):
            key = event.key()
            self.config[f"key_{action}"] = key
            save_config(self.config)
            btn.setText(f"{action}: {QKeySequence(key).toString()}")
            self.keybinding_changed.emit(action, key)
            # On enlève l'event handler
            self.removeEventFilter(filter_obj)
            return True

        class Filter(QObject):
            def eventFilter(self, obj, event):
                if event.type() == QEvent.KeyPress:
                    key_press(event)
                    return True
                return False

        filter_obj = Filter()
        self.installEventFilter(filter_obj)

    # handlers storing config & emitting signals
    def handle_volume(self, val):
        self.config["volume"] = val
        save_config(self.config)
        self.volume_changed.emit(val)

    def handle_fullscreen(self, val):
        self.config["fullscreen"] = val
        save_config(self.config)
        self.fullscreen_toggled.emit(val)

    def handle_difficulty(self, text):
        self.config["difficulty"] = text
        save_config(self.config)
        self.difficulty_changed.emit(text)

    def handle_effects(self, val):
        self.config["effects"] = val
        save_config(self.config)
        self.effects_toggled.emit(val)

    def handle_theme(self, text):
        self.config["theme"] = text
        save_config(self.config)
        self.theme_changed.emit(text)

    def handle_speed(self, val):
        self.config["notespeed"] = val
        save_config(self.config)
        self.notespeed_changed.emit(val)

    def handle_language(self, text):
        self.config["language"] = text
        save_config(self.config)
        self.language_changed.emit(text)

class MainMenu(QWidget):
    play_clicked = Signal()
    multiplayer_clicked = Signal()
    mods_clicked = Signal()
    options_clicked = Signal()
    quit_clicked = Signal()
    editor_clicked = Signal()
    tutorial_clicked = Signal()  # signal tutoriel ajouté

    def __init__(self, sound_effects=None):
        super().__init__()
        layout = QVBoxLayout(spacing=20)
        layout.addWidget(AnimatedLabel("PyFNF"))

        buttons = [
            ("Jouer", self.play_clicked),
            ("Multijoueur", self.multiplayer_clicked),
            ("Mods", self.mods_clicked),
            ("Éditeur", self.editor_clicked),
            ("Options", self.options_clicked),
            ("Tutoriel", self.tutorial_clicked),
            ("Quitter", self.quit_clicked)
        ]

        for txt, sig in buttons:
            btn = MenuButton(txt, sound_effects)
            btn.clicked.connect(sig.emit)
            layout.addWidget(btn, alignment=Qt.AlignCenter)

        self.setLayout(layout)

class GameMenuWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PyFNF - Menu")
        self.setFixedSize(1000, 800)

        self.menu_bg = MenuWidget()
        self.menu_bg.setParent(self)
        self.menu_bg.bg_label.setGeometry(0, 0, 1000, 800)
        self.menu_bg.bg_label.setScaledContents(True)
        self.menu_bg.bg_label.lower()

        self.stack = QStackedWidget(self)
        self.stack.setGeometry(0, 0, 1000, 800)

        # Chargement sons hover + click
        self.sound_hover = QSoundEffect()
        hover_path = os.path.join(os.path.dirname(__file__), "data", "assets", "sounds", "hover.wav")
        self.sound_hover.setSource(QUrl.fromLocalFile(hover_path))
        self.sound_hover.setVolume(0.2)

        self.sound_click = QSoundEffect()
        click_path = os.path.join(os.path.dirname(__file__), "data", "assets", "sounds", "click.wav")
        self.sound_click.setSource(QUrl.fromLocalFile(click_path))
        self.sound_click.setVolume(0.3)

        self.main_menu = MainMenu(sound_effects={
            'hover': self.sound_hover,
            'click': self.sound_click
        })
        self.options_menu = OptionsMenu()
        self.stack.addWidget(self.main_menu)
        self.stack.addWidget(self.options_menu)

        self.setStyleSheet("background-color: #121212;")

        self.player = QMediaPlayer()
        self.output = QAudioOutput()
        self.player.setAudioOutput(self.output)
        music_path = os.path.join(os.path.dirname(__file__), "data", "assets", "menu_music.mp3")
        self.player.setSource(QUrl.fromLocalFile(music_path))
        self.output.setVolume(0.1)  # 30% du volume max
        self.player.play()

        self.main_menu.play_clicked.connect(self.launch_game)
        self.main_menu.editor_clicked.connect(self.launch_editor)
        self.main_menu.options_clicked.connect(self.show_options)
        self.main_menu.quit_clicked.connect(self.close)
        self.main_menu.tutorial_clicked.connect(self.show_tutorial)

        self.options_menu.back_btn.clicked.connect(self.show_main_menu)
        self.options_menu.volume_changed.connect(lambda v: self.output.setVolume(v / 100))
        self.options_menu.fullscreen_toggled.connect(self.toggle_fullscreen)
        self.options_menu.notespeed_changed.connect(lambda v: setattr(self, 'notespeed', v))
        self.options_menu.difficulty_changed.connect(lambda d: setattr(self, 'difficulty', d))
        self.options_menu.effects_toggled.connect(lambda e: setattr(self, 'effects', e))
        self.options_menu.theme_changed.connect(lambda t: setattr(self, 'theme', t))
        self.options_menu.language_changed.connect(lambda l: setattr(self, 'language', l))

        self.main_menu.mods_clicked.connect(self.show_mods)
        self.main_menu.multiplayer_clicked.connect(self.launch_multiplayer)

    def animate_transition(self, new_widget):
        old_widget = self.stack.currentWidget()
        old_index = self.stack.currentIndex()
        new_index = self.stack.indexOf(new_widget)

        if new_index == -1:
            self.stack.addWidget(new_widget)
            new_index = self.stack.indexOf(new_widget)

        direction = 1 if new_index > old_index else -1

        # Positionne le nouveau widget hors écran
        new_widget.setGeometry(self.stack.width() * direction, 0, self.stack.width(), self.stack.height())
        new_widget.show()

        # Animation de l'ancien widget
        anim_old = QPropertyAnimation(old_widget, b"geometry")
        anim_old.setDuration(300)
        anim_old.setStartValue(old_widget.geometry())
        anim_old.setEndValue(QRect(-self.stack.width() * direction, 0, self.stack.width(), self.stack.height()))

        # Animation du nouveau widget
        anim_new = QPropertyAnimation(new_widget, b"geometry")
        anim_new.setDuration(300)
        anim_new.setStartValue(new_widget.geometry())
        anim_new.setEndValue(QRect(0, 0, self.stack.width(), self.stack.height()))

        anim_old.start()
        anim_new.start()

        self.stack.setCurrentWidget(new_widget)

    def launch_game(self):
        path, _ = QFileDialog.getOpenFileName(self, "Choisir une map", "", "*.pyfnf")
        if not path:
            return
        self.player.stop()  # Arrêter la musique menu
        self.game_window = GameWindow(path)
        cfg = self.options_menu.config
        for k, v in cfg.items():
            setattr(self.game_window, k, v)
        self.game_window.show()
        self.close()

    def show_options(self):
        self.stack.setCurrentWidget(self.options_menu)

    def launch_editor(self):
        self.editor_window = EditorWindow()
        self.editor_window.show()
        self.close()

    def show_main_menu(self):
        self.stack.setCurrentWidget(self.main_menu)

    def toggle_fullscreen(self, checked):
        self.setWindowState(Qt.WindowFullScreen if checked else Qt.WindowNoState)

    def show_tutorial(self):
        TutorialPopup().exec()

    def show_mods(self):
        self.animate_transition(self.options_menu)  # Clear page
        mods_page = QWidget()
        layout = QVBoxLayout()

        title = QLabel("Sélection du Mod")
        title.setStyleSheet("font-size: 32px; color: #00e676;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        self.mod_combo = QComboBox()
        mods_dir = os.path.join(os.path.dirname(__file__), "mods")
        valid_mods = []

        for file in os.listdir(mods_dir):
            if file.endswith(".zip"):
                with zipfile.ZipFile(os.path.join(mods_dir, file), 'r') as zip_ref:
                    names = zip_ref.namelist()
                    if any(n.endswith(".mp3") for n in names) and any(n.endswith(".pyfnf") for n in names):
                        valid_mods.append(file)

        if not valid_mods:
            self.mod_combo.addItem("Aucun mod valide trouvé")
            self.mod_combo.setEnabled(False)
        else:
            self.mod_combo.addItems(valid_mods)

        layout.addWidget(self.mod_combo)

        btn_start = MenuButton("Lancer le mod")
        btn_start.clicked.connect(self.launch_selected_mod)
        layout.addWidget(btn_start, alignment=Qt.AlignCenter)

        btn_back = MenuButton("Retour")
        btn_back.clicked.connect(self.show_main_menu)
        layout.addWidget(btn_back, alignment=Qt.AlignCenter)

        mods_page.setLayout(layout)
        self.stack.addWidget(mods_page)
        self.stack.setCurrentWidget(mods_page)

    def launch_selected_mod(self):
        mod_name = self.mod_combo.currentText()
        if not mod_name.endswith(".zip"):
            return

        mods_dir = os.path.join(os.path.dirname(__file__), "mods")
        mod_path = os.path.join(mods_dir, mod_name)
        temp_dir = os.path.join(os.path.dirname(__file__), ".temp_mod")

        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        os.makedirs(temp_dir, exist_ok=True)

        with zipfile.ZipFile(mod_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)

        map_path = None
        music_path = None
        for f in os.listdir(temp_dir):
            if f.endswith(".pyfnf"):
                map_path = os.path.join(temp_dir, f)
            elif f.endswith(".mp3"):
                music_path = os.path.join(temp_dir, f)

        if not map_path or not music_path:
            QMessageBox.critical(self, "Erreur", "Fichiers .pyfnf ou .mp3 manquants.")
            return

        self.player.stop()
        self.game_window = GameWindow(map_path)
        for k, v in self.options_menu.config.items():
            setattr(self.game_window, k, v)
        self.game_window.temp_mod_dir = temp_dir
        self.game_window.show()
        self.close()

    def launch_multiplayer(self):
        self.stack.setCurrentWidget(QWidget())  # clear
        self.lobby = MultiplayerLobby()
        self.lobby.start_game.connect(self.start_multiplayer_game)
        self.stack.addWidget(self.lobby)
        self.stack.setCurrentWidget(self.lobby)

    def start_multiplayer_game(self, path):
        self.player.stop()
        self.game_window = MultiplayerGameWindow(path)
        self.game_window.show()
        self.close()

class MultiplayerLobby(QWidget):
    start_game = Signal(str)  # envoie le chemin de la map

    def __init__(self):
        super().__init__()
        self.ready1 = False
        self.ready2 = False
        self.map_path = ""

        layout = QVBoxLayout()

        self.select_btn = QPushButton("Choisir une map")
        self.select_btn.clicked.connect(self.choose_map)

        self.label_map = QLabel("Aucune map sélectionnée")
        self.ready_btn1 = QPushButton("Joueur 1 prêt")
        self.ready_btn2 = QPushButton("Joueur 2 prêt")

        self.ready_btn1.clicked.connect(self.toggle_ready1)
        self.ready_btn2.clicked.connect(self.toggle_ready2)

        layout.addWidget(self.label_map)
        layout.addWidget(self.select_btn)
        layout.addWidget(self.ready_btn1)
        layout.addWidget(self.ready_btn2)

        self.setLayout(layout)

    def choose_map(self):
        path, _ = QFileDialog.getOpenFileName(self, "Choisir une map", "", "*.pyfnf")
        if path:
            self.map_path = path
            self.label_map.setText(f"Map sélectionnée : {os.path.basename(path)}")

    def toggle_ready1(self):
        self.ready1 = not self.ready1
        self.ready_btn1.setText("Joueur 1 prêt" if self.ready1 else "Joueur 1 prêt")
        self.check_start()

    def toggle_ready2(self):
        self.ready2 = not self.ready2
        self.ready_btn2.setText("Joueur 2 prêt" if self.ready2 else "Joueur 2 prêt")
        self.check_start()

    def check_start(self):
        if self.ready1 and self.ready2 and self.map_path:
            self.start_game.emit(self.map_path)



if __name__ == "__main__":
    start_rich_presence()
    os.makedirs("mods", exist_ok=True)
    app.setStyleSheet(dark_style)
    menu = GameMenuWindow()
    menu.show()
    sys.exit(app.exec())
