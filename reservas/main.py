import firebirdsql as fdb
import datetime as dt
import traceback

from PyQt5.QtWidgets import QMainWindow, QApplication, QTableWidgetItem
from PyQt5.QtGui import QFont
from PyQt5.QtCore import QDate
from decouple import config
from interface import Ui_MainWindow


class AppComparativoReservas(QMainWindow):
    def __init__(self, parent=None):
        super(AppComparativoReservas, self).__init__(parent)
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
        relativo = self.ui.checkBoxRelativo_1.isChecked()
        canceladas = self.ui.checkBoxCanceladas_1.isChecked()
        tabela = self.ui.tableWidgetComparativo_1
        self.verificarPeriodo(
            data_in, data_out, com_nota, lancamento, relativo, canceladas, tabela
        )

    def pesquisar2(self):
        data_in = self.ui.dateEditInicio_2.date().toPyDate()
        data_out = self.ui.dateEditFim_2.date().toPyDate()
        com_nota = self.ui.checkBoxComNota_2.isChecked()
        lancamento = self.ui.checkBoxLancamento_2.isChecked()
        relativo = self.ui.checkBoxRelativo_2.isChecked()
        canceladas = self.ui.checkBoxCanceladas_2.isChecked()
        tabela = self.ui.tableWidgetComparativo_2
        self.verificarPeriodo(
            data_in, data_out, com_nota, lancamento, relativo, canceladas, tabela
        )

    def verificarPeriodo(
        self, data_in, data_out, com_nota, lancamento, relativo, canceladas, tabela
    ):
        try:
            antbug = ""
            if data_in >= dt.date(2017, 11, 1):
                con = fdb.connect(
                    host=config("HOST"),
                    database=config("BANCO_ATUAL"),
                    user=config("USER"),
                    password=config("PASSWORD"),
                    charset="UTF8",
                )
            else:
                con = fdb.connect(
                    host=config("HOST"),
                    database=config("BANCO_ANTIGO"),
                    user=config("USER"),
                    password=config("PASSWORD"),
                    charset="UTF8",
                )
                antbug = "AND R.F_HOSPEDE <> 43656 AND R.F_HOSPEDE <> 11103 AND R.F_HOSPEDE <> 583"
            cur = con.cursor()
            criterio = "F_SAIDA"
            if lancamento:
                criterio = "EMISSAO"
            criterio2 = "-1"
            if com_nota:
                criterio2 = "0"
            criterio3 = dt.datetime.today().strftime("%m/%d/%y")
            if relativo:
                if (
                    dt.datetime.today().date() <= data_out
                    or data_out.year < dt.datetime.today().year
                ):
                    criterio3 = (
                        dt.datetime.today()
                        .replace(year=data_in.year)
                        .strftime("%m/%d/%y")
                    )
                else:
                    criterio3 = (
                        dt.datetime.today()
                        .replace(year=data_in.year - 1)
                        .strftime("%m/%d/%y")
                    )
            criterio4 = "0"
            if canceladas:
                criterio4 = "1"
            consulta = """SELECT * FROM (
SELECT DISTINCT T2.EMPRESA, COUNT(DISTINCT T2.NUMERORESERVA) QTDE, SUM(T2.LINHA) DIARIAS, SUM(T2.VALOR) TOTAL, IIF(SUM(T2.LINHA) = 0, 0, SUM(T2.VALOR)/SUM(T2.LINHA)) MEDIA FROM (
    SELECT T.NUMERORESERVA, T.LINHA, T.VALOR,
        IIF(T.TIPOCONTA > 0, T.DESCCONTA, (SELECT E.F_NOME FROM TABEMPR E WHERE E.F_COD = T.EMPRESA)) EMPRESA FROM (
            SELECT DISTINCT TS.NUMERORESERVA, TS.DESCCONTA, TS.TIPOCONTA, SUM(TS.LINHA) LINHA, SUM(TS.VALOR) VALOR, TS.F_SAIDA,
            IIF(TS.EMISSAO IS NULL, CAST(TS.F_SAIDA AS TIMESTAMP), TS.EMISSAO) EMISSAO, TS.EMPRESA, TS.COMNOTA, 0 CANCELADA FROM (
                SELECT R.NUMERORESERVA, R.DESCCONTA, R.TIPOCONTA, 1 LINHA,
                (L.F_VALOR - L.F_DESCONTO) VALOR, R.F_SAIDA,
                (SELECT FIRST 1 R2.EMISSAO FROM TABRESER R2 WHERE R2.F_APTO IS NOT NULL AND R2.NUMERORESERVA = R.NUMERORESERVA) EMISSAO,
                (SELECT FIRST 1 R2.F_EMPRESA FROM TABRESER R2 WHERE R2.F_APTO IS NOT NULL AND R2.NUMERORESERVA = R.NUMERORESERVA) EMPRESA,
                (SELECT COUNT(N.CHAVE) FROM TABNFSE1 N WHERE N.RESERVA = R.F_RES) COMNOTA
                FROM TABLANCA L
                INNER JOIN TABRESER R ON R.F_RES = L.F_RES
                WHERE L.F_CODHISTOR = 1 AND L.F_ESTORNO <> 'S' AND L.F_ESTORNO <> 'P'
                AND (R.F_STATUS = 'SAI' OR R.F_STATUS = 'PAR' OR R.F_STATUS = 'PEN') %s
            ) TS WHERE TS.VALOR > 1 GROUP BY TS.EMPRESA, TS.NUMERORESERVA, TS.DESCCONTA, TS.TIPOCONTA, TS.F_SAIDA, TS.EMISSAO, TS.EMPRESA, TS.COMNOTA
            UNION ALL
            SELECT TS.NUMERORESERVA, TS.DESCCONTA, TS.TIPOCONTA, TS.DIAS LINHA, IIF(TS.FLUT = 0,
            CAST(((TS.F_DIARIA - (TS.F_DIARIA * TS.DESCONTO)) * TS.DIAS) AS DECIMAL(10,2)),
            (SELECT SUM(R2.VALOR) FROM TABRES1 R2 WHERE R2.RES = TS.F_RES)) VALOR, TS.F_SAIDA, TS.EMISSAO, TS.EMPRESA, 0 COMNOTA, 0 CANCELADA FROM (
                SELECT R.F_RES, R.NUMERORESERVA, R.DESCCONTA, R.TIPOCONTA, IIF(R.F_ENTRADA = R.F_SAIDA, 1, DATEDIFF(DAY FROM R.F_ENTRADA TO R.F_SAIDA)) DIAS,
                R.F_DIARIA, CAST(R.F_DESCONTO / 100 AS NUMERIC(5,4)) DESCONTO, R.F_EMPRESA EMPRESA, R.F_SAIDA, R.EMISSAO,
                (SELECT COUNT(*) FROM TABRES1 R2 WHERE R2.RES = R.F_RES) FLUT
                FROM TABRESER R
                WHERE (R.F_STATUS = 'CON' OR R.F_STATUS = 'HOS')
                AND R.F_APTO IS NOT NULL AND R.F_DIARIA > 0
            ) TS
            UNION ALL
            SELECT DISTINCT TS.NUMERORESERVA, TS.DESCCONTA, TS.TIPOCONTA, TS.DIAS LINHA,
            CAST(((TS.F_DIARIA - (TS.F_DIARIA * TS.DESCONTO)) * TS.DIAS) AS DECIMAL(10,2)) VALOR, TS.F_SAIDA, TS.EMISSAO, TS.EMPRESA, 0 COMNOTA, 1 CANCELADA FROM (
                SELECT R.NUMERORESERVA, R.DESCCONTA, R.TIPOCONTA, IIF(R.F_ENTRADA = R.F_SAIDA, 1, DATEDIFF(DAY FROM R.F_ENTRADA TO R.F_SAIDA)) DIAS,
                CAST(R.F_DESCONTO / 100 AS NUMERIC(5,4)) DESCONTO, R.F_DIARIA, R.F_SAIDA, R.EMISSAO, R.F_EMPRESA EMPRESA
                FROM TABRESER R
                WHERE R.F_STATUS = 'CAN'
            ) TS
            UNION ALL
            SELECT DISTINCT TS.NUMERORESERVA, TS.DESCCONTA, TS.TIPOCONTA, TS.DIAS LINHA,
            CAST(((TS.F_DIARIA - (TS.F_DIARIA * TS.DESCONTO)) * TS.DIAS) AS DECIMAL(10,2)) VALOR, TS.F_SAIDA, TS.EMISSAO, TS.EMPRESA, 0 COMNOTA, 0 CANCELADA FROM (
                SELECT R.NUMERORESERVA, R.DESCCONTA, R.TIPOCONTA, IIF(R.F_ENTRADA = R.F_SAIDA, 1, DATEDIFF(DAY FROM R.F_ENTRADA TO R.F_SAIDA)) DIAS,
                CAST(R.F_DESCONTO / 100 AS NUMERIC(5,4)) DESCONTO, R.F_DIARIA, R.F_SAIDA, R.EMISSAO, R.F_EMPRESA EMPRESA
                FROM TABRESER R
                WHERE R.F_STATUS = 'CAN' AND (SELECT FIRST 1 CAST(L.DATA AS DATE) FROM TABLOG L WHERE L.ITEM = R.F_RES AND L.DE = 'CON') > '%s'
            ) TS
            UNION ALL
            SELECT 0 NUMERORESERVA, H.F_HISTOR DESCCONTA, 1 TIPOCONTA, 0 LINHA, -L2.F_VALOR VALOR, R2.F_SAIDA, CAST(L2.F_DATA AS TIMESTAMP) EMISSAO, 0 EMPRESA, 0 COMNOTA, 0 CANCELADA
            FROM TABLANCA L2
            INNER JOIN TABRESER R2 ON R2.F_RES = L2.F_RES
            INNER JOIN TABHISTO H ON H.F_COD = L2.F_CODHISTOR
            WHERE L2.F_CODHISTOR = 107 AND L2.F_ESTORNO <> 'S' AND L2.F_ESTORNO <> 'P'
        ) T WHERE T.%s BETWEEN '%s' AND '%s' AND T.COMNOTA > %s AND T.EMISSAO <= '%s' AND T.CANCELADA = %s
    ) T2 WHERE ABS(T2.VALOR) > 1 GROUP BY T2.EMPRESA
) T3 ORDER BY T3.TOTAL DESC""" % (
                antbug,
                criterio3,
                criterio,
                data_in.strftime("%m/%d/%y"),
                data_out.strftime("%m/%d/%y"),
                criterio2,
                criterio3,
                criterio4,
            )
            cur.execute(consulta)
            resultados = []
            total_qtde = 0
            total_diarias = 0
            receita_total = 0
            diaria_media = 0
            for resultado in cur.fetchall():
                resultados.append(resultado)
                total_qtde += resultado[1]
                total_diarias += resultado[2]
                receita_total += resultado[3]
            if total_diarias > 0:
                diaria_media = round(float(receita_total) / total_diarias, 2)
            tabela.setColumnCount(6)
            tabela.setRowCount(len(resultados) + 1)
            tabela.setHorizontalHeaderLabels(
                ["Empresa", "Qtde", "Diarias", "Total", "Media", "%"]
            )
            aux = 0
            for r in resultados:
                if r[0] is None:
                    tabela.setItem(aux, 0, QTableWidgetItem("NAO INFORMADA"))
                else:
                    tabela.setItem(aux, 0, QTableWidgetItem(r[0]))
                tabela.setItem(aux, 1, QTableWidgetItem(str(r[1])))
                tabela.setItem(aux, 2, QTableWidgetItem(str(r[2])))
                tabela.setItem(aux, 3, QTableWidgetItem("R$ " + str(r[3])))
                tabela.setItem(aux, 4, QTableWidgetItem("R$ " + str(r[4])))
                tabela.setItem(
                    aux,
                    5,
                    QTableWidgetItem(str(round((r[3] / receita_total) * 100, 2))),
                )
                aux += 1
            table_empresa = QTableWidgetItem("TOTAIS")
            table_empresa.setFont(QFont("Segoe UI", weight=QFont.Bold))
            table_qtde = QTableWidgetItem(str(total_qtde))
            table_qtde.setFont(QFont("Segoe UI", weight=QFont.Bold))
            table_diarias = QTableWidgetItem(str(total_diarias))
            table_diarias.setFont(QFont("Segoe UI", weight=QFont.Bold))
            table_total = QTableWidgetItem("R$ " + str(receita_total))
            table_total.setFont(QFont("Segoe UI", weight=QFont.Bold))
            table_media = QTableWidgetItem("R$ " + str(diaria_media))
            table_media.setFont(QFont("Segoe UI", weight=QFont.Bold))
            table_percentual = QTableWidgetItem("100.00")
            table_percentual.setFont(QFont("Segoe UI", weight=QFont.Bold))
            tabela.setItem(aux, 0, table_empresa)
            tabela.setItem(aux, 1, table_qtde)
            tabela.setItem(aux, 2, table_diarias)
            tabela.setItem(aux, 3, table_total)
            tabela.setItem(aux, 4, table_media)
            tabela.setItem(aux, 5, table_percentual)
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
    acr = AppComparativoReservas()
    acr.show()
    return app.exec_()


if __name__ == "__main__":
    main()
