import sys, os
import numpy as np
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt, QSignalBlocker, QEvent
from PySide6.QtWidgets import *
from PySide6.QtGui import QIcon, QPixmap, QIntValidator, QDoubleValidator, QGuiApplication, QAction, QPen, QColor
from PySide6.QtQml import QQmlApplicationEngine
import pyqtgraph as pg
from pyqtgraph import PlotWidget
from sPyktro_raman import Raman_Spectra
from sPyktro_window import Ui_MainWindow
from sPyktro_misc import Raman_Spectra_Init_Dialog, Preferences_window, Line_window

class Spectra_item():
    def __init__(self, spectra, line_color, line_width = 1, plot_bool = True, select_bool = False):
        
        self.spectra = spectra
        self.line_color = line_color
        self.line_width = line_width
        self.plot_bool = plot_bool
        self.select_bool = select_bool

    def copy(self):
        return Spectra_item(self.spectra.copy(), QColor(self.line_color), 
            line_width = self.line_width, plot_bool = self.plot_bool, select_bool = self.select_bool)

