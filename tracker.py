import cv2
from datetime import timedelta
from ultralytics import YOLO

class MouseTracker:
    # Конструктор
    def __init__(self):
        self.square_model = YOLO('models/findSquare.pt') # Модель для поиска квадратов
        self.mouse_model = YOLO('models/findMouse.pt') # Модель для поиска мыши
        self.cap = None
        self.squares = [] # Квадраты лабиринта
        self.log_data = [] # Логи
        self.prev_square = -1 # Предыдущая позиция мыши
        self.frame_count = 0 # Счетчик кадров

    # Открыть видео
    def open_video(self, video_path):
        self.cap = cv2.VideoCapture(video_path) # Открываем видео
        self.squares = self.find_squares_in_video() # Ищем квадраты
        return self.squares is not None # 1 если квадраты найдены

    # Поиск квадратов в видео
    def find_squares_in_video(self):
        total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames == 0:
            return None

        mid_frame = total_frames // 2
        search_order = list(range(mid_frame, -1, -1)) + list(range(mid_frame + 1, total_frames))

        for frame_pos in search_order:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
            ret, frame = self.cap.read()
            if not ret:
                continue

            squares = self.find_squares(frame)
            if squares:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                return squares
        return None

    def find_squares(self, frame):
        square_results = self.square_model(frame)
        squares = []

        for result in square_results:
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2
                squares.append({
                    'coords': (x1, y1, x2, y2),
                    'center': (center_x, center_y)
                })

        if len(squares) == 25:
            squares.sort(key=lambda s: s['center'][1])
            sorted_squares = []
            for row in range(5):
                row_squares = squares[row * 5: (row + 1) * 5]
                row_squares.sort(key=lambda s: s['center'][0])
                sorted_squares.extend(row_squares)
            return [s['coords'] for s in sorted_squares]
        return []


    def get_timestamp(self):
        fps = self.cap.get(cv2.CAP_PROP_FPS)
        timestamp_ms = int((self.frame_count / fps) * 1000)
        td = timedelta(milliseconds=timestamp_ms)
        return str(td)

    # Найти цент прямоугольника
    @staticmethod
    def get_center(x1, y1, x2, y2):
        return ((x1 + x2) // 2, (y1 + y2) // 2)

    def find_square(self, point, squares):
        x, y = point
        for i, (x1, y1, x2, y2) in enumerate(squares):
            if x1 <= x <= x2 and y1 <= y <= y2:
                return i
        return -1

    # Преобразуем индексы в шахматную нотацию
    @staticmethod
    def get_chess_notation(index):
        if 0 <= index < 25:
            col = chr(ord('A') + (index % 5))
            row = str((index // 5) + 1)
            return f"{col}{row}"
        return "Unknown"

    def export_log(self, filename):
        with open(filename, 'w') as f:
            f.write("timestamp,position,x,y\n")
            for entry in self.log_data:
                x, y = entry['coords']
                f.write(f"{entry['time']},{entry['position']},{x},{y}\n")

    def release(self):
        if self.cap:
            self.cap.release()

    def process_frame(self, frame):
        results = self.mouse_model(frame)
        current_square = -1

        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                center = self.get_center(x1, y1, x2, y2)
                current_square = self.find_square(center, self.squares)
                break

        # Записываем только при смене квадрата
        if current_square != -1 and current_square != self.prev_square:
            timestamp_sec = self.frame_count / self.cap.get(cv2.CAP_PROP_FPS)
            self.log_data.append((
                self.frame_count,
                timestamp_sec,
                current_square
            ))
            self.prev_square = current_square

        self.frame_count += 1
        return current_square

    def finalize_log(self):
        """Финализация лога - добавляем последнюю позицию если она не была записана"""
        if (self.prev_square != -1  and (not self.log_data or self.log_data[-1][2] != self.prev_square)):
            timestamp_sec = (self.frame_count - 1) / self.cap.get(cv2.CAP_PROP_FPS)
            self.log_data.append((
                self.frame_count - 1,
                timestamp_sec,
                self.prev_square
            ))