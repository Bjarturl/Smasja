from PyQt5.uic import loadUiType 
from PyQt5.QtCore import QRunnable, pyqtSlot, QObject, pyqtSignal, QThreadPool
Ui_MainWindow, QMainWindow = loadUiType('smasja.ui')

class Axis():
    def __init__(self, fig, num): #klasi sem heldur utan um subplot, tekur inn widget og staðsetningu
        self.plot_counter = 0 #fjoldi lína
        self.pot_index = -1 #staðsetning á keri á grafi
        self.scatters = [] #scatter gröf fyrir undo virkni
        self.ax = fig.add_subplot(num)
        self.ax.grid()
        self.ax.tick_params(axis ='x', rotation = -90) #snúa ticks á x-ás um 90°


    def clearGraph(self): #hreinsa allt af subplotti (restart)
        self.ax.clear()
        self.ax.grid()
        self.ax.tick_params(axis ='x', rotation = -90)
        self.plot_counter = 0
        self.pot_index = -1
        self.scatters = []

class SecondaryAxis(): #Klasi sem heldur utan um gröf á vinstri y-ásnum
    def __init__(self, ax):
        self.plot_counter = 0
        self.pot_index = -1
        self.scatters = []
        self.ax = ax.ax.twinx()
        self.ax.tick_params(axis ='x', rotation = -90)
        self.set_visible(False)
        
    def set_visible(self, bool): #Sýna ticks
        if bool:
            self.ax.get_yaxis().set_visible(True)
        else:
            self.ax.get_yaxis().set_visible(False)
    
    def clearGraph(self):
        self.ax.clear()
        self.ax.tick_params(axis ='x', rotation = -90)
        self.plot_counter = 0
        self.pot_index = -1
        self.scatters = []

class WorkerSignals(QObject): #Signals fyrir worker thread
    finished = pyqtSignal() #Tókst upp
    error = pyqtSignal(tuple) #Villa
    progress = pyqtSignal(int) #Thread í gangi

class Worker(QRunnable):
    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()
        self.fn = fn #Fall sem á að keyra
        self.args = args #arguments fyrir callback fallið
        self.kwargs = kwargs #keywords fyrir callback fallið
        self.signals = WorkerSignals() 
        self.kwargs['progress_callback'] = self.signals.progress

    @pyqtSlot()
    def run(self):
        try:
            result = self.fn(*self.args, **self.kwargs) #keyrum fallið
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        finally: #Keyrslu lokið
            self.signals.finished.emit() 

class Main(QMainWindow, Ui_MainWindow): #Öll virkni
    def __init__(self, ):
        super(Main, self).__init__()
        self.setupUi(self)
        self.setWindowTitle('SMÁSJÁ (Sjá Myndræna Ástandssögu Skála og Jaðarkera í Álframleiðslu)')
        self.setWindowIcon(QtGui.QIcon('microscope.ico'))
        #Upphafsstilla nokkur gildi
        self.msglabel.hide() 
        self.textfixer.setStyleSheet('QWidget#textfixer {border:none}')
        self.potlistbox.setStyleSheet('QWidget#potlistbox {border:none}')
        self.header = self.xlist.horizontalHeader()       
        self.header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        self.xlist.setHorizontalHeaderLabels(['X', 'Y'])
        self.keyboard = Controller() #til að gera macros
        self.threadpool = QThreadPool()
        #Skilgreini breytur
        self.pot_or_line = 'line' #segir til um hvort pot eða line sé valið til að teikna
        self.save_location = path.expanduser("~").replace("\\","/") + '/' #default save staðsetning er heimasvæði notanda
        self.graphed_data = '' #heldur utan um hvað er til sýnis til að setja í save file nafnið
        #Skilgreini subplots
        self.fig = Figure()
        self.one_ax = Axis(self.fig, 111)
        self.one_ax_a2 = SecondaryAxis(self.one_ax)
        self.one_ax.ax.set_visible(False) #fela stóru myndina í byrjun
        self.one_ax_a2.ax.set_visible(False) 
        self.left_ax = Axis(self.fig, 121)
        self.left_ax_a2 = SecondaryAxis(self.left_ax)
        self.right_ax = Axis(self.fig, 122)
        self.right_ax_a2 = SecondaryAxis(self.right_ax)
        self.curr_ax = self.left_ax #default byrjunarstaður er vinstri mynd
        self.canvas = FigureCanvas(self.fig) #Sér um birtingu á gröfum
        self.plotLayout.addWidget(self.canvas) #bæti striga á interface-ið
        #Skilgreini shortcuts
        self.save_shortcut = QtWidgets.QShortcut(QtGui.QKeySequence('Ctrl+S'), self)
        self.save_shortcut.activated.connect(self.saveGraph)
        self.updateData_shortcut = QtWidgets.QShortcut(QtGui.QKeySequence('Ctrl+U'), self)
        self.updateData_shortcut.activated.connect(self.prepareUpdate)
        self.undo_shortcut = QtWidgets.QShortcut(QtGui.QKeySequence('Ctrl+Z'), self)
        self.undo_shortcut.activated.connect(self.undo)
        self.clearAx_shortcut = QtWidgets.QShortcut(QtGui.QKeySequence('Ctrl+A'), self)
        self.clearAx_shortcut.activated.connect(self.clearAxis)
        #tengist oracle gagnagrunni
        conn = 'REDACTED' = connect.cursor()
        self.xvals = ["REDACTED"] #Fyrirfram skilgreind x og y gildi 
        self.yvals = ["REDACTED"]
        self.populateComboBox(self.xbox, self.xvals) #bæti í drop down listann
        self.populateComboBox(self.ybox, self.yvals)
        c.execute("SELECT DISTINCT(REDACTED) FROM REDACTED") #vel öll kerskálanúmer úr töflu
        c.execute("SELECT DISTINCT(REDACTED) FROM REDACTED") #vel öll ár úr töflu
        self.yearbox.addItem('') #autt gildi sem táknar öll ár í boði
        self.populateComboBox(self.yearbox, [row[0] for row in c.fetchall()])
        c.close()
        self.potbutton.toggled.connect(self.updatePotOrLine) #Þegar ýtt er á "Ker" radio takkann tengjast updatePotOrLine fallinu
        self.potroombutton.toggled.connect(self.updatePotOrLine) #"Kerskáli" radio takkinn
        self.analysismode.toggled.connect(self.analyzePot) #Þegar greiningarhamur er gerður virkur
        self.secondarybox.toggled.connect(self.switchAx) #"Teikna á annan y-ás" boxið
        self.leftgraph.toggled.connect(self.changeGraphs) #Vinstri gluggi
        self.rightgraph.toggled.connect(self.changeGraphs) #Hægri gluggi
        self.multpotplots.toggled.connect(self.analysisCheck) #Mörg gröf á ker
        self.populateComboBox(self.colorbox, ['Blár', 'Grænn', 'Rauður', 'Ljósblár', 'Fjólublár', 'Gulur', 'Svartur']) #Fylli lita-dropdownlistann
        self.updateButton.pressed.connect(self.checkUpdateMethod) #"Uppfæra" takkinn
        self.clearchart.pressed.connect(self.clearGraph) #"Hreinsa graf" takkinn
        self.prodButton.pressed.connect(self.plotProd) #Framleiðslugögn
        self.pottapbutton.pressed.connect(self.potTappingData) #Áltökugögn
        self.folderbutton.pressed.connect(self.selectFolder) #Velja möppu
        self.savebutton.pressed.connect(self.saveGraph)
        self.clearaxis.pressed.connect(self.clearAxis)
        self.curr_x = self.xboxConvert() #Valið x-gildi 


    def populateComboBox(self, box, rows): #Fall sem fyllir fellilista af sóttum gögnum
        for row in rows:
            box.addItem(row)


    def updateContainer(self, x, y): #Fall til að uppfæra töflu
        self.xlist.setSortingEnabled(False)
        self.xlist.setRowCount(0) #Núllstilli töflu
        y, x = (list(t) for t in zip(*sorted(zip(y, x)))) #Raða x og y samhliða eftir gildum á y
        self.xlist.setHorizontalHeaderLabels([self.xbox.currentText(), self.ybox.currentText()]) #Breyti headers á töflunni í nöfnin á gögnum
        for i in range (0, len(x)):
            rowPosition = self.xlist.rowCount() #núverandi staðsetning
            self.xlist.insertRow(rowPosition) #Bæti við nýrri röð
            self.xlist.setItem(rowPosition, 0, QTableWidgetItem(str(x[i]))) #Læt gildi í dálk 0 vera næsta x-gildi í röðuðum lista
            self.xlist.setItem(rowPosition, 1, QTableWidgetItem("{:7.2f}".format(round(y[i], 2)))) #Læt gildi í dálk 1 vera næsta y-gildi í röðuðum lista
        self.xlist.setSortingEnabled(True)        

    def updatePotOrLine(self): #Fall sem uppfærir drop down listann fyrir ker eða skála eftir núv. vali
        line = self.potorline.text()
        if self.potbutton.isChecked():
            self.pot_or_line = 'pot'
            self.prodButton.setEnabled(False) #framleiðslutölur eru aðeins fyrir skála
            self.pottapbutton.setEnabled(False)
            self.scatterButton.setEnabled(False) 
            self.lineButton.setChecked(True)
            self.xbox.setCurrentIndex(0) #ef einhver skyldi hafa ker valið á x-ás kæmi bara einn punktur.. 
            potval = int((int(line[0]) * 1000) + 1)
            if potval > 3001:
                potval = 3001
            self.potorline.setText(str(potval))
        else:
            self.pot_or_line = 'line'
            self.prodButton.setEnabled(True)
            self.pottapbutton.setEnabled(True)
            self.scatterButton.setEnabled(True)
            if int(line[0]) > 3:
                line = "3"
            self.potorline.setText(line[0])

    def checkUpdateMethod(self): #Fall sem gáir hvort notandi sé í greiningarham
        if "Uppfær" not in self.msglabel.text():
            self.msglabel.hide() #Viljum alltaf stroka út síðustu skilaboð þegar graf er uppfært
        if self.analysismode.isChecked(): 
            self.potAnalysis() #sérfall fyrir greiningarham
        else:
            if not self.validateInput(): #Gá hvort rétt sé slegið inn
                return
            if self.autoclean.isChecked(): #ef notandi valdi að þurrka alltaf út fyrir hverja uppfærslu
                self.clearGraph()
            self.updateGraph() 
        if self.autosavebox.isChecked(): #Ef notandi vill savea eftir hverja uppfærslu
            self.saveGraph()
    
    def analysisCheck(self): #Fall sem hreinsar grafið aðeins ef ekki í analysis mode, gert fyrir multpotplots
        if not self.analysismode.isChecked():
            self.clearGraph()

    def switchAx(self): #Fall sem víxlar milli hægri og vinstri y-ás þegar checkað er í box
        if self.secondarybox.isChecked():
            if self.leftgraph.isChecked():
                self.curr_ax = self.left_ax_a2
            elif self.onegraph.isChecked():
                self.curr_ax = self.one_ax_a2
            else:
                self.curr_ax = self.right_ax_a2
        else:
            if self.leftgraph.isChecked():
                self.curr_ax = self.left_ax
            elif self.onegraph.isChecked():
                self.curr_ax = self.one_ax
            else:
                self.curr_ax = self.right_ax

    def analyzePot(self): #Fall sem er keyrt þegar notandi checkar í greiningarhams boxið
        if self.analysismode.isChecked(): #gá hvort notandi sé að fara í eða úr greiningarham
            #Núllstilli valmynd
            if not self.validateInput():
                self.analysismode.setChecked(False)
                return
            self.yearbox.setCurrentIndex(0)
            self.secondarybox.setChecked(False)
            self.multpotplots.setChecked(False)
            self.lineButton.setChecked(True)
            self.autoclean.setChecked(False)
            self.potroombutton.setChecked(True)
            line = int(self.potorline.text()) #margfeldi fyrir upphafs index á pot
            self.curr_ax = self.left_ax #byrjum á vinstri mynd
            self.leftgraph.setChecked(True)
            self.clearGraph()
            self.colorbox.setCurrentIndex(2) #rauð lína
            self.plotProd() #Teiknum framleiðslu
            self.colorbox.setCurrentIndex(0) #blá lína
            self.xbox.setCurrentIndex(0) #REDACTED
            self.ybox.setCurrentIndex(0) #REDACTED
            self.updateGraph() #Teiknum
            self.potbutton.setChecked(True) #Teikna gögn fyrir ker
            self.pot_or_line = 'pot'
            self.potorline.setText(str(line * 1000 + 1)) #byrjum á fyrsta keri í skála
            #Lokum fyrir ákveðna takka í greiningarham
            self.enableButtons(False)                  
            #Teiknum fyrsta graf
            self.potAnalysis() 
            #Byrjum á að highlighta potbox
            self.keyboard.press(Key.right)
            self.keyboard.release(Key.right)
        else:
            #Ef notandi er að fara úr greiningarham opnum við alla virkni aftur og hreinsum út
            self.clearGraph()
            self.potroombutton.setChecked(True)
            self.scatterButton.setEnabled(True)
            self.enableButtons(True)      

    def enableButtons(self, boolval):    
        self.scatterButton.setEnabled(boolval)
        self.xbox.setEnabled(boolval)
        self.ybox.setEnabled(boolval)
        self.pottapbutton.setEnabled(boolval)
        self.potbutton.setEnabled(boolval)
        self.colorbox.setEnabled(boolval)
        self.autoclean.setEnabled(boolval)
        self.potroombutton.setEnabled(boolval)
        self.leftgraph.setEnabled(boolval)
        self.rightgraph.setEnabled(boolval)
        self.onegraph.setEnabled(boolval)
        self.secondarybox.setEnabled(boolval)
        self.multpotplots.setEnabled(boolval)
        self.clearchart.setEnabled(boolval)
        self.prodButton.setEnabled(boolval)
        self.clearaxis.setEnabled(boolval)

    def potAnalysis(self):
        self.graphed_data = '' #núllstilli filename
        self.curr_ax = self.right_ax #byrja á hægri mynd
        self.rightgraph.setChecked(True)
        self.right_ax.clearGraph()
        self.right_ax_a2.clearGraph()
        self.multpotplots.setChecked(True)
        self.colorbox.setCurrentIndex(2) #rauður
        self.ybox.setCurrentIndex(2) #REDACTED
        self.updateGraph()
        self.colorbox.setCurrentIndex(0) #blár
        self.secondarybox.setChecked(True)
        self.curr_ax = self.right_ax_a2
        self.ybox.setCurrentIndex(3) #REDACTED
        self.updateGraph()
        self.colorbox.setCurrentIndex(1) #grænn
        self.ybox.setCurrentIndex(4) #REDACTED
        self.updateGraph()
        self.multpotplots.setChecked(False)
        self.secondarybox.setChecked(False)

        self.curr_ax = self.left_ax #vel vinstri mynd
        self.leftgraph.setChecked(True)
        self.colorbox.setCurrentIndex(6) #svartur
        self.ybox.setCurrentIndex(1) #REDACTED
        self.updateGraph()
        self.graphed_data += 'REDACTED' #frá fyrra falli
    
    def potTappingData(self): #Fall sem sýnir áltökugögn fyrir öll ker í völdum skála
        if not self.validateInput(): #Gá hvort rétt sé slegið inn
                return
        self.clearGraph()
        self.curr_ax = self.one_ax #Teikna á eina mynd
        self.secondarybox.setChecked(False)
        self.onegraph.setChecked(True)
        self.scatterButton.setChecked(True)
        self.xbox.setCurrentIndex(1) #REDACTED
        self.ybox.setCurrentIndex(0) #REDACTED
        self.potroombutton.setChecked(True)
        self.updateGraph()
        self.clearGraph()
        self.checkUpdateMethod()

    def getAxisValues(self): #Fall sem sækir gögn til að teikna á x og y ás eftir völdum gildum
        #gildi til að sækja eftir úr töflu
        potroom_val = self.potorline.text()
        year_val = self.yearbox.currentText()
        y_val = self.yboxConvert()
        conn = 'REDACTED' 
        connect = cx_Oracle.connect(conn)
        c = connect.cursor()
        if self.yearbox.currentText() == '': #sækja öll gögn sem uppfylla skilyrði
            c.execute("SELECT DISTINCT({0}) FROM REDACTED where {2} = {1} order by {0}".format(self.curr_x, potroom_val, self.pot_or_line))
            x = [row[0] for row in c.fetchall()]
            c.execute("SELECT avg({0}), {1} FROM REDACTED WHERE {3} = {2} group by {1} order by {1}".format(y_val, self.curr_x, potroom_val, self.pot_or_line))
        else: #Bæta við skilyrði um ár
            c.execute("SELECT DISTINCT({0}) FROM REDACTED where {3} = {1} and REDACTED = {2} order by {0}".format(self.curr_x, potroom_val, year_val, self.pot_or_line))
            x = [row[0] for row in c.fetchall()]
            c.execute("SELECT avg({0}), {1} FROM REDACTED WHERE REDACTED = {2} AND {4} = {3} group by {1} order by {1}".format(y_val, self.curr_x, year_val, potroom_val, self.pot_or_line))
        y = [row[0] for row in c.fetchall()]
        c.close()   
        return x, y

    def getStartDate(self): #Fall sem sækir hvenær keri var startað síðast
        conn = 'REDACTED'
        connect = cx_Oracle.connect(conn)
        c = connect.cursor()
        c.execute("""SELECT CONCAT(CONCAT(to_char(REDACTED,'yyyy'),'-'),to_char(REDACTED,'mm')) 
                     FROM REDACTED WHERE REDACTED = 
                     (SELECT MAX(REDACTED) FROM REDACTED where REDACTED = {0})""".format(self.potorline.text()))
        date = [row[0] for row in c.fetchall()]
        c.close()
        return date[0]

    def colorConvert(self): #Fall sem breytir litavali í skiljanlegt gildi fyrir plot fallið
        if self.colorbox.currentText() == 'Blár':
            return 'b'
        elif self.colorbox.currentText() == 'Grænn':
            return 'g'
        elif self.colorbox.currentText() == 'Rauður':
            return 'r'
        elif self.colorbox.currentText() == 'Ljósblár':
            return 'c'
        elif self.colorbox.currentText() == 'Fjólublár':
            return 'm'
        elif self.colorbox.currentText() == 'Gulur':
            return 'y'
        elif self.colorbox.currentText() == 'Svartur':
            return 'k'
    
    def xboxConvert(self): #Fall sem breytir íslensku vali á x-ás í skiljanlegt gildi fyrir plot fallið
        if self.xbox.currentText() == "REDACTED":
            return "REDACTED" 
        elif self.xbox.currentText() == "REDACTED":
            return "REDACTED" 
        elif self.xbox.currentText() == "REDACTED":
            return "REDACTED" 
    
    def yboxConvert(self): #Fall sem breytir íslensku vali á y-ás í skiljanlegt gildi fyrir gagnagrunn
        if self.ybox.currentText() == "REDACTED":
            return "REDACTED"
        elif self.ybox.currentText() == "REDACTED":
            return "REDACTED"
        elif self.ybox.currentText() == "REDACTED":
            return "REDACTED"
        elif self.ybox.currentText() == "REDACTED":
            return "REDACTED"
        elif self.ybox.currentText() == "REDACTED":
            return "REDACTED"
        elif self.ybox.currentText() == "REDACTED":
            return "REDACTED"
        elif self.ybox.currentText() == "REDACTED":
            return "REDACTED"
        elif self.ybox.currentText() == "REDACTED":
            return "REDACTED"
        elif self.ybox.currentText() == "REDACTED":
            return "REDACTED"
        elif self.ybox.currentText() == "REDACTED":
            return "REDACTED"
        elif self.ybox.currentText() == "REDACTED":
            return "REDACTED"
        elif self.ybox.currentText() == "REDACTED":
            return "REDACTED"
        elif self.ybox.currentText() == "REDACTED":
            return "REDACTED"
        elif self.ybox.currentText() == "REDACTED":
            return "REDACTED"
    
    def clearGraph(self): #Fall sem hreinsar allar myndir
        self.left_ax_a2.set_visible(False) #Fela seinni y-ása
        self.right_ax_a2.set_visible(False)
        self.left_ax.clearGraph()
        self.left_ax_a2.clearGraph()
        self.right_ax.clearGraph()
        self.right_ax_a2.clearGraph()
        self.one_ax.clearGraph()
        self.one_ax_a2.clearGraph()
        self.xlist.setRowCount(0)
        self.xlist.setHorizontalHeaderLabels(['X', 'Y'])
        self.graphed_data = ''
        self.msglabel.hide()
        self.canvas.draw() 
    
    def clearAxis(self):
        self.curr_ax.clearGraph()
        self.canvas.draw()

    def changeGraphs(self): #Fall sem keyrist þegar notandi vill breyta staðsetningu teikningar
        self.secondarybox.setChecked(False)
        if self.leftgraph.isChecked(): #Ef vinstri gluggi er valinn
            self.curr_ax = self.left_ax
            self.left_ax.ax.set_visible(True)  
            self.right_ax.ax.set_visible(True)  #birta líka hægri glugga
            self.left_ax_a2.ax.set_visible(True)  
            self.right_ax_a2.ax.set_visible(True)
            self.one_ax.ax.set_visible(False) #fela stóra gluggann
            self.one_ax_a2.ax.set_visible(False)
        elif self.onegraph.isChecked(): #Ef einn gluggi er valinn
            self.curr_ax = self.one_ax 
            self.left_ax.ax.set_visible(False)  #fela vinstri glugga
            self.right_ax.ax.set_visible(False) #fela hægri glugga
            self.left_ax_a2.ax.set_visible(False)  
            self.right_ax_a2.ax.set_visible(False)
            self.one_ax.ax.set_visible(True)
            self.one_ax_a2.ax.set_visible(True)
        else:
            self.curr_ax = self.right_ax
            self.left_ax.ax.set_visible(True)  
            self.right_ax.ax.set_visible(True)  
            self.left_ax_a2.ax.set_visible(True)  
            self.right_ax_a2.ax.set_visible(True)
            self.one_ax.ax.set_visible(False)
            self.one_ax_a2.ax.set_visible(False)

    def selectFolder(self): #Fall til að velja staðsetningu til að vista myndir
        save_dir = QtWidgets.QFileDialog.getExistingDirectory(self, "Velja möppu", 
                                                          self.save_location, #byrja á síðasta valda vistunarstað
                                                          QtWidgets.QFileDialog.ShowDirsOnly)
        self.save_location = str(save_dir) + '/' #Endurstilli vistunarstað

    def saveGraph(self): #Fall til að vista myndir
        graph = self.canvas.grab()
        if not path.exists(self.save_location + 'gröf'): #bý til möppu ef ekki til
            mkdir(self.save_location + 'gröf')
        if self.yearbox.currentText() == '': 
            filename = (self.save_location + 'gröf/' + self.potorline.text() + '+' + self.graphed_data + '.jpg')
        else:
            filename = (self.save_location + 'gröf/' + self.potorline.text() + '+' + self.yearbox.currentText() + "_" + self.graphed_data + '.jpg')
        if self.save_location == '/': #Ef heimamappa fannst ekki
            self.msglabel.setText("Tókst ekki að vista skrá,\nvinsamlegast veldu möppu.")
            self.msglabel.setStyleSheet('QLabel#msglabel {color: blue}')
            self.msglabel.show()
        elif self.graphed_data != '': #Ef graf er ekki tómt
            if graph.save(filename):
                self.msglabel.setText(filename + "\nvistað!")
                self.msglabel.setStyleSheet('QLabel#msglabel {color: green}')
                self.msglabel.show()
        else: #Eitthvað fór úrskeiðis eða graf var tómt
            self.msglabel.setText("Tókst ekki að vista\n" + filename)
            self.msglabel.setStyleSheet('QLabel#msglabel {color: red}')
            self.msglabel.show()

    def keyPressEvent(self, event): #Fall fyrir hotkeys
        if not self.validateInput():
            return
        key = event.key()
        if (key == Qt.Key_Minus or key == Qt.Key_Left) and self.pot_or_line == 'pot': #Flakka milli kera með örvatökkum
            if int(self.potorline.text()) > 1001:
                if (int(self.potorline.text()) % 1000) - 1 == 0:
                    self.potorline.setText(str(int(self.potorline.text()) - 840)) #Hoppa milli skála
                self.potorline.setText(str(int(self.potorline.text()) - 1))
        if (key == Qt.Key_Plus or key == Qt.Key_Right) and self.pot_or_line == 'pot':
            if int(self.potorline.text()) < 3160:
                if (int(self.potorline.text()) % 1000) - 160 == 0:
                    self.potorline.setText(str(int(self.potorline.text()) + 840))
                self.potorline.setText(str(int(self.potorline.text()) + 1))
        if (key == Qt.Key_Return or key == Qt.Key_Enter) and self.updateButton.isEnabled(): #Teikna með enter
            self.checkUpdateMethod()
        if key == Qt.Key_Delete and not self.analysismode.isChecked(): #Hreinsa graf
            self.clearGraph()

    
    def createGraph(self, x, y, ax, loc, scatters): #Fall sem býr til grafið sem á að teikna
        if self.pot_or_line == 'pot': #fyrir legend
            printval = "ker"
        else:
            printval = "skála"

        if self.lineButton.isChecked(): #teikna línurit
            ax.plot(x, y, color=self.colorConvert(), label="{0} fyrir {1} {2}".format(self.ybox.currentText(), printval, self.potorline.text()))
        else: #teikna punktarit
            sc = ax.scatter(x, y, color=self.colorConvert(), label="{0} fyrir {1} {2}".format(self.ybox.currentText(), printval, self.potorline.text()))
            scatters.append(sc)

        if self.pot_or_line == 'pot' and not self.multpotplots.isChecked(): #Teikna startdags á keri
            self.curr_ax.ax.axvline(x=self.getStartDate(), label="Startdags. á keri {0}".format(self.potorline.text()))
            self.curr_ax.plot_counter += 1
        if self.pot_or_line != "pot" and not self.multpotplots.isChecked(): #Vil bara breyta lit ef ekki er verið að teikna stök kergögn
            self.colorbox.setCurrentIndex((self.colorbox.currentIndex() + 1) % 7)        
        self.createLegend(self.curr_ax.ax) #uppfæri legend
        if self.yearbox.currentText() == "": #uppfæri titil í samræmi við ársval
            self.curr_ax.ax.title.set_text('Frá og með jan 2014')
        else:
            self.curr_ax.ax.title.set_text('Árið ' + self.yearbox.currentText())
        ax.set_xlim([min(x), max(x)]) #Skala ása
        if self.xboxConvert() == 'REDACTED': #Merki á 4 kera fresti
            ax.xaxis.set_major_locator(ticker.MultipleLocator(4))
        elif self.xboxConvert() == 'REDACTED': #Merki á 3 mánaða fresti
            if self.yearbox.currentText() == '': #Ef verið er að sýna öll ár
                ax.xaxis.set_major_locator(ticker.MultipleLocator(3))
            else:
                ax.xaxis.set_major_locator(ticker.MultipleLocator(1))

    def createLegend(self, ax): #Fall sem setur legend út fyrir graf
        if self.leftgraph.isChecked():
            self.fig.subplots_adjust(left=0.15) #gera pláss fyrir legend
            if self.secondarybox.isChecked():
                ax.legend(loc='upper left', prop={'size':8}, bbox_to_anchor=(-0.47,0.3)) #nákvæm vísindi
            else:
                ax.legend(loc='upper left', prop={'size':8}, bbox_to_anchor=(-0.47,1))
        elif self.onegraph.isChecked():
            self.fig.subplots_adjust(left=0.05)
            self.fig.subplots_adjust(right=0.85)
            if self.secondarybox.isChecked():
                ax.legend(loc='upper left', prop={'size':8}, bbox_to_anchor=(1.05,0.3))                
            else:
                ax.legend(loc='upper left', prop={'size':8}, bbox_to_anchor=(1.05,1))     
        else:
            self.fig.subplots_adjust(right=0.85)
            if self.secondarybox.isChecked():
                ax.legend(loc='upper left', prop={'size':8}, bbox_to_anchor=(1.1,0.3))                
            else:
                ax.legend(loc='upper left', prop={'size':8}, bbox_to_anchor=(1.1,1))       

    def validateInput(self): #Gá hvort rétt sé slegið inn
        potroom_val = self.potorline.text()
        try:
            potroom_val = int(potroom_val)            
        except Exception:
            QMessageBox.about(self, 'Villa','Aðeins tölustafir leyfðir!')
            return False
        try:
            if self.pot_or_line == 'pot':
                if potroom_val < 1001 or (potroom_val > 1160 and potroom_val < 2001) or (potroom_val > 2160 and potroom_val < 3001) or potroom_val > 3160:
                   raise Exception
            else:
                if round(potroom_val) < 1 or round(potroom_val) > 3:
                    raise Exception
        except Exception:
            if self.pot_or_line == 'pot':
                QMessageBox.about(self, 'Villa', 'Kernúmer ekki til!')
            else:
                QMessageBox.about(self, 'Villa', 'Skáli ekki til!')
            return False
        return True

    def updateGraph(self): #Fall sem sér um að tengja uppfærslur saman og smíða grafið
        if self.ybox.currentText() not in self.graphed_data: #Svo ekki sé nefnt gildi tvisvar í filename
            if self.graphed_data != '':
                self.graphed_data += '+'
            self.graphed_data += self.ybox.currentText()
        if self.xboxConvert() != self.curr_x: #Gæti ruglað í hlutum að teikna 2 gröf með 2 mismunandi x gildum
            self.clearGraph()
            self.curr_x = self.xboxConvert() #uppfæri global breytu
        x, y = self.getAxisValues() #gögn til að teikna eftir
        self.updateContainer(x,y) #Uppfæri töflu
        if self.secondarybox.isChecked(): #Hvorn ásinn á að teikna á
            self.removedups(self.curr_ax) #Teikna eitt ker í einu
            self.curr_ax.set_visible(True) #Birta falinn ás
            self.createGraph(x, y, self.curr_ax.ax, "upper left", self.curr_ax.scatters) #bý grafið til á valda mynd 
        else:
            self.changeGraphs() #Vel rétta mynd
            self.removedups(self.curr_ax)
            self.createGraph(x, y, self.curr_ax.ax, "upper right", self.curr_ax.scatters)
        if self.lineButton.isChecked(): #Uppfæri línuteljara       
                self.curr_ax.plot_counter += 1
        self.canvas.draw() #Teikna myndina


        
    def removedups(self, ax):
        if self.pot_or_line == 'pot': #Viljum bara kanna hvort kerteikning sé til staðar
            if not self.multpotplots.isChecked(): #Nema annað sé tekið fram
                if ax.pot_index >= 0: #Er búið að teikna ker
                    ax.ax.lines[ax.pot_index].remove() #fjarlægja kerteikninguna á þeim stað
                    ax.ax.lines[ax.pot_index].remove() #og start date
                    ax.plot_counter -= 2
            ax.pot_index = self.curr_ax.plot_counter
        else:
            ax.pot_index = -1

    def plotProd(self): #Teikna framleiðslutölur, aðeins öðruvísi en allt hitt og þarf því sér fall
        if not self.validateInput(): #Gá hvort rétt sé slegið inn
                return
        if self.xboxConvert() != 'REDACTED': #Teiknum bara eftir REDACTED
            self.clearGraph()
            self.curr_x = 'REDACTED'
        if "REDACTED" not in self.graphed_data: 
            if self.graphed_data != '':
                self.graphed_data += '+'
            self.graphed_data += "REDACTED"
        conn = 'REDACTED'
        connect = cx_Oracle.connect(conn)
        c = connect.cursor()
        c.execute("SELECT MIN(REDACTED) FROM REDACTED")
        minYear = [row[0] for row in c.fetchall()][0] #Viljum bara gögn í samræmi við REDACTED töfluna
        if self.yearbox.currentText() == '':
            c.execute("SELECT REDACTED FROM REDACTED where REDACTED = to_number({0}) AND REDACTED >= {1} AND REDACTED > 0".format(self.potorline.text(), minYear)) 
            y = [row[0] for row in c.fetchall()] #Sæki framleiðslutölur
            c.execute("""SELECT DISTINCT(REDACTED) FROM REDACTED where LINE = 1 GROUP BY REDACTED 
                         HAVING REDACTED <= (select MAX(CONCAT(CONCAT(REDACTED, '-'), SUBSTR(CONCAT('0',REDACTED),-2))) FROM REDACTED)""".format(self.potorline.text()))
            x = [row[0] for row in c.fetchall()] #Sæki REDACTED í samræmi við REDACTED töfluna ef önnur tafla skyldi hafa nýrri gögn en hin
        else:
            c.execute("""SELECT DISTINCT(CONCAT(CONCAT(to_char(REDACTED), '-'), to_char(REDACTED))) 
                         FROM REDACTED where REDACTED = to_number({0}) AND REDACTED = {1} AND REDACTED > 0""".format(self.potorline.text(), self.yearbox.currentText()))
            x = [row[0] for row in c.fetchall()]
            c.execute("SELECT REDACTED FROM REDACTED where REDACTED = to_number({0}) AND REDACTED = {1} AND REDACTED > 0".format(self.potorline.text(), self.yearbox.currentText()))
            y = [row[0] for row in c.fetchall()]
        c.close()

        self.updateContainer(x,y) #Uppfæri töflu
        self.xlist.setHorizontalHeaderLabels([self.xbox.currentText(), "Dagsframleiðsla"]) #Breyti headers á töflunni
        if self.lineButton.isChecked(): #Teikna línurit
            self.curr_ax.ax.plot(x, y, color=self.colorConvert(), label="Dagsframleiðsla skála {0}".format(self.potorline.text()))
        else: #Teikna punktarit
            sc = self.curr_ax.ax.scatter(x, y, color=self.colorConvert(), label="Dagsframleiðsla skála {0}".format(self.potorline.text()))
            self.curr_ax.scatters.append(sc)

        if self.pot_or_line != "pot" and not self.multpotplots.isChecked(): #vel næsta lit í röðinni
            self.colorbox.setCurrentIndex((self.colorbox.currentIndex() + 1) % 7)
        self.createLegend(self.curr_ax.ax) #uppfæri legend
        if self.yearbox.currentText() == "": #Titill í samræmi við val á ári
            self.curr_ax.ax.title.set_text('Frá og með jan 2014')
        else:
            self.curr_ax.ax.title.set_text('Árið ' + self.yearbox.currentText())
        self.curr_ax.ax.set_xlim([min(x), max(x)]) #Skala ása
        self.curr_ax.ax.xaxis.set_major_locator(ticker.MultipleLocator(3)) #X-ás hleypur á 3 mánuðum
        self.canvas.draw() #Teikna graf
        if self.lineButton.isChecked():        
            self.curr_ax.plot_counter += 1
        if self.autosavebox.isChecked(): #Vista mynd
            self.saveGraph()
    
    def prepareUpdate(self):
        self.msglabel.setText("Uppfæri gögn")
        self.msglabel.show()
        worker = Worker(self.updateData)
        self.threadpool.start(worker)


    def updateData(self, progress_callback): #Fall til að uppfæra töflu í gagnagrunni með keyboard shortcut
        conn = 'REDACTED'
        connect = cx_Oracle.connect(conn)
        c = connect.cursor()
        try:
            c.execute("CREATE TABLE REDACTED_UPDATING AS SELECT DISTINCT(MAX(REDACTED)) AS TMP FROM REDACTED") #Proberen, svo enginn reyni að uppfæra samtímis
            c.execute("""CREATE TABLE REDACTED_TEMP AS SELECT 
            R.REDACTED AS REDACTED,
            MIN(R.REDACTED) AS REDACTED,
            MAX(R.REDACTED) AS REDACTED,
            SUBSTR(R.REDACTED,1,1) AS REDACTED,
            to_char(R.REDACTED, 'yyyy') AS REDACTED,
            to_char(R.REDACTED, 'mm') AS REDACTED,
            CONCAT(CONCAT(to_char(R.REDACTED, 'yyyy'), '-'), to_char(R.REDACTED, 'mm')) AS REDACTED,
            ROUND(SUM(R.REDACTED)/(COUNT(*)), 1) AS REDACTED,
            ROUND(AVG(R.REDACTED), 4) AS REDACTED,
            ROUND(AVG(R.REDACTED), 2) AS REDACTED,
            ROUND(AVG(R.REDACTED), 2) AS REDACTED,
            ROUND(SUM(SUM(R.REDACTED))
            OVER (PARTITION BY R.REDACTED ORDER BY MAX(R.REDACTED) ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) / SUM((COUNT(*) * 2)) 
            OVER (PARTITION BY R.REDACTED ORDER BY MAX(R.REDACTED) ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 1)*2 AS REDACTED,
            R.REDACTED AS REDACTED,
            R.REDACTED AS REDACTED,
            SUM(R.REDACTED) AS REDACTED,
            SUM(R.REDACTED) AS REDACTED,
            ROUND(AVG(R.REDACTED), 1) AS REDACTED,
            ROUND(AVG(R.REDACTED), 2) AS REDACTED,
            ROUND(AVG(R.REDACTED), 2) AS REDACTED,
            ROUND(AVG(R.REDACTED), 2) AS REDACTED,
            SUM(R.REDACTED) AS REDACTED,
            SUM(R.REDACTED) AS REDACTED,
            SUM(R.REDACTED) AS REDACTED,
            SUM(R.REDACTED) AS REDACTED,
            SUM(R.REDACTED) AS REDACTED,
            SUM(R.REDACTED) AS REDACTED,
            SUM(R.REDACTED) AS REDACTED,
            SUM(R.REDACTED) AS REDACTED,
            SUM(R.REDACTED) AS REDACTED,
            ROUND(SUM(R.REDACTED)/COUNT(R.REDACTED), 2) AS REDACTED,
            ROUND(SUM(R.REDACTED)/COUNT(R.REDACTED), 1) AS REDACTED,
            ROUND(AVG(R.REDACTED), 2) AS REDACTED,
            ROUND(AVG(R.REDACTED), 1) AS REDACTED,
            ROUND(AVG(R.REDACTED), 1) AS REDACTED,
            ROUND(SUM(R.REDACTED)/COUNT(R.REDACTED), 1) AS REDACTED,
            ROUND(SUM(R.REDACTED)/COUNT(R.REDACTED), 1) AS REDACTED,
            ROUND(AVG(R.REDACTED), 1) AS REDACTED,
            ROUND(AVG(R.REDACTED), 1) AS REDACTED,
            ROUND(AVG(R.REDACTED), 1) AS REDACTED,
            ROUND(AVG(R.REDACTED), 1) AS REDACTED,
            ROUND(AVG(R.REDACTED), 1) AS REDACTED,
            ROUND(AVG(R.REDACTED), 1) AS REDACTED,
            ROUND(AVG(R.REDACTED), 1) AS REDACTED,
            ROUND(AVG(R.REDACTED), 1) AS REDACTED,
            SUM(R.REDACTED) AS REDACTED,
            SUM(R.REDACTED) AS REDACTED,
            ROUND(AVG(R.REDACTED), 2) AS REDACTED,
            ROUND(AVG(R.REDACTED), 1) AS REDACTED,
            SUM(R.REDACTED) AS REDACTED,
            SUM(R.REDACTED) AS REDACTED,
            ROUND(AVG(R.REDACTED), 2) AS REDACTED,
            ROUND(AVG(R.REDACTED), 2) AS REDACTED,
            ROUND(AVG(R.REDACTED), 5) AS REDACTED,
            ROUND(AVG(R.REDACTED), 5) AS REDACTED,
            ROUND(AVG(R.REDACTED), 5) AS REDACTED,
            ROUND(AVG(R.REDACTED), 3) AS REDACTED,
            ROUND(AVG(R.REDACTED), 1) AS REDACTED,
            SUM(R.REDACTED) AS REDACTED,
            SUM(R.REDACTED) AS REDACTED,
            SUM(R.REDACTED) AS REDACTED,
            SUM(R.REDACTED) AS REDACTED,
            SUM(R.REDACTED) AS REDACTED,
            SUM(R.REDACTED) AS REDACTED,
            SUM(R.REDACTED) AS REDACTED,
            SUM(R.REDACTED) AS REDACTED,
            SUM(R.REDACTED) AS REDACTED,
            SUM(R.REDACTED) AS REDACTED,
            SUM(R.REDACTED) AS REDACTED,
            SUM(R.REDACTED) AS REDACTED,
            SUM(R.REDACTED) AS REDACTED,
            SUM(R.REDACTED) AS REDACTED,
            SUM(R.REDACTED) AS REDACTED,
            SUM(R.REDACTED) AS REDACTED,
            SUM(R.REDACTED) AS REDACTED,
            SUM(R.REDACTED) AS REDACTED,
            SUM(R.REDACTED) AS REDACTED,
            SUM(R.REDACTED) AS REDACTED,
            SUM(R.REDACTED) AS REDACTED,
            SUM(R.REDACTED) AS REDACTED,
            MAX(R.REDACTED) AS REDACTED,
            SUM(R.REDACTED) AS REDACTED,
            SUM(R.REDACTED) AS REDACTED,
            SUM(R.REDACTED) AS REDACTED,
            ROUND(SUM(R.REDACTED)/COUNT(R.REDACTED), 6) AS REDACTED,
            FROM 
                REDACTED R
            WHERE
                R.REDACTED >= 1001 AND     
                R.REDACTED <= 3160 AND      
                R.REDACTED >= '1/1/2014' AND
                R.REDACTED = 'R' 
            HAVING
                COUNT(*) >= 11
            GROUP BY
                R.REDACTED,
                to_char(R.REDACTED, 'yyyy'),
                to_char(R.REDACTED, 'mm'),
                to_char(R.REDACTED, 'MON'),
                R.REDACTED,
                R.REDACTED
            ORDER BY
                R.REDACTED,
                to_char(R.REDACTED, 'yyyy'),
                to_char(R.REDACTED, 'mm')""")
            c.execute("""DROP TABLE REDACTED""") #Eyði gömlu töflunni
            c.execute("""RENAME REDACTED_TEMP TO REDACTED""") #Breyti temp í nýju töfluna
            c.execute("""GRANT INDEX, UPDATE, SELECT, REFERENCES, ON COMMIT REFRESH, QUERY REWRITE, DEBUG, FLASHBACK on "REDACTED"."REDACTED" to "REDACTED" """) #Granta réttindi
            c.execute("DROP TABLE REDACTED_UPDATING") #Verhogen, uppfærslu lokið
            self.msglabel.show()
            self.msglabel.setText("Uppfærsla á gögnum tókst!")
        except:
            if self.msglabel.text() != "Uppfæri gögn": #Ef annar notandi reynir að uppfæra samtímis
                self.msglabel.show()
                self.msglabel.setText("Uppfærsla á gögnum mistókst!") #Eitthvað fór úrskeiðis, líklega annar að uppfæra á sama tíma
        c.close()
        return "Done." #loka þræði

    def undo(self): #Fjarlægja síðustu línu
        if not self.analysismode.isChecked(): #Viljum ekki geta undoað í analysis mode
            if self.curr_ax.plot_counter - 1 >= 0: #Ef lína er til staðar
                self.curr_ax.ax.lines[self.curr_ax.plot_counter-1].remove() #Fjarlægja síðasta graf
                self.curr_ax.plot_counter -= 1 
                if self.pot_or_line == "pot" and not self.multpotplots.isChecked() and self.curr_ax.plot_counter - 1 >= 0: #Ef ker
                    self.curr_ax.ax.lines[self.curr_ax.plot_counter-1].remove() #fjarlægja start date líka
                    self.curr_ax.pot_index = -1 #núllstilla ker index
                    self.curr_ax.plot_counter -= 1
            else:
                if len(self.curr_ax.scatters) > 0: #Ef scatter er til staðar
                    self.curr_ax.scatters[len(self.curr_ax.scatters) - 1].remove()
                    self.curr_ax.scatters.pop() #fjarlægja úr lista
            if self.curr_ax == self.right_ax_a2 or self.curr_ax == self.left_ax_a2 or self.curr_ax == self.one_ax_a2: #fjarlægja legend
                self.createLegend(self.curr_ax.ax)        
            else:
                self.createLegend(self.curr_ax.ax)       
            self.canvas.draw() #endurteikna mynd
        
    
if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication #Importa bara nauðsynjum til að birta glugga
    from PyQt5 import QtGui, QtWidgets 
    import traceback, sys
    import cx_Oracle
    from os import path, mkdir, getcwd
    from pynput.keyboard import Controller
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
    app = QApplication(sys.argv)
    app.setStyle('Breeze') #Stíll á tökkum o.fl.
    palette = QtGui.QPalette()
    palette.setColor(QtGui.QPalette.Window, QtGui.QColor(178, 198, 217)) #ljósblár bakgrunnur
    app.setPalette(palette)
    main = Main() #upphafsstilli glugga
    main.showMaximized() #Opna glugga
    from PyQt5 import Qt #Importa restinni
    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QMessageBox
    import matplotlib.ticker as ticker
    from pynput.keyboard import Key
    sys.exit(app.exec_())
