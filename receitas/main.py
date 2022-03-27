import firebirdsql as fdb
import datetime as dt
import traceback

from PyQt5.QtWidgets import QMainWindow, QApplication, QTableWidgetItem
from PyQt5.QtGui import QFont
from PyQt5.QtCore import QDate
from decouple import config
from interface import Ui_MainWindow


class AppComparativoReceitas(QMainWindow):
    def __init__(self, parent=None):
        super(AppComparativoReceitas, self).__init__(parent)
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
        tabela = self.ui.tableWidgetComparativo_1
        self.verificarPeriodo(data_in, data_out, tabela)

    def pesquisar2(self):
        data_in = self.ui.dateEditInicio_2.date().toPyDate()
        data_out = self.ui.dateEditFim_2.date().toPyDate()
        tabela = self.ui.tableWidgetComparativo_2
        self.verificarPeriodo(data_in, data_out, tabela)

    def verificarPeriodo(self, data_in, data_out, tabela):
        try:
            con = fdb.connect(
                host=config("HOST"),
                database=config("BANCO_ATUAL"),
                user=config("USER"),
                password=config("PASSWORD"),
                charset="UTF8",
            )
            cur = con.cursor()
            consulta = """SELECT DISTINCT T.DESCRICAO, SUM(T.VALOR) TOTAL FROM (
    SELECT H.F_HISTOR DESCRICAO, (L.F_VALOR - L.F_DESCONTO) VALOR, R.F_SAIDA DATA
        FROM TABLANCA L
        INNER JOIN TABRESER R ON R.F_RES = L.F_RES
        INNER JOIN TABHISTO H ON H.F_COD = L.F_CODHISTOR
        WHERE (H.F_COD = 80 OR H.F_COD = 85 OR H.F_COD = 109)
        AND L.F_ESTORNO <> 'S' AND L.F_ESTORNO <> 'P'
        AND (R.F_STATUS = 'SAI' OR R.F_STATUS = 'PAR' OR R.F_STATUS = 'PEN')
    UNION ALL
    SELECT 'FATURAMENTO', (L.F_VALOR - L.F_DESCONTO) VALOR, R.F_SAIDA DATA
        FROM TABLANCA L
        INNER JOIN TABRESER R ON R.F_RES = L.F_RES
        INNER JOIN TABHISTO H ON H.F_COD = L.F_CODHISTOR
        WHERE (H.F_COD = 83 OR H.F_COD = 84)
        AND L.F_ESTORNO <> 'S' AND L.F_ESTORNO <> 'P'
        AND (R.F_STATUS = 'SAI' OR R.F_STATUS = 'PAR' OR R.F_STATUS = 'PEN')
    UNION ALL
    SELECT 'CARTAO CREDITO', (L.F_VALOR - L.F_DESCONTO) VALOR, R.F_SAIDA DATA
        FROM TABLANCA L
        INNER JOIN TABRESER R ON R.F_RES = L.F_RES
        INNER JOIN TABHISTO H ON H.F_COD = L.F_CODHISTOR
        WHERE (H.F_COD = 87 OR H.F_COD = 88 OR H.F_COD = 90 OR  H.F_COD = 98 OR H.F_COD = 99 OR H.F_COD = 101 OR H.F_COD = 102 OR H.F_COD = 103 OR H.F_COD = 104 OR H.F_COD = 105 OR H.F_COD = 110 OR H.F_COD = 111)
        AND L.F_ESTORNO <> 'S' AND L.F_ESTORNO <> 'P'
        AND (R.F_STATUS = 'SAI' OR R.F_STATUS = 'PAR' OR R.F_STATUS = 'PEN')
    UNION ALL
    SELECT 'CARTAO DEBITO', (L.F_VALOR - L.F_DESCONTO) VALOR, R.F_SAIDA DATA
        FROM TABLANCA L
        INNER JOIN TABRESER R ON R.F_RES = L.F_RES
        INNER JOIN TABHISTO H ON H.F_COD = L.F_CODHISTOR
        WHERE (H.F_COD = 89 OR H.F_COD = 97 OR H.F_COD = 100 OR H.F_COD = 106 OR H.F_COD = 112)
        AND L.F_ESTORNO <> 'S' AND L.F_ESTORNO <> 'P'
        AND (R.F_STATUS = 'SAI' OR R.F_STATUS = 'PAR' OR R.F_STATUS = 'PEN')
    UNION ALL
    SELECT 'REC PREVISAO' DESCRICAO, IIF(TS.FLUT = 0, CAST(((TS.F_DIARIA - (TS.F_DIARIA * TS.DESCONTO)) * TS.DIAS) AS DECIMAL(10,2)),
        (SELECT SUM(R2.VALOR) FROM TABRES1 R2 WHERE R2.RES = TS.F_RES)) VALOR, TS.F_SAIDA DATA FROM (
            SELECT R.F_RES, IIF(R.F_ENTRADA = R.F_SAIDA, 1, DATEDIFF(DAY FROM R.F_ENTRADA TO R.F_SAIDA)) DIAS,
            R.F_DIARIA, CAST(R.F_DESCONTO / 100 AS NUMERIC(5,4)) DESCONTO, R.F_SAIDA,
            (SELECT COUNT(*) FROM TABRES1 R2 WHERE R2.RES = R.F_RES) FLUT
            FROM TABRESER R
            WHERE (R.F_STATUS = 'CON' OR R.F_STATUS = 'HOS')
            AND R.F_APTO IS NOT NULL AND R.F_DIARIA > 0
        ) TS
    UNION ALL
    SELECT 'VENDA RAPIDA' DESCRICAO, E.TOTAL VALOR, E.DATA
        FROM TABE8 E
        WHERE E.RESERVA = 0 AND E.TOTAL > 0 AND E.TIPOLANCTO = 0
    UNION ALL
    SELECT 'DEMAIS RECEITAS' DESCRICAO, R.VALOR, R.EMISSAO DATA
        FROM TABREC R
        WHERE (R.STATUS = 'F' OR R.STATUS = 'A') AND R.GRUPO = '1.1.06.03'
    UNION ALL
    SELECT G.DESCRICAO, IIF(M.TIPO = 'C', M.VALOR, -M.VALOR) VALOR, M.DATA
        FROM TABMOVB M
        INNER JOIN TABGRUPF G ON G.CODGRUPO = M.GRUPO
        WHERE M.GRUPO IN ('1.1.06.03','1.1.07.05') AND TITULO = 0
    ) T WHERE T.DATA BETWEEN '%s' AND '%s'
    GROUP BY T.DESCRICAO ORDER BY SUM(T.VALOR) DESC""" % (
                data_in.strftime("%m/%d/%y"),
                data_out.strftime("%m/%d/%y"),
            )
            cur.execute(consulta)
            resultados = []
            receita_total = 0
            for resultado in cur.fetchall():
                resultados.append(resultado)
                receita_total += resultado[1]
            tabela.setColumnCount(3)
            tabela.setRowCount(len(resultados) + 1)
            tabela.setHorizontalHeaderLabels(["Historico", "Total", "%"])
            aux = 0
            for r in resultados:
                tabela.setItem(aux, 0, QTableWidgetItem(r[0]))
                tabela.setItem(aux, 1, QTableWidgetItem("R$ " + str(r[1])))
                tabela.setItem(
                    aux,
                    2,
                    QTableWidgetItem(str(round((r[1] / receita_total) * 100, 2))),
                )
                aux += 1
            table_historico = QTableWidgetItem("TOTAL")
            table_historico.setFont(QFont("Segoe UI", weight=QFont.Bold))
            table_total = QTableWidgetItem("R$ " + str(receita_total))
            table_total.setFont(QFont("Segoe UI", weight=QFont.Bold))
            table_percentual = QTableWidgetItem("100.00")
            table_percentual.setFont(QFont("Segoe UI", weight=QFont.Bold))
            tabela.setItem(aux, 0, table_historico)
            tabela.setItem(aux, 1, table_total)
            tabela.setItem(aux, 2, table_percentual)
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
    acr = AppComparativoReceitas()
    acr.show()
    return app.exec_()


if __name__ == "__main__":
    main()
