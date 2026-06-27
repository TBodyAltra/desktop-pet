"""Transparent always-on-top window for the desktop pet."""

from __future__ import annotations

import logging
from collections import deque
from typing import Callable

from PySide6.QtCore import QPoint, QPointF, Qt, QTimer
from PySide6.QtGui import QAction, QCursor, QGuiApplication, QMouseEvent, QPixmap
from PySide6.QtWidgets import QApplication, QLabel, QMenu, QSystemTrayIcon, QWidget

from pet.behavior import FLING_MIN_SPEED, BehaviorState
from pet.hotkeys import GlobalHotkeyFilter
from pet.sprites import CANVAS, CatVariant, Pose, SCALE, render_frame, render_play_frame
from pet.playtime import PLAY_H, PLAY_W


class PetWindow(QWidget):
    CHASE_RANGE = 160
    CHASE_COOLDOWN_TICKS = 90

    def __init__(self) -> None:
        super().__init__()
        self.state = BehaviorState()
        self._drag_offset = QPoint()
        self._dragging = False
        self._drag_history: deque[tuple[QPointF, float]] = deque(maxlen=6)
        self._on_quit: Callable[[], None] | None = None
        self._hotkey_filter: GlobalHotkeyFilter | None = None
        self._chase_cooldown = 0
        self._compact_geometry = self.frameGeometry()

        self._label = QLabel(self)
        self._label.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(CANVAS, CANVAS)
        self._label.setGeometry(0, 0, CANVAS, CANVAS)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_tick)
        self._timer.start(80)

        screen = QGuiApplication.primaryScreen()
        if screen is not None:
            geometry = screen.availableGeometry()
            self.move(geometry.right() - CANVAS - 40, geometry.bottom() - CANVAS - 20)

        self._refresh_sprite()

    def set_quit_handler(self, handler: Callable[[], None]) -> None:
        self._on_quit = handler

    def install_hotkeys(self, app: QApplication) -> None:
        self._hotkey_filter = GlobalHotkeyFilter(self._toggle_visibility)
        app.installNativeEventFilter(self._hotkey_filter)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if self._hotkey_filter is not None:
            self._hotkey_filter.register(int(self.winId()))

    def closeEvent(self, event) -> None:
        if self._hotkey_filter is not None:
            self._hotkey_filter.unregister(int(self.winId()))
        super().closeEvent(event)

    def _toggle_visibility(self) -> None:
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.raise_()

    def _on_tick(self) -> None:
        try:
            if self.state.context_changed:
                self.state.context_changed = False

            if not self._dragging and not self.state.flying and not self.state.playtime.active:
                self._maybe_chase_cursor()

            dx, dy = self.state.tick()

            if self.state.playtime_enter and not self.state.playtime.active:
                self._enter_playtime()

            if self.state.playtime.active:
                if self.state.playtime.tick():
                    self._exit_playtime()
                    self.state.on_playtime_finished()
            elif dx or dy:
                self._move_within_screen(dx, dy)
            self._refresh_sprite()
        except Exception:  # noqa: BLE001 - keep the animation loop alive
            logging.exception("Error in animation tick")

    def _maybe_chase_cursor(self) -> None:
        if self._chase_cooldown > 0:
            self._chase_cooldown -= 1
            return

        cursor = QCursor.pos()
        pet_center = self.frameGeometry().center()
        offset_x = cursor.x() - pet_center.x()
        offset_y = cursor.y() - pet_center.y()

        if abs(offset_x) < 30 or abs(offset_x) > self.CHASE_RANGE or abs(offset_y) > 80:
            return

        self.state.chase_toward(offset_x)
        self._chase_cooldown = self.CHASE_COOLDOWN_TICKS

    def _screen_geometry(self):
        center = QPoint(self.width() // 2, self.height() // 2)
        screen = QGuiApplication.screenAt(self.pos() + center)
        if screen is None:
            screen = QGuiApplication.primaryScreen()
        return screen.availableGeometry() if screen is not None else None

    def _move_within_screen(self, dx: int, dy: int) -> None:
        geometry = self._screen_geometry()
        if geometry is None:
            self.move(self.x() + dx, self.y() + dy)
            return

        new_x = self.x() + dx
        new_y = self.y() + dy
        bounced_x = False
        bounced_y = False

        if new_x <= geometry.left():
            new_x = geometry.left()
            bounced_x = True
        elif new_x + self.width() >= geometry.right():
            new_x = geometry.right() - self.width()
            bounced_x = True

        if new_y <= geometry.top():
            new_y = geometry.top()
            bounced_y = True
        elif new_y + self.height() >= geometry.bottom():
            new_y = geometry.bottom() - self.height()
            bounced_y = True

        self.move(new_x, new_y)

        if self.state.flying:
            self.state.update_flight(new_y)

        if not self.state.flying:
            return

        if bounced_x:
            self.state.bounce_x()
        if bounced_y:
            self.state.bounce_y()

        if bounced_y and new_y >= geometry.bottom() - self.height():
            if abs(self.state.vy) < 4:
                self.state.land()

    def _refresh_sprite(self) -> None:
        if self.state.playtime.active:
            pixmap = render_play_frame(
                self.state.playtime,
                self.state.frame,
                variant=self.state.variant,
            )
        else:
            pixmap = render_frame(
                self.state.pose(),
                self.state.frame,
                facing_left=self.state.facing_left,
                variant=self.state.variant,
                drops=self.state.drops.drops,
            )
        self._label.setPixmap(pixmap)

    def _grid_from_event(self, event: QMouseEvent) -> tuple[int, int]:
        local = event.position().toPoint()
        return local.x() // SCALE, local.y() // SCALE

    def _record_drag_sample(self, global_pos: QPointF) -> None:
        import time

        self._drag_history.append((global_pos, time.monotonic()))

    def _release_velocity(self) -> tuple[float, float]:
        if len(self._drag_history) < 2:
            return 0.0, 0.0

        (x0, t0), (x1, t1) = self._drag_history[0], self._drag_history[-1]
        dt = t1 - t0
        if dt <= 0:
            return 0.0, 0.0

        vx = (x1.x() - x0.x()) / dt * 0.08
        vy = (x1.y() - x0.y()) / dt * 0.08
        return vx, vy

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            if self.state.playtime.active:
                self._exit_playtime()
                self.state.stop_playtime()
                self.state.pet()
                self._refresh_sprite()
                event.accept()
                return

            grid_x, grid_y = self._grid_from_event(event)
            collected = self.state.drops.try_collect(grid_x, grid_y)
            if collected is not None:
                self.state.pet()
                self._refresh_sprite()
                event.accept()
                return

            self._dragging = True
            self._drag_history.clear()
            self._record_drag_sample(event.globalPosition())
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
            return

        if event.button() == Qt.MouseButton.RightButton:
            self._show_menu(event.globalPosition().toPoint())
            event.accept()
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._dragging and not self.state.playtime.active and event.buttons() & Qt.MouseButton.LeftButton:
            self._record_drag_sample(event.globalPosition())
            self.move(event.globalPosition().toPoint() - self._drag_offset)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._dragging:
            self._dragging = False
            vx, vy = self._release_velocity()
            speed = (vx * vx + vy * vy) ** 0.5
            if speed >= FLING_MIN_SPEED:
                self.state.fling(vx, vy)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            if self.state.playtime.active:
                self._exit_playtime()
            self.state.pet()
            self._refresh_sprite()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

    def _show_menu(self, global_pos: QPoint) -> None:
        menu = QMenu(self)

        variant_menu = menu.addMenu("猫咪品种")
        for variant, label in (
            (CatVariant.TABBY, "橘猫 Tabby"),
            (CatVariant.TUXEDO, "黑白 Tuxedo"),
            (CatVariant.SIAMESE, "暹罗 Siamese"),
        ):
            action = QAction(label, self)
            action.setCheckable(True)
            action.setChecked(self.state.variant == variant)
            action.triggered.connect(lambda _checked=False, v=variant: self._set_variant(v))
            variant_menu.addAction(action)

        menu.addSeparator()

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

    def _set_variant(self, variant: CatVariant) -> None:
        self.state.set_variant(variant)
        self._refresh_sprite()

    def _enter_playtime(self) -> None:
        if self.state.playtime.active:
            return
        self._compact_geometry = self.frameGeometry()
        self.state.start_playtime()
        self.setFixedSize(PLAY_W, PLAY_H)
        self._label.setGeometry(0, 0, PLAY_W, PLAY_H)
        geometry = self._screen_geometry()
        if geometry is not None:
            x = min(self.x(), geometry.right() - PLAY_W)
            x = max(geometry.left(), x)
            y = min(self.y(), geometry.bottom() - PLAY_H)
            y = max(geometry.top(), y)
            self.move(x, y)
        self._refresh_sprite()

    def _exit_playtime(self) -> None:
        if not self.state.playtime.active and self.width() == CANVAS:
            return
        self.setFixedSize(CANVAS, CANVAS)
        self._label.setGeometry(0, 0, CANVAS, CANVAS)
        self.move(self._compact_geometry.topLeft())
        self._refresh_sprite()

    def _toggle_pause(self) -> None:
        self.state.toggle_pause()

    def _reset_position(self) -> None:
        if self.state.playtime.active:
            self._exit_playtime()
            self.state.stop_playtime()
        self.state.reset()
        screen = QGuiApplication.primaryScreen()
        if screen is not None:
            geometry = screen.availableGeometry()
            self.move(geometry.right() - CANVAS - 40, geometry.bottom() - CANVAS - 20)
        self._refresh_sprite()

    def _request_quit(self) -> None:
        if self._on_quit is not None:
            self._on_quit()
        else:
            QApplication.quit()


def create_tray_icon(
    app: QApplication,
    window: PetWindow,
    on_show: Callable[[], None],
    on_quit: Callable[[], None],
) -> QSystemTrayIcon:
    pixmap = render_frame(Pose.IDLE, 0, variant=window.state.variant)
    icon = QSystemTrayIcon(pixmap, app)

    tray_menu = QMenu()
    show_action = QAction("显示宠物 (Ctrl+Alt+P)", tray_menu)
    show_action.triggered.connect(on_show)
    tray_menu.addAction(show_action)

    quit_action = QAction("退出", tray_menu)
    quit_action.triggered.connect(on_quit)
    tray_menu.addAction(quit_action)

    icon.setContextMenu(tray_menu)
    icon.setToolTip("桌面宠物 | Ctrl+Alt+P")
    icon.show()
    return icon
