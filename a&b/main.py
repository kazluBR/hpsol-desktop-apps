import firebirdsql as fdb
import datetime as dt
import traceback

from PyQt5.QtWidgets import QMainWindow, QApplication, QTableWidgetItem
from PyQt5.QtGui import QFont
from PyQt5.QtCore import QDate
from interface import Ui_MainWindow

BANCO_ATUAL = "C:\\nethotel\POUSADA_SOL.FB"
BANCO_ANTIGO = "C:\\nethotel\PSOL2_CONSULTA.FB"


class AppComparativoAeB(QMainWindow):
    def __init__(self, parent=None):
        super(AppComparativoAeB, self).__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.conectarSinais()

    def conectarSinais(self):
        self.ui.dateEditInicio_1.setDate(QDate.currentDate())
        self.ui.dateEditFim_1.setDate(QDate.currentDate().addDays(1))
        self.ui.dateEditInicio_1.dateChanged.connect(self.atualizarFim1)
        self.ui.dateEditInicio_2.setDate(QDate.currentDate())
        self.ui.dateEditFim_2.setDate(QDate.currentDate().addDays(1))
        self.ui.dateEditInicio_2.dateChanged.connect(self.atualizarFim2)
        self.ui.pushButtonPesquisar_1.clicked.connect(self.pesquisar1)
        self.ui.pushButtonPesquisar_2.clicked.connect(self.pesquisar2)

    def atualizarFim1(self):
        self.ui.dateEditFim_1.setDate(self.ui.dateEditInicio_1.date().addDays(1))

    def atualizarFim2(self):
        self.ui.dateEditFim_2.setDate(self.ui.dateEditInicio_2.date().addDays(1))

    def pesquisar1(self):
        data_in = self.ui.dateEditInicio_1.date().toPyDate()
        data_out = self.ui.dateEditFim_1.date().toPyDate()
        com_nota = self.ui.checkBoxComNota_1.isChecked()
        lancamento = self.ui.checkBoxLancamento_1.isChecked()
        venda_rapida = self.ui.checkBoxVendaRapida_1.isChecked()
        tabela = self.ui.tableWidgetComparativo_1
        self.verificarPeriodo(
            data_in, data_out, com_nota, lancamento, venda_rapida, tabela
        )

    def pesquisar2(self):
        data_in = self.ui.dateEditInicio_2.date().toPyDate()
        data_out = self.ui.dateEditFim_2.date().toPyDate()
        com_nota = self.ui.checkBoxComNota_2.isChecked()
        lancamento = self.ui.checkBoxLancamento_2.isChecked()
        venda_rapida = self.ui.checkBoxVendaRapida_2.isChecked()
        tabela = self.ui.tableWidgetComparativo_2
        self.verificarPeriodo(
            data_in, data_out, com_nota, lancamento, venda_rapida, tabela
        )

    def verificarPeriodo(
        self, data_in, data_out, com_nota, lancamento, venda_rapida, tabela
    ):
        try:
            antbug = ""
            if data_in >= dt.date(2017, 11, 1):
                con = fdb.connect(
                    host="172.16.1.11",
                    database=BANCO_ATUAL,
                    user="SYSDBA",
                    password="masterkey",
                )
            else:
                con = fdb.connect(
                    host="172.16.1.11",
                    database=BANCO_ANTIGO,
                    user="SYSDBA",
                    password="masterkey",
                )
                antbug = "AND R.F_HOSPEDE <> 43656 AND R.F_HOSPEDE <> 11103 AND R.F_HOSPEDE <> 583"
            cur = con.cursor()
            criterio = "R.F_SAIDA"
            if lancamento:
                criterio = "L.F_DATA"
                criterio_aux = ""
            criterio2 = "-1"
            if com_nota:
                criterio2 = "0"
            criterio3 = "-1"
            if venda_rapida:
                criterio3 = "0"
            consulta = """SELECT * FROM (
SELECT DISTINCT T2.DESCRICAO, COUNT(T2.LINHA) QTDE, SUM(T2.VALOR) TOTAL FROM (
    SELECT T.LINHA, T.DESCRICAO, T.VALOR FROM (
            SELECT L.LINHA, H.F_HISTOR DESCRICAO, (L.F_VALOR - L.F_DESCONTO) VALOR, %s DATA, 0 PDV,
            (SELECT COUNT(N.CHAVE) FROM TABNFREC N WHERE N.RESERVA = R.F_RES AND N.TIPODOC = 'NFE') COMNOTA
            FROM TABLANCA L
            INNER JOIN TABRESER R ON R.F_RES = L.F_RES
            INNER JOIN TABHISTO H ON H.F_COD = L.F_CODHISTOR
            WHERE H.F_TIPO = 'D' AND H.SUBALMOX > 0 AND L.F_ESTORNO <> 'S' AND L.F_ESTORNO <> 'P'
            %s
            UNION ALL
            SELECT E.CHAVE LINHA, H.F_HISTOR DESCRICAO, E.TOTAL VALOR, E.DATA, 1 PDV, 0 COMNOTA
            FROM TABE8 E
            INNER JOIN TABSUBAL S ON S.CODIGO = E.SUBAL
            INNER JOIN TABHISTO H ON H.F_COD = S.HISTORICO
            WHERE E.RESERVA = 0 AND E.TOTAL > 0 AND E.TIPOLANCTO = 0
            UNION ALL
            SELECT 0 LINHA, 'CORTESIA A&B' DESCRICAO, -L2.F_VALOR VALOR, R2.F_SAIDA DATA, 0 PDV, 0 COMNOTA
            FROM TABLANCA L2
            INNER JOIN TABRESER R2 ON R2.F_RES = L2.F_RES
            WHERE L2.F_CODHISTOR = 113 AND L2.F_ESTORNO <> 'S' AND L2.F_ESTORNO <> 'P'
        ) T WHERE T.DATA BETWEEN '%s' AND '%s' AND T.COMNOTA > %s AND T.PDV > %s
    ) T2 GROUP BY T2.DESCRICAO
) T3 ORDER BY T3.TOTAL DESC""" % (
                criterio,
                antbug,
                data_in.strftime("%m/%d/%y"),
                data_out.strftime("%m/%d/%y"),
                criterio2,
                criterio3,
            )
            cur.execute(consulta)
            resultados = []
            total_qtde = 0
            receita_total = 0
            for resultado in cur.fetchall():
                resultados.append(resultado)
                total_qtde += resultado[1]
                receita_total += resultado[2]
            tabela.setColumnCount(4)
            tabela.setRowCount(len(resultados) + 1)
            tabela.setHorizontalHeaderLabels(["Historico", "Qtde", "Total", "%"])
            aux = 0
            for r in resultados:
                tabela.setItem(aux, 0, QTableWidgetItem(r[0]))
                tabela.setItem(aux, 1, QTableWidgetItem(str(r[1])))
                tabela.setItem(aux, 2, QTableWidgetItem("R$ " + str(r[2])))
                tabela.setItem(
                    aux,
                    3,
                    QTableWidgetItem(str(round((r[2] / receita_total) * 100, 2))),
                )
                aux += 1
            table_empresa = QTableWidgetItem("TOTAIS")
            table_empresa.setFont(QFont("Segoe UI", weight=QFont.Bold))
            table_qtde = QTableWidgetItem(str(total_qtde))
            table_qtde.setFont(QFont("Segoe UI", weight=QFont.Bold))
            table_total = QTableWidgetItem("R$ " + str(receita_total))
            table_total.setFont(QFont("Segoe UI", weight=QFont.Bold))
            table_percentual = QTableWidgetItem("100.00")
            table_percentual.setFont(QFont("Segoe UI", weight=QFont.Bold))
            tabela.setItem(aux, 0, table_empresa)
            tabela.setItem(aux, 1, table_qtde)
            tabela.setItem(aux, 2, table_total)
            tabela.setItem(aux, 3, table_percentual)
            tabela.resizeColumnsToContents()
            con.close()
        except Exception as e:
            with open("log.txt", "a") as f:
                print(str(e))
                print(traceback.format_exc())
                f.write(str(e))
                f.write(traceback.format_exc())


def main():
    app = QApplication([])
    acab = AppComparativoAeB()
    acab.show()
    return app.exec_()


if __name__ == "__main__":
    main()
