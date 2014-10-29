#!/usr/bin/python
import sys, time, math, os.path
import xml.etree.cElementTree as ET
from classes import * #Grain, Used_Grain, Hop, Used_Hop, Yeast, brewCalendar, MessageBox
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
        self.plusMinus = QtCore.QChar(0x00B1)
        self.recipe_filename = None
        self.path = ""
        self.dateList = []
        self.months = {'Jan':1, 'Feb':2, 'Mar':3, 'Apr':4, 'May':5, 'Jun':6, 'Jul':7, 
            'Aug':8, 'Sep':9, 'Oct':10, 'Nov':11, 'Dec':12}
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
        self.ui.button_saveNotes.clicked.connect(self.save_notes)
        self.ui.button_startTimer.clicked.connect(self.startTimer)
        self.ui.button_stopTimer.clicked.connect(self.stopTimer)
        self.ui.button_writeNotes.clicked.connect(self.writeNotes)
        self.ui.button_use.clicked.connect(self.use)
        self.ui.button_reStock.clicked.connect(self.reStock)
        self.ui.button_useRecipe.clicked.connect(self.useRecipe)
        self.ui.button_saveBrew.clicked.connect(self.openSaveDlg)
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

        self.ui.button_search.clicked.connect(self.search)
        self.ui.search_results.itemClicked.connect(self.load_search)

        #Sub-classed qt widgets, etc
        self.textEd = textEdit(self)
        self.calendar_brew = brewCalendar(self, 1045, 473)
        self.calendar_search = brewCalendar(self, 40, 473)
        self.calendar_search.clicked.connect(self.cellClicked)
        self.saveDialogue = saveDialogue(self)

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
            self.stopTimer()            
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
        self.ui.label_plusMinus.setText(self.plusMinus)
        self.ui.label_plusMinus.setGeometry(QtCore.QRect(90, 200, 46, 12))
        font = self.ui.label_plusMinus.font()
        font.setPixelSize(15)
        self.ui.label_plusMinus.setFont(font)
        self.ui.label_brewName.setText("")
        self.hiLightDate()
 

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


    def keyPressEvent(self, qKeyEvent):

        """ Triggers calculation of used items and sorts tables to 
        eliminate blank lines. ?Bug: if kg./grams/time not all filled 
        entry is removed """

        if qKeyEvent.key() == QtCore.Qt.Key_Return: 
            self.useGrain()
            self.usedGrain_update()
            self.useHop()
            self.usedHop_update()

    ###########################################################################
    # Grain

    def grainGrp_update(self):

        """ Adds an instance of class Grain to grain_list list of
        instances, sorts the list by EBC value and calls grain_table_update"""

        self.grain_list = []        
        for row in xrange(self.ui.grain_stock.rowCount()):
            if self.ui.grain_stock.item(row,0) != None:
                if self.ui.grain_stock.item(row,0).text() != "":                
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
                    if self.ui.grain_use.item(row,1) != None:               
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
        #       total += wgt

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
                if self.ui.hop_stock.item(row,0).text() != "":               
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
                    if self.ui.hop_use.item(row,1) != None: 
                        if self.ui.hop_use.item(row,2) != None:               
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
            wgt = str(Used_Hop.get_wgt(item)) 
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
                if self.ui.yeast_stock.item(row,0).text() != "":                
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
    # Save/Load data               

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

        path =  "./stockData.xml" 
        with open(path, "w") as fo:
            tree = ET.ElementTree(root)
            tree.write(fo)


    def load_data(self):
       
        path =  "./stockData.xml"
        with open(path, "a") as fo:
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

################################################################################
#Save/Load brew

    def writeNotes(self):

        self.textEd.setGeometry(150, 475, 200, 200)
        self.textEd.setWindowTitle("Process Notes")    
        self.textEd.show()


    def openSaveDlg(self):

        self.saveDialogue.setGeometry(780, 290, 400, 180)
        self.saveDialogue.show()


    def save_brew(self, fname):

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
        procNote.text = str(self.textEd.txt.toPlainText())

        dir = './Brews'
        if not os.path.isdir(dir): os.makedirs(dir)
        path = './Brews/' + fname
        with open(path, "w") as fo:
            self.ui.label_brewName.setText(fname)
            tree = ET.ElementTree(root)
            tree.write(fo)


    def save_notes(self):

        style = str(self.ui.box_style.currentText())
        taste = self.ui.tastingNotes.toPlainText()
        rating = str(self.ui.rating.value())
        path =  'Brews' + '/' + self.recipe_filename
        tree = ET.parse(path)
        root = tree.getroot()
        for elem in root.iter('Style'):
            elem.text = style
        for elem in root.iter('Tasting'):
            elem.text =  str(taste)
        for elem in root.iter('Rating'):
            elem.text = rating
        tree.write(path)



    def load_brew(self, name):
        
        """Loads brew selected from calendar/search into review panel"""
        self.loadingBrew = True
        self.grainRecipe_list = []
        self.hopRecipe_list = []

        if name == False:
            fname = unicode(QtGui.QFileDialog.getOpenFileName(self))
            self.recipe_filename = os.path.basename(fname)
        else:
            self.recipe_filename = name
        path =  'Brews' + '/' + self.recipe_filename
        self.ui.label_name.setText(self.recipe_filename)
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
                    else:
                        self.ui.processNotes.clear() 

                if elem.tag =='Tasting':
                    if elem.text != None:
                        self.ui.tastingNotes.setPlainText(elem.text)
                    else:
                        self.ui.tastingNotes.clear()

                if elem.tag == 'Style':
                    if elem.text != None:
                        style = elem.text
                        index = self.ui.box_style.findText(style)
                        self.ui.box_style.setCurrentIndex(index)
                    else:
                        self.ui.box_style.setCurrentIndex(0)

                if elem.tag == 'Rating':
                    if elem.text != None:
                        self.ui.rating.setValue(int(elem.text))
                    else:
                        self.ui.rating.setValue(0)

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
        #self.recipe_filename = None
        self.loadingBrew = False


    def useRecipe(self):

        """Loads recipe from review panel into recipe panel"""

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
            self.ui.label_brewName.setText("Not Saved")
            self.use()
       

    def noStock(self, msg):

        mb = MessageBox()
        mb.setText(msg)
        mb.exec_()

################################################################################
#Search
    
    def hiLightDate(self):

        brewList = []

        for brewFile in os.listdir('Brews'):
            if not brewFile.startswith('.'): #filter unix hidden files
                day = int(brewFile[0:2])
                month = str(brewFile[2:5])
                year = int('20'+brewFile[5:7])       
                numMonth = int(self.months[month])
                date = QtCore.QDate(year, numMonth, day)
                brewList.append(date)
        self.calendar_search.dates(brewList)


    def search(self):

        search_word = str(self.ui.search_box.text())
        result = []
        rating_list = []
        rating = int(self.ui.rating_input.value())
        ratingRange = self.ui.ratingPlusMinus.value()


        if rating != 0:
            for brewFile in os.listdir('Brews'):
                if not brewFile.startswith('.'): #filter unix hidden files
                    with open('Brews' + '/' + brewFile) as brew: 
                        tree = ET.parse(brew)              
                        root = tree.getroot()
                        for elem in root.iter():
                            if elem.tag == 'Rating':
                                brewRating = int(elem.text)
                                if rating - ratingRange <=  brewRating <= rating + ratingRange:
                                    rating_list.append(brewFile) 

        #now search only the files in rating_list
            for brewFile in rating_list:
                with open('Brews' + '/' + brewFile) as brew: 
                    for line in brew:                    
                        if search_word.lower() in line.lower():
                            result.append(brewFile) 
                            break
        #condition if rating not entered
        else:
            for brewFile in os.listdir('Brews'):
                if not brewFile.startswith('.'):
                    with open('Brews' + '/' + brewFile) as brew: 
                        for line in brew:                    
                            if search_word.lower() in line.lower():
                                result.append(brewFile) 
                                break

        if result != []: 
            if search_word == "":
                filler = ''
            else:
                filler = ' '
            heading =  search_word + filler + '(' + 'Rating' + ' ' + str(rating) + ')'
            heading = QtGui.QListWidgetItem(heading)
            heading.setFont(QtGui.QFont('Sans Serif', 9, QtGui.QFont.Bold))  
            self.ui.search_results.addItem(heading)
            #self.ui.search_results.addItem(self.plusMinus)        
            self.ui.search_results.addItems(result)
            self.ui.search_results.addItem("")
        else:
            self.ui.search_results.addItem(search_word)
            self.ui.search_results.addItem("Not Found")
            self.ui.search_results.addItem("")


    def load_search(self):
        basename = self.ui.search_results.currentItem()
        basename = basename.text()
        self.load_brew(basename)


#################################################################################
#Brew calendar display

    def convertDate(self):

        self.dateList = []
        dateString = self.recipe_filename
        day = int(dateString[0:2])
        month = str(dateString[2:5])
        year = int('20'+dateString[5:7])       
        numMonth = int(self.months[month])

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


    def selectBrew(self, date):
       
        day = date.day()
        month = date.month()
        month = date.shortMonthName(month)
        year = date.year()
        year = str(year - 2000)
        month = str(month)
        day = str(day)
        brew = day + month + year
        self.load_brew(brew)


    def cellClicked(self, date):        
         self.selectBrew(date)






################################################################################


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    myapp = Mainwindow()
    myapp.show()
    myapp.load_data()
    myapp.initParams()
    sys.exit(app.exec_())  
