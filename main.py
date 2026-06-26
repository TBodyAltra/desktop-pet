"""Entry point for the Windows desktop pet."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from pet.window import PetWindow, create_tray_icon


def main() -> int:
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("Desktop Pet")
    app.setApplicationDisplayName("MC 方块猫")

    window = PetWindow()
    window.install_hotkeys(app)

    def show_window() -> None:
        window.show()
        window.raise_()
        window.activateWindow()

    def quit_app() -> None:
        app.quit()

    window.set_quit_handler(quit_app)
    tray = create_tray_icon(app, window, show_window, quit_app)
    tray.activated.connect(
        lambda reason: show_window()
        if reason == tray.ActivationReason.DoubleClick
        else None
    )

    show_window()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
