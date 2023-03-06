import functools
from argparse import ArgumentParser
from logging import StreamHandler
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Literal

from chemistry_lang import evaluate, interpreter, handler
from chemistry_lang.ch_handler import logger
from chemistry_lang.objs.ch_work import NativeWork


def parse():
    parser = ArgumentParser()
    gp = parser.add_mutually_exclusive_group()
    gp.add_argument(
        "-f",
        "--file",
        type=Path,
        help="File to run",
        nargs="?",
        default=None,
    )
    gp.add_argument("-g", "--gui", action="store_true", help="Run gui")
    return parser.parse_args()


def run(file: str | Path):
    """
    Run a file

    :param file: File to run
    """
    file = Path(file)
    if not file.exists():
        print(f"File {file} does not exist")
        exit(1)
    with open(file) as f:
        evaluate(f.read())


def repl():
    """
    Just a REPL
    """

    while True:
        lines: list[str] = []
        try:
            while True:
                line = input(">>> ")
                if line == "":
                    break
                lines.append(line)
        except (KeyboardInterrupt, EOFError):
            exit(0)
        result = evaluate("\n".join(lines))
        print(result)


def gui():
    """
    Gui version of REPL
    """

    from PySide6.QtWidgets import (
        QApplication,
        QMainWindow,
        QTextEdit,
        QVBoxLayout,
        QWidget,
        QHBoxLayout,
        QLabel,
        QPlainTextEdit,
    )
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QIcon, QKeyEvent, QTextCursor, QFont

    def row(
        *widgets: QWidget,
        spacing: int = 4,
        as_layout: bool = False,
        stylesheet: str = "",
    ) -> QHBoxLayout | QWidget:
        """
        Create a row layout/QHBoxLayout
        """

        layout = QHBoxLayout()
        return _layout_helper(as_layout, layout, spacing, widgets, stylesheet)

    def column(
        *widgets: QWidget,
        spacing: int = 4,
        as_layout: bool = False,
        stylesheet: str = "",
    ) -> QVBoxLayout | QWidget:
        """
        Create a column layout/QVBoxLayout
        """

        layout = QVBoxLayout()
        return _layout_helper(as_layout, layout, spacing, widgets, stylesheet)

    def _layout_helper(as_layout, layout, spacing, widgets, stylesheet):
        layout.setSpacing(spacing)
        layout.setContentsMargins(0, 0, 0, 0)
        for widget in widgets:
            layout.addWidget(widget)
        if as_layout:
            assert not stylesheet, "Cannot set stylesheet on layout"
            return layout
        widget = QWidget()
        widget.setLayout(layout)
        widget.setContentsMargins(0, 0, 0, 0)
        widget.setStyleSheet(stylesheet)
        return widget

    def title(text: str) -> QWidget:
        """
        Create a title widget
        """

        label = QLabel(text)
        label.setStyleSheet(
            """
            font-family: Inter, "Segoe UI", sans-serif;
            font-size: 16px;
            font-weight: 600;
            color: #1e293b;
            """
        )
        font = label.font()
        font.setStyleStrategy(QFont.PreferAntialias)
        return label

    class Stream(QTextEdit):
        def __init__(
            self, *args, type: Literal["stdout", "stderr"] = "stdout", **kwargs
        ):
            super().__init__(*args, **kwargs)
            self.setAcceptRichText(True)
            self.setReadOnly(True)
            self.type = type
            self.setStyleSheet(
                """
                border: 1px solid #d1d5db;
                border-radius: 4px;
                font-size: 14px;
                font-family: Fira Code, "Segoe UI Mono", monospace;
                padding: 8px;
                """
            )

        def clear(self):
            self.document().clear()

        def write(self, text, type: Literal["stdout", "stderr"] = ""):
            self.document().lastBlock()
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.End)
            style = "black" if (type or self.type) == "stdout" else "red"
            cursor.insertHtml(f'<p style="color: {style}">{text}</p>')
            cursor.insertHtml("<br>")
            self.setTextCursor(cursor)
            self.ensureCursorVisible()

        def flush(self):
            pass

        def read(self):
            return self.toPlainText()

        def as_stream(self, type: Literal["stdout", "stderr"] = ""):
            return SimpleNamespace(
                write=lambda x: self.write(x, type=type),
                flush=lambda: None,
                read=lambda: self.read(),
            )

    class MainWidget(QWidget):
        """
        |----------------|
        | input | stream |
        |       |--------|
        |       |  eval  |
        | ---------------|
        """

        def __init__(self, parent: QMainWindow):
            super().__init__(parent)
            self.parent = parent
            right = column(
                column(title("Output"), output := Stream()),
                column(
                    title("Result"),
                    result := Stream(),
                ),
                spacing=8,
            )
            left = column(
                title("Input"),
                repl := QPlainTextEdit(),
            )
            self.setLayout(row(left, right, as_layout=True, spacing=16))
            self.setContentsMargins(16, 16, 16, 16)
            repl.setStyleSheet(
                """
                font-family: Fira Code, "Segoe UI Mono", monospace;
                font-size: 14px;
                background-color: #e2e8f0;
                border: 1px solid #d1d5db;
                border-radius: 4px;
                padding: 8px;
                """
            )
            self.repl = repl
            self.output = output
            self.result = result
            self.redirect_output()

        def clear(self):
            self.output.clear()
            self.result.clear()

        def redirect_output(self):
            env = interpreter.global_env.assign(
                "print",
                NativeWork(lambda x: [self.print(interpreter.stringify(x) + "\n"), x][1], 1),
            ).assign("clear", NativeWork(lambda: self.clear(), 0))
            interpreter.global_env = env
            interpreter.env = env
            logger.addHandler(StreamHandler(self.output.as_stream("stderr")))

        @functools.wraps(Stream.write)
        def print(self, *args, **kwargs):
            self.output.write(*args, **kwargs)

        def eval(self):
            code = self.repl.toPlainText()
            result: Any
            try:
                result = evaluate(code)
            except Exception as e:
                result = str(e)
                handler.had_error = False
            self.result.setText(interpreter.stringify(result))

        def keyPressEvent(self, event: QKeyEvent):
            if event.key() == Qt.Key_Return and event.modifiers() == Qt.ControlModifier:
                self.eval()
            if event.key() == Qt.Key_L and event.modifiers() == Qt.ControlModifier:
                self.clear()
            if event.key() == Qt.Key_R and event.modifiers() == Qt.ControlModifier:
                interpreter.reset()
                self.redirect_output()
            super().keyPressEvent(event)

    class MainWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Chemistry Lang")
            self.setCentralWidget(MainWidget(self))
            self.setStyleSheet(
                """
                background-color: #f8fafc;
                """
            )

    app = QApplication()
    icon = QIcon("assets/atom.png")
    app.setWindowIcon(icon)
    window = MainWindow()
    window.show()
    app.exec()


def main():
    args = parse()
    if args.gui:
        gui()
    elif args.file:
        run(args.file)
    else:
        repl()


if __name__ == "__main__":
    main()
