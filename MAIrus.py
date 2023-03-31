import os
import openai
import time
from functools import partial
from enum import Enum
import threading
import subprocess

import sys

from pymel.core import *
import maya.OpenMayaUI as omui

from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets
from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *

from shiboken2 import wrapInstance

from utils import *

from Prefs import *

import maya.OpenMaya as OpenMaya

# ######################################################################################################################

# TODO Change the prefs name for this project
_FILE_NAME_PREFS = "mAIrus"

_MODELS = {
    "gpt-4": {
        "max_token":8192,
        "beautified":"GPT 4",
    },
    "gpt-3.5-turbo":{
        "max_token":4096,
        "beautified":"GPT 3.5",
    },
    "text-davinci-003":{
        "max_token":4096,
        "beautified":"GPT 3",
    },
}

_WAITING_COLOR = "#AC8E33"
_COMPUTING_COLOR = "#6F9EF5"
_OUTPUT_SUCCESS_COLOR = "green"
_OUTPUT_ERROR_COLOR = "red"
_INTERVAL_COMPUTING = 0.75

# ######################################################################################################################


class MAIrusState(Enum):
    INACTIVE = 0
    WAITING = 10
    COMPUTING = 20
    OUTPUTING_SUCCESS = 30
    OUTPUTING_ERROR = 40

class MAIrus(QDialog):

    def __init__(self, prnt=wrapInstance(int(omui.MQtUtil.mainWindow()), QWidget)):
        super(MAIrus, self).__init__(prnt)
        
        # Common Preferences (common preferences on all tools)
        self.__common_prefs = Prefs()
        # Preferences for this tool
        self.__prefs = Prefs(_FILE_NAME_PREFS)

        # Model attributes
        self.__mAIrus_state = MAIrusState.WAITING
        self.__model = "gpt-3.5-turbo"
        openai.api_key = open(os.path.join(os.path.dirname(__file__),"openai_key.py"),"r").read()

        # UI attributes
        self.__ui_width = 600
        self.__ui_height = 800
        self.__ui_min_width = 400
        self.__ui_min_height = 500
        self.__ui_pos = QDesktopWidget().availableGeometry().center() - QPoint(self.__ui_width,self.__ui_height)/2

        self.__retrieve_prefs()

        # name the window
        self.setWindowTitle("mAIrus")
        # make the window a "tool" in Maya's eyes so that it stays on top when you click off
        self.setWindowFlags(QtCore.Qt.Tool)
        # Makes the object get deleted from memory, not just hidden, when it is closed.
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        # Create the layout, linking it to actions and refresh the display
        self.__create_ui()
        self.__refresh_ui()

    # Save preferences
    def __save_prefs(self):
        size = self.size()
        self.__prefs["window_size"] = {"width": size.width(), "height": size.height()}
        pos = self.pos()
        self.__prefs["window_pos"] = {"x": pos.x(), "y": pos.y()}
        self.__prefs["model"] = self.__model

    # Retrieve preferences
    def __retrieve_prefs(self):
        if "window_size" in self.__prefs:
            size = self.__prefs["window_size"]
            self.__ui_width = size["width"]
            self.__ui_height = size["height"]

        if "window_pos" in self.__prefs:
            pos = self.__prefs["window_pos"]
            self.__ui_pos = QPoint(pos["x"],pos["y"])

        if "model" in self.__prefs:
            self.__model = self.__prefs["model"]

    def showEvent(self, arg__1: QShowEvent) -> None:
        pass

    # Remove callbacks
    def hideEvent(self, arg__1: QCloseEvent) -> None:
        self.__mAIrus_state = MAIrusState.INACTIVE
        self.__save_prefs()

    # Create the ui
    def __create_ui(self):
        # Reinit attributes of the UI
        self.setMinimumSize(self.__ui_min_width, self.__ui_min_height)
        self.resize(self.__ui_width, self.__ui_height)
        self.move(self.__ui_pos)

        height_button = 35

        # Main Layout
        main_lyt = QVBoxLayout()
        main_lyt.setAlignment(Qt.AlignTop)
        main_lyt.setContentsMargins(10, 15, 10, 15)
        main_lyt.setSpacing(10)
        self.setStyleSheet("font-size:12px")
        self.setLayout(main_lyt)

        # Intro and Instructions
        intro_lbl = QLabel(
            "Make a request to mAIrus. It will try to answer you as best as possible with Python code.")
        intro_lbl.setWordWrap(True)
        intro_lbl.setAlignment(Qt.AlignCenter)
        instruction_lbl = QLabel(
            "Request example : \nGive me an UI displaying a list of the names of all the nodes in the scene. "
            "Also I want to be able to select multiple nodes in the UI in order to delete them with a button")
        instruction_lbl.setWordWrap(True)
        instruction_lbl.setAlignment(Qt.AlignCenter)
        main_lyt.addWidget(intro_lbl)
        main_lyt.addWidget(instruction_lbl)

        # Model combobox
        self.__ui_model_combobox = QComboBox()
        for model, model_data in _MODELS.items():
            self.__ui_model_combobox.addItem(model_data["beautified"], userData=model)
        self.__ui_model_combobox.currentIndexChanged.connect(self.__on_model_changed)
        main_lyt.addWidget(self.__ui_model_combobox)

        # Input Area
        self.__ui_input_area = QPlainTextEdit(self)
        self.__ui_input_area.setPlaceholderText("Write your request here")
        main_lyt.addWidget(self.__ui_input_area)

        # Executing phase layout
        executing_phase_layout = QHBoxLayout()
        main_lyt.addLayout(executing_phase_layout)

        # Submit request button
        self.__ui_submit_request_btn = QPushButton("Ask to mAIrus >>>")
        self.__ui_submit_request_btn.setFixedHeight(height_button)
        self.__ui_submit_request_btn.setStyleSheet("QPushButton{font-weight:bold}")
        self.__ui_submit_request_btn.clicked.connect(self.__send_to_openai)
        executing_phase_layout.addWidget(self.__ui_submit_request_btn,2)

        # mAIrus state
        self.__ui_mAIrus_state_lbl = QLabel()
        self.__ui_mAIrus_state_lbl.setAlignment(Qt.AlignCenter)
        executing_phase_layout.addWidget(self.__ui_mAIrus_state_lbl,2)

        # Output Area
        self.__ui_output_area = QPlainTextEdit(self)
        self.__ui_output_area.setPlaceholderText("mAIrus response will be displayed here")
        self.__ui_output_area.setReadOnly(True)
        main_lyt.addWidget(self.__ui_output_area)

        # Use response layout
        use_response_phase_layout = QHBoxLayout()
        main_lyt.addLayout(use_response_phase_layout)

        # Stop computing button
        self.__ui_stop_computing_btn = QPushButton("Stop")
        self.__ui_stop_computing_btn.setFixedHeight(height_button)
        use_response_phase_layout.addWidget(self.__ui_stop_computing_btn)

        # Execute Response button
        self.__ui_execute_response_btn = QPushButton("Execute")
        self.__ui_execute_response_btn.setFixedHeight(height_button)
        use_response_phase_layout.addWidget(self.__ui_execute_response_btn,1)

        # Copy ro ClipBoard button
        self.__ui_copy_response_btn = QPushButton("Copy to ClibBoard")
        self.__ui_copy_response_btn.setFixedHeight(height_button)
        use_response_phase_layout.addWidget(self.__ui_copy_response_btn,1)


    # Refresh the ui according to the model attribute
    def __refresh_ui(self):
        for index in range(self.__ui_model_combobox.count()):
            if self.__ui_model_combobox.itemData(index,Qt.UserRole) == self.__model:
                self.__ui_model_combobox.setCurrentIndex(index)
        self.__refresh_mairus_state()

    def __refresh_mairus_state(self):
        if self.__mAIrus_state == MAIrusState.WAITING:
            self.__ui_mAIrus_state_lbl.setStyleSheet("border:1px solid " + _WAITING_COLOR)
            self.__ui_mAIrus_state_lbl.setText("Waiting input request")
        elif self.__mAIrus_state == MAIrusState.COMPUTING:
            weight_border = int((time.time() % (_INTERVAL_COMPUTING*2))/_INTERVAL_COMPUTING)
            self.__ui_mAIrus_state_lbl.setStyleSheet("border:"+str(weight_border)+"px solid " + _COMPUTING_COLOR)
            self.__ui_mAIrus_state_lbl.setText("Computing response")
            threading.Timer(_INTERVAL_COMPUTING, self.__refresh_mairus_state).start()
        elif self.__mAIrus_state == MAIrusState.OUTPUTING_SUCCESS:
            self.__ui_mAIrus_state_lbl.setStyleSheet("border:1px solid " + _OUTPUT_SUCCESS_COLOR)
            self.__ui_mAIrus_state_lbl.setText("Output Success")
        elif self.__mAIrus_state == MAIrusState.OUTPUTING_ERROR:
            self.__ui_mAIrus_state_lbl.setStyleSheet("border:1px solid " + _OUTPUT_ERROR_COLOR)
            self.__ui_mAIrus_state_lbl.setText("Output Error")

    def __on_model_changed(self, index):
        self.__model = self.__ui_model_combobox.itemData(index,Qt.UserRole)

    def __send_to_openai(self):
        prompt = self.__ui_input_area.toPlainText()

        # Generate a response
        completion = openai.Completion.create(
            engine=self.__model,
            prompt=prompt,
            max_tokens=_MODELS[self.__model]["max_token"] - len(prompt),
            temperature=0.5,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )

        self.__ui_output_area.setPlainText(completion.choices[0].text.strip(" \n"))