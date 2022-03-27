import firebirdsql as fdb
import http.client
import json
import datetime as dt
import traceback
import time

from PyQt5.QtWidgets import (
    QMainWindow,
    QApplication,
    QTableWidgetItem,
    QProgressDialog,
)
from PyQt5.QtCore import QDate, QThread, Qt, QTimer, pyqtSignal
from decouple import config
from interface import Ui_MainWindow

POUSADA_DO_SOL = 257826


class Worker(QThread):
    setValorBooking = pyqtSignal(float)

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
        valor = 0.00
        conn = http.client.HTTPSConnection("apidojo-booking-v1.p.rapidapi.com")
        conn.request("GET", self.url, headers=self.headers)

        res = conn.getresponse()
        data = res.read()

        json_data = json.loads(data.decode("utf-8"))

        for hotel in json_data["result"]:
            if int(hotel["hotel_id"]) == POUSADA_DO_SOL:
                try:
                    valor = float(hotel["price_breakdown"]["gross_price"])
                except KeyError:
                    pass
                break
        self.setValorBooking.emit(valor)


class AppTarifaFacil(QMainWindow):
    def __init__(self, parent=None):
        super(AppTarifaFacil, self).__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.conectarSinais()

    def conectarSinais(self):
        self.ui.dateEditEntrada.setDate(QDate.currentDate())
        self.ui.dateEditSaida.setDate(QDate.currentDate().addDays(1))
        self.ui.dateEditEntrada.dateChanged.connect(self.atualizarSaida)
        self.ui.pushButtonVerificar.clicked.connect(self.verificarPeriodo)
        self.progresso = QProgressDialog(
            "Pesquisando tarifas...", "Cancelar", 0, 100, self
        )
        self.progresso.setWindowTitle("Aguarde")
        self.progresso.setWindowModality(Qt.WindowModal)
        self.progresso.canceled.connect(self.cancelar)
        self.progresso.cancel()
        self.contador = QTimer()
        self.contador.timeout.connect(self.carregando)

    def cancelar(self):
        self.valorBooking = 0
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

    def setValorBooking(self, valor):
        if valor > 0:
            self.valorBooking = valor / float(self.diarias)
        else:
            self.valorBooking = 999

    def buscaValorBooking(self):
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
                data_in=self.data_in.strftime("%Y-%m-%d"),
                data_out=self.data_out.strftime("%Y-%m-%d"),
            )
        )
        self.worker = Worker(url)
        self.worker.setValorBooking.connect(self.setValorBooking)
        self.worker.finished.connect(self.preencherTarifario)
        self.contador.start()
        self.worker.start()

    def verificarPeriodo(self):
        try:
            self.con = fdb.connect(
                host=config("HOST"),
                database=config("BANCO_ATUAL"),
                user=config("USER"),
                password=config("PASSWORD"),
                charset="UTF8",
            )
            self.data_in = self.ui.dateEditEntrada.date().toPyDate()
            self.data_out = self.ui.dateEditSaida.date().toPyDate()
            d = self.data_in
            delta = dt.timedelta(days=1)
            self.aptos = []
            self.cur = self.con.cursor()
            self.ocupacoes = []
            self.dias = []
            self.diarias = 0
            while d < self.data_out:
                consulta = """SELECT A1.F_COD FROM TABAPTOS A1 WHERE A1.F_POSICAO <> 'MAN' AND A1.F_POSICAO <> 'INT'
                        AND A1.F_CLASSE < 9 AND NOT EXISTS (
                        SELECT 1 FROM TABRESER R
                        INNER JOIN TABAPTOS A2 ON A2.F_COD = R.F_APTO
                        WHERE (R.F_STATUS = 'CON' OR R.F_STATUS = 'BLO' OR R.F_STATUS = 'HOS')
                        AND A2.F_CLASSE < 9
                        AND '%s' BETWEEN R.F_ENTRADA AND R.F_SAIDA AND '%s' <> R.F_SAIDA
                        AND R.F_APTO = A1.F_COD)""" % (
                    d.strftime("%m/%d/%y"),
                    d.strftime("%m/%d/%y"),
                )
                self.cur.execute(consulta)
                aux = []
                for apto in self.cur.fetchall():
                    aux.append(apto[0])
                self.aptos = self.aptos + [aux]
                percentual = round(((81 - len(aux)) / 81.0) * 100)
                self.ocupacoes.append(percentual)
                self.dias.append(d.strftime("%d/%m/%y"))
                d += delta
                self.diarias += 1
            self.ui.tableWidgetOcupacao.setColumnCount(self.diarias)
            self.ui.tableWidgetOcupacao.setRowCount(1)
            self.ui.tableWidgetOcupacao.setHorizontalHeaderLabels(self.dias)
            for i in range(len(self.ocupacoes)):
                self.ui.tableWidgetOcupacao.setItem(
                    0, i, QTableWidgetItem(str(self.ocupacoes[i]) + "%")
                )
            self.ui.tableWidgetOcupacao.resizeRowsToContents()
            self.ui.tableWidgetOcupacao.resizeColumnsToContents()
            self.valorBooking = 0
            self.buscaValorBooking()
        except Exception as e:
            with open("log.txt", "a") as f:
                print(str(e))
                print(traceback.format_exc())
                f.write(str(e))
                f.write(traceback.format_exc())

    def preencherTarifario(self):
        try:
            if self.valorBooking > 0:
                consulta = """SELECT FIRST 1 D.CONTRATO, C.NOME FROM TABDIAR D
                                INNER JOIN TABCONTR C ON C.CHAVE = D.CONTRATO
                                WHERE D.ADULTOS = 2 AND D.CLASSE = 6 AND EXTRACT(YEAR FROM D.DE) = %s
                                AND D.VALOR <= %s ORDER BY D.VALOR DESC""" % (
                    self.data_in.strftime("%Y"),
                    str(self.valorBooking),
                )
                self.cur.execute(consulta)
                contrato = "0"
                nome_contrato = ""
                for x in self.cur.fetchall():
                    contrato = x[0]
                    nome_contrato = x[1]
                self.ui.lineEditTarifario.setText(nome_contrato)
                self.ui.lineEditDiarias.setText(str(int(self.diarias)))
                self.ui.lineEditTaxas.setText(
                    "R$ " + str(int(3 * float(self.diarias))) + ",00"
                )
                aptos_disp = []
                for i in range(len(self.aptos) - 1):
                    if len(aptos_disp) == 0:
                        a = set(self.aptos[i])
                    else:
                        a = set(aptos_disp)
                    b = set(self.aptos[i + 1])
                    aptos_disp = list(a.intersection(b))
                if len(aptos_disp) == 0:
                    aptos_disp = self.aptos[0]
                aptos_disp_in = ""
                for i in range(len(aptos_disp)):
                    aptos_disp_in += str(aptos_disp[i]) + ","
                aptos_disp_in = aptos_disp_in[: len(aptos_disp_in) - 1]
                consulta = """SELECT DISTINCT A.F_CLASSE FROM TABAPTOS A
                                WHERE A.F_COD IN (%s)""" % (
                    aptos_disp_in
                )
                self.cur.execute(consulta)
                classes_disp = []
                for classe in self.cur.fetchall():
                    classes_disp.append(classe[0])
                classes_disp_in = ""
                for i in range(len(classes_disp)):
                    classes_disp_in += str(classes_disp[i]) + ","
                classes_disp_in = classes_disp_in[: len(classes_disp_in) - 1]
                consulta = """SELECT C.F_CLASSE,
                        (SELECT COUNT(*) FROM TABAPTOS A
                            WHERE A.F_COD IN (%s) AND A.F_CLASSE = C.F_COD),
                        (SELECT D.VALOR FROM TABDIAR D
                            WHERE D.ADULTOS = 1 AND D.CLASSE = C.F_COD AND D.CONTRATO = %s AND D.VALOR > 0),
                        (SELECT D.VALOR FROM TABDIAR D
                            WHERE D.ADULTOS = 2 AND D.CLASSE = C.F_COD AND D.CONTRATO = %s AND D.VALOR > 0),
                        (SELECT D.VALOR FROM TABDIAR D
                            WHERE D.ADULTOS = 3 AND D.CLASSE = C.F_COD AND D.CONTRATO = %s AND D.VALOR > 0),
                        (SELECT D.VALOR FROM TABDIAR D
                            WHERE D.ADULTOS = 4 AND D.CLASSE = C.F_COD AND D.CONTRATO = %s AND D.VALOR > 0)
                        FROM TABCLASS C
                            WHERE C.F_COD IN (%s)""" % (
                    aptos_disp_in,
                    contrato,
                    contrato,
                    contrato,
                    contrato,
                    classes_disp_in,
                )
                self.cur.execute(consulta)
                self.ui.tableWidgetTarifario.setColumnCount(6)
                self.ui.tableWidgetTarifario.setRowCount(len(classes_disp))
                self.ui.tableWidgetTarifario.setHorizontalHeaderLabels(
                    ["Classe", "Qtde UHs", "1 PAX", "2 PAX", "3 PAX", "4 PAX"]
                )
                aux = 0
                for tarifario in self.cur.fetchall():
                    self.ui.tableWidgetTarifario.setItem(
                        aux, 0, QTableWidgetItem(tarifario[0])
                    )
                    self.ui.tableWidgetTarifario.setItem(
                        aux, 1, QTableWidgetItem(str(tarifario[1]))
                    )
                    if tarifario[2] is None:
                        self.ui.tableWidgetTarifario.setItem(
                            aux, 2, QTableWidgetItem("-")
                        )
                    else:
                        self.ui.tableWidgetTarifario.setItem(
                            aux,
                            2,
                            QTableWidgetItem(
                                "R$ %s,00" % str(tarifario[2] * int(self.diarias))
                            ),
                        )
                    if tarifario[3] is None:
                        self.ui.tableWidgetTarifario.setItem(
                            aux, 3, QTableWidgetItem("-")
                        )
                    else:
                        self.ui.tableWidgetTarifario.setItem(
                            aux,
                            3,
                            QTableWidgetItem(
                                "R$ %s,00" % str(tarifario[3] * int(self.diarias))
                            ),
                        )
                    if tarifario[4] is None:
                        self.ui.tableWidgetTarifario.setItem(
                            aux, 4, QTableWidgetItem("-")
                        )
                    else:
                        self.ui.tableWidgetTarifario.setItem(
                            aux,
                            4,
                            QTableWidgetItem(
                                "R$ %s,00" % str(tarifario[4] * int(self.diarias))
                            ),
                        )
                    if tarifario[5] is None:
                        self.ui.tableWidgetTarifario.setItem(
                            aux, 5, QTableWidgetItem("-")
                        )
                    else:
                        self.ui.tableWidgetTarifario.setItem(
                            aux,
                            5,
                            QTableWidgetItem(
                                "R$ %s,00" % str(tarifario[5] * int(self.diarias))
                            ),
                        )
                    aux += 1
                self.ui.tableWidgetTarifario.resizeRowsToContents()
                self.ui.tableWidgetTarifario.resizeColumnsToContents()
            self.con.close()
            self.contador.stop()
            self.progresso.hide()
        except Exception as e:
            with open("log.txt", "a") as f:
                print(str(e))
                print(traceback.format_exc())
                f.write(str(e))
                f.write(traceback.format_exc())


def main():
    app = QApplication([])
    aau = AppTarifaFacil()
    aau.show()
    return app.exec_()


if __name__ == "__main__":
    main()
