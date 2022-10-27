import functools
from argparse import ArgumentParser
from logging import StreamHandler
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Literal

from PySide6.QtGui import QKeyEvent, QFont
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPlainTextEdit

from chemistry_lang import evaluate, interpreter
from chemistry_lang.ch_handler import logger
from chemistry_lang.ch_work import NativeWork


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
    )
    from PySide6.QtCore import Qt
    from qt_material import apply_stylesheet

    def row(*widgets, spacing=4, as_layout=False):
        layout = QHBoxLayout()
        layout.setSpacing(spacing)
        for widget in widgets:
            layout.addWidget(widget)
        if as_layout:
            return layout
        widget = QWidget()
        widget.setLayout(layout)
        return widget

    def column(*widgets, spacing=4, as_layout=False):
        layout = QVBoxLayout()
        layout.setSpacing(spacing)
        for widget in widgets:
            layout.addWidget(widget)
        if as_layout:
            return layout
        widget = QWidget()
        widget.setLayout(layout)
        return widget

    def title(text):
        label = QLabel(text)
        label.setStyleSheet("font-size: 10px")
        label.setStyleSheet("font-weight: bold")
        return label

    class Stream(QTextEdit):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.setAcceptRichText(True)
            self.setReadOnly(True)

        def write(self, text, stream: Literal["stdout", "stderr"] = "stdout"):
            style = {}
            if stream == "stdout":
                style["color"] = "black"
            elif stream == "stderr":
                style["color"] = "red"
            else:
                raise ValueError(f"Unknown stream {stream}")
            style_str = ";".join(f"{k}: {v}" for k, v in style.items())
            self.document().setHtml(
                self.document().toHtml() + f'<span style="{style_str}">{text}</span>'
            )

        def flush(self):
            pass

        def read(self):
            return self.text.toPlainText()

        def as_stream(self, stream: Literal["stdout", "stderr"] = "stdout"):
            ns = SimpleNamespace()
            ns.write = functools.partial(self.write, stream=stream)
            ns.flush = self.flush
            return ns

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
                column(title("Result"), [result := QTextEdit(), result.setReadOnly(True)][0]),
                spacing=8,
            )
            left = column(title("Input"), input := QPlainTextEdit(), spacing=4)
            main = row(left, right, spacing=8, as_layout=True)
            self.setLayout(main)

            controls = {
                "input": input,
                "output": output,
                "result": result,
            }

            self.__dict__.update(controls)
            self.redirect_output()

            for control in controls.values():
                control.setStyleSheet("font-size: 12px; font-family: Fira Code, monospace")
                control.setFont(QFont("Fira Code, monospace"))

        def clear(self):
            self.output.clear()
            self.result.clear()

        def redirect_output(self):
            env = interpreter.global_env.assign(
                "print", NativeWork(lambda x: self.print(interpreter.stringify(x)), 1)
            ).assign(
                "clear", NativeWork(lambda: self.clear(), 0)
            )
            interpreter.global_env = env
            interpreter.env = env

            logger.addHandler(StreamHandler(self.output.as_stream("stderr")))

        @functools.wraps(Stream.write)
        def print(self, *args, **kwargs):
            self.output.write(*args, **kwargs)

        def eval(self):
            code = self.input.toPlainText()
            result: Any
            try:
                result = evaluate(code)
            except Exception as e:
                result = str(e)
            self.result.setText(interpreter.stringify(result))

        def keyPressEvent(self, event: QKeyEvent):
            if event.key() == Qt.Key_Return and event.modifiers() == Qt.ControlModifier:
                self.eval()

    class MainWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Chemistry Lang")
            self.setCentralWidget(MainWidget(self))

    app = QApplication()
    window = MainWindow()
    apply_stylesheet(app, theme="light_blue.xml")
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
