#!/usr/bin/python
import sys, time
from PyQt4 import QtCore, QtGui
from alestock_v2_0_01 import Ui_MainWindow

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
        self.mash_temp = 66
        self.mash_deg = 0
        self.total_col = 0
        self.total_ebu = 0
        self.pkt_use = 3 
        self.vol = 60
        self.dirty = False

        self.alarm_time = 0
        self.palette = QtGui.QPalette()          

        # Connect signals to slots
        self.ui.button_noteSave.clicked.connect(self.test)
        self.ui.button_startTimer.clicked.connect(self.start_timer)
        self.ui.button_stopTimer.clicked.connect(self.stop_timer)
        self.ui.button_grainUpdate.clicked.connect(self.grain_grp_update)
        self.ui.button_hopUpdate.clicked.connect(self.hop_grp_update)
        self.ui.button_yeastUpdate.clicked.connect(self.yeast_grp_update)
        self.ui.button_grainUseUpdate.clicked.connect(self.useGrain)

        #self.ui.grain_use.itemChanged.connect(self.used_grain_wgt_enter)
        #self.ui.hop_use.itemChanged.connect(self.used_hop_calc)


    ###########################################################################
    
        self.ctimer = QtCore.QTimer()
        QtCore.QObject.connect(self.ctimer, QtCore.SIGNAL("timeout()"), self.alarm)

    ###########################################################################



    # Timer

    def start_timer(self):
        
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


    def stop_timer(self):

        self.ctimer.stop()
        self.ui.rem_time.setPlainText(str(0))
        self.palette.setColor(QtGui.QPalette.Base,QtCore.Qt.white)
        self.ui.rem_time.setPalette(self.palette)

    ###########################################################################
    # Grain

    def grain_grp_update(self):

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
        self.grain_table_update()


    def grain_table_update(self): 

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

        wgt = float(0)
        extr = ""
        ebc = ""
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



        print ""
        print len(self.used_grain_list)
        for item in self.used_grain_list:
            print item.name
            print item.wgt
            print item.extr
            print item.ebc

    def contextMenuEvent(self, event):
        self.menu = QtGui.QMenu(self)
        Action = QtGui.QAction('Delete', self)
        Action.triggered.connect(self.test)
        self.menu.addAction(Action)
        # add other required actions
        self.menu.popup(QtGui.QCursor.pos())
    
    def test(self):
        thing = self.ui.grain_use.currentRow()
        print thing

    def used_grain_update(self):

        for item in self.used_grain_list:
            pos = self.used_grain_list.index(item)
            name = Used_Grain.get_name(item)
            wgt = Used_Grain.get_wgt(item)
            ebc = Used_Grain.get_ebc(item)
  
        name = QtGui.QTableWidgetItem(name)
        self.ui.grain_use.setItem(pos, 0, name)

        wgt = QtGui.QTableWidgetItem(wgt)
        self.ui.grain_use.setItem(pos, 1, wgt)



   


    ###########################################################################
    #Hops

    def hop_grp_update(self):

        """ Adds an instance of class Hop to hop_list list of
        instances, sorts the list alphabetically and calls hop_table_update"""

        self.hop_list = []
        for row in xrange(self.ui.hop_stock.rowCount()):
            if self.ui.hop_stock.item(row,0) != None:                
                hop_name = self.ui.hop_stock.item(row,0).text()                
                hop_alpha = self.ui.hop_stock.item(row,1).text()            
                hop_qty = self.ui.hop_stock.item(row,2).text()
                a_hop = Hop(hop_name, hop_alpha, hop_qty)
                if hop_name != "":
                    self.hop_list.append(a_hop)
        num = -1 + len(self.hop_list)
        if len(self.hop_list) > 5:
            self.ui.hop_stock.setRowCount(num + 1)
        self.hop_list.sort(key = lambda Hop: Hop.name)
        self.hop_table_update()


    def hop_table_update(self):

        self.ui.hop_stock.clearContents()

        for item in self.hop_list:
            pos = self.hop_list.index(item)
            name = Hop.get_name(item)
            alpha = Hop.get_alpha(item)
            wgt = Hop.get_wgt(item)

            name = QtGui.QTableWidgetItem(name)
            self.ui.hop_stock.setItem(pos, 0, name)

            val = QtGui.QTableWidgetItem(alpha)
            self.ui.hop_stock.setItem(pos, 1, val)

            qty = QtGui.QTableWidgetItem(wgt)
            self.ui.hop_stock.setItem(pos, 2, qty)        

    ###########################################################################
    #Yeast

    def yeast_grp_update(self):

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
        self.yeast_table_update()

    def yeast_table_update(self):

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
    sys.exit(app.exec_())  
