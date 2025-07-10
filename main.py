import sys
from PyQt5.QtWidgets import QApplication # Главное приложение
from ui.main_window import MouseTrackerApp # Сделанное окно

if __name__ == "__main__": # Выполняем при запуске файла
    app = QApplication(sys.argv) # Объект приложения Qt
    window = MouseTrackerApp() # Объект нашего окна
    window.show() # Показываем окно на экране
    sys.exit(app.exec_())