from PyQt5.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton, QWidget)
from ui.video_player import VideoPlayer


class MouseTrackerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Логирование мыши в лабиринте")
        self.setGeometry(100, 100, 800, 600)
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()

        # Панель управления
        control_layout = QHBoxLayout()
        self.video_player = VideoPlayer(self)

        # Настройка соединений сигналов
        self.video_player.videoOpened.connect(self.on_video_opened)
        self.video_player.videoFinished.connect(self.on_video_finished)
        self.video_player.statusMessage.connect(self.statusBar().showMessage)

        # Кнопки
        self.btn_open = QPushButton("Открыть видео")
        self.btn_open.clicked.connect(self.open_video)
        control_layout.addWidget(self.btn_open)

        self.btn_pause = QPushButton("Пауза")
        self.btn_pause.clicked.connect(self.video_player.toggle_pause)
        self.btn_pause.setEnabled(False)
        control_layout.addWidget(self.btn_pause)

        self.btn_stop = QPushButton("Прекратить видео")
        self.btn_stop.clicked.connect(self.stop_video)
        self.btn_stop.setEnabled(False)
        control_layout.addWidget(self.btn_stop)

        self.btn_export = QPushButton("Экспортировать лог")
        self.btn_export.clicked.connect(self.video_player.export_log)
        self.btn_export.setEnabled(False)
        control_layout.addWidget(self.btn_export)

        layout.addLayout(control_layout)
        layout.addWidget(self.video_player)

        central_widget.setLayout(layout)

    def open_video(self):
        """Открытие нового видео"""
        if self.video_player.is_playing:
            self.stop_video()
        self.video_player.open_video()

    def stop_video(self):
        """Полная остановка видео и трекинга"""
        self.video_player.stop_playback()
        self.on_video_finished()

    def on_video_opened(self):
        """Видео успешно открыто, видео запускается автоматически"""
        self.btn_pause.setEnabled(True)
        self.btn_stop.setEnabled(True)
        self.btn_export.setEnabled(False)

    def on_video_finished(self):
        """Видео завершено или остановлено"""
        self.btn_pause.setEnabled(False)
        self.btn_stop.setEnabled(False)
        self.btn_export.setEnabled(True)