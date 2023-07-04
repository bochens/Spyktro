import sys, os
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtWidgets import *
from PySide6.QtGui import QIcon, QPixmap
from sPyktro_raman import Raman_Spectra
from sPyktro_window import Ui_MainWindow

class Raman_Spectra_Init_Dialog(QDialog):
    # open after load is clicked from the menu and a file selected in the file navigation dialog
    def __init__(self, path):
        super().__init__()
        self.path = path

        self.show_name_error_bool = False
        self.show_limit_error_bool = False
        self.show_range_error_bool = False

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.name_textboxes = []
        self.start_textboxes = []
        self.end_textboxes = []

        self.layout = QFormLayout()
        if len(self.path) == 1:
            self.setWindowTitle("Load a Spectra")
            message = QLabel("Laod a file")
        elif len(self.path) > 1:
            self.setWindowTitle("Load Spectras")
            message = QLabel("Laod " + str(len(self.path)) + " files")
        self.layout.addRow(message)

        for i in range(len(self.path)):
            textbox1 = QLineEdit(self)
            textbox2 = QLineEdit(self)
            textbox3 = QLineEdit(self)
            file_name = os.path.splitext(os.path.basename(self.path[i]))[0]
            textbox1.setText(file_name)
            sub_layout = QHBoxLayout()
            sub_layout.addWidget(QLabel("Name:"))
            sub_layout.addWidget(textbox1)
            sub_layout.addWidget(QLabel("x axis:"))
            sub_layout.addWidget(QLabel("Start:"))
            sub_layout.addWidget(textbox2)
            sub_layout.addWidget(QLabel("End:"))
            sub_layout.addWidget(textbox3)
            self.layout.addRow("Sample "+str(i)+" :", sub_layout)
            self.name_textboxes.append(textbox1)
            self.start_textboxes.append(textbox2)
            self.end_textboxes.append(textbox3)
        
        self.over_textbox1 = None
        self.over_textbox2 = None
        self.over_textbox3 = None
        if len(self.path) > 1:
            self.over_textbox1 = QLineEdit(self)
            self.over_textbox2 = QLineEdit(self)
            self.over_textbox3 = QLineEdit(self)
            override_layout = QHBoxLayout()
            override_layout.addWidget(QLabel("Name:"))
            override_layout.addWidget(self.over_textbox1)
            override_layout.addWidget(QLabel("x axis:"))
            override_layout.addWidget(QLabel("Start:"))
            override_layout.addWidget(self.over_textbox2)
            override_layout.addWidget(QLabel("End:"))
            override_layout.addWidget(self.over_textbox3)

            self.layout.addRow("Set for all :", override_layout)


        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)

        self.sample_name_string_list = []
        self.start_float_list = []
        self.end_float_list = []
        self.return_path = []

    def accept(self):
        if len(self.path) > 1:
            self.over_sample_name_string = self.over_textbox1.text()
            self.over_start_string = self.over_textbox2.text()
            self.over_end_string = self.over_textbox3.text()
        else:
            self.over_sample_name_string = None
            self.over_start_string = None
            self.over_end_string = None

        for i in range(len(self.path)):
            if len(self.path) == 1 or self.over_sample_name_string == "":
                sample_name_string = self.name_textboxes[i].text()
            else:
                sample_name_string = self.over_sample_name_string
            
            if len(self.path) == 1 or self.over_start_string == "":
                start_string = self.start_textboxes[i].text()
            else:
                start_string = self.over_start_string
            
            if len(self.path) == 1 or self.over_end_string == "":
                end_string = self.end_textboxes[i].text()
            else:
                end_string = self.over_end_string

            if sample_name_string == "":
                self.show_name_error_bool = True
            else:
                try:
                    if start_string != "":
                        start_float = float(start_string)
                    else:
                        start_float = 0
                    
                    if end_string != "":
                        end_float = float(end_string)
                    else:
                        end_float = None
                
                except:
                    self.show_limit_error_bool = True
                
                else:
                    if start_float is not None and end_float is not None and start_float >= end_float:
                        print("test")
                        self.show_range_error_bool = True
                    else:
                        self.sample_name_string_list.append(sample_name_string)
                        self.start_float_list.append(start_float)
                        self.end_float_list.append(end_float)
                        self.return_path.append(self.path[i])
        
        if self.show_name_error_bool:
            self.show_error_win("Input Error", "Missing sample name")

        if self.show_limit_error_bool:
            self.show_error_win("Input Error", "Please input a number for Start and End Ramanshift")

        if self.show_range_error_bool:
            self.show_error_win("Input Error", "Start has to be smaller than End")

        super().accept()

    def reject(self):
        print ("Raman Spectra Init Dialog dialog canceled")
        super().reject()
    
    def show_error_win(self, text, informative_txt):
        error_win = QMessageBox()
        error_win.setWindowTitle("Error")
        error_win.setText(text)
        error_win.setInformativeText(informative_txt)
        error_win.exec_()

class Preferences_window(QDialog):
    def __init__(self, background_color):
        super().__init__()
        self.setWindowTitle("Preferences")

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.background_color = background_color

        self.radiobox = QHBoxLayout()
        self.r1 = QRadioButton("White")
        self.r2 = QRadioButton("Black")

        if background_color == "w":
            self.r1.setChecked(True)
        elif background_color == "k":
            self.r2.setChecked(True)

        self.radiobox.addWidget(self.r1)
        self.radiobox.addWidget(self.r2)
        self.radiobox.addStretch()

        self.layout = QFormLayout()
        self.layout.addRow(QLabel("Chart background"),self.radiobox)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)

    def accept(self):
        if self.r1.isChecked():
            self.background_color = 'w'
        elif self.r2.isChecked():
            self.background_color = 'k'
        super().accept()

    def reject(self):
        super().reject()

class Line_window(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Line Width")

        self.line_width = 0

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.textbox_linewidth = QLineEdit(self)

        self.layout = QFormLayout()

        self.layout.addRow(QLabel("Set Line Width"), self.textbox_linewidth)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)

    def accept(self):
        line_width = self.textbox_linewidth.text()
        try:
            self.line_width = float(line_width)
            super().accept()      

        except:
            self.show_error_win("Input Error", "Please input a number for Line Width")
            super().reject()

    def reject(self):
        super().reject()

    def show_error_win(self, text, informative_txt):
        error_win = QMessageBox()
        error_win.setWindowTitle("Error")
        error_win.setText(text)
        error_win.setInformativeText(informative_txt)
        error_win.exec_()