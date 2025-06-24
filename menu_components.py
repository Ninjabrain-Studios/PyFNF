import json
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit
)
from PySide6.QtGui import QFont, QCursor
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve


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
    def __init__(self, text):
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
            }
            QPushButton:hover {
                background-color: #00e676;
                color: #111;
            }
            QPushButton:pressed {
                background-color: #00b359;
            }
        """)


class MainMenu(QWidget):
    play_clicked = Signal()
    options_clicked = Signal()
    quit_clicked = Signal()

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.setSpacing(30)

        # Titre animé
        self.title = AnimatedLabel("PyFNF")
        layout.addWidget(self.title)

        # Boutons
        self.play_btn = MenuButton("Jouer")
        self.options_btn = MenuButton("Options")
        self.quit_btn = MenuButton("Quitter")
        layout.addWidget(self.play_btn, alignment=Qt.AlignCenter)
        layout.addWidget(self.options_btn, alignment=Qt.AlignCenter)
        layout.addWidget(self.quit_btn, alignment=Qt.AlignCenter)

        # Changelog Box
        self.changelog_box = QTextEdit()
        self.changelog_box.setReadOnly(True)
        self.changelog_box.setFixedHeight(120)
        self.changelog_box.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #00e676;
                border: 1px solid #00e676;
                border-radius: 8px;
                padding: 6px;
                font-family: Consolas, monospace;
                font-size: 14px;
            }
        """)

        # Charger changelog depuis fichier
        try:
            with open("data/changelog.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                log = "\n".join(f"• {line}" for line in data.get("changelog", []))
                self.changelog_box.setText(f"📜 Changelog:\n\n{log}")
        except Exception as e:
            self.changelog_box.setText("📜 Changelog:\n\nErreur de chargement.")

        layout.addWidget(self.changelog_box, alignment=Qt.AlignRight)

        self.setLayout(layout)

        # Connect
        self.play_btn.clicked.connect(self.play_clicked.emit)
        self.options_btn.clicked.connect(self.options_clicked.emit)
        self.quit_btn.clicked.connect(self.quit_clicked.emit)
