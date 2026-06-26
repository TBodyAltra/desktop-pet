"""Transparent always-on-top window for the desktop pet."""

from __future__ import annotations

import logging
from typing import Callable

from PySide6.QtCore import QPoint, Qt, QTimer
from PySide6.QtGui import QAction, QGuiApplication, QMouseEvent, QPixmap
from PySide6.QtWidgets import QApplication, QLabel, QMenu, QSystemTrayIcon, QWidget

from pet.behavior import BehaviorState
from pet.hotkeys import GlobalHotkeyFilter
from pet.sprites import CANVAS, CatVariant, Pose, SCALE, render_frame


class PetWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.state = BehaviorState()
        self._drag_offset = QPoint()
        self._dragging = False
        self._on_quit: Callable[[], None] | None = None
        self._hotkey_filter: GlobalHotkeyFilter | None = None

        self._label = QLabel(self)
        self._label.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._bubble = QLabel(self)
        self._bubble.setStyleSheet(
            "background: rgba(20, 20, 20, 210); color: #E2E8F0; "
            "border: 2px solid #4A5568; border-radius: 4px; padding: 4px 6px; "
            "font-family: 'Consolas', 'Courier New', monospace; font-size: 11px;"
        )
        self._bubble.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._bubble.hide()

        self._bubble_timer = QTimer(self)
        self._bubble_timer.setSingleShot(True)
        self._bubble_timer.timeout.connect(self._bubble.hide)

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

    def _show_bubble(self, text: str, ms: int = 3500) -> None:
        self._bubble.setText(text)
        self._bubble.adjustSize()
        self._bubble.move(max(0, (CANVAS - self._bubble.width()) // 2), 0)
        self._bubble.show()
        self._bubble.raise_()
        self._bubble_timer.start(ms)

    def _on_tick(self) -> None:
        try:
            dx, dy = self.state.tick()
            if dx or dy:
                self._move_within_screen(dx, dy)
            self._refresh_sprite()
        except Exception:  # noqa: BLE001 - keep the animation loop alive
            logging.exception("Error in animation tick")

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
            variant=self.state.variant,
            drops=self.state.drops.drops,
        )
        self._label.setPixmap(pixmap)

    def _grid_from_event(self, event: QMouseEvent) -> tuple[int, int]:
        local = event.position().toPoint()
        return local.x() // SCALE, local.y() // SCALE

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            grid_x, grid_y = self._grid_from_event(event)
            collected = self.state.drops.try_collect(grid_x, grid_y)
            if collected is not None:
                label = "经验球 +1" if collected.name == "XP" else "小鱼干 +1"
                self._show_bubble(label, 1500)
                self._refresh_sprite()
                event.accept()
                return

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

    def _toggle_pause(self) -> None:
        self.state.toggle_pause()

    def _reset_position(self) -> None:
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
    icon.setToolTip("MC 方块猫 | Ctrl+Alt+P")
    icon.show()
    return icon
