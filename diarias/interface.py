# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'interface.ui'
#
# Created by: PyQt5 UI code generator 5.15.6
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(500, 601)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.dateEditEntrada = QtWidgets.QDateEdit(self.centralwidget)
        self.dateEditEntrada.setGeometry(QtCore.QRect(50, 40, 110, 22))
        self.dateEditEntrada.setCalendarPopup(True)
        self.dateEditEntrada.setObjectName("dateEditEntrada")
        self.dateEditSaida = QtWidgets.QDateEdit(self.centralwidget)
        self.dateEditSaida.setGeometry(QtCore.QRect(210, 40, 110, 22))
        self.dateEditSaida.setCalendarPopup(True)
        self.dateEditSaida.setObjectName("dateEditSaida")
        self.labelEntrada = QtWidgets.QLabel(self.centralwidget)
        self.labelEntrada.setGeometry(QtCore.QRect(50, 20, 111, 16))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.labelEntrada.setFont(font)
        self.labelEntrada.setObjectName("labelEntrada")
        self.labelEntrada_2 = QtWidgets.QLabel(self.centralwidget)
        self.labelEntrada_2.setGeometry(QtCore.QRect(210, 20, 111, 16))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.labelEntrada_2.setFont(font)
        self.labelEntrada_2.setObjectName("labelEntrada_2")
        self.pushButtonPesquisar = QtWidgets.QPushButton(self.centralwidget)
        self.pushButtonPesquisar.setGeometry(QtCore.QRect(380, 40, 75, 23))
        self.pushButtonPesquisar.setObjectName("pushButtonPesquisar")
        self.tableWidgetComparativo = QtWidgets.QTableWidget(self.centralwidget)
        self.tableWidgetComparativo.setGeometry(QtCore.QRect(50, 80, 401, 441))
        self.tableWidgetComparativo.setObjectName("tableWidgetComparativo")
        self.tableWidgetComparativo.setColumnCount(0)
        self.tableWidgetComparativo.setRowCount(0)
        self.pushButtonSalvar = QtWidgets.QPushButton(self.centralwidget)
        self.pushButtonSalvar.setGeometry(QtCore.QRect(210, 520, 75, 23))
        self.pushButtonSalvar.setObjectName("pushButtonSalvar")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 500, 26))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Comparativo de Diárias"))
        self.labelEntrada.setText(_translate("MainWindow", "Entrada"))
        self.labelEntrada_2.setText(_translate("MainWindow", "Saída"))
        self.pushButtonPesquisar.setText(_translate("MainWindow", "PESQUISAR"))
        self.pushButtonSalvar.setText(_translate("MainWindow", "SALVAR"))
