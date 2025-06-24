import os
import time
import random
from PySide6.QtCore import Qt, QTimer, QUrl, QPropertyAnimation, QRect
from PySide6.QtGui import QPainter, QColor, QPixmap, QFont, QMovie, QFontDatabase
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QLabel, QPushButton, QVBoxLayout
)
from .utils import load_song_notes

# Constantes
NOTE_SPEED = 300
HIT_WINDOW = 0.2
TARGET_Y = 400
MAX_LIFE = 100
LIFE_LOSS = 15
LIFE_GAIN = 5

KEY_MAPPING = {
    Qt.Key_Left: "left",
    Qt.Key_Down: "down",
    Qt.Key_Up: "up",
    Qt.Key_Right: "right"
}

NOTE_X_POS = {
    "left": 50,
    "down": 150,
    "up": 250,
    "right": 350,
}

ASSET_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "assets")
FONT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "assets", "Quicksand-Bold.ttf")

class GameWindow(QMainWindow):
    def __init__(self, map_path):
        super().__init__()

        # Police custom
        if os.path.exists(FONT_PATH):
            fid = QFontDatabase.addApplicationFont(FONT_PATH)
            if families := QFontDatabase.applicationFontFamilies(fid):
                self.setFont(QFont(families[0], 12))

        # Fond animé (GIF)
        self.bg = QLabel(self)
        self.bg.setGeometry(0, 0, self.width(), self.height())
        if os.path.exists(os.path.join(ASSET_PATH, "bg.gif")):
            movie = QMovie(os.path.join(ASSET_PATH, "bg.gif"))
            movie.setScaledSize(self.size())
            self.bg.setMovie(movie)
            movie.start()
            self.bg.lower()

        self.showFullScreen()

        self.map_data = load_song_notes(map_path)
        self.notes = self.map_data["notes"]
        self.score = 0
        self.combo = 0
        self.max_combo = 0
        self.life = MAX_LIFE
        self.paused = False

        # Audio
        self.player = QMediaPlayer()
        self.output = QAudioOutput()
        self.player.setAudioOutput(self.output)

        # Canvas
        self.canvas = GameCanvas(self.notes, self)
        self.setCentralWidget(self.canvas)

        self.player.setSource(QUrl.fromLocalFile(self.map_data["song"]))
        self.start_time = None

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_game)
        self.start_game()

    def start_game(self):
        self.start_time = time.perf_counter()
        self.player.play()
        self.timer.start(16)

    def pause_game(self):
        if self.paused:
            self.paused = False
            self.player.play()
            self.timer.start(16)
        else:
            self.paused = True
            self.player.pause()
            self.timer.stop()

    def update_game(self):
        if self.paused:
            return
        current_time = time.perf_counter() - self.start_time
        self.canvas.update_time(current_time)
        self.canvas.repaint()
        if current_time > max(n["time"] for n in self.notes) + 2 or self.life <= 0:
            self.timer.stop()
            self.player.stop()
            self.show_results()

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Escape:
            self.pause_game()
            return
        if key in KEY_MAPPING and not self.paused:
            direction = KEY_MAPPING[key]
            current_time = time.perf_counter() - self.start_time
            self.canvas.hit_note(direction, current_time)

    def show_results(self):
        total_notes = len(self.notes)
        hit_notes = sum(1 for n in self.notes if n.get("hit"))
        missed_notes = total_notes - hit_notes
        accuracy = (hit_notes / total_notes) * 100 if total_notes else 0

        duration = self.current_time if hasattr(self, "current_time") else 0
        minutes = int(duration) // 60
        seconds = int(duration) % 60

        results_widget = QWidget()
        layout = QVBoxLayout()
        results_widget.setStyleSheet("background-color: black; color: white;")

        def make_label(text):
            lbl = QLabel(text)
            lbl.setStyleSheet("font-size: 22px;")
            lbl.setAlignment(Qt.AlignCenter)
            return lbl

        layout.addWidget(make_label(f"🎯 Précision : {accuracy:.1f}%"))
        layout.addWidget(make_label(f"✅ Notes touchées : {hit_notes}/{total_notes}"))
        layout.addWidget(make_label(f"❌ Miss : {missed_notes}"))
        layout.addWidget(make_label(f"💯 Score : {self.score}"))
        layout.addWidget(make_label(f"🔥 Combo max : {self.max_combo}"))
        layout.addWidget(make_label(f"⏱ Temps de jeu : {minutes} min {seconds:02}s"))

        # Boutons
        retry_btn = QPushButton("🔁 Rejouer")
        menu_btn = QPushButton("🏠 Menu principal")

        for btn in (retry_btn, menu_btn):
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #00e676;
                    color: black;
                    font-size: 18px;
                    padding: 10px;
                    border-radius: 10px;
                }
                QPushButton:hover {
                    background-color: #00c95e;
                }
            """)
            layout.addWidget(btn, alignment=Qt.AlignCenter)

        retry_btn.clicked.connect(self.retry_game)
        menu_btn.clicked.connect(self.return_to_menu)

        results_widget.setLayout(layout)
        self.setCentralWidget(results_widget)

    def retry_game(self):
        self.player.stop()
        self.timer.stop()
        for note in self.notes:
            note.pop("hit", None)  # reset hit status
        self.score = 0
        self.combo = 0
        self.max_combo = 0
        self.life = MAX_LIFE
        self.start_time = None

        # Crée une nouvelle instance canvas avec notes réinitialisées
        self.canvas = GameCanvas(self.notes, self)
        self.setCentralWidget(self.canvas)

        self.start_game()

    def return_to_menu(self):
        self.close()


class GameCanvas(QWidget):
    def __init__(self, notes, parent):
        super().__init__()
        self.notes = notes
        self.parent = parent
        self.current_time = 0.0

        # Effet feedback
        self.feedback = ""
        self.feedback_size = 0
        self.feedback_opacity = 0.0
        self.feedback_timer = QTimer(self)
        self.feedback_timer.timeout.connect(self.animate_feedback)

        # Equalizer
        self.bars = [10] * 20
        self.bar_timer = QTimer(self)
        self.bar_timer.setInterval(100)
        self.bar_timer.timeout.connect(self.update_bars)
        self.bar_timer.start()

        # Sprites
        self.sprites = {
            d: QPixmap(os.path.join(ASSET_PATH, f"arrow_{d}.png"))
            for d in ["left", "down", "up", "right"]
        }

    def update_time(self, t):
        self.current_time = t

    def hit_note(self, direction, current_time):
        for note in self.notes:
            if note.get("hit"):
                continue
            if note["direction"] == direction and abs(note["time"] - current_time) < HIT_WINDOW:
                note["hit"] = True
                self.trigger_feedback(direction.upper())
                self.parent.score += 100 + self.parent.combo * 10
                self.parent.combo += 1
                self.parent.max_combo = max(self.parent.max_combo, self.parent.combo)
                self.parent.life = min(MAX_LIFE, self.parent.life + LIFE_GAIN)
                return
        self.trigger_feedback("MISS")
        self.parent.combo = 0
        self.parent.life -= LIFE_LOSS

    def trigger_feedback(self, text):
        self.feedback = text
        self.feedback_size = 48
        self.feedback_opacity = 1.0
        self.feedback_timer.start(30)

    def animate_feedback(self):
        self.feedback_size -= 2
        self.feedback_opacity -= 0.05
        if self.feedback_opacity <= 0:
            self.feedback_timer.stop()
        self.update()

    def update_bars(self):
        self.bars = [random.randint(5, 60) for _ in self.bars]
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#111"))
        painter.setPen(QColor("white"))
        painter.drawLine(0, TARGET_Y, self.width(), TARGET_Y)

        # Notes
        for note in self.notes:
            y = TARGET_Y - ((note["time"] - self.current_time) * NOTE_SPEED)

            # Vérifie si la note est trop basse et non touchée -> MISS
            if not note.get("hit") and y > TARGET_Y + 50:
                note["hit"] = True
                self.trigger_feedback("MISS")
                self.parent.combo = 0
                self.parent.life -= LIFE_LOSS
                continue

            if note.get("hit"):
                continue

            if y > self.height():
                continue

            x = NOTE_X_POS[note["direction"]]
            painter.drawPixmap(int(x), int(y), 40, 40, self.sprites[note["direction"]])

        # Score & combo
        painter.setPen(QColor("#00e676"))
        font = QFont(self.font().family(), 14, QFont.Bold)
        painter.setFont(font)
        painter.drawText(20, 40, f"Score: {self.parent.score}")
        painter.drawText(20, 70, f"Combo: {self.parent.combo}")

        # Life bar
        life_w = int((self.parent.life / MAX_LIFE) * (self.width() - 40))
        painter.setBrush(QColor("#4caf50"))
        painter.drawRect(20, 90, life_w, 10)
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(20, 90, self.width() - 40, 10)

        # BPM & time
        bpm = self.parent.map_data.get("bpm", 120)
        painter.drawText(350, 40, f"BPM: {bpm}")
        painter.drawText(350, 70, f"Temps: {self.current_time:.2f}s")

        # Feedback
        if self.feedback_opacity > 0:
            painter.setPen(QColor(255, 255, 255, int(self.feedback_opacity * 255)))
            font.setPointSize(self.feedback_size)
            painter.setFont(font)
            w = painter.fontMetrics().horizontalAdvance(self.feedback)
            painter.drawText((self.width() - w)//2, TARGET_Y - 100, self.feedback)

        # Equalizer bars
        for i, h in enumerate(self.bars):
            painter.setBrush(QColor("#00e676"))
            painter.drawRect(20 + i * 25, self.height() - h - 10, 15, h)