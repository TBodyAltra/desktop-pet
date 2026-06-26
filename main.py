"""Entry point for the Windows desktop pet."""

from __future__ import annotations

import logging
import os
import sys
import tempfile
import traceback

from PySide6.QtWidgets import QApplication

from pet.window import PetWindow, create_tray_icon


LOG_PATH = os.path.join(tempfile.gettempdir(), "desktop_pet.log")


def _setup_logging() -> None:
    logging.basicConfig(
        filename=LOG_PATH,
        filemode="w",
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    logging.info("Desktop pet starting. Python %s", sys.version)

    def _excepthook(exc_type, exc_value, exc_tb) -> None:
        logging.error(
            "Uncaught exception:\n%s",
            "".join(traceback.format_exception(exc_type, exc_value, exc_tb)),
        )
        sys.__excepthook__(exc_type, exc_value, exc_tb)

    sys.excepthook = _excepthook


def _show_fatal(message: str) -> None:
    try:
        from PySide6.QtWidgets import QMessageBox

        QMessageBox.critical(None, "桌面宠物启动失败", message)
    except Exception:  # noqa: BLE001
        pass


def main() -> int:
    _setup_logging()

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
    logging.info("Event loop started.")
    return app.exec()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001
        logging.error("Fatal startup error:\n%s", traceback.format_exc())
        _show_fatal(f"{exc}\n\n详细日志: {LOG_PATH}")
        raise SystemExit(1)
