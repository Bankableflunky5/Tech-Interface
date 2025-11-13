from PyQt5.QtWidgets import (
    QSplashScreen, QProgressBar, QVBoxLayout, QHBoxLayout,
    QLabel, QWidget, QGraphicsOpacityEffect
)
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import Qt, QPropertyAnimation, QRect, QEasingCurve


# SplashScreen Class
# ----------------------
# This class creates a splash screen UI with a progress bar 
# using PyQt5. It extends QSplashScreen to display an initial 
# screen while the application is loading or initializing.
#
# The __init__() method sets up the splash screen by:
# - Loading and scaling a custom splash image (replace 'splash.png' 
#   with your own logo).
# - Adding a progress bar at the bottom of the screen, styled 
#   with custom CSS to match the application's design.
# - Adding a title ("Initializing...") above the progress bar.
#
# The update_progress() method is used to update the value of 
# the progress bar. It takes an integer value (0-100) to represent 
# the progress of the initialization process. This can be connected 
# to a background thread (e.g., InitializationThread) to reflect 
# real-time progress during application startup.



class SplashScreen(QSplashScreen):
    """Upgraded Splash Screen with centered layout and progress bar."""

    def __init__(self, image_path="splash.png"):
        # Load and scale splash image
        splash_pix = QPixmap(image_path).scaled(500, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        super().__init__(splash_pix)

        # 🔆 Pulsing glow effect on the whole splash


        # Opacity effect applied to the whole splash screen
        self.opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0.4)


        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Container over splash to hold layout
        self.container = QWidget(self)
        self.container.setGeometry(0, 0, self.width(), self.height())
        self.container.setStyleSheet("background: transparent;")

        # Title Label
        self.title_label = QLabel("Loading...", self.container)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.title_label.setStyleSheet("color: white;")

        # Progress Bar
        self.progress_bar = QProgressBar(self.container)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setFixedHeight(26)       # ⬅️ Slightly taller than before
        self.progress_bar.setFixedWidth(200)       # ⬅️ Slightly wider

        self.progress_bar.setTextVisible(True)
        self.progress_bar.setAlignment(Qt.AlignCenter)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #3A9EF5;
                border-radius: 5px;
                text-align: center;
                color: white;
                background-color: #444;
            }
            QProgressBar::chunk {
                background-color: #3A9EF5;
            }
        """)

        

        # ✨ Shimmer effect overlay
        self.shimmer_label = QLabel(self.progress_bar)
        self.shimmer_label.setStyleSheet("""
            background: qlineargradient(
                x1: 0, y1: 0, x2: 1, y2: 0,
                stop: 0 rgba(255, 255, 255, 0),
                stop: 0.5 rgba(255, 255, 255, 80),
                stop: 1 rgba(255, 255, 255, 0)
            );
            border: none;
        """)
        self.shimmer_label.resize(80, self.progress_bar.height())

        # Animation: slide shimmer from left to right
        self.shimmer_anim = QPropertyAnimation(self.shimmer_label, b"geometry")
        self.shimmer_anim.setDuration(1500)
        self.shimmer_anim.setLoopCount(-1)
        self.shimmer_anim.setEasingCurve(QEasingCurve.InOutQuad)

        start_rect = QRect(-80, 0, 80, self.progress_bar.height())
        end_rect = QRect(self.progress_bar.width(), 0, 80, self.progress_bar.height())

        self.shimmer_anim.setStartValue(start_rect)
        self.shimmer_anim.setEndValue(end_rect)
        self.shimmer_anim.start()


        # ⬅️ NEW: HBox layout just for centering the progress bar
        progress_bar_wrapper = QHBoxLayout()
        progress_bar_wrapper.addStretch()
        progress_bar_wrapper.addWidget(self.progress_bar)
        progress_bar_wrapper.addStretch()

        # Layout
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(40, 200, 40, 40)
        layout.setSpacing(15)
        layout.setAlignment(Qt.AlignBottom)
        layout.addWidget(self.title_label)
        layout.addLayout(progress_bar_wrapper)  # ✅ progress bar centered!

    def update_progress(self, value):
        """Update progress bar and glow brightness."""
        self.progress_bar.setValue(value)

        # Dynamically adjust brightness based on progress
        # Map 0 → 0.4 (dim), 100 → 1.0 (full glow)
        min_opacity = 0.4
        max_opacity = 1.0
        scaled_opacity = min_opacity + (max_opacity - min_opacity) * (value / 100)

        self.opacity_effect.setOpacity(scaled_opacity)

    def set_status_message(self, message: str):
        self.title_label.setText(message)
