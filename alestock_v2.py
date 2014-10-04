#!/usr/bin/python
import sys, time, math
import xml.etree.cElementTree as ET
from PyQt4 import QtCore, QtGui
from alestockUI_v2 import Ui_MainWindow
from xml.parsers import expat

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


#####################################################################################
#This version uses drag and drop for picking the grain to use


class Mainwindow (QtGui.QMainWindow):
    def __init__(self, parent = None):
        QtGui.QWidget.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.grain_list = []
        self.sel_grain = 0
        self.used_grain_list = []
        self.hop_list = []
        self.used_hop = []
        self.yeast_list = []
        self.used_yeast = ""
        self.grain_select = 0
        self.hop_select = 0
        self.yeast_select = 0
        self.mash_temp = str(66)
        self.mash_eff = str(80)
        self.vol = str(60)
        self.mash_deg = 0
        self.total_col = 0
        self.total_ebu = 0
        self.pkt_use = 3 
        self.dirty = False
        self.ui.button_reStock.setChecked(True)
        self.mode_grp = [self.ui.button_reStock, self.ui.button_use]

        self.alarm_time = 0
        self.palette = QtGui.QPalette() 

        #Event filters
        self.ui.grain_use.installEventFilter(self)         

        # Connect signals to slots
        self.ui.Save_Data.triggered.connect(self.save_data)
        self.ui.Load_data.triggered.connect(self.load_data)
        #self.ui.button_noteSave.clicked.connect(self.test)
        self.ui.button_startTimer.clicked.connect(self.startTimer)
        self.ui.button_stopTimer.clicked.connect(self.stopTimer)
        self.ui.button_use.clicked.connect(self.grpUpdates)
        self.ui.button_reStock.clicked.connect(self.recipeForm)
        self.ui.button_grainUseUpdate.clicked.connect(self.useGrain)
        self.ui.button_hopUseUpdate.clicked.connect(self.useHop)

        self.ui.grain_use.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.ui.grain_use.connect(self.ui.grain_use, QtCore.SIGNAL
            ("customContextMenuRequested(QPoint)"), self.grainUse_RClick)

        self.ui.hop_use.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.ui.hop_use.connect(self.ui.hop_use, QtCore.SIGNAL
            ("customContextMenuRequested(QPoint)"), self.hopUse_RClick)

        self.ui.yeast_use.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.ui.yeast_use.connect(self.ui.yeast_use, QtCore.SIGNAL
            ("customContextMenuRequested(QPoint)"), self.yeastUse_RClick)


    ###########################################################################
    
        self.ctimer = QtCore.QTimer()
        QtCore.QObject.connect(self.ctimer, QtCore.SIGNAL("timeout()"), self.alarm)

    ###########################################################################
    # Timer

    def startTimer(self):
        
        stop_time = self.ui.time_input.value() * 60
        self.alarm_time = QtCore.QTime.currentTime().addSecs(stop_time) # secs
        self.warning_time = QtCore.QTime.currentTime().addSecs(stop_time - 300) # secs

        self.ctimer.start(5000)    # millisecs
           

    def alarm(self):

        rmng_time = QtCore.QTime.currentTime().secsTo(self.alarm_time)
        rmng_time = (rmng_time // 60) + 1
        self.ui.rem_time.setPlainText(str(rmng_time))
        mb = MessageBox()

        if QtCore.QTime.currentTime() >= self.alarm_time:
            self.stop_timer()            
            mb.setText("Finished")
            mb.exec_()
       
        elif QtCore.QTime.currentTime() >= self.warning_time:
            self.palette.setColor(QtGui.QPalette.Base,QtCore.Qt.red)
            self.ui.rem_time.setPalette(self.palette)


    def stopTimer(self):

        self.ctimer.stop()
        self.ui.rem_time.setPlainText(str(0))
        self.palette.setColor(QtGui.QPalette.Base,QtCore.Qt.white)
        self.ui.rem_time.setPalette(self.palette)

    ###########################################################################
    # General management

    def initParams(self):

        self.mash_temp = QtGui.QTableWidgetItem(self.mash_temp)
        self.ui.brew_params.setItem(0, 0, self.mash_temp)
        self.mash_eff = QtGui.QTableWidgetItem(self.mash_eff)
        self.ui.brew_params.setItem(0, 1, self.mash_eff)
        self.vol = QtGui.QTableWidgetItem(self.vol)
        self.ui.brew_params.setItem(0, 2, self.vol)

    def grpUpdates(self):

        self.grainGrp_update()
        self.ui.grain_stock.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.ui.grain_use.setEditTriggers(QtGui.QAbstractItemView.AllEditTriggers)
        self.ui.grain_stock.clearSelection() 

        self.hopGrp_update()
        self.ui.hop_stock.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.ui.hop_use.setEditTriggers(QtGui.QAbstractItemView.AllEditTriggers)
        self.ui.hop_stock.clearSelection() 

        self.yeastGrp_update()
        self.ui.yeast_stock.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.ui.yeast_use.setEditTriggers(QtGui.QAbstractItemView.AllEditTriggers)
        self.ui.yeast_stock.clearSelection() 

    def recipeForm(self):

        self.ui.grain_stock.setEditTriggers(QtGui.QAbstractItemView.DoubleClicked)
        self.ui.grain_use.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)    

        self.ui.hop_stock.setEditTriggers(QtGui.QAbstractItemView.DoubleClicked)
        self.ui.hop_use.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)

        self.ui.yeast_stock.setEditTriggers(QtGui.QAbstractItemView.DoubleClicked)
        self.ui.yeast_use.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
    ###########################################################################
    # Grain

    def grainGrp_update(self):

        """ Adds an instance of class Grain to grain_list list of
        instances, sorts the list by EBC value and calls grain_table_update"""

        self.grain_list = []        
        for row in xrange(self.ui.grain_stock.rowCount()):
            if self.ui.grain_stock.item(row,0) != None:                
                name = self.ui.grain_stock.item(row,0).text()                
                ebc = self.ui.grain_stock.item(row,1).text() 
                extr = self.ui.grain_stock.item(row,2).text()             
                wgt = self.ui.grain_stock.item(row,3).text()
                a_grain = Grain(name, ebc, extr, wgt)
                if name != "":
                    self.grain_list.append(a_grain)

        num = -1 + len(self.grain_list)
        if len(self.grain_list) > 5:
            self.ui.grain_stock.setRowCount(num + 1)
        # sort using int or 3, 10, 1 sorts to 1, 10, 3
        self.grain_list.sort(key = lambda Grain: int(Grain.ebc))
        self.grainTable_update()


    def grainTable_update(self): 

        """ Fills cells in the grain stock table with instances 
        from grain_list. """

        self.ui.grain_stock.clearContents()

        for item in self.grain_list:
            pos = self.grain_list.index(item)
            name = Grain.get_name(item)
            ebc = Grain.get_ebc(item)
            extr = Grain.get_extr(item)
            wgt = Grain.get_wgt(item)

            name = QtGui.QTableWidgetItem(name)
            self.ui.grain_stock.setItem(pos, 0, name)

            col = QtGui.QTableWidgetItem(ebc)
            self.ui.grain_stock.setItem(pos, 1, col)

            extr = QtGui.QTableWidgetItem(extr)
            self.ui.grain_stock.setItem(pos, 2, extr)

            qty = QtGui.QTableWidgetItem(wgt)
            self.ui.grain_stock.setItem(pos, 3, qty)



    def useGrain(self):

        self.used_grain_list = []
        total = 0

        for row in xrange(self.ui.grain_use.rowCount()):
            if self.ui.grain_use.item(row,0) != None:                
                name = self.ui.grain_use.item(row,0).text()
                wgt = float(self.ui.grain_use.item(row,1).text())
                for item in self.grain_list:
                    if name == item.get_name():
                        extr = item.get_extr()
                        ebc = item.get_ebc() 
                total += wgt              
                a_used_grain = Used_Grain(name, wgt, extr, ebc)
                self.used_grain_list.append(a_used_grain)

        if total > 0:   # Calculate percentages in table
            for item in self.used_grain_list:
                pos = self.used_grain_list.index(item)
                wgt = float(Used_Grain.get_wgt(item))

                perCent = int((wgt / total) * 100)  
                perCent = str(perCent)

                perCent = QtGui.QTableWidgetItem(perCent)
                self.ui.grain_use.setItem(pos, 2, perCent)
         
        self.ui.grain_use.clearSelection()              
        self.grain_infoCalc()


    def grain_infoCalc(self):

        self.mash_eff = float(self.ui.brew_params.item(0, 1).text())
        self.vol = float(self.ui.brew_params.item(0, 2).text())
        self.mash_deg = 0
        self.total_col = 0

        for item in self.used_grain_list:
            pos = self.used_grain_list.index(item)
            wgt = float(Used_Grain.get_wgt(item))
            extr = float(Used_Grain.get_extr(item))
            col = int(Used_Grain.get_ebc(item))
            deg = (extr * wgt * (self.mash_eff / 100)) / self.vol
            self.mash_deg += deg
            col *= wgt     
            self.total_col += col


        OG = int(self.mash_deg)
        OG = str(OG)
        OG = QtGui.QTableWidgetItem(OG)

        self.total_col = int(self.total_col * 10 * (self.mash_eff / 100)) / self.vol    
        colour = int(self.total_col)
        colour = str(colour)
        colour = QtGui.QTableWidgetItem(colour)

        self.ui.brew_results.setItem(0, 1, colour)

        self.ui.brew_results.setItem(0, 2, OG)


    def grainUse_RClick(self):

        self.menu = QtGui.QMenu(self)
        Action = QtGui.QAction('Delete', self)        
        self.menu.addAction(Action)
        self.menu.popup(QtGui.QCursor.pos())
        Action.triggered.connect(self.deleteUsedGrain)



    def deleteUsedGrain(self):
        #Get the value in the right-clicked cell
        row = self.ui.grain_use.currentRow()
        column = self.ui.grain_use.currentColumn()
        sel = self.ui.grain_use.item(row, column)
        row = int(row)
        self.used_grain_list.pop(row)
        self.usedGrain_update()


    def usedGrain_update(self):

        self.ui.grain_use.clearContents()

        for item in self.used_grain_list:
            pos = self.used_grain_list.index(item)
            name = Used_Grain.get_name(item)
            wgt = str(Used_Grain.get_wgt(item)) #tablewidget won't accept float. Gawdnosewhy
            ebc = Used_Grain.get_ebc(item)

            name = QtGui.QTableWidgetItem(name)
            self.ui.grain_use.setItem(pos, 0, name)

            wgt = QtGui.QTableWidgetItem(wgt)
            self.ui.grain_use.setItem(pos, 1, wgt)

        self.useGrain()



    ###########################################################################
    #Hops

    def hopGrp_update(self):

        """ Adds an instance of class Hop to hop_list list of
        instances, sorts the list alphabetically and calls hop_table_update"""

        self.hop_list = []
        for row in xrange(self.ui.hop_stock.rowCount()):
            if self.ui.hop_stock.item(row,0) != None:                
                name = self.ui.hop_stock.item(row,0).text()                
                alpha = self.ui.hop_stock.item(row,1).text()            
                wgt = self.ui.hop_stock.item(row,2).text()
                a_hop = Hop(name, alpha, wgt)
                if name != "":
                    self.hop_list.append(a_hop)
        num = -1 + len(self.hop_list)
        if len(self.hop_list) > 5:
            self.ui.hop_stock.setRowCount(num + 1)
        self.hop_list.sort(key = lambda Hop: Hop.name)
        self.hopTable_update()


    def hopTable_update(self):

        self.ui.hop_stock.clearContents()

        for item in self.hop_list:
            pos = self.hop_list.index(item)
            name = Hop.get_name(item)
            alpha = Hop.get_alpha(item)
            wgt = Hop.get_wgt(item)

            name = QtGui.QTableWidgetItem(name)
            self.ui.hop_stock.setItem(pos, 0, name)

            alpha = QtGui.QTableWidgetItem(alpha)
            self.ui.hop_stock.setItem(pos, 1, alpha)

            wgt = QtGui.QTableWidgetItem(wgt)
            self.ui.hop_stock.setItem(pos, 2, wgt)     

    def useHop(self):

        self.used_hop_list = []
        total = 0

        for row in xrange(self.ui.hop_use.rowCount()):
            if self.ui.hop_use.item(row,0) != None:                
                name = self.ui.hop_use.item(row,0).text()
                wgt = float(self.ui.hop_use.item(row,1).text())
                time = float(self.ui.hop_use.item(row,2).text())
                for item in self.hop_list:
                    if name == item.get_name():
                        alpha = item.get_alpha()
                total += wgt 
          
                a_used_hop = Used_Hop(name, alpha, wgt, time)
                self.used_hop_list.append(a_used_hop)
       
        self.ui.hop_use.clearSelection() 
        self.hop_infoCalc()


    def hop_infoCalc(self):

        baseUtn = float(37)
        curve = float(15)
        curve *= -0.001
        self.total_ebu = 0
        vol = float(self.vol)

        for item in self.used_hop_list:
            wgt = float(Used_Hop.get_wgt(item))
            alpha = float(Used_Hop.get_alpha(item))
            time = float(Used_Hop.get_time(item))
            boilComp = 1 - math.e ** (curve * time)
            ut = baseUtn * boilComp
            ebu = (wgt * alpha * ut) / (vol * 10)
            self.total_ebu += int(ebu)

        EBU = QtGui.QTableWidgetItem(str(self.total_ebu))
        self.ui.brew_results.setItem(0, 0, EBU)


    def hopUse_RClick(self):

        self.menu = QtGui.QMenu(self)
        Action = QtGui.QAction('Delete', self)        
        self.menu.addAction(Action)
        self.menu.popup(QtGui.QCursor.pos())
        Action.triggered.connect(self.deleteUsedHop)



    def deleteUsedHop(self):
        #Get the value in the right-clicked cell
        row = self.ui.hop_use.currentRow()
        column = self.ui.hop_use.currentColumn()
        sel = self.ui.hop_use.item(row, column)
        row = int(row)
        self.used_hop_list.pop(row)
        self.usedHop_update()


    def usedHop_update(self):

        self.ui.hop_use.clearContents()

        for item in self.used_hop_list:
            pos = self.used_hop_list.index(item)
            name = Used_Hop.get_name(item)
            wgt = str(Used_Hop.get_wgt(item)) #tablewidget won't accept float. Gawdnosewhy
            time = str(Used_Hop.get_time(item))

            name = QtGui.QTableWidgetItem(name)
            self.ui.hop_use.setItem(pos, 0, name)

            wgt = QtGui.QTableWidgetItem(wgt)
            self.ui.hop_use.setItem(pos, 1, wgt)

            time = QtGui.QTableWidgetItem(time)
            self.ui.hop_use.setItem(pos, 2, time)

        self.useHop()


    ###########################################################################
    #Yeast

    def yeastGrp_update(self):

        self.yeast_list = []
        for row in xrange(self.ui.yeast_stock.rowCount()):
            if self.ui.yeast_stock.item(row,0) != None:                
                yeast_name = self.ui.yeast_stock.item(row,0).text()                          
                yeast_qty = self.ui.yeast_stock.item(row,1).text()
                a_yeast = Yeast(yeast_name, yeast_qty)
                if yeast_name != "":
                    self.yeast_list.append(a_yeast)
        num = -1 + len(self.yeast_list)
        if len(self.yeast_list) > 5:
            self.ui.yeast_stock.setRowCount(num + 1)
        self.yeast_list.sort(key = lambda yeast: yeast.name)
        self.yeastTable_update()


    def useYeast(self):

        self.used_yeast = self.ui.yeast_use.item(0, 0)
        self.pkt_use = self.ui.yeast_use.item(0, 1)
        self.ui.yeast_use.clearSelection() 


    def yeastUse_RClick(self):

        self.menu = QtGui.QMenu(self)
        Action = QtGui.QAction('Delete', self)        
        self.menu.addAction(Action)
        self.menu.popup(QtGui.QCursor.pos())
        Action.triggered.connect(self.deleteUsedYeast)


    def deleteUsedYeast(self):

        self.used_yeast = None
        self.pkt_use = None
        self.ui.yeast_use.clearContents()


    def yeastTable_update(self):

        self.ui.yeast_stock.clearContents()
        for item in self.yeast_list:
            pos = self.yeast_list.index(item)
            name = Yeast.get_name(item)
            pkts = Yeast.get_pkts(item)
            name = QtGui.QTableWidgetItem(name)
            self.ui.yeast_stock.setItem(pos, 0, name)
            qty = QtGui.QTableWidgetItem(pkts)
            self.ui.yeast_stock.setItem(pos, 1, qty)

    ############################################################################

    def save_data(self):

        root = ET.Element('Root')
        stock = ET.SubElement(root, 'Stock')

        #data_file = open("stockData", "w")

        for item in self.grain_list:
            name = item.get_name()
            name = str(name)
            name = ET.SubElement(stock, name)


            ebc = str(item.get_ebc())
            ebc = "_" + ebc
            ebc = ET.SubElement(name, ebc)

            extr = str(item.get_extr())
            extr = "_" + extr
            extr = ET.SubElement(name, extr)

            wgt = str(item.get_wgt())
            wgt = "_" + wgt
            wgt = ET.SubElement(name, wgt)
            #print name, ebc, extr, wgt


        #basename = "alestock_XML_test01.xml"
        path =  "/home/andy/D_Drive/Python/XML/alestock_XML_test01.xml" 
        with open(path, "w") as fo:
            noteTree = ET.ElementTree(root)
            noteTree.write(fo)


    def load_data(self):

        root = ET.Element('Root')
        path =  "/home/andy/D_Drive/Python/XML/alestock_XML_test01.xml"
        with open(path, "r") as fo:
            noteTree = ET.ElementTree(root)
            noteTree.parse(fo)
            print "OK"










################################################################################
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
    def __init__(self, name, wgt, extr, ebc):
        self.name = name
        self.wgt = wgt
        self.extr = extr
        self.ebc = ebc
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





if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    myapp = Mainwindow()
    myapp.show()
    #myapp.load_data()
    myapp.initParams()
    sys.exit(app.exec_())  
