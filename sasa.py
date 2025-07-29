#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Project: SASA
Description: Sleep Apnea Saturation Analysis
Author: Christopher Scott Ward, christopher.ward@bcm.edu
Created: 2025
License: MIT-X

GUI wrapper for SASA
"""
__version__ = "0.1.0"
__license__ = "MIT License"
__license_text__ = """
MIT License

Copyright (c) 2021 Christopher S Ward

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

# %% import libraries
import main

import logging
import os
from PySide6 import QtWidgets
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile
import sys


class GUI_Logger:
    def __init__(
        self,
        gui_loglevel: int = logging.INFO,
        console_loglevel: int = logging.ERROR,
        file_loglevel: int = logging.DEBUG,
        log_file_path: str = None,
        gui_handler: QtWidgets.QTextEdit = None,
        logname: str = __name__,
    ):

        self.log_levels = {
            "notset": 0,
            "debug": 10,
            "info": 20,
            "warning": 30,
            "error": 40,
            "critical": 50,
        }

        self.logger = logging.getLogger(logname)
        self.logger.setLevel(logging.DEBUG)

        self.gui_handler = gui_handler
        self.gui_loglevel = self.fix_level(gui_loglevel)

        # create format for log and apply to handlers
        log_format = logging.Formatter(
            "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
        )

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(console_loglevel)
        console_handler.setFormatter(log_format)
        self.logger.addHandler(console_handler)

        if log_file_path:
            file_handler = logging.FileHandler(log_file_path)
            file_handler.setLevel(file_loglevel)
            file_handler.setFormatter(log_format)
            self.logger.addHandler(file_handler)

        # log initial inputs
        self.log("info", "Logger Started")

    def info(self, msg):
        self.log("info", msg)

    def debug(self, msg):
        self.log("debug", msg)

    def warning(self, msg):
        self.log("warning", msg)

    def error(self, msg):
        self.log("error", msg)

    def fix_level(self, level):
        if type(level) is not int:
            if type(level) is not str:
                level = 40
            elif level.lower() in self.log_levels:
                level = self.log_levels[level.lower()]
            else:
                level = 40
        elif level not in self.log_levels.values():
            level = 40

        return level

    def log(
        self,
        level,
        message,
        gui_color: str = None,
        gui_style: str = None,
    ):

        if type(level) is not int:
            if type(level) is not str:
                old_level = level
                message += f" |Abnormal log level provided: {old_level}|"
                level = 40
            elif level.lower() in self.log_levels:
                level = self.log_levels[level.lower()]
            else:
                old_level = level
                message += f" |Abnormal log level provided: {old_level}|"
                level = 40
        elif level not in self.log_levels.values():
            old_level = level
            message += f" |Abnormal log level provided: {old_level}|"
            level = 40

        self.logger.log(level, message)
        if level >= self.gui_loglevel and self.gui_handler:
            if not gui_color:
                if level < 20:
                    gui_color = "green"
                elif level > 20:
                    gui_color = "red"
                else:
                    gui_color = "black"
            if not gui_style:
                if level >= 40:
                    gui_style = "strong"

            self.gui_handler.insertHtml(
                (
                    f'<span style="color:{gui_color}"><{gui_style}>'
                    + f"{message}"
                    + f"</{gui_style}></span><br>"
                )
            )
            self.gui_handler.verticalScrollBar().setValue(
                self.gui_handler.verticalScrollBar().maximum()
            )


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, ui):
        super(MainWindow, self).__init__()

        self.ui = ui

        # migrate ui children to parent level of class
        for att, val in ui.__dict__.items():
            setattr(self, att, val)

        self.ui.setWindowTitle(f"SASA - {main.__version__}")

        self.pushButton_input.clicked.connect(self.action_input)
        self.pushButton_output.clicked.connect(self.action_output)
        self.pushButton_settings.clicked.connect(self.action_settings)
        self.pushButton_run.clicked.connect(self.action_run)

        self.logger = GUI_Logger(gui_handler=self.textEdit_log)
        self.textEdit_log.setStyleSheet("background-color: white;")

        self.input_path = None
        self.output_path = None
        self.settings_path = None

    def action_input(self):
        self.input_path = QtWidgets.QFileDialog.getExistingDirectory(
            None, "Select Input Folder"
        )
        self.logger.info(f"input path set: {self.input_path}")

    def action_output(self):
        self.output_path = QtWidgets.QFileDialog.getExistingDirectory(
            None, "Select Output Folder"
        )
        self.logger.info(f"output path set: {self.output_path}")

    def action_settings(self):
        self.settings_path = QtWidgets.QFileDialog.getOpenFileName(
            None, "Select Settings File", "", "Excel Files (*.xlsx);;All Files (*)"
        )
        self.logger.info(f"settings path set: {self.settings_path}")

    def action_run(self):
        if self.input_path and self.output_path and self.settings_path:
            self.logger.info("launching run")
            main.main(
                input_file_path=self.input_path,
                output_file_path=self.output_path,
                settings_file_path=self.settings_path,
                logger=self.logger,
            )
        else:
            self.logger.warning(
                "missing input, settings, or output paths. please complete entry and try again"
            )

    # create the application


def sasa():
    loader = QUiLoader()
    app = QtWidgets.QApplication()
    ui_file = QFile(os.path.join(os.path.dirname(__file__), "gui.ui"))
    window_ui = loader.load(ui_file)

    window_ui.show()

    ui = MainWindow(window_ui)

    ui.version_info = {"GUI": __version__, "MAIN": main.__version__}

    sys.exit(app.exec())


# %% run main
if __name__ == "__main__":
    sasa()
