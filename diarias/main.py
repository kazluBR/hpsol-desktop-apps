import http.client
import json
import traceback
import csv
import time
import unicodedata

from PyQt5.QtWidgets import (
    QMainWindow,
    QApplication,
    QTableWidgetItem,
    QMessageBox,
    QFileDialog,
    QProgressDialog,
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import QDate, QThread, Qt, QTimer, pyqtSignal
from interface import Ui_MainWindow

POUSADA_DO_SOL = 257826


class Worker(QThread):
    addHotel = pyqtSignal(int, "QString", float)

    def __init__(self, url):
        QThread.__init__(self)
        self.url = url
        self.headers = {
            "x-rapidapi-host": "apidojo-booking-v1.p.rapidapi.com",
            "x-rapidapi-key": "d01f210c0amsh1a9ef21e5c06669p148c8ejsn34644c8acd17",
        }

    def stop(self):
        self.terminate()

    def run(self):
        conn = http.client.HTTPSConnection("apidojo-booking-v1.p.rapidapi.com")
        conn.request("GET", self.url, headers=self.headers)

        res = conn.getresponse()
        data = res.read()

        json_data = json.loads(data.decode("utf-8"))

        for hoteis in json_data["result"]:
            hotel_id = int(hoteis["hotel_id"])
            hotel_nome = hoteis["hotel_name"]
            try:
                hotel_valor = float(hoteis["price_breakdown"]["gross_price"])
            except KeyError:
                hotel_valor = 0.00
                pass
            self.addHotel.emit(
                hotel_id,
                hotel_nome,
                hotel_valor,
            )


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
        self.progresso = QProgressDialog(
            "Pesquisando na Booking...", "Cancelar", 0, 100, self
        )
        self.progresso.setWindowTitle("Aguarde")
        self.progresso.setWindowModality(Qt.WindowModal)
        self.progresso.canceled.connect(self.cancelar)
        self.progresso.cancel()
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
            self.ui.tableWidgetComparativo.setColumnCount(2)
            self.ui.tableWidgetComparativo.setRowCount(len(self.hoteis))
            self.ui.tableWidgetComparativo.setHorizontalHeaderLabels(
                ["Hotel", "Valor Periodo"]
            )
            aux = 0
            for h in self.hoteis:
                table_nome = QTableWidgetItem(h[1])
                if h[2] > 0:
                    table_valor = QTableWidgetItem("R$ {0:.2f}".format(h[2]))
                else:
                    table_valor = QTableWidgetItem("Esgotado")
                if h[0] == POUSADA_DO_SOL:
                    table_nome.setFont(QFont("Segoe UI", weight=QFont.Bold))
                    table_valor.setFont(QFont("Segoe UI", weight=QFont.Bold))
                self.ui.tableWidgetComparativo.setItem(aux, 0, table_nome)
                self.ui.tableWidgetComparativo.setItem(aux, 1, table_valor)
                aux += 1
            self.ui.tableWidgetComparativo.resizeColumnsToContents()
        self.contador.stop()
        self.progresso.hide()

    def addHotel(self, hotel_id, hotel_nome, hotel_valor):
        self.hoteis.append([hotel_id, hotel_nome, hotel_valor])

    def pesquisarPeriodo(self):
        try:
            self.hoteis = []
            data_in = self.ui.dateEditEntrada.date().toPyDate()
            data_out = self.ui.dateEditSaida.date().toPyDate()
            url = (
                "/properties/list?search_id=none&"
                "order_by=popularity&"
                "languagecode=pt-br&"
                "search_type=city&"
                "offset=0&"
                "dest_ids=-625529&"
                "categories_filter=breakfast_included::1,property_type::204&"
                "guest_qty=2&"
                "arrival_date={data_in}&"
                "departure_date={data_out}&"
                "room_qty=1".format(
                    data_in=data_in.strftime("%Y-%m-%d"),
                    data_out=data_out.strftime("%Y-%m-%d"),
                )
            )
            self.worker = Worker(url)
            self.worker.addHotel.connect(self.addHotel)
            self.worker.finished.connect(self.preencherRanking)
            self.contador.start()
            self.worker.start()
        except Exception as e:
            QMessageBox.critical(self, "Messagem", "Ocorreu um erro, tente novamente.")
            print(str(e))
            print(traceback.format_exc())
            with open("log.txt", "a") as f:
                f.write(str(e))
                f.write(traceback.format_exc())

    def salvarPeriodo(self):
        try:
            caminho = QFileDialog.getSaveFileName(
                self, "Salvar...", "comparativo", "CSV(*.csv)"
            )
            if not caminho.isEmpty():
                with open(unicodedata(caminho), "wb") as arquivo:
                    data_in = self.ui.dateEditEntrada.date().toPyDate()
                    data_out = self.ui.dateEditSaida.date().toPyDate()
                    periodo = (
                        "De "
                        + data_in.strftime("%d/%m/%y")
                        + " a "
                        + data_out.strftime("%d/%m/%y")
                    )
                    writer = csv.writer(arquivo, delimiter=";")
                    writer.writerow(["Hotel", periodo])
                    for linha in range(self.ui.tableWidgetComparativo.rowCount()):
                        hotel = self.ui.tableWidgetComparativo.item(linha, 0)
                        valor = self.ui.tableWidgetComparativo.item(linha, 1)
                        writer.writerow([hotel.text(), valor.text()])
        except Exception as e:
            QMessageBox.critical(self, "Messagem", "Ocorreu um erro ao salvar arquivo.")
            print(str(e))
            print(traceback.format_exc())
            with open("log.txt", "a") as f:
                f.write(str(e))
                f.write(traceback.format_exc())


def main():
    app = QApplication([])
    acd = AppComparaDiarias()
    acd.show()
    return app.exec_()


if __name__ == "__main__":
    main()
