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
import pandas as pd


__application__ = "CSV Compare"
__author__ = "Patrick Hanckmann"
__copyright__ = "Copyright 2020, Lord Dashboard b.v."

__license__ = "Apache License 2.0"
__version__ = "0.2.1"
__maintainer__ = "Patrick Hanckmann"
__email__ = "hanckmann@gmail.com"
__status__ = "Development"  # "Production"


class CompareModel(QtCore.QAbstractTableModel):
    def __init__(self, data1, data2, parent=None):
        QtCore.QAbstractTableModel.__init__(self, parent)
        self._data1 = data1
        self._data2 = data2
        self._data1_header = list(data1.columns.values)
        self._data2_header = list(data2.columns.values)
        self._header = list(data1.columns.values) + [item for item in data2.columns.values if item not in data1.columns.values]

    def rowCount(self, parent=None):
        rows_data1 = len(self._data1)
        rows_data2 = len(self._data2)
        return max(rows_data1, rows_data2) * 2

    def columnCount(self, parent=None):
        cols_data1 = self._data1.columns.size
        cols_data2 = self._data2.columns.size
        cols_datacompare = max(cols_data1, cols_data2)
        return cols_datacompare

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
                    if data_row < len(self._data1) and data1_col is not None:
                        return QtCore.QVariant(str(self._data1.values[data_row][data1_col]))
                elif data_select == 1:
                    if data_row < len(self._data2) and data2_col is not None:
                        return QtCore.QVariant(str(self._data2.values[data_row][data2_col]))
                else:
                    raise ValueError("DataSelector error")
            if role == QtCore.Qt.BackgroundRole:
                color = QtCore.Qt.white
                if data_row % 2 == 0:
                    color = QtGui.QColor(216, 216, 216)
                if data_row < len(self._data1) and data1_col is not None and \
                   data_row < len(self._data2) and data2_col is not None:
                    if not str(self._data1.values[data_row][data1_col]) == str(self._data2.values[data_row][data2_col]):
                        color = QtCore.Qt.red
                else:
                    if data_row < len(self._data1) and data1_col is not None or \
                       data_row < len(self._data2) and data2_col is not None:
                        color = QtCore.Qt.red
                return QtGui.QBrush(color)
        return QtCore.QVariant()

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

    def __init__(self, parent=None, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setup_ui()

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
        if left is None:
            self.status_message_left.setText(left)
        if center is None:
            self.status_message_center.setText(center)
        if right is None:
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
        if not self.file1_lineedit.text():
            self.file1_lineedit.setText("/home/patrick/Projects/csvcompare/data/data1.csv")
        if not self.file2_lineedit.text():
            self.file2_lineedit.setText("/home/patrick/Projects/csvcompare/data/data2.csv")
        df_file1 = None
        df_file2 = None
        try:
            df_file1 = pd.read_csv(self.file1_lineedit.text(), sep=';')
        except Exception as e:
            self.show_error_message(message="{}\n{}".format("Error reading csv file 1:", str(e)), title="Error reading csv files")
            return
        try:
            df_file2 = pd.read_csv(self.file2_lineedit.text(), sep=';')
        except Exception as e:
            self.show_error_message(message="{}\n{}".format("Error reading csv file 2:", str(e)), title="Error reading csv files")
            return
        try:
            model = CompareModel(df_file1, df_file2)
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
    # Start UI
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())
