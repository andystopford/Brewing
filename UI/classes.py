from PyQt4 import QtCore, QtGui
import xml.etree.cElementTree as ET
from correctOG import Ui_Dialog

#####################################################################
#alestock_v2.0_beta_classes
#####################################################################

class Grain:
    def __init__(self, name, EBC, extr, wgt):
        self.name = name
        self.ebc = EBC
        self.extr = extr
        self.wgt = wgt
    def get_name(self):
        return self.name
    def get_ebc(self):
        return self.ebc
    def get_extr(self):
        return self.extr
    def get_wgt(self):
        return self.wgt
    def __str__(self):
        return (self.name)


class Used_Grain:
    def __init__(self, name, EBC, extr, wgt):
        self.name = name
        self.wgt = wgt
        self.extr = extr
        self.ebc = EBC
    def get_name(self):
        return self.name
    def get_wgt(self):
        return self.wgt
    def get_extr(self):
        return self.extr
    def get_ebc(self):
        return self.ebc
    def __str__(self):
        return (self.name)


class Hop:
    def __init__(self, name, alpha, wgt):
        self.name = name
        self.alpha = alpha
        self.wgt = wgt
    def get_name(self):
        return self.name
    def get_alpha(self):
        return self.alpha
    def get_wgt(self):
        return self.wgt


class Used_Hop:
    def __init__(self, name, alpha, wgt, time):
        self.name = name
        self.wgt = wgt
        self.alpha = alpha
        self.time = time
    def get_name(self):
        return self.name
    def get_wgt(self):
        return self.wgt
    def get_alpha(self):
        return self.alpha
    def get_time(self):
        return self.time
    def __str__(self):
        return (self.name)


class Yeast:
    def __init__(self, name, pkts):
        self.name = name
        self.pkts = pkts
    def get_name(self):
        return self.name
    def get_pkts(self):
        return self.pkts


class MessageBox(QtGui.QMessageBox):
    def __init__(self):
        QtGui.QMessageBox.__init__(self)
        self.setSizeGripEnabled(True)

    def event(self, e):
        result = QtGui.QMessageBox.event(self, e)
        
        self.setMinimumHeight(0)
        self.setMaximumHeight(16777215)
        self.setMinimumWidth(300)
        self.setMaximumWidth(16777215)
        self.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)

        textEdit = self.findChild(QtGui.QTextEdit)
        if textEdit != None :
            textEdit.setMinimumHeight(0)
            textEdit.setMaximumHeight(16777215)
            textEdit.setMinimumWidth(0)
            textEdit.setMaximumWidth(16777215)
            textEdit.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        return result


class brewCalendar(QtGui.QCalendarWidget):
    def __init__(self, parent, x, y):    
        QtGui.QCalendarWidget.__init__(self, parent)
        self.setHorizontalHeaderFormat(QtGui.QCalendarWidget.SingleLetterDayNames)
        self.color = QtGui.QColor(self.palette().color(QtGui.QPalette.Highlight))
        self.color.setRgb(0,0,255)
        self.color.setAlpha(64)
        self.selectionChanged.connect(self.updateCells)
        #self.clicked.connect(self.cellClicked)
        self.dateList = []
        self.setGridVisible(True)
        self.setPos(x, y)

    def setPos(self, x, y):
        self.setGeometry(QtCore.QRect(x, y, 232, 129))

    def paintCell(self, painter, rect, date):
        QtGui.QCalendarWidget.paintCell(self, painter, rect, date)
        if date in self.dateList:
            painter.fillRect(rect, self.color)
            

    def dates(self, dateList):
        self.dateList = dateList
        self.updateCells()


    #def cellClicked(self, date):        
    #    Mainwindow.selectBrew(myapp, date)


class textEdit(QtGui.QDialog):

    def __init__(self, parent):
        QtGui.QWidget.__init__(self, parent)
        self.txt = QtGui.QTextEdit(self)

    def closeEvent(self, event):
        #in case needed to call function (e.g. keepNotes())in mainwindow
        text = self.txt.toPlainText()
        par = self.parent()
        #par.keepNotes(text)


class saveDialogue(QtGui.QDialog):
    def __init__(self, parent = None):
        QtGui.QWidget.__init__(self, parent)
        self.cal = brewCalendar(self, 20, 20)

        self.button_brew = QtGui.QRadioButton(self)
        self.button_brew.setText("Brew Records")
        self.button_brew.setGeometry(QtCore.QRect(275, 33, 120, 21))
        self.button_brew.setChecked(True)

        self.button_design = QtGui.QRadioButton(self)
        self.button_design.setText("Brew Design")
        self.button_design.setGeometry(QtCore.QRect(275, 53, 120, 21))

        font = QtGui.QFont()
        font.setPointSize(12)

        self.label1 = QtGui.QLabel(self)
        self.label1.setAlignment(QtCore.Qt.AlignCenter)
        self.label1.setGeometry(QtCore.QRect(280, 18, 100, 16))
        self.label1.setWordWrap(True) #see UI file line 829
        self.label1.setText("Save To:")

        self.label2 = QtGui.QLabel(self)
        self.label2.setAlignment(QtCore.Qt.AlignCenter)
        self.label2.setGeometry(QtCore.QRect(280, 81, 100, 16))
        self.label2.setWordWrap(True) #see UI file line 829
        self.label2.setText("Saving As:")

        self.fnameBox = QtGui.QTextEdit(self)
        self.fnameBox.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.fnameBox.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
        self.fnameBox.setFont(font)
        self.fnameBox.setGeometry(QtCore.QRect(278, 98, 100, 30))

        self.button_save = QtGui.QPushButton(self)
        self.button_save.setGeometry(QtCore.QRect(288, 130, 80, 21))
        self.button_save.setText("Save")
        self.button_save.clicked.connect(self.save)

        self.cal.clicked.connect(self.selectDate)
        self.brew = ""

    def save(self):

        par = self.parent()
        if self.button_brew.isChecked():
            par.save_brew(self.brew)
        else:
            path = QtCore.QString("./BrewDesign/untitled.xml")
            dlg = QtGui.QFileDialog
            dlg.getSaveFileName(self, "Save Design", path, ".xml")
        par.brew_dirty = False
        self.close()

    def selectDate(self, date):
        day = date.day()
        month = date.month()
        month = date.shortMonthName(month)
        year = date.year()
        year = str(year - 2000)
        month = str(month)
        if day < 10:
            day = "0" + str(day)
        day = str(day)
        self.brew = day + month + year
        brew = "<html><head/><body><p align=center>" + self.brew + "</p></body></html>"
        self.fnameBox.setText(brew)



class prefDialogue(QtGui.QDialog):
    def __init__(self, parent = None):
        QtGui.QWidget.__init__(self, parent)
        self.resize(273, 206)
        self.setWindowTitle("Preferences")

        self.label_days = QtGui.QLabel(self)
        self.label_days.setGeometry(QtCore.QRect(75, 22, 171, 26))
        self.label_days.setText("<html><head/><body><p>Max number of days since brewing<br/>to \
            display in timeline calendar</p></body></html>")

        self.label_length = QtGui.QLabel(self)
        self.label_length.setGeometry(QtCore.QRect(75, 56, 101, 16))
        self.label_length.setText("<html><head/><body><p>Brew Length (Litres)</p></body></html>")

        self.label_temp = QtGui.QLabel(self)
        self.label_temp.setGeometry(QtCore.QRect(75, 82, 76, 16))
        self.label_temp.setText("<html><head/><body><p>Mash Temp (&deg;C)</p></body></html>")

        self.label_eff = QtGui.QLabel(self)
        self.label_eff.setGeometry(QtCore.QRect(75, 108, 100, 16))
        self.label_eff.setText("<html><head/><body><p>Mash Efficiency %</p></body></html>")

        self.label_pkts = QtGui.QLabel(self)
        self.label_pkts.setGeometry(QtCore.QRect(75, 134, 152, 16))
        self.label_pkts.setText("<html><head/><body><p>Number of Yeast Packets/Brew</p></body></html>")

        self.spinBox_days = QtGui.QSpinBox(self)
        self.spinBox_days.setGeometry(QtCore.QRect(23, 23, 39, 22))
        

        self.spinBox_length = QtGui.QSpinBox(self)
        self.spinBox_length.setGeometry(QtCore.QRect(23, 53, 39, 22))
        

        self.spinBox_temp = QtGui.QSpinBox(self)
        self.spinBox_temp.setGeometry(QtCore.QRect(23, 79, 39, 22))
        

        self.spinBox_eff = QtGui.QSpinBox(self)
        self.spinBox_eff.setGeometry(QtCore.QRect(23, 105, 39, 22))
        

        self.spinBox_pkts = QtGui.QSpinBox(self)
        self.spinBox_pkts.setGeometry(QtCore.QRect(23, 131, 39, 22))
        

        self.button_apply = QtGui.QPushButton(self)
        self.button_apply.setGeometry(QtCore.QRect(90, 165, 81, 21))
        self.button_apply.setText("Apply")
        self.button_apply.clicked.connect(self.apply)

        self.path = './Data/prefs.xml'

        self.initParams()


    def initParams(self):

        try:
            with open(self.path, "r") as fo:
                tree = ET.ElementTree(file = self.path)
                root = tree.getroot()
                for elem in root.iter():
                    if elem.tag == 'Days':
                        self.spinBox_days.setValue(int(elem.text))
                    if elem.tag == 'Length':
                        self.spinBox_length.setValue(int(elem.text))
                    if elem.tag == 'Temp':
                        self.spinBox_temp.setValue(int(elem.text))
                    if elem.tag == 'Eff':
                        self.spinBox_eff.setValue(int(elem.text))
                    if elem.tag == 'Pkts':
                        self.spinBox_pkts.setValue(int(elem.text))
        except:
            print "No Preference File Found"

    def apply(self):

        self.days = str(self.spinBox_days.text())
        self.length = str(self.spinBox_length.text())
        self.temp = str(self.spinBox_temp.text())
        self.eff = str(self.spinBox_eff.text())
        self.pkts = str(self.spinBox_pkts.text())

        par = self.parent()
        par.setPrefs(self.days, self.length, self.temp, self.eff, self.pkts)
        self.save()
        self.close()


    def save(self):

        root = ET.Element('Root')
        days = ET.SubElement(root, 'Days')
        length = ET.SubElement(root, 'Length')
        temp = ET.SubElement(root, 'Temp')
        eff = ET.SubElement(root, 'Eff')
        pkts = ET.SubElement(root, 'Pkts')

        days.text = self.days
        length.text = self.length
        temp.text = self.temp
        eff.text = self.eff
        pkts.text = self.pkts

        with open(self.path, "w") as fo:
            tree = ET.ElementTree(root)
            tree.write(fo)


class conversionWindow(QtGui.QDialog):
    def __init__(self, parent = None):
        QtGui.QWidget.__init__(self, parent)
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.ui.button_calc.clicked.connect(self.calc)
        self.ui.box_calTemp.setValue(20)
        self.setWindowTitle("Hydrometer Correction")


    def calc(self):

        cg = 0 #corrected sg
        mg = self.ui.box_mesrOG.value() #measured sg
        tr = self.ui.box_mesrTemp.value() #temp at measured sg
        tc = self.ui.box_calTemp.value() #calibration temp

        mg = mg / float(1000) + 1
        tr = ((tr * 9) / 5) + 32
        tc = ((tc * 9) / 5) + 32

        cg = mg * ((1.00130346 - 0.000134722124 * tr + 0.00000204052596 * tr**2 - 0.00000000232820948 * tr**3)\
         / (1.00130346 - 0.000134722124 * tc + 0.00000204052596 * tc**2 - 0.00000000232820948 * tc**3))
        cg = (cg - 1) * 1000
        cg = round(cg)
        self.ui.box_corrOG.setValue(cg)