import os
import datetime
import time
import traceback

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from PyQt4.QtGui import QMainWindow, QApplication, QWidget, QTableWidgetItem, QMessageBox, QFont, QProgressDialog
from PyQt4.QtCore import QDate, QRunnable, QThreadPool, Qt
from interface import Ui_MainWindow

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

done = False
class Runnable(QRunnable):

    def __init__(self, progresso):
        super(Runnable, self).__init__()
        self.progresso = progresso

    def run(self):
        cont = 0
        self.progresso.setValue(cont)
        while not done:
            if cont == 100:
                cont = 0
            self.progresso.setValue(cont)
            time.sleep(0.05)
            cont += 1
        self.progresso.hide()
            

options = Options()
options.headless = True
directory = os.path.abspath(os.path.dirname(__file__))

class AppComparaDiarias(QMainWindow):

    def __init__(self, parent=None):
        super(AppComparaDiarias, self).__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.conectarSinais()
        
    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Messagem', "Deseja realmente sair?", "Sim", "Nao")
        if reply == 0:
            event.accept()
        else:
            event.ignore()

    def conectarSinais(self):
        self.ui.dateEditEntrada.setDate(QDate.currentDate())
        self.ui.dateEditSaida.setDate(QDate.currentDate().addDays(1))
        self.ui.dateEditEntrada.dateChanged.connect(self.atualizarSaida)
        self.ui.pushButtonPesquisar.clicked.connect(self.pesquisarPeriodo)
        self.progresso = QProgressDialog('Pesquisando na Booking...', 'Cancelar', 0, 100, self)
        self.progresso.setWindowTitle('Aguarde')
        self.progresso.setWindowModality(Qt.WindowModal)

    def atualizarSaida(self):
        self.ui.dateEditSaida.setDate(self.ui.dateEditEntrada.date().addDays(1))

    def carregarHoteis(self):
        WebDriverWait(self.driver, 30).until(EC.visibility_of_all_elements_located((By.CLASS_NAME, 'sr_item')))
        print 'Resultados encontrados: ' + str(len(self.driver.find_elements_by_class_name('sr_item')))
        for hotel in self.driver.find_elements_by_class_name('sr_item'):
            hotel_id = int(hotel.get_attribute('data-hotelid'))
            if encontrar(hotel_id) is not None:
                try:
                    valor_str = hotel.find_element_by_class_name('price')
                    hotel_valor = int(''.join(c for c in valor_str.text if c.isdigit()))
                except:
                    hotel_valor = 0
                self.hoteis.append([hotel_id, '', hotel_valor])

    def preencherRanking(self):
        self.carregarHoteis()
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
        
        self.ui.tableWidgetComparativo.setColumnCount(2)
        self.ui.tableWidgetComparativo.setRowCount(len(self.hoteis))
        self.ui.tableWidgetComparativo.setHorizontalHeaderLabels(['Hotel/Pousada','Valor Periodo'])
        aux = 0
        for h in self.hoteis:
            table_nome = QTableWidgetItem(h[1])
            if h[2] > 0:
                table_valor = QTableWidgetItem('R$ %s,00' % (str(h[2])))
            else:
                table_valor = QTableWidgetItem('Esgotado')
            if (h[0] == POUSADA_DO_SOL):
                table_nome.setFont(QFont('Open Sans', weight=QFont.Bold))
                table_valor.setFont(QFont('Open Sans', weight=QFont.Bold))
            self.ui.tableWidgetComparativo.setItem(aux, 0, table_nome)
            self.ui.tableWidgetComparativo.setItem(aux, 1, table_valor)
            aux += 1
        self.ui.tableWidgetComparativo.resizeRowsToContents()
        self.ui.tableWidgetComparativo.resizeColumnsToContents()

    def pesquisarPeriodo(self):
        try:
            global done
            done = False
            self.hoteis = []
            self.progresso.show()
            runnable = Runnable(self.progresso)
            QThreadPool.globalInstance().start(runnable)
            self.driver = webdriver.Chrome(directory + '\chromedriver.exe', chrome_options=options)
            data_in = self.ui.dateEditEntrada.date().toPyDate()
            data_out = self.ui.dateEditSaida.date().toPyDate()
            adultos = 2
            url = 'https://www.booking.com/'
            self.driver.get(url)

            self.driver.execute_script('document.getElementsByName("checkin_month")[0].style="text"')
            self.driver.execute_script('document.getElementsByName("checkin_year")[0].style="text"')
            self.driver.execute_script('document.getElementsByName("checkout_month")[0].style="text"')
            self.driver.execute_script('document.getElementsByName("checkout_year")[0].style="text"')

            self.driver.find_element_by_name('ss').send_keys('Aracaju')
            try:
                self.driver.find_element_by_xpath('//input[@name="checkin_monthday"]').send_keys(data_in.strftime('%d'))
            except:
                Select(self.driver.find_element_by_name('checkin_monthday')).select_by_value(data_in.strftime('%d'))        
            self.driver.find_element_by_xpath('//input[@name="checkin_month"]').send_keys(data_in.strftime('%m'))
            self.driver.find_element_by_xpath('//input[@name="checkin_year"]').send_keys(data_in.strftime('%Y'))
            try:
                self.driver.find_element_by_xpath('//input[@name="checkout_monthday"]').send_keys(data_out.strftime('%d'))
            except:
                Select(self.driver.find_element_by_name('checkout_monthday')).select_by_value(data_out.strftime('%d'))
            self.driver.find_element_by_xpath('//input[@name="checkout_month"]').send_keys(data_out.strftime('%m'))
            self.driver.find_element_by_xpath('//input[@name="checkout_year"]').send_keys(data_out.strftime('%Y'))
            self.driver.find_element_by_class_name('sb-searchbox__button').click()

            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, '//a[@data-id="ht_id-204"]')))
            self.driver.find_element_by_xpath('//a[@data-id="ht_id-204"]').click()
            self.preencherRanking()
            self.driver.quit()
            done = True
        except Exception as e:
            self.driver.quit()
            done = True
            with open('log.txt', 'a') as f:
                QMessageBox.critical(self, "Messagem", "Ocorreu um erro, tente novamente.")
                print str(e)
                print traceback.format_exc()
                f.write(str(e))
                f.write(traceback.format_exc())

def main():
    app = QApplication([])
    acd = AppComparaDiarias()
    acd.show()
    return app.exec_()
    
if __name__ == "__main__":
    main()

