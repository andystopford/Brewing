# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'correctOG.ui'
#
# Created by: PyQt4 UI code generator 4.10.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName(_fromUtf8("Dialog"))
        Dialog.resize(171, 179)
        self.layoutWidget = QtGui.QWidget(Dialog)
        self.layoutWidget.setGeometry(QtCore.QRect(10, 15, 179, 127))
        self.layoutWidget.setObjectName(_fromUtf8("layoutWidget"))
        self.gridLayout = QtGui.QGridLayout(self.layoutWidget)
        self.gridLayout.setMargin(0)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.label_3 = QtGui.QLabel(self.layoutWidget)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.gridLayout.addWidget(self.label_3, 2, 1, 1, 1)
        self.label_4 = QtGui.QLabel(self.layoutWidget)
        self.label_4.setObjectName(_fromUtf8("label_4"))
        self.gridLayout.addWidget(self.label_4, 3, 1, 1, 1)
        self.box_mesrTemp = QtGui.QSpinBox(self.layoutWidget)
        self.box_mesrTemp.setMaximumSize(QtCore.QSize(50, 16777215))
        self.box_mesrTemp.setObjectName(_fromUtf8("box_mesrTemp"))
        self.gridLayout.addWidget(self.box_mesrTemp, 1, 0, 1, 1)
        self.box_mesrOG = QtGui.QSpinBox(self.layoutWidget)
        self.box_mesrOG.setMaximumSize(QtCore.QSize(50, 16777215))
        self.box_mesrOG.setObjectName(_fromUtf8("box_mesrOG"))
        self.gridLayout.addWidget(self.box_mesrOG, 2, 0, 1, 1)
        self.box_corrOG = QtGui.QSpinBox(self.layoutWidget)
        self.box_corrOG.setMaximumSize(QtCore.QSize(50, 16777215))
        self.box_corrOG.setButtonSymbols(QtGui.QAbstractSpinBox.NoButtons)
        self.box_corrOG.setObjectName(_fromUtf8("box_corrOG"))
        self.gridLayout.addWidget(self.box_corrOG, 3, 0, 1, 1)
        self.label_2 = QtGui.QLabel(self.layoutWidget)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.gridLayout.addWidget(self.label_2, 1, 1, 1, 1)
        self.label = QtGui.QLabel(self.layoutWidget)
        self.label.setObjectName(_fromUtf8("label"))
        self.gridLayout.addWidget(self.label, 0, 1, 1, 1)
        self.box_calTemp = QtGui.QSpinBox(self.layoutWidget)
        self.box_calTemp.setMaximumSize(QtCore.QSize(50, 16777215))
        self.box_calTemp.setObjectName(_fromUtf8("box_calTemp"))
        self.gridLayout.addWidget(self.box_calTemp, 0, 0, 1, 1)
        self.button_calc = QtGui.QPushButton(Dialog)
        self.button_calc.setGeometry(QtCore.QRect(45, 150, 81, 21))
        self.button_calc.setObjectName(_fromUtf8("button_calc"))

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(_translate("Dialog", "Dialog", None))
        self.label_3.setText(_translate("Dialog", "Measured OG", None))
        self.label_4.setText(_translate("Dialog", "Corrected OG", None))
        self.label_2.setText(_translate("Dialog", "<html><head/><body><p>Measured Temp °C</p></body></html>", None))
        self.label.setText(_translate("Dialog", "<html><head/><body><p>Calibration Temp °C</p></body></html>", None))
        self.button_calc.setText(_translate("Dialog", "Calculate", None))

