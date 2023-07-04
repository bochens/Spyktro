import sys, os
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
from sPyktro_item import Spectra_item
import numpy as np
import darkdetect


class sPyktro(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(sPyktro, self).__init__(parent)
        # inherited from Ui_MainWindow
        self.setupUi(self)

        self.counter = 0

        self.dir = os.path.dirname(__file__)
        
        # status of the plot area (graphWidget) background color
        if darkdetect.isLight():
            self.background_color = "w"
        else:
            self.background_color = "k"
        
        self.graphWidget.setBackground(self.background_color)

        # init setting of the plot area (graphWidget)
        self.graphPlotItem = self.graphWidget.getPlotItem()
        self.graphViewBox = self.graphPlotItem.getViewBox()
        self.graphQactions = self.graphViewBox.menu.actions()

        self.graphPlotItem.sigRangeChanged.connect(self.qtgraph_range_changed)

        # disable right click menu for the plot area
        self.graphPlotItem.setMenuEnabled(False)
        #for i in self.graphQactions:
        #    i.setVisible(False)

        # disable the lower left button
        self.graphPlotItem.hideButtons()

        # new use this
        self.spectra_items = []

        # undo and redo
        self.actionUndo.triggered.connect(self.history_undo)
        self.actionRedo.triggered.connect(self.history_redo)

        # call out color picker
        self.actionColor.triggered.connect(self.color_picker)
        self.actionLinewidth.triggered.connect(self.set_line_width)
        
        # open about page
        self.actionAbout_sPyktro.triggered.connect(self.show_about_popup)

        # load a spectra
        self.actionLoad.triggered.connect(self.load_new_raman_spectra)
        # preference
        self.actionPreference.triggered.connect(self.preferences_setting)

        # list widget operation
        self.listWidget.itemChanged.connect(self.listWidget_item_just_checked)
        self.listWidget.itemSelectionChanged.connect(self.listWidget_item_just_selected)
        self.listWidget.installEventFilter(self)

        #delete
        self.actionDelete.triggered.connect(self.delete_selected_spectras)
        #duplicate
        self.actionDuplicate.triggered.connect(self.duplicate_selected_spectras)

        # update the limits of the plot area (graphWidget)
        self.onlyFloat = QDoubleValidator()
        self.lineEdit_x_min.setValidator(self.onlyFloat)
        self.lineEdit_x_max.setValidator(self.onlyFloat)
        self.lineEdit_y_min.setValidator(self.onlyFloat)
        self.lineEdit_y_max.setValidator(self.onlyFloat)
        self.pushUpdate.clicked.connect(self.update_all_limits)
        self.lineEdit_x_min.returnPressed.connect(self.pushUpdate.click)
        self.lineEdit_x_max.returnPressed.connect(self.pushUpdate.click)
        self.lineEdit_y_min.returnPressed.connect(self.pushUpdate.click)
        self.lineEdit_y_max.returnPressed.connect(self.pushUpdate.click)
        self.pushButton_Reset.clicked.connect(self.button_reset_limit)

        self.lineEdit_x_min.textChanged.connect(self.make_push_button_blue)
        self.lineEdit_x_max.textChanged.connect(self.make_push_button_blue)
        self.lineEdit_y_min.textChanged.connect(self.make_push_button_blue)
        self.lineEdit_y_max.textChanged.connect(self.make_push_button_blue)
        
        self.lineEdit_x_min.blockSignals(True)
        self.lineEdit_x_max.blockSignals(True)
        self.lineEdit_y_min.blockSignals(True)
        self.lineEdit_y_max.blockSignals(True)
        self.graphWidget_set_x_limit(0.0,1.0)
        self.graphWidget_set_y_limit(0.0,1.0)
        self.lineEdit_x_min.blockSignals(False)
        self.lineEdit_x_max.blockSignals(False)
        self.lineEdit_y_min.blockSignals(False)
        self.lineEdit_y_max.blockSignals(False)

        self.history_states = []
        self.history_which = -1
        self.history_maximum = 20
        self.history_update()


    def eventFilter(self, source, event):
        if event.type() == QEvent.ContextMenu and source is self.listWidget:
            menu = QMenu()
            context_duplicate = menu.addAction('Duplicate')
            context_delete = menu.addAction('Delete')
            menu.addSeparator()
            context_show = menu.addAction('Show')
            context_hide = menu.addAction('Hide')
            menu.addSeparator()
            context_color = menu.addAction('Line Color')
            context_width = menu.addAction('Line Width')

            context_duplicate.triggered.connect(self.duplicate_selected_spectras)
            context_delete.triggered.connect(self.delete_selected_spectras)
            context_show.triggered.connect(self.listWidget_item_show)
            context_hide.triggered.connect(self.listWidget_item_hide)
            context_color.triggered.connect(self.color_picker)
            context_width.triggered.connect(self.set_line_width)

            menu.exec(event.globalPos())

            return True
        return False


    def make_push_button_reset(self):
        self.pushUpdate.setStyleSheet('')

    def make_push_button_blue(self):
        self.pushUpdate.setStyleSheet('QPushButton {color: blue;}')

    def test_connect(self):
        print("connected")

    def get_spectra_nums(self):
        return len(self.spectra_items)

    def show_about_popup(self):
        about_win = QMessageBox()
        about_win.setWindowTitle("About sPyktro")
        about_win.setText("sPyktro")
        
        #about_win.setIconPixmap(QPixmap(os.path.join(self.dir, 'icon','icon_path')))
        about_win.setInformativeText(" Version 0.1 \n Designed by Bo Chen \n Copyright \xA9 Bo Chen \n All rights reserved.")
        about_win.exec()

    def preferences_setting(self):
        popup = Preferences_window(self.background_color)
        result = popup.exec()
        if result: # the changes made in the preferences window is accepted
            self.background_color = popup.background_color
            self.graphWidget.setBackground(self.background_color)
            
    def show_error_win(self, text, informative_txt):
        error_win = QMessageBox()
        error_win.setWindowTitle("Error")
        error_win.setText(text)
        error_win.setInformativeText(informative_txt)
        error_win.exec()

    def load_new_raman_spectra(self):
        # open a file dialog and create a new Raman_Spectra object
        path_list = QFileDialog.getOpenFileNames(self, 'Open a file', '', 'All Files (*.*)')
        self.rm_init(path_list[0])    

    def rm_init(self, path):
        try:
            popup = Raman_Spectra_Init_Dialog(path)
            result = popup.exec()
        except Exception as x:
            print(x)
        
        else:
            if result: # the raman init dialog is accepted
                sample_name_string_list = popup.sample_name_string_list
                start_float_list = popup.start_float_list
                end_float_list = popup.end_float_list
                generated_path_list = popup.return_path

                for i in range(len(generated_path_list)):
                    sample_name_string = sample_name_string_list[i]
                    start_float = start_float_list[i]
                    end_float = end_float_list[i]
                    generated_path = generated_path_list[i]

                    try:
                        new_spectra = Raman_Spectra(generated_path, sample_name_string, start=start_float, end=end_float)
                    except UnicodeDecodeError:
                        self.show_error_win('Error', "UnicodeDecodeError raised while initializing " + sample_name_string)
                    else:

                        if self.background_color == "k":
                            new_color = QColor(255, 255, 255)
                        elif self.background_color == "w":
                            new_color = QColor(0, 0, 0)

                        self.spectra_items.append(Spectra_item(new_spectra, new_color))

                        self.graphWidget_plot_update()
                        self.reset_limit()
                        self.listWidget_item_update()
                        self.listWidget_checkbox_update()
                        self.listWidget_color_update()

                self.history_update()

    def update_all_limits(self):
        ax_x = self.graphPlotItem.getAxis("bottom")
        now_x_min = ax_x.range[0]
        now_x_max = ax_x.range[1]
        ax_y = self.graphPlotItem.getAxis("left")
        now_y_min = ax_y.range[0]
        now_y_max = ax_y.range[1]

        a_bool = True

        if self.lineEdit_x_min.text() != "" and self.lineEdit_x_max.text() != "":
            x_min_num = float(self.lineEdit_x_min.text())
            x_max_num = float(self.lineEdit_x_max.text())
            if x_max_num > x_min_num:
                self.graphWidget_set_x_limit(x_min_num, x_max_num)
            else:
                a_bool = False

        if self.lineEdit_x_min.text() != "" and self.lineEdit_x_max.text() == "":
            x_min_num = float(self.lineEdit_x_min.text())
            if now_x_max > x_min_num:
                self.graphWidget_set_x_limit(x_min_num, now_x_max)
            else:
                a_bool = False

        if self.lineEdit_x_min.text() == "" and self.lineEdit_x_max.text() != "":
            x_max_num = float(self.lineEdit_x_max.text())
            if now_x_min < x_max_num:
                self.graphWidget_set_x_limit(now_x_min, x_max_num)
            else:
                a_bool = False
        
        if self.lineEdit_y_min.text() != "" and self.lineEdit_y_max.text() != "":
            y_min_num = float(self.lineEdit_y_min.text())
            y_max_num = float(self.lineEdit_y_max.text())
            if y_max_num > y_min_num:
                self.graphWidget_set_y_limit(y_min_num, y_max_num)
            else:
                a_bool = False

        if self.lineEdit_y_min.text() != "" and self.lineEdit_y_max.text() == "":
            y_min_num = float(self.lineEdit_y_min.text())
            if now_y_max > y_min_num:
                self.graphWidget_set_y_limit(y_min_num, now_y_max)
            else:
                a_bool = False

        if self.lineEdit_y_min.text() == "" and self.lineEdit_y_max.text() != "":
            y_max_num = float(self.lineEdit_y_max.text())
            if now_y_min < y_max_num:
                self.graphWidget_set_y_limit(now_y_min, y_max_num)
            else:
                a_bool = False
        
        if a_bool:
            self.make_push_button_reset()
        
        self.history_update()

    def button_reset_limit(self):
        self.reset_limit()
        self.history_update()
        

    def reset_limit(self):
        if self.get_spectra_nums != 0:
            xmin, xmax, ymin, ymax = self.get_largerst_axis_lim()
            self.graphWidget_set_x_limit(xmin, xmax)
            self.graphWidget_set_y_limit(ymin, ymax)

            self.make_push_button_reset()
            return xmin, xmax, ymin, ymax
        else:
            self.make_push_button_reset()
            return 0, 1, 0, 1
        
    def get_largerst_axis_lim(self):
        xmin_list = []
        xmax_list = []
        ymin_list = []
        ymax_list = []

        for item in self.spectra_items:
            if item.plot_bool:
                a_x, a_y = item.spectra.get_spectra()
                xmin_list.append(np.amin(a_x))
                xmax_list.append(np.amax(a_x))
                ymin_list.append(np.amin(a_y))
                ymax_list.append(np.amax(a_y))

        return np.amin(xmin_list), np.amax(xmax_list), np.amin(ymin_list), np.amax(ymax_list)
    
    def graphWidget_plot_update(self):
        self.graphPlotItem.clear()
        for item in self.spectra_items:
            if item.plot_bool:
                a_x, a_y = item.spectra.get_spectra()
                self.graphPlotItem.plot(a_x, a_y, pen=pg.mkPen(item.line_color, width = item.line_width))


    def graphWidget_set_x_limit(self, x_lower, x_higher):
        if x_lower is not None and x_higher is not None:
            self.lineEdit_x_min.setText(str(round(x_lower,2)))
            self.lineEdit_x_max.setText(str(round(x_higher,2)))
            self.graphViewBox.setXRange(x_lower, x_higher, padding=0)
    
    def graphWidget_set_y_limit(self, y_lower, y_higher):
        if y_lower is not None and y_higher is not None:
            self.lineEdit_y_min.setText(str(round(y_lower,2)))
            self.lineEdit_y_max.setText(str(round(y_higher,2)))
            self.graphViewBox.setYRange(y_lower, y_higher, padding=0)

    def qtgraph_range_changed(self):
        self.graphWidget.blockSignals(True)
        ax_x = self.graphPlotItem.getAxis("bottom")
        now_x_min = ax_x.range[0]
        now_x_max = ax_x.range[1]
        ax_y = self.graphPlotItem.getAxis("left")
        now_y_min = ax_y.range[0]
        now_y_max = ax_y.range[1]

        self.lineEdit_x_min.setText(str(round(now_x_min,2)))
        self.lineEdit_x_max.setText(str(round(now_x_max,2)))
        self.lineEdit_y_min.setText(str(round(now_y_min,2)))
        self.lineEdit_y_max.setText(str(round(now_y_max,2)))

        self.graphWidget.blockSignals(False)

        #self.history_update()

    def listWidget_item_update(self):
        # repopulate the listWidget
        self.listWidget.blockSignals(True)
        self.listWidget.clear()
        self.listWidget.blockSignals(False)

        for item in self.spectra_items:
            sample_name = item.spectra.sample_name
            q_item = QListWidgetItem(sample_name)
            q_item.setCheckState(Qt.Checked)
            self.listWidget.addItem(q_item)
        
        self.listWidget_color_update()

    def listWidget_color_update(self):
        # called wafter color_picker is called, and as listWidget item update is called
        self.listWidget.blockSignals(True)
        for i in range(self.get_spectra_nums()):
            q_item = self.listWidget.item(i)
            q_item.setForeground(self.spectra_items[i].line_color)
        self.listWidget.blockSignals(False)

    def listWidget_item_just_checked(self):
        for i in range(self.get_spectra_nums()):
            q_item = self.listWidget.item(i)
            q_item_bool = (Qt.Checked == q_item.checkState())
            self.spectra_items[i].plot_bool = q_item_bool

        self.history_update()
        self.graphWidget_plot_update()
    
    def listWidget_item_show(self):
        self.listWidget.blockSignals(True)
        for i in range(self.get_spectra_nums()):
            if self.spectra_items[i].select_bool:
                self.spectra_items[i].plot_bool = True
                self.listWidget.item(i).setCheckState(Qt.Checked)

        self.history_update()
        self.graphWidget_plot_update()

        self.listWidget.blockSignals(False)

    def listWidget_item_hide(self):
        self.listWidget.blockSignals(True)
        for i in range(self.get_spectra_nums()):
            if self.spectra_items[i].select_bool:
                self.spectra_items[i].plot_bool = False
                self.listWidget.item(i).setCheckState(Qt.Unchecked)

        self.history_update()
        self.graphWidget_plot_update()
        
        self.listWidget.blockSignals(False)

    def listWidget_item_just_selected(self):
        for i in range(self.get_spectra_nums()):
            q_item = self.listWidget.item(i)
            q_item_bool = q_item.isSelected()
            self.spectra_items[i].select_bool = q_item_bool
    
    def listWidget_checkbox_update(self):
        # when the check box state is not changed by the user.
        # Because this update is presenting the current state instead of setting the current state,
        # the signal should be blocked.
        self.listWidget.blockSignals(True)
        for i in range(self.get_spectra_nums()):
            q_item = self.listWidget.item(i)
            if self.spectra_items[i].plot_bool:
                q_item.setCheckState(Qt.Checked)
            else:
                q_item.setCheckState(Qt.Unchecked)
        self.listWidget.blockSignals(False)

    def delete_selected_spectras(self):
        new_spectra_items = []
        
        for item in self.spectra_items:
            if not item.select_bool:
                new_spectra_items.append(item.copy())

        self.spectra_items = new_spectra_items

        self.graphWidget_plot_update()
        self.listWidget_item_update()
        self.listWidget_checkbox_update()
        self.history_update()

    def duplicate_selected_spectras(self):
        n = self.get_spectra_nums()

        for i in range(n):
            if self.spectra_items[i].select_bool:
                self.spectra_items.append(self.spectra_items[i].copy())

        self.graphWidget_plot_update()
        self.listWidget_item_update()
        self.listWidget_checkbox_update()
        self.history_update()
        
                
    def color_picker(self):
        color = QColorDialog.getColor()
        
        for item in self.spectra_items:
            if item.select_bool:
                item.line_color = color
        
        self.history_update()
        self.graphWidget_plot_update()
        self.listWidget_color_update()

    def set_line_width(self):
        line_window = Line_window()
        result = line_window.exec()

        if result:
            for item in self.spectra_items:
                if item.select_bool:
                    item.line_width = line_window.line_width
        
        self.history_update()
        self.graphWidget_plot_update()

    def history_update(self):
        if self.history_which == self.history_maximum:
            print("history full")
            self.history_states.pop(0)
            self.history_which = self.history_which - 1

        self.history_states = self.history_states[0: self.history_which+1]
        
        ax_x = self.graphPlotItem.getAxis("bottom")
        now_x_min = ax_x.range[0]
        now_x_max = ax_x.range[1]
        ax_y = self.graphPlotItem.getAxis("left")
        now_y_min = ax_y.range[0]
        now_y_max = ax_y.range[1]

        new_spectra_items = []

        for item in self.spectra_items:
            new_spectra_items.append(item.copy())

        self.history_states.append((new_spectra_items.copy(), (now_x_min, now_x_max, now_y_min, now_y_max)))
        self.history_which = self.history_which + 1

    
    def history_undo(self):
        if self.history_which != -1 and self.history_which != 0:
            self.history_which = self.history_which - 1
            self.time_travel()
    
    def history_redo(self):
        if self.history_which != len(self.history_states)-1:
            self.history_which = self.history_which + 1
            self.time_travel()
    
    def time_travel(self):
        self.spectra_items = []
        for item in self.history_states[self.history_which][0]:
            self.spectra_items.append(item.copy())

        self.graphWidget_plot_update()
        self.listWidget_item_update()
        self.listWidget_checkbox_update()

        limit = self.history_states[self.history_which][1]

        self.graphWidget_set_x_limit(float(limit[0]),float(limit[1]))
        self.graphWidget_set_y_limit(float(limit[2]),float(limit[3]))
        self.make_push_button_reset()
        

# Open the application
def main():
    app = QApplication(sys.argv)
    main = sPyktro()
    main.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()