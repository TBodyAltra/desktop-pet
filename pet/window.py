"""Transparent always-on-top window for the desktop pet."""

from __future__ import annotations

import sys
from typing import Callable

from PySide6.QtCore import QPoint, Qt, QTimer
from PySide6.QtGui import QAction, QGuiApplication, QMouseEvent, QPixmap
from PySide6.QtWidgets import QApplication, QLabel, QMenu, QSystemTrayIcon, QWidget

from pet.behavior import BehaviorState
from pet.sprites import CANVAS, Pose, render_frame


class PetWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.state = BehaviorState()
        self._drag_offset = QPoint()
        self._dragging = False
        self._label = QLabel(self)
        self._label.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._on_quit: Callable[[], None] | None = None

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(CANVAS, CANVAS)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_tick)
        self._timer.start(80)

        screen = QGuiApplication.primaryScreen()
        if screen is not None:
            geometry = screen.availableGeometry()
            self.move(
                geometry.right() - CANVAS - 40,
                geometry.bottom() - CANVAS - 20,
            )

        self._refresh_sprite()

    def set_quit_handler(self, handler: Callable[[], None]) -> None:
        self._on_quit = handler

    def _on_tick(self) -> None:
        dx, dy = self.state.tick()
        if dx or dy:
            self._move_within_screen(dx, dy)
        self._refresh_sprite()

    def _move_within_screen(self, dx: int, dy: int) -> None:
        screen = QGuiApplication.screenAt(self.pos() + QPoint(CANVAS // 2, CANVAS // 2))
        if screen is None:
            screen = QGuiApplication.primaryScreen()
        if screen is None:
            self.move(self.x() + dx, self.y() + dy)
            return

        geometry = screen.availableGeometry()
        new_x = max(geometry.left(), min(self.x() + dx, geometry.right() - self.width()))
        new_y = max(geometry.top(), min(self.y() + dy, geometry.bottom() - self.height()))
        self.move(new_x, new_y)

    def _refresh_sprite(self) -> None:
        pixmap: QPixmap = render_frame(
            self.state.pose(),
            self.state.frame,
            facing_left=self.state.facing_left,
        )
        self._label.setPixmap(pixmap)
        self._label.resize(CANVAS, CANVAS)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
            return
        if event.button() == Qt.MouseButton.RightButton:
            self._show_menu(event.globalPosition().toPoint())
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._dragging and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_offset)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = False
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.state.pet()
            self._refresh_sprite()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

    def _show_menu(self, global_pos: QPoint) -> None:
        menu = QMenu(self)
        pause_action = QAction("继续动画" if self.state.paused else "暂停动画", self)
        pause_action.triggered.connect(self._toggle_pause)
        menu.addAction(pause_action)

        reset_action = QAction("重置位置", self)
        reset_action.triggered.connect(self._reset_position)
        menu.addAction(reset_action)

        menu.addSeparator()
        quit_action = QAction("退出", self)
        quit_action.triggered.connect(self._request_quit)
        menu.addAction(quit_action)
        menu.exec(global_pos)

    def _toggle_pause(self) -> None:
        self.state.toggle_pause()

    def _reset_position(self) -> None:
        self.state.reset()
        screen = QGuiApplication.primaryScreen()
        if screen is not None:
            geometry = screen.availableGeometry()
            self.move(
                geometry.right() - CANVAS - 40,
                geometry.bottom() - CANVAS - 20,
            )
        self._refresh_sprite()

    def _request_quit(self) -> None:
        if self._on_quit is not None:
            self._on_quit()
        else:
            QApplication.quit()


def create_tray_icon(app: QApplication, on_show: Callable[[], None], on_quit: Callable[[], None]) -> QSystemTrayIcon:
    pixmap = render_frame(Pose.IDLE, 0)
    icon = QSystemTrayIcon(pixmap, app)

    tray_menu = QMenu()
    show_action = QAction("显示宠物", tray_menu)
    show_action.triggered.connect(on_show)
    tray_menu.addAction(show_action)

    quit_action = QAction("退出", tray_menu)
    quit_action.triggered.connect(on_quit)
    tray_menu.addAction(quit_action)

    icon.setContextMenu(tray_menu)
    icon.setToolTip("桌面宠物")
    icon.show()
    return icon
