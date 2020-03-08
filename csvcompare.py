#!/usr/bin/env python
#
# Copyright (c) Lord Dashboard b.v.
# All rights reserved.
#
# License information is provided in LICENSE.md
#
# Author: Patrick Hanckmann <patrick@hanckmann.com>
# Project: Adaptics Report Automation

import sys

from PyQt5 import QtCore, QtGui, QtWidgets
from functools import lru_cache
import datatable as dt


__application__ = "CSV Compare"
__author__ = "Patrick Hanckmann"
__copyright__ = "Copyright 2020, Lord Dashboard b.v."

__license__ = "Apache License 2.0"
__version__ = "0.3.2"
__maintainer__ = "Patrick Hanckmann"
__email__ = "hanckmann@gmail.com"
__status__ = "Development"  # "Production"


class CompareModel(QtCore.QAbstractTableModel):
    def __init__(self, data1, data2, parent=None):
        QtCore.QAbstractTableModel.__init__(self, parent)
        self._data1_filename = data1
        self._data2_filename = data2
        self._data1 = dt.fread(data1)
        self._data2 = dt.fread(data2)
        self._data1_header = list(self._data1.names)
        self._data2_header = list(self._data2.names)
        self._header = self._data1_header + [item for item in self._data2_header if item not in self._data1_header]

    @lru_cache(maxsize=1)
    def rowCount_data1(self):
        return self._data1.shape[0]

    @lru_cache(maxsize=1)
    def rowCount_data2(self):
        return self._data2.shape[0]

    @lru_cache(maxsize=1)
    def columnCount_data1(self):
        return self._data1.shape[1]

    @lru_cache(maxsize=1)
    def columnCount_data2(self):
        return self._data2.shape[1]

    @lru_cache(maxsize=1)
    def rowCount(self, parent=None):
        return max(self.rowCount_data1(), self.rowCount_data2()) * 2

    @lru_cache(maxsize=1)
    def columnCount(self, parent=None):
        return max(self.columnCount_data1(), self.columnCount_data2())

    @lru_cache(maxsize=512)
    def data(self, index, role=QtCore.Qt.DisplayRole):
        data_row = int(index.row() / 2)
        data_select = index.row() % 2
        column_name = self._header[index.column()]
        data1_col = None
        data2_col = None
        if column_name in self._data1_header:
            data1_col = self._data1_header.index(column_name)
        if column_name in self._data2_header:
            data2_col = self._data2_header.index(column_name)

        if index.isValid():
            if role == QtCore.Qt.DisplayRole:
                if data_select == 0:
                    if data_row < self.rowCount_data1() and data1_col is not None:
                        return QtCore.QVariant(str(self._data1[data_row, data1_col]))
                elif data_select == 1:
                    if data_row < self.rowCount_data2() and data2_col is not None:
                        return QtCore.QVariant(str(self._data2[data_row, data2_col]))
                else:
                    raise ValueError("DataSelector error")
            if role == QtCore.Qt.BackgroundRole:
                color = QtCore.Qt.white
                if data_row % 2 == 0:
                    color = QtGui.QColor(216, 216, 216)
                if data_row < self.rowCount_data1() and data1_col is not None and \
                   data_row < self.rowCount_data2() and data2_col is not None:
                    if not str(self._data1[data_row, data1_col]) == str(self._data2[data_row, data2_col]):
                        color = QtCore.Qt.red
                else:
                    if data_row < self.rowCount_data1() and data1_col is not None or \
                       data_row < self.rowCount_data2() and data2_col is not None:
                        color = QtCore.Qt.red
                return QtGui.QBrush(color)
        return QtCore.QVariant()

    @lru_cache(maxsize=512)
    def headerData(self, section, orientation, role):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                return self._header[section]
            if orientation == QtCore.Qt.Vertical:
                data_select = section % 2
                data_row = int(section / 2)
                if not data_select:
                    return "line {} » File {} ".format(data_row, data_select + 1)
                return "File {} ".format(data_select + 1)


class MainWindow(QtWidgets.QMainWindow):

    call_process_signal = QtCore.pyqtSignal(str)
    call_preprocessing_signal = QtCore.pyqtSignal()
    call_spss_processing_signal = QtCore.pyqtSignal()
    call_report_generation_signal = QtCore.pyqtSignal()

    def __init__(self, parent=None, file1=None, file2=None, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setup_ui()
        if file1:
            self.file1_lineedit.setText(file1)
        if file2:
            self.file2_lineedit.setText(file2)

    def setup_ui(self):
        self.ui_titlebar()
        self.ui_menu()
        self.ui_statusbar()
        self.statusbar_message()
        # Load files and start
        file1_label = QtWidgets.QLabel("File 1:")
        file1_lineedit = QtWidgets.QLineEdit()
        file1_button = QtWidgets.QPushButton(text="...",
                                             clicked=lambda: self.show_file1_input_dialog())
        file1_button.setFixedSize(25, 25)
        self.file1_lineedit = file1_lineedit
        file2_label = QtWidgets.QLabel("File 2:")
        file2_lineedit = QtWidgets.QLineEdit()
        file2_button = QtWidgets.QPushButton(text="...",
                                             clicked=lambda: self.show_file2_input_dialog())
        file2_button.setFixedSize(25, 25)
        self.file2_lineedit = file2_lineedit
        compare_button = QtWidgets.QPushButton(text="COMPARE",
                                               clicked=lambda: self.compare())
        files_layout = QtWidgets.QHBoxLayout()
        files_layout.addWidget(file1_label)
        files_layout.addWidget(self.file1_lineedit)
        files_layout.addWidget(file1_button)
        files_layout.addSpacing(50)
        files_layout.addWidget(compare_button)
        files_layout.addSpacing(50)
        files_layout.addWidget(file2_label)
        files_layout.addWidget(self.file2_lineedit)
        files_layout.addWidget(file2_button)
        files_widget = QtWidgets.QWidget()
        files_widget.setLayout(files_layout)
        # Show data
        self.compare_tableview = QtWidgets.QTableView()
        self.compare_tableview.resizeColumnsToContents()
        self.compare_tableview.verticalHeader().setDefaultAlignment(QtCore.Qt.AlignRight)
        # Build Main Window
        central_layout = QtWidgets.QVBoxLayout()
        central_layout.addWidget(files_widget)
        central_layout.addWidget(self.compare_tableview)
        central_widget = QtWidgets.QWidget()
        central_widget.setLayout(central_layout)
        self.setCentralWidget(central_widget)

    def ui_titlebar(self, title=None, icon=None):
        if not title:
            title = "{} :: {}".format(__application__, __version__)
        self.setWindowTitle(title)
        if not icon:
            icon = 'iconsvg.svg'
        self.setWindowIcon(QtGui.QIcon(icon))

    def ui_menu(self):
        about_button = QtWidgets.QAction('About', self)
        about_button.setShortcut('Ctrl+A')
        about_button.setStatusTip('About')
        about_button.triggered.connect(self.show_about)
        exit_button = QtWidgets.QAction('Exit', self)
        exit_button.setShortcut('Ctrl+Q')
        exit_button.setStatusTip('Exit application')
        exit_button.triggered.connect(self.close)
        main_menu = self.menuBar()
        file_menu = main_menu.addMenu('File')
        file_menu.addAction(about_button)
        file_menu.addAction(exit_button)

    def ui_statusbar(self):
        self.status_message_left = QtWidgets.QLabel("left")
        self.status_message_center = QtWidgets.QLabel("center")
        self.status_message_center.setAlignment(QtCore.Qt.AlignHCenter)
        self.status_message_right = QtWidgets.QLabel("right")
        self.status_message_right.setAlignment(QtCore.Qt.AlignRight)
        self.statusbar = QtWidgets.QStatusBar()
        self.statusbar.addWidget(self.status_message_left, 1)
        self.statusbar.addWidget(self.status_message_center, 0)
        self.statusbar.addWidget(self.status_message_right, 1)
        self.setStatusBar(self.statusbar)
        self.statusbar_message(left="", center="", right="")

    def statusbar_message(self, left=None, center=None, right=None):
        if left is not None:
            self.status_message_left.setText(left)
        if center is not None:
            self.status_message_center.setText(center)
        if right is not None:
            self.status_message_right.setText(right)

    def show_file1_input_dialog(self):
        filename = QtWidgets.QFileDialog.getOpenFileName(self,
                                                         "Open CSV File",
                                                         ".",
                                                         "Data Files (*.csv)")
        self.file1_lineedit.setText(filename[0])

    def show_file2_input_dialog(self):
        filename = QtWidgets.QFileDialog.getOpenFileName(self,
                                                         "Open CSV File",
                                                         ".",
                                                         "Data Files (*.csv)")
        self.file2_lineedit.setText(filename[0])

    def compare(self):
        if not self.file1_lineedit.text() or not self.file2_lineedit.text():
            self.show_error_message(message="Please provide files to compare", title="Error reading csv files")

        file1_name = self.file1_lineedit.text()
        file2_name = self.file2_lineedit.text()
        try:
            model = CompareModel(file1_name, file2_name)
        except ValueError as e:
            self.show_error_message(message="{}\n{}".format("Error reading data:", str(e)), title="Error reading csv files")
            return
        self.compare_tableview.setModel(model)
        self.compare_tableview.resizeColumnsToContents()

    def show_error_message(self, message: str, title=None):
        print("ERROR: {}".format(message))
        if not title:
            title = "Error"
        QtWidgets.QMessageBox.critical(self, title, message)

    def show_about(self):
        QtWidgets.QMessageBox.about(self, "About", "\n".join((__application__,
                                                              " ",
                                                              "Version\t: {}".format(__version__),
                                                              "Author \t: {}".format(__author__),
                                                              "Email  \t: {}".format(__email__),
                                                              " ",
                                                              __copyright__.replace('Copyright', '©'))))


if __name__ == '__main__':
    # Input files as argument
    filename1 = None
    filename2 = None
    if len(sys.argv) >= 2:
        filename1 = sys.argv[1]
    if len(sys.argv) >= 3:
        filename2 = sys.argv[2]
    # Start UI
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow(file1=filename1, file2=filename2)
    w.show()
    sys.exit(app.exec_())
