import datetime
import traceback
import urllib2
import csv
import time

from bs4 import BeautifulSoup
from PyQt4.QtGui import QMainWindow, QApplication, QWidget, QTableWidgetItem, QMessageBox, QFont, QFileDialog, QProgressDialog
from PyQt4.QtCore import QDate, QThread, Qt, QTimer, SIGNAL
from interface import Ui_MainWindow

BOOKING_URL = 'https://www.booking.com'

POUSADA_DO_SOL = 257826

LISTA_HOTEIS = [[257826, 'Hotel Pousada do Sol'],
                [266256, 'Radisson Hotel Aracaju'],
                [263599, 'Aruana Eco Praia Hotel'],
                [259359, 'Celi Hotel Aracaju'],
                [418112, 'Del Mar Hotel'],
                [259411, 'Aquarios Praia Hotel'],
                [257667, 'Real Classic Hotel'],
                [266254, 'Quality Hotel Aracaju'],
                [257673, 'Hotel da Costa'],
                [258698, 'Del Canto Hotel'],
                [258541, 'Apart Hotel Residence'],
                [2108017,'Comfort Hotel Aracaju'],
                [257777, 'Real Praia Hotel'],
                [259132, 'Sandrin Praia Hotel']]

def encontrar(hotel_id):
    for i in range (len(LISTA_HOTEIS)):
        if hotel_id == LISTA_HOTEIS[i][0]:
            return LISTA_HOTEIS[i]
    return None

class Worker(QThread):
    def __init__(self, url):
        QThread.__init__(self)
        self.url = url
        self.user_agent = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0)'}

    def __del__(self):
        self.wait()

    def stop(self):
        self.terminate()

    def run(self):
        while True:
            request = urllib2.Request(self.url, headers = self.user_agent)
            html = urllib2.urlopen(request).read()
            conteudo = BeautifulSoup(html, "lxml")
            hoteis_encontrados = conteudo.find_all("div", {"class" : "sr_item"})
            for hotel in hoteis_encontrados:
                hotel_id = int(hotel['data-hotelid'])
                if encontrar(hotel_id) is not None:
                    if hotel.find("strong", {"class" : "price"}):
                        hotel_valor_text = hotel.find("strong", {"class" : "price"}).text
                        hotel_valor = int(''.join(c for c in hotel_valor_text if c.isdigit()))
                    else:
                        hotel_valor = 0
                    self.emit(SIGNAL('addHotel(int,int)'), hotel_id, hotel_valor)
            paginacao = conteudo.find("div", {"class" : "results-paging"})
            if paginacao:
                proximo = paginacao.find("a", {"class" : "paging-next"})
                if proximo:
                    self.url = BOOKING_URL + proximo['href']
                else:
                    break
            else:
                break

class AppComparaDiarias(QMainWindow):

    def __init__(self, parent=None):
        super(AppComparaDiarias, self).__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.conectarSinais()
        
    def conectarSinais(self):
        self.ui.dateEditEntrada.setDate(QDate.currentDate())
        self.ui.dateEditSaida.setDate(QDate.currentDate().addDays(1))
        self.ui.dateEditEntrada.dateChanged.connect(self.atualizarSaida)
        self.ui.pushButtonPesquisar.clicked.connect(self.pesquisarPeriodo)
        self.ui.pushButtonSalvar.clicked.connect(self.salvarPeriodo)
        self.progresso = QProgressDialog('Pesquisando na Booking...', 'Cancelar', 0, 100, self)
        self.progresso.setWindowTitle('Aguarde')
        self.progresso.setWindowModality(Qt.WindowModal)
        self.progresso.canceled.connect(self.cancelar)
        self.contador = QTimer()
        self.contador.timeout.connect(self.carregando)

    def cancelar(self):
        self.hoteis = []
        self.worker.stop()

    def carregando(self):
        cont = 0
        self.progresso.show()
        while self.contador.isActive():
            if cont == 100:
                cont = 0
            self.progresso.setValue(cont)
            time.sleep(0.1)
            cont += 1

    def atualizarSaida(self):
        self.ui.dateEditSaida.setDate(self.ui.dateEditEntrada.date().addDays(1))

    def preencherRanking(self):
        if len(self.hoteis) > 0:
            self.hoteis.sort(key=lambda x: x[2], reverse=True)
            for h1 in LISTA_HOTEIS:
                achou = False
                for h2 in self.hoteis:
                    if h2[0] == h1[0]:
                        achou = True
                        h2[1] = h1[1]
                        break
                if not achou:
                    self.hoteis.append([h1[0], h1[1], 0])
            self.hoteis = filter(lambda x: x[1] != '', self.hoteis)
            self.ui.tableWidgetComparativo.setColumnCount(2)
            self.ui.tableWidgetComparativo.setRowCount(len(self.hoteis))
            self.ui.tableWidgetComparativo.setHorizontalHeaderLabels(['Hotel', 'Valor Periodo'])
            aux = 0
            for h in self.hoteis:
                table_nome = QTableWidgetItem(h[1])
                if h[2] > 0:
                    table_valor = QTableWidgetItem('R$ %s,00' % (str(h[2])))
                else:
                    table_valor = QTableWidgetItem('Esgotado')
                if (h[0] == POUSADA_DO_SOL):
                    table_nome.setFont(QFont('Segoe UI', weight=QFont.Bold))
                    table_valor.setFont(QFont('Segoe UI', weight=QFont.Bold))
                self.ui.tableWidgetComparativo.setItem(aux, 0, table_nome)
                self.ui.tableWidgetComparativo.setItem(aux, 1, table_valor)
                aux += 1
            self.ui.tableWidgetComparativo.resizeColumnsToContents()
        self.contador.stop()
        self.progresso.hide()

    def addHotel(self, hotel_id, hotel_valor):
        self.hoteis.append([hotel_id, '', hotel_valor])

    def pesquisarPeriodo(self):
        try:
            self.hoteis = []
            data_in = self.ui.dateEditEntrada.date().toPyDate()
            data_out = self.ui.dateEditSaida.date().toPyDate()
            url = '{booking}/searchresults.pt-br.html?'\
                        'checkin_month={mes_in}&'\
                        'checkin_monthday={dia_in}&'\
                        'checkin_year={ano_in}&'\
                        'checkout_month={mes_out}&'\
                        'checkout_monthday={dia_out}&'\
                        'checkout_year={ano_out}&'\
                        'no_rooms=1&'\
                        'group_adults={adultos}&'\
                        'ss=Aracaju&'\
                        'nflt=ht_id%3D204%3B'.format(
                            booking=BOOKING_URL,
                            mes_in=data_in.strftime('%m'),
                            dia_in=data_in.strftime('%d'),
                            ano_in=data_in.strftime('%Y'),
                            mes_out=data_out.strftime('%m'),
                            dia_out=data_out.strftime('%d'),
                            ano_out=data_out.strftime('%Y'),
                            adultos=2)
            self.worker = Worker(url)
            self.connect(self.worker, SIGNAL("addHotel(int,int)"), self.addHotel)
            self.connect(self.worker, SIGNAL("finished()"), self.preencherRanking)
            self.contador.start()
            self.worker.start()
        except Exception as e:
            QMessageBox.critical(self, "Messagem", "Ocorreu um erro, tente novamente.")
            print str(e)
            print traceback.format_exc()
            with open('log.txt', 'a') as f:
                f.write(str(e))
                f.write(traceback.format_exc())

    def salvarPeriodo(self):
        try:
            caminho = QFileDialog.getSaveFileName(self, 'Salvar...', 'comparativo', 'CSV(*.csv)')
            if not caminho.isEmpty():
                with open(unicode(caminho), 'wb') as arquivo:
                    data_in = self.ui.dateEditEntrada.date().toPyDate()
                    data_out = self.ui.dateEditSaida.date().toPyDate()
                    periodo = 'De ' + data_in.strftime('%d/%m/%y') + ' a ' + data_out.strftime('%d/%m/%y')
                    writer = csv.writer(arquivo, delimiter=';')
                    writer.writerow(['Hotel', periodo])
                    for linha in range(self.ui.tableWidgetComparativo.rowCount()):
                        hotel = self.ui.tableWidgetComparativo.item(linha, 0)
                        valor = self.ui.tableWidgetComparativo.item(linha, 1)
                        writer.writerow([hotel.text(),valor.text()])
        except Exception as e:
            QMessageBox.critical(self, "Messagem", "Ocorreu um erro ao salvar arquivo.")
            print str(e)
            print traceback.format_exc()
            with open('log.txt', 'a') as f:
                f.write(str(e))
                f.write(traceback.format_exc())

def main():
    app = QApplication([])
    acd = AppComparaDiarias()
    acd.show()
    return app.exec_()
    
if __name__ == "__main__":
    main()

