from PySide6.QtWidgets import (
    QMainWindow, QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout,
    QListWidget, QFileDialog, QLineEdit, QAbstractItemView, QMessageBox
)
from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtGui import QPainter, QColor, QFont
import os
import time
import copy
import random

from editor.file_handler import save_map, load_map  # ton module perso

class NotesPlayerWidget(QWidget):
    def __init__(self, editor_window):
        super().__init__()
        self.editor = editor_window
        self.current_time = 0.0
        self.note_radius = 15
        self.speed = 100  # pixels par seconde
        self.active = False
        self.setMinimumHeight(100)

    def start(self):
        self.current_time = 0.0
        self.active = True
        self.update()

    def stop(self):
        self.active = False
        self.current_time = 0.0
        self.update()

    def update_time(self, elapsed):
        self.current_time = elapsed
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#121212"))

        width = self.width()
        height = self.height()
        center_y = height // 2

        # Ligne centrale
        painter.setPen(QColor("#007acc"))
        painter.drawLine(0, center_y, width, center_y)

        if not self.active:
            return

        # Affichage des notes
        for note in self.editor.map_data["notes"]:
            dt = note["time"] - self.current_time
            x = width - dt * self.speed
            if 0 <= x <= width:
                color_map = {
                    "left": "#ff4c4c",
                    "down": "#4cff4c",
                    "up": "#4c4cff",
                    "right": "#ffff4c",
                }
                color = QColor(color_map.get(note["direction"], "#ffffff"))
                painter.setBrush(color)
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(int(x), center_y - self.note_radius, self.note_radius*2, self.note_radius*2)

                painter.setPen(QColor("#000000"))
                font = QFont("Arial", 10, QFont.Bold)
                painter.setFont(font)
                direction_letter = note["direction"][0].upper()
                painter.drawText(int(x) + self.note_radius - 6, center_y + 6, direction_letter)

class EditorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Editor")
        self.resize(700, 600)

        # Données
        self.map_data = {"song": "", "bpm": 120, "notes": []}
        self.start_time = None

        # Undo/Redo stack
        self.history = []
        self.history_index = -1

        # Player audio
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)

        # Timer update interface
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time_label)

        # Directions fixes
        self.directions = ["left", "down", "up", "right"]

        # Widget visuel des notes en lecture
        self.notes_player = NotesPlayerWidget(self)

        # UI Setup
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout()

        # --- Top control buttons ---
        top_btn_layout = QHBoxLayout()
        self.btn_choose_song = QPushButton("🎵 Choisir musique")
        self.btn_play = QPushButton("▶️ Lecture")
        self.btn_pause = QPushButton("⏸ Pause")
        self.btn_stop = QPushButton("■ Stop")
        self.btn_add_note = QPushButton("➕ Ajouter note")
        self.btn_delete_note = QPushButton("❌ Supprimer note")
        self.btn_undo = QPushButton("↩ Undo")
        self.btn_redo = QPushButton("↪ Redo")
        self.btn_save = QPushButton("💾 Sauvegarder .pyfnf")
        self.btn_load = QPushButton("📂 Charger .pyfnf")

        for btn in (self.btn_choose_song, self.btn_play, self.btn_pause, self.btn_stop,
                    self.btn_add_note, self.btn_delete_note, self.btn_undo, self.btn_redo,
                    self.btn_save, self.btn_load):
            top_btn_layout.addWidget(btn)

        main_layout.addLayout(top_btn_layout)

        # --- Time label ---
        self.time_label = QLabel("Temps : 0.00s")
        main_layout.addWidget(self.time_label)

        # --- Notes list ---
        self.note_list = QListWidget()
        self.note_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.note_list.setDragDropMode(QAbstractItemView.InternalMove)
        self.note_list.setDefaultDropAction(Qt.MoveAction)
        self.note_list.model().rowsMoved.connect(self.on_notes_reordered)
        main_layout.addWidget(self.note_list, 1)

        # --- Notes player visuel ---
        main_layout.addWidget(self.notes_player)

        # --- Editing fields ---
        edit_layout = QHBoxLayout()
        self.edit_time = QLineEdit()
        self.edit_time.setPlaceholderText("Temps (ex: 12.34)")
        self.edit_dir = QLineEdit()
        self.edit_dir.setPlaceholderText("Direction (left/down/up/right)")
        self.btn_apply_edit = QPushButton("✏️ Appliquer modification")
        edit_layout.addWidget(self.edit_time)
        edit_layout.addWidget(self.edit_dir)
        edit_layout.addWidget(self.btn_apply_edit)
        main_layout.addLayout(edit_layout)

        # Container widget
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # Connect signals
        self.btn_choose_song.clicked.connect(self.choose_song)
        self.btn_play.clicked.connect(self.play_music)
        self.btn_pause.clicked.connect(self.pause_music)
        self.btn_stop.clicked.connect(self.stop_music)
        self.btn_add_note.clicked.connect(self.add_note)
        self.btn_delete_note.clicked.connect(self.delete_selected_note)
        self.btn_save.clicked.connect(self.save_map)
        self.btn_load.clicked.connect(self.load_map)
        self.btn_undo.clicked.connect(self.undo)
        self.btn_redo.clicked.connect(self.redo)
        self.btn_apply_edit.clicked.connect(self.apply_note_edit)
        self.note_list.itemSelectionChanged.connect(self.load_selected_note_into_edit)

    def update_time_label(self):
        if self.start_time:
            elapsed = time.perf_counter() - self.start_time
            self.time_label.setText(f"Temps : {elapsed:.2f}s")
            self.notes_player.update_time(elapsed)

    def choose_song(self):
        path, _ = QFileDialog.getOpenFileName(self, "Choisir une musique", "", "*.mp3 *.ogg *.wav")
        if path:
            self.map_data["song"] = path
            self.setWindowTitle(f"Éditeur ULTIME - {os.path.basename(path)}")

    def play_music(self):
        if not self.map_data["song"]:
            QMessageBox.warning(self, "Erreur", "Choisissez d'abord une musique !")
            return
        self.start_time = time.perf_counter()
        self.player.setSource(QUrl.fromLocalFile(self.map_data["song"]))
        self.player.play()
        self.timer.start(50)
        self.notes_player.start()

    def pause_music(self):
        self.player.pause()
        self.timer.stop()

    def stop_music(self):
        self.player.stop()
        self.timer.stop()
        self.start_time = None
        self.time_label.setText("Temps : 0.00s")
        self.notes_player.stop()

    def add_note(self):
        if not self.start_time:
            QMessageBox.warning(self, "Erreur", "Lancez la musique pour ajouter des notes.")
            return
        current_time = time.perf_counter() - self.start_time
        direction = random.choice(self.directions)  # <-- ici on prend une direction aléatoire
        note = {"time": round(current_time, 2), "direction": direction}
        self.map_data["notes"].append(note)
        self.push_history()
        self.refresh_note_list()
        self.note_list.setCurrentRow(len(self.map_data["notes"]) - 1)

    def delete_selected_note(self):
        row = self.note_list.currentRow()
        if row >= 0:
            del self.map_data["notes"][row]
            self.push_history()
            self.refresh_note_list()

    def refresh_note_list(self):
        self.note_list.clear()
        for n in self.map_data["notes"]:
            self.note_list.addItem(f"{n['time']:.2f}s → {n['direction']}")

    def on_notes_reordered(self, *args):
        new_notes = []
        for i in range(self.note_list.count()):
            text = self.note_list.item(i).text()
            time_str, dir_str = text.split("s → ")
            new_notes.append({"time": float(time_str), "direction": dir_str})
        self.map_data["notes"] = new_notes
        self.push_history()

    def load_selected_note_into_edit(self):
        row = self.note_list.currentRow()
        if row < 0 or row >= len(self.map_data["notes"]):
            self.edit_time.clear()
            self.edit_dir.clear()
            return
        note = self.map_data["notes"][row]
        self.edit_time.setText(f"{note['time']:.2f}")
        self.edit_dir.setText(note["direction"])

    def apply_note_edit(self):
        row = self.note_list.currentRow()
        if row < 0:
            return
        try:
            new_time = float(self.edit_time.text())
            if new_time < 0:
                raise ValueError()
        except ValueError:
            QMessageBox.warning(self, "Erreur", "Temps invalide (doit être un nombre positif).")
            return
        new_dir = self.edit_dir.text().lower()
        if new_dir not in self.directions:
            QMessageBox.warning(self, "Erreur", f"Direction invalide, doit être une de : {', '.join(self.directions)}")
            return
        self.map_data["notes"][row] = {"time": round(new_time, 2), "direction": new_dir}
        self.push_history()
        self.refresh_note_list()
        self.note_list.setCurrentRow(row)

    def save_map(self):
        path, _ = QFileDialog.getSaveFileName(self, "Sauvegarder la map", "", "*.pyfnf")
        if path:
            save_map(path, self.map_data)
            QMessageBox.information(self, "Succès", "Map sauvegardée avec succès.")

    def load_map(self):
        path, _ = QFileDialog.getOpenFileName(self, "Charger une map", "", "*.pyfnf")
        if path:
            self.map_data = load_map(path)
            self.push_history(reset=True)
            self.refresh_note_list()
            QMessageBox.information(self, "Succès", "Map chargée avec succès.")

    # Undo/Redo
    def push_history(self, reset=False):
        if reset:
            self.history = []
            self.history_index = -1
        else:
            self.history = self.history[:self.history_index + 1]

        snapshot = copy.deepcopy(self.map_data)
        self.history.append(snapshot)
        self.history_index += 1

        if len(self.history) > 50:
            self.history.pop(0)
            self.history_index -= 1

    def undo(self):
        if self.history_index > 0:
            self.history_index -= 1
            self.map_data = copy.deepcopy(self.history[self.history_index])
            self.refresh_note_list()
        else:
            QMessageBox.information(self, "Undo", "Plus d'actions à annuler.")

    def redo(self):
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.map_data = copy.deepcopy(self.history[self.history_index])
            self.refresh_note_list()
        else:
            QMessageBox.information(self, "Redo", "Plus d'actions à rétablir.")
