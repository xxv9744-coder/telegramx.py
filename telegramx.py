import sys
import math
import random
import keyboard
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import Qt, QTimer, QPointF
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QPainterPath


class Cockroach:
    def __init__(self, width, height):
        self.w = width
        self.h = height
        self.x = random.uniform(50, width - 50)
        self.y = random.uniform(50, height - 50)
        self.angle = random.uniform(0, 2 * math.pi)
        self.speed = random.uniform(2.5, 5.5)
        self.scale = random.uniform(0.8, 1.3)
        self.leg_phase = random.uniform(0, 2 * math.pi)
        self.antenna_phase = random.uniform(0, 2 * math.pi)
        self.state = "run"  # run или pause
        self.state_timer = random.randint(30, 150)

    def update(self):
        self.state_timer -= 1
        if self.state_timer <= 0:
            if self.state == "run" and random.random() < 0.35:
                self.state = "pause"
                self.state_timer = random.randint(20, 80)
            else:
                self.state = "run"
                self.state_timer = random.randint(40, 180)
                self.angle += random.uniform(-1.2, 1.2)

        if self.state == "run":
            # Небольшое виляние при беге
            self.angle += random.uniform(-0.15, 0.15)
            self.x += math.cos(self.angle) * self.speed
            self.y += math.sin(self.angle) * self.speed
            self.leg_phase += self.speed * 0.45

            # Отскок от краев экрана
            margin = 20
            if self.x < margin:
                self.x = margin
                self.angle = random.uniform(-math.pi / 2, math.pi / 2)
            elif self.x > self.w - margin:
                self.x = self.w - margin
                self.angle = random.uniform(math.pi / 2, 3 * math.pi / 2)

            if self.y < margin:
                self.y = margin
                self.angle = random.uniform(0, math.pi)
            elif self.y > self.h - margin:
                self.y = self.h - margin
                self.angle = random.uniform(math.pi, 2 * math.pi)
        else:
            # Шевелит усами, когда стоит
            self.antenna_phase += 0.2

    def draw(self, painter):
        painter.save()
        painter.translate(self.x, self.y)
        painter.rotate(math.degrees(self.angle))
        painter.scale(self.scale, self.scale)

        # Тень под тараканом
        painter.setBrush(QBrush(QColor(0, 0, 0, 60)))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(0, 2), 14, 7)

        # Лапки (6 штук)
        leg_pen = QPen(QColor(45, 22, 10), 1.5, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(leg_pen)
        leg_offsets = [-6, 0, 6]
        for i, lx in enumerate(leg_offsets):
            swing = math.sin(self.leg_phase + i * 2.1) * 4 if self.state == "run" else 0
            # Левая лапа
            path_l = QPainterPath()
            path_l.moveTo(lx, -3)
            path_l.lineTo(lx + swing * 0.5, -11)
            path_l.lineTo(lx - 3 + swing, -16)
            painter.drawPath(path_l)
            # Правая лапа
            path_r = QPainterPath()
            path_r.moveTo(lx, 3)
            path_r.lineTo(lx - swing * 0.5, 11)
            path_r.lineTo(lx - 3 - swing, 16)
            painter.drawPath(path_r)

        # Усики
        ant_pen = QPen(QColor(60, 30, 15), 1.0, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(ant_pen)
        wiggle = math.sin(self.antenna_phase + self.leg_phase * 0.3) * 3
        ant_l = QPainterPath()
        ant_l.moveTo(12, -2)
        ant_l.quadTo(20, -8 + wiggle, 28, -12 + wiggle)
        painter.drawPath(ant_l)
        ant_r = QPainterPath()
        ant_r.moveTo(12, 2)
        ant_r.quadTo(20, 8 - wiggle, 28, 12 - wiggle)
        painter.drawPath(ant_r)

        # Брюшко / надкрылья
        painter.setPen(QPen(QColor(35, 15, 5), 1))
        painter.setBrush(QBrush(QColor(92, 44, 18)))
        painter.drawEllipse(QPointF(-2, 0), 12, 6.5)

        # Полоска по центру спины
        painter.setPen(QPen(QColor(55, 24, 8), 1))
        painter.drawLine(-13, 0, 7, 0)

        # Грудной щиток (переднеспинка)
        painter.setBrush(QBrush(QColor(68, 30, 10)))
        painter.drawEllipse(QPointF(8, 0), 5, 5.2)

        # Голова
        painter.setBrush(QBrush(QColor(40, 18, 8)))
        painter.drawEllipse(QPointF(13, 0), 2.5, 2.8)

        painter.restore()


class DesktopOverlay(QWidget):
    def __init__(self):
        super().__init__()
        # Настройка прозрачного окна поверх всего, без рамок и без перехвата мыши
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool |
            Qt.WindowTransparentForInput
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground)

        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen)

        # В начале 30 тараканов
        self.roaches = [Cockroach(screen.width(), screen.height()) for _ in range(30)]

        # Таймер отрисовки (60 FPS)
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self.tick)
        self.anim_timer.start(16)

        # Таймер размножения: +2 таракана раз в минуту (60 000 мс)
        self.breed_timer = QTimer(self)
        self.breed_timer.timeout.connect(self.breed)
        self.breed_timer.start(60000)

    def breed(self):
        for _ in range(2):
            self.roaches.append(Cockroach(self.width(), self.height()))

    def tick(self):
        # Проверка комбинации Z + M (работает и на английской, и на русской раскладке)
        if (keyboard.is_pressed('z') and keyboard.is_pressed('m')) or \
           (keyboard.is_pressed('я') and keyboard.is_pressed('ь')):
            QApplication.quit()
            return

        for r in self.roaches:
            r.update()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        for r in self.roaches:
            r.draw(painter)

    # Блокируем стандартное закрытие через Alt+F4
    def closeEvent(self, event):
        event.ignore()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    overlay = DesktopOverlay()
    overlay.show()
    sys.exit(app.exec_())
