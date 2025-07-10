from PyQt5.QtWidgets import QLabel, QFileDialog
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
import cv2
from tracker import MouseTracker


class VideoPlayer(QLabel):
    videoOpened = pyqtSignal()
    videoFinished = pyqtSignal()
    statusMessage = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setText("Откройте видео для начала работы")
        self.setMinimumSize(1000, 1000)

        self.tracker = MouseTracker()
        self.is_playing = False # Флаг воспроизведения видео
        self.is_paused = False # Флаг паузы
        self.is_tracking = False # Флаг трекинга мыши

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)

    def open_video(self):
        """Открытие видеофайла"""
        filename, _ = QFileDialog.getOpenFileName(self, "Открыть видео", "","Video Files (*.mp4 *.avi *.mov);;All Files (*)")

        if filename:
            if self.tracker.open_video(filename):
                self.start_playback()
                self.start_tracking()
                self.videoOpened.emit()
                self.statusMessage.emit(f"Загружено: {filename.split('/')[-1]}")
            else:
                self.statusMessage.emit("Не удалось обнаружить квадраты в видео")

    def start_playback(self):
        """Начать воспроизведение видео"""
        self.is_playing = True
        self.is_paused = False
        self.timer.start(30)  # ~33 FPS

    def stop_playback(self):
        self.is_playing = False
        self.is_paused = False
        self.is_tracking = False
        self.timer.stop()
        self.tracker.finalize_log()  # Добавить эту строку
        self.tracker.release()
        self.clear()
        self.setText("Воспроизведение завершено")
        self.videoFinished.emit()

    def toggle_pause(self):
        """Поставить/снять с паузы"""
        if not self.is_playing:
            return

        if self.is_paused:
            self.timer.start(30)
            self.is_paused = False
            self.statusMessage.emit("Трекинг возобновлен")
        else:
            self.timer.stop()
            self.is_paused = True
            self.statusMessage.emit("Трекинг на паузе")

    def start_tracking(self):
        """Начать трекинг мыши"""
        self.is_tracking = True
        self.tracker.log_data = []
        self.tracker.frame_count = 0
        self.tracker.prev_square = -1
        self.statusMessage.emit("Трекинг начат")

    def update_frame(self):
        """Обновление кадров видео"""
        if not self.tracker.cap or not self.is_playing or self.is_paused:
            return

        ret, frame = self.tracker.cap.read()
        if not ret:
            self.stop_playback()
            return

        current_square = -1
        if self.is_tracking:
            current_square = self.tracker.process_frame(frame)

        self.display_frame(frame, current_square)

    def display_frame(self, frame, current_square):
        """Отображение кадра с разметкой"""
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        if self.tracker.squares:
            for i, (x1, y1, x2, y2) in enumerate(self.tracker.squares):
                color = (0, 255, 0) if i == current_square else (0, 0, 255)
                cv2.rectangle(frame_rgb, (x1, y1), (x2, y2), color, 2)
                cv2.putText(frame_rgb, self.tracker.get_chess_notation(i),
                           (x1 + 5, y1 + 20), cv2.FONT_HERSHEY_SIMPLEX,
                           0.5, (255, 255, 255), 1)

        h, w, ch = frame_rgb.shape
        q_img = QImage(frame_rgb.data, w, h, ch * w, QImage.Format_RGB888)
        self.setPixmap(QPixmap.fromImage(q_img))

    def export_log(self):
        """Экспорт данных трекинга"""
        if not self.tracker.log_data:
            self.statusMessage.emit("Нет данных для экспорта")
            return

        filename, _ = QFileDialog.getSaveFileName(
            self, "Сохранить лог", "", "Text Files (*.txt);;All Files (*)")

        if not filename:
            return

        if not filename.lower().endswith('.txt'):
            filename += '.txt'

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("часы:минуты:секунды:милисекунды координата\n")

                for frame_count, timestamp_sec, square in self.tracker.log_data:
                    # Форматирование времени
                    hours = int(timestamp_sec // 3600)
                    minutes = int((timestamp_sec % 3600) // 60)
                    seconds = int(timestamp_sec % 60)
                    milliseconds = int((timestamp_sec % 1) * 1000)

                    # Шахматная нотация
                    coord = self.tracker.get_chess_notation(square)

                    # Запись строки
                    f.write(f"{hours:02d}:{minutes:02d}:{seconds:02d}:{milliseconds:03d} {coord}\n")

            self.statusMessage.emit(f"Лог сохранен в {filename}")
        except Exception as e:
            self.statusMessage.emit(f"Ошибка при сохранении: {str(e)}")