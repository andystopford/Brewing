#!/usr/bin/python
import sys, time, math, os.path
import xml.etree.cElementTree as ET
from PyQt4 import QtCore, QtGui
from alestockUI_v2 import Ui_MainWindow

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


class Mainwindow (QtGui.QMainWindow):
    def __init__(self, parent = None):
        QtGui.QWidget.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.grain_list = []
        self.sel_grain = 0
        self.used_grain_list = []
        self.grainRecipe_list = []
        self.hop_list = []
        self.used_hop_list = []
        self.hopRecipe_list = []
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
        self.loadingBrew = False
        self.dirty = False
        self.brew_filename = None
        self.path = ""
        self.dateList = []
        self.ui.button_reStock.setChecked(True)
        self.mode_grp = [self.ui.button_reStock, self.ui.button_use]

        self.alarm_time = 0
        self.palette = QtGui.QPalette() 

        #Event filters
        self.ui.grain_use.installEventFilter(self)         

        # Connect signals to slots
        self.ui.Save_Data.triggered.connect(self.save_data)
        self.ui.Load_data.triggered.connect(self.load_data)
        self.ui.Save_Brew.triggered.connect(self.save_brew)
        self.ui.Load_Brew.triggered.connect(self.load_brew)
        #self.ui.button_saveNotes.clicked.connect(self.convertDate)
        self.ui.button_startTimer.clicked.connect(self.startTimer)
        self.ui.button_stopTimer.clicked.connect(self.stopTimer)

        self.ui.button_use.clicked.connect(self.use)
        self.ui.button_reStock.clicked.connect(self.reStock)
        self.ui.button_useRecipe.clicked.connect(self.useRecipe)

        self.ui.button_grainUseUpdate.clicked.connect(self.useGrain)
        self.ui.button_hopUseUpdate.clicked.connect(self.useHop)
        self.ui.button_commit.clicked.connect(self.commit)

        self.ui.grain_use.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.ui.grain_use.connect(self.ui.grain_use, QtCore.SIGNAL
            ("customContextMenuRequested(QPoint)"), self.grainUse_RClick)

        self.ui.hop_use.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.ui.hop_use.connect(self.ui.hop_use, QtCore.SIGNAL
            ("customContextMenuRequested(QPoint)"), self.hopUse_RClick)

        self.ui.yeast_use.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.ui.yeast_use.connect(self.ui.yeast_use, QtCore.SIGNAL
            ("customContextMenuRequested(QPoint)"), self.yeastUse_RClick)

        #Sub-class qt widgets
        self.calendar_brew = brewCalendar(self)


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
        self.reStock()
        self.ui.tabWidget.setCurrentIndex(1)
        self.ui.button_commit.setEnabled(False)
        plusMinus = QtCore.QChar(0x00B1)
        self.ui.label_plusMinus.setText(plusMinus)
        self.ui.label_plusMinus.setGeometry(QtCore.QRect(90, 200, 46, 12))
        font = self.ui.label_plusMinus.font()
        font.setPixelSize(15)
        font.setBold(True)
        self.ui.label_plusMinus.setFont(font)


    def use(self):

        self.grainGrp_update()
        self.ui.grain_stock.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.ui.grain_use.setEditTriggers(QtGui.QAbstractItemView.AllEditTriggers)
        self.ui.grain_use.setAcceptDrops(True)
        self.ui.grain_stock.clearSelection() 

        self.hopGrp_update()
        self.ui.hop_stock.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.ui.hop_use.setEditTriggers(QtGui.QAbstractItemView.AllEditTriggers)
        self.ui.hop_use.setAcceptDrops(True)
        self.ui.hop_stock.clearSelection() 

        self.yeastGrp_update()
        self.ui.yeast_stock.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.ui.yeast_use.setEditTriggers(QtGui.QAbstractItemView.AllEditTriggers)
        self.ui.yeast_use.setAcceptDrops(True)
        self.ui.yeast_stock.clearSelection() 
        self.ui.tabWidget.setCurrentIndex(0)


    def reStock(self):

        self.ui.grain_stock.setEditTriggers(QtGui.QAbstractItemView.DoubleClicked)
        self.ui.grain_use.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers) 
        self.ui.grain_use.setAcceptDrops(False)   

        self.ui.hop_stock.setEditTriggers(QtGui.QAbstractItemView.DoubleClicked)
        self.ui.hop_use.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.ui.hop_use.setAcceptDrops(False)

        self.ui.yeast_stock.setEditTriggers(QtGui.QAbstractItemView.DoubleClicked)
        self.ui.yeast_use.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.ui.yeast_use.setAcceptDrops(False)
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

        total = 0

        if self.loadingBrew == False:
            self.used_grain_list = []
            stockList = []           
            for row in xrange(self.ui.grain_use.rowCount()):
                if self.ui.grain_use.item(row,0) != None:                
                    name = self.ui.grain_use.item(row,0).text()
                    wgt = float(self.ui.grain_use.item(row,1).text())
                    for item in self.grain_list:
                        if name == item.get_name():
                            stockName = item.get_name()
                            stockList.append(stockName) 
                            extr = item.get_extr()
                            ebc = item.get_ebc()
                    if name not in stockList:
                        self.noStock("Warning: "+name+" not in stock")
                        self.ui.grain_use.removeRow(row)
                    else:
                        total += wgt              
                        a_used_grain = Used_Grain(name, ebc, extr, wgt)
                        self.used_grain_list.append(a_used_grain)
        else:
            for item in self.used_grain_list:
                wgt = float(item.get_wgt())
                total += wgt

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
        self.commit_enable()


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
        #self.loadingBrew = False


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

    def grainRecipe_update (self):

        self.ui.grain_recipe.clearContents()
        total = 0

        for item in self.grainRecipe_list:
            pos = self.grainRecipe_list.index(item)
            name = Used_Grain.get_name(item)
            wgt = str(Used_Grain.get_wgt(item)) 

            name = QtGui.QTableWidgetItem(name)
            self.ui.grain_recipe.setItem(pos, 0, name)

            wgt = QtGui.QTableWidgetItem(wgt)
            self.ui.grain_recipe.setItem(pos, 1, wgt)

            wgt = float(Used_Grain.get_wgt(item))
            total += wgt

        for item in self.grainRecipe_list:
            pos = self.grainRecipe_list.index(item)
            wgt = float(Used_Grain.get_wgt(item))
            perCent = int((wgt / total) * 100)  
            perCent = str(perCent)

            perCent = QtGui.QTableWidgetItem(perCent)
            self.ui.grain_recipe.setItem(pos, 2, perCent)


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

        if self.loadingBrew == False:
            self.used_hop_list = []
            total = 0
            stockList = []

            for row in xrange(self.ui.hop_use.rowCount()):
                if self.ui.hop_use.item(row,0) != None:                
                    name = self.ui.hop_use.item(row,0).text()
                    wgt = float(self.ui.hop_use.item(row,1).text())
                    time = float(self.ui.hop_use.item(row,2).text())
                    for item in self.hop_list:
                        if name == item.get_name():
                            stockName = item.get_name()
                            stockList.append(stockName)
                            alpha = item.get_alpha()
                    if name not in stockList:
                        print name
                        self.noStock("Warning: " +name + " not in stock")
                        self.ui.hop_use.removeRow(row)
                    else:
                        total += wgt               
                        a_used_hop = Used_Hop(name, alpha, wgt, time)
                        self.used_hop_list.append(a_used_hop)

        self.ui.hop_use.clearSelection() 
        self.hop_infoCalc()
        self.commit_enable()


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


    def hopRecipe_update(self):

        self.ui.hop_recipe.clearContents()

        for item in self.hopRecipe_list:
            pos = self.hopRecipe_list.index(item)
            name = Used_Hop.get_name(item)
            wgt = str(Used_Hop.get_wgt(item)) #tablewidget won't accept float. Gawdnosewhy
            time = str(Used_Hop.get_time(item))

            name = QtGui.QTableWidgetItem(name)
            self.ui.hop_recipe.setItem(pos, 0, name)

            wgt = QtGui.QTableWidgetItem(wgt)
            self.ui.hop_recipe.setItem(pos, 1, wgt)

            time = QtGui.QTableWidgetItem(time)
            self.ui.hop_recipe.setItem(pos, 2, time)


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

        self.used_yeast = self.ui.yeast_use.item(0, 0).text()
        self.pkt_use = int(self.ui.yeast_use.item(0, 1).text())
        self.ui.yeast_use.clearSelection() 
        self.commit_enable()


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
    def commit_enable(self):
        self.ui.button_commit.setEnabled(True)

    def commit(self):

        reply = QtGui.QMessageBox.question(self, "Commit Changes", 
            "Commit changes to Database? (Data Save will still be required)", 
                QtGui.QMessageBox.Yes|QtGui.QMessageBox.No|QtGui.QMessageBox.Cancel)
        if reply == QtGui.QMessageBox.Cancel:
                return False
        elif reply == QtGui.QMessageBox.Yes:

            for item in self.used_grain_list:
                used_name = Used_Grain.get_name(item)
                used_wgt = float(Used_Grain.get_wgt(item))
                grain_dict = dict([(used_name, used_wgt)])
                for item in self.grain_list:
                    grain_name = Grain.get_name(item)
                    if grain_name == used_name:
                        item.wgt = float (item.wgt)
                        item.wgt -= used_wgt
                        if item.wgt < 0:
                            item.wgt = 0
                        item.wgt = str(item.wgt)
                        self.grainTable_update()

            for item in self.used_hop_list:
                used_name = Used_Hop.get_name(item)
                used_wgt = float(Used_Hop.get_wgt(item))
                hop_dict = dict([(used_name, used_wgt)])
                for item in self.hop_list:
                    hop_name = Hop.get_name(item)
                    if hop_name == used_name:
                        item.wgt = float (item.wgt)
                        item.wgt -= used_wgt
                        if item.wgt < 0:
                            item.wgt = 0
                        item.wgt = str(item.wgt)
                        self.hopTable_update()

            self.useYeast()
            for item in self.yeast_list:
                yeast_name = Yeast.get_name(item)
                if yeast_name == self.used_yeast:
                    item.pkts = int(item.pkts)
                    item.pkts -= self.pkt_use
                    if item.pkts < 0:
                        item.pkts = 0
                    item.pkts = str(item.pkts)
                    self.yeastTable_update()  

                self.ui.button_commit.setEnabled(False)                  


    ###########################################################################                

    def save_data(self):

        root = ET.Element('Root')
        stock = ET.SubElement(root, 'Stock')
        grain = ET.SubElement(stock, 'Grain')
        hop = ET.SubElement(stock, 'Hop')
        yeast = ET.SubElement(stock, 'Yeast')

        for item in self.grain_list:
            name = item.get_name()
            name = str(name)
            name = name.replace(' ', '_')
            name = ET.SubElement(grain, name)
            ebc = str(item.get_ebc())
            ebc = "_" + ebc
            ebc = ET.SubElement(name, ebc)
            extr = str(item.get_extr())
            extr = "_" + extr
            extr = ET.SubElement(name, extr)
            wgt = str(item.get_wgt())
            wgt = "_" + wgt
            wgt = ET.SubElement(name, wgt)

        for item in self.hop_list:
            name = item.get_name()
            name = str(name)
            name = name.replace(' ', '_')
            name = ET.SubElement(hop, name)
            alpha = str(item.get_alpha())
            alpha = "_" + alpha
            alpha = ET.SubElement(name, alpha)
            wgt = str(item.get_wgt())
            wgt = "_" + wgt
            wgt = ET.SubElement(name, wgt)

        for item in self.yeast_list:
            name = item.get_name()
            name = str(name)
            name = name.replace(' ', '_')
            name = ET.SubElement(yeast, name)
            pkts = str(item.get_pkts())
            pkts = "_" + pkts
            pkts = ET.SubElement(name, pkts)

        #basename = "alestock_XML_test01.xml"
        path =  "/home/andy/D_Drive/Python/XML/alestock_XML_test01.xml" 
        with open(path, "w") as fo:
            tree = ET.ElementTree(root)
            tree.write(fo)


    def load_data(self):
       
        path =  "/home/andy/D_Drive/Python/XML/alestock_XML_test01.xml"
        with open(path, "r") as fo:
            tree = ET.ElementTree(file = path)
            root = tree.getroot()
            for elem in root.iter():
                if elem.tag == 'Grain':
                    for grain in elem:
                        grainData = []
                        for data in grain:
                            data = data.tag[1:]
                            grainData.append(data)
                        grainName = grain.tag.replace('_', ' ')
                        a_grain = Grain(grainName, grainData[0], grainData[1], grainData[2])
                        self.grain_list.append(a_grain)
                    self.grainTable_update()

                if elem.tag == 'Hop':
                    for hop in elem:
                        hopData = []
                        for data in hop:
                            data = data.tag[1:]
                            hopData.append(data)
                        hopName = hop.tag.replace('_', ' ')
                        a_hop = Hop(hopName, hopData[0], hopData[1])
                        self.hop_list.append(a_hop)
                    self.hopTable_update()

                if elem.tag == 'Yeast':
                    for yeast in elem:
                        yeastData = []
                        for data in yeast:
                            data = data.tag[1:]
                            yeastData.append(data)
                        yeastName = yeast.tag.replace('_', ' ')
                        a_yeast = Yeast(yeastName, yeastData[0])
                        self.yeast_list.append(a_yeast)
                    self.yeastTable_update()


    def save_brew(self):

        if self.brew_filename is None:
            self.save_brew_as()

        else:       
            root = ET.Element('Root')
            ingredient = ET.SubElement(root, 'Ingredient')
            notes = ET.SubElement(root, 'Notes')
            grain = ET.SubElement(ingredient, 'Grain')
            hop = ET.SubElement(ingredient, 'Hops')
            yeast = ET.SubElement(ingredient, 'Yeast')

            params = ET.SubElement(root, 'Params')
            temp = ET.SubElement(params, 'Temp')
            eff = ET.SubElement(params, 'Eff')
            vol = ET.SubElement(params, 'Vol')

            results = ET.SubElement(root, 'Results')
            EBU = ET.SubElement(results, 'EBU')
            EBC = ET.SubElement(results, 'EBC')
            OG = ET.SubElement(results, 'OG')

            procNote = ET.SubElement(notes, 'Process')
            tastNote = ET.SubElement(notes, 'Tasting')
            style = ET.SubElement(notes, 'Style')
            rating = ET.SubElement(notes, 'Rating')

            for item in self.used_grain_list:
                name = item.get_name()
                name = str(name)
                name = name.replace(' ', '_')
                name = ET.SubElement(grain, name)
                ebc = str(item.get_ebc())
                ebc = "_" + ebc
                ebc = ET.SubElement(name, ebc)
                extr = str(item.get_extr())
                extr = "_" + extr
                extr = ET.SubElement(name, extr)
                wgt = str(item.get_wgt())
                wgt = "_" + wgt
                wgt = ET.SubElement(name, wgt)
                
            for item in self.used_hop_list:
                name = item.get_name()
                name = str(name)
                name = name.replace(' ', '_')
                name = ET.SubElement(hop, name)
                alpha = str(item.get_alpha())
                alpha = "_" + alpha
                alpha = ET.SubElement(name, alpha)
                wgt = str(item.get_wgt())
                wgt = "_" + wgt
                wgt = ET.SubElement(name, wgt)
                time = str(item.get_time())
                time = "_" + time
                time = ET.SubElement(name, time)

            usedYeast = self.ui.yeast_use.item(0, 0).text()
            usedYeast = str(usedYeast)
            usedYeast = usedYeast.replace(' ', '_')
            usedYeast = ET.SubElement(yeast, usedYeast)

            pkts = self.pkt_use
            pkts = str(pkts)
            usedYeast.text = pkts

            temp.text = str(self.ui.brew_params.item(0, 0).text())
            eff.text = str(self.ui.brew_params.item(0, 1).text())
            vol.text = str(self.ui.brew_params.item(0, 2).text())
            EBU.text = str(self.ui.brew_results.item(0, 0).text())
            EBC.text = str(self.ui.brew_results.item(0, 1).text())
            OG.text = str(self.ui.brew_results.item(0, 2).text())
            style.text = str(self.ui.box_style.currentText())
            rating.text = str(self.ui.rating.value())

            procNote.text = str(self.ui.processNotes.toPlainText())
            tastNote.text = str(self.ui.tastingNotes.toPlainText())

            with open(self.brew_filename, "w") as fo:
                tree = ET.ElementTree(root)
                tree.write(fo)

    def save_brew_as(self):

        dir = './Brews'
        if not os.path.isdir(dir): os.makedirs(dir)
        fname = self.brew_filename if self.brew_filename is not None else "."
        fname = unicode(QtGui.QFileDialog.getSaveFileName(self))
        self.brew_filename = fname 
        self.save_brew()

    def save_notes(self):
        print self.grainRecipe_list


    def load_brew(self):

        self.loadingBrew = True
        fname = unicode(QtGui.QFileDialog.getOpenFileName(self))
        self.brew_filename = os.path.basename(fname)
        self.grainRecipe_list = []
        self.hopRecipe_list = []

        path =  'Brews' + '/' + self.brew_filename 
        #basename = basename.replace('.xml', '')
        self.ui.label_name.setText(self.brew_filename)
        with open(path, "r") as fo:
            tree = ET.ElementTree(file = path)
            root = tree.getroot()
            for elem in root.iter():
                if elem.tag == 'Grain':
                    for grain in elem:
                        grainData = []
                        for data in grain:
                            data = data.tag[1:]
                            grainData.append(data)
                        grainName = grain.tag.replace('_', ' ')
                        a_grain = Used_Grain(grainName, grainData[0], grainData[1], grainData[2])
                        self.grainRecipe_list.append(a_grain)
                    self.grainRecipe_update()

                if elem.tag == 'Hops':
                    for hop in elem:
                        hopData = []
                        for data in hop:
                            data = data.tag[1:]
                            hopData.append(data)
                        hopName = hop.tag.replace('_', ' ')
                        a_hop = Used_Hop(hopName, hopData[0], hopData[1], hopData[2])
                        self.hopRecipe_list.append(a_hop)
                    self.hopRecipe_update()

                if elem.tag == 'Yeast':
                    for yeast in elem:
                        name = yeast.tag
                        pkts = yeast.text
                    name = name.replace('_', ' ')
                    name = QtGui.QTableWidgetItem(name)
                    pkts = QtGui.QTableWidgetItem(pkts)
                    self.ui.recipe_results.setItem(0, 4, name)

                if elem.tag =='Process':
                    if elem.text != None:
                        self.ui.processNotes.setPlainText(elem.text) 

                if elem.tag =='Tasting':
                    if elem.text != None:
                        self.ui.tastingNotes.setPlainText(elem.text)

                if elem.tag == 'Style':
                    style = elem.text
                    index = self.ui.box_style.findText(style)
                    self.ui.box_style.setCurrentIndex(index)

                if elem.tag == 'Rating':
                    self.ui.rating.setValue(int(elem.text))

                if elem.tag == 'EBU':
                    ebu = str(elem.text)
                    ebu = QtGui.QTableWidgetItem(ebu)
                    self.ui.recipe_results.setItem(0, 0, ebu)

                if elem.tag == 'EBC':
                    ebc = str(elem.text)
                    ebc = QtGui.QTableWidgetItem(ebc)
                    self.ui.recipe_results.setItem(0, 1, ebc)

                if elem.tag == 'OG':
                    og = str(elem.text)
                    og = QtGui.QTableWidgetItem(og)
                    self.ui.recipe_results.setItem(0, 2, og)

                if elem.tag == 'Temp':
                    temp = str(elem.text)
                    temp = QtGui.QTableWidgetItem(temp)
                    self.ui.recipe_results.setItem(0, 3, temp)

        self.convertDate()
        self.loadingBrew = False


    def useRecipe(self):

        if self.grain_list == []:
            msg = "Error: no stock data"
            self.noStock(msg)
        elif self.hop_list == []:
            msg = "Error: no stock data"
            self.noStock(msg)            
        elif self.yeast_list == []:
            msg = "Error: no stock data"
            self.noStock(msg)

        else:
            self.ui.grain_use.clearContents()
            self.ui.hop_use.clearContents()
            stockList = []

            for item in self.grainRecipe_list:
                pos = self.grainRecipe_list.index(item)
                name = Used_Grain.get_name(item)
                wgt = str(Used_Grain.get_wgt(item)) #tablewidget won't accept float. Gawdnosewhy
                ebc = Used_Grain.get_ebc(item)

                name = QtGui.QTableWidgetItem(name)
                self.ui.grain_use.setItem(pos, 0, name)

                wgt = QtGui.QTableWidgetItem(wgt)
                self.ui.grain_use.setItem(pos, 1, wgt)

            self.useGrain()

            for item in self.hopRecipe_list:
                pos = self.hopRecipe_list.index(item)
                name = Used_Hop.get_name(item)
                wgt = str(Used_Hop.get_wgt(item)) 
                time = str(Used_Hop.get_time(item))

                name = QtGui.QTableWidgetItem(name)
                self.ui.hop_use.setItem(pos, 0, name)

                wgt = QtGui.QTableWidgetItem(wgt)
                self.ui.hop_use.setItem(pos, 1, wgt)

                time = QtGui.QTableWidgetItem(time)
                self.ui.hop_use.setItem(pos, 2, time)

            self.useHop()
            
            temp = str(self.ui.recipe_results.item(0, 3).text())
            temp = QtGui.QTableWidgetItem(temp)
            self.ui.brew_params.setItem(0, 0, temp)

            yeast = str(self.ui.recipe_results.item(0, 4).text())
            for item in self.yeast_list:
                stockName = item.get_name()
                stockList.append(stockName)
            if yeast not in stockList:
                self.noStock("Warning: "+yeast+" not in stock")
            else:
                yeast = QtGui.QTableWidgetItem(yeast)                        
                pkts = str(3)
                pkts = QtGui.QTableWidgetItem(pkts)
                self.ui.yeast_use.setItem(0, 0, yeast)
                self.ui.yeast_use.setItem(0, 1, pkts)
            self.use()
       

    def noStock(self, msg):

        mb = MessageBox()
        mb.setText(msg)
        mb.exec_()


#################################################################################
#Brew calendar display
    def convertDate(self):

        self.dateList = []
        dateString = self.brew_filename
        day = int(dateString[0:2])
        month = dateString[2:5]
        year = int('20'+dateString[5:7])
        months = {'Jan':1, 'Feb':2, 'Mar':3, 'Apr':4, 'May':5, 'Jun':6, 'Jul':7, 
            'Aug':8, 'Sep':9, 'Oct':10, 'Nov':11, 'Dec':12}
        numMonth = int(months[month])

        date = QtCore.QDate()
        num = -1 #use -1 to avoid colouring current day
        currDate = self.calendar_brew.selectedDate()
        brewDate = QtCore.QDate(year,numMonth,day)
        days = currDate.daysTo(brewDate)
        while num >= days:
            date = currDate.addDays(num)
            self.dateList.append(date)
            num -= 1
        #if statement here for old (>3 months? - Preferences) brews
        self.calendar_brew.dates(self.dateList)



class brewCalendar(QtGui.QCalendarWidget):
    def __init__(self, parent):    
        QtGui.QCalendarWidget.__init__(self, parent)
        self.setGeometry(QtCore.QRect(1045, 473, 232, 129))
        self.setHorizontalHeaderFormat(QtGui.QCalendarWidget.SingleLetterDayNames)
        self.color = QtGui.QColor(self.palette().color(QtGui.QPalette.Highlight))
        self.color.setRgb(255,0,0)
        self.color.setAlpha(64)
        self.selectionChanged.connect(self.updateCells)
        self.selectionChanged.connect(self.message)
        self.dateList = []
        self.setGridVisible(True)


    def paintCell(self, painter, rect, date):
        QtGui.QCalendarWidget.paintCell(self, painter, rect, date)
        if date in self.dateList:
            painter.fillRect(rect, self.color)
            

    def dates(self, dateList):
        self.dateList = dateList
        self.updateCells()


    def message(self):
        print "changed"


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


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    myapp = Mainwindow()
    myapp.show()
    #myapp.load_data()
    myapp.initParams()
    sys.exit(app.exec_())  
