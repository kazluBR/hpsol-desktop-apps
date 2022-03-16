import firebirdsql as fdb
import datetime as dt
import traceback

from PyQt5.QtWidgets import QMainWindow, QApplication, QTableWidgetItem
from PyQt5.QtGui import QFont
from PyQt5.QtCore import QDate
from interface import Ui_MainWindow

BANCO_ATUAL = "C:\\nethotel\POUSADA_SOL.FB"
BANCO_ANTIGO = "C:\\nethotel\PSOL2_CONSULTA.FB"


class AppComparativoDespesas(QMainWindow):
    def __init__(self, parent=None):
        super(AppComparativoDespesas, self).__init__(parent)
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
        detalhado = self.ui.checkBoxDetalhado_1.isChecked()
        codigo = self.ui.lineEditCodigo_1.text()
        tabela = self.ui.tableWidgetComparativo_1
        self.verificarPeriodo(data_in, data_out, detalhado, codigo, tabela)

    def pesquisar2(self):
        data_in = self.ui.dateEditInicio_2.date().toPyDate()
        data_out = self.ui.dateEditFim_2.date().toPyDate()
        detalhado = self.ui.checkBoxDetalhado_2.isChecked()
        codigo = self.ui.lineEditCodigo_2.text()
        tabela = self.ui.tableWidgetComparativo_2
        self.verificarPeriodo(data_in, data_out, detalhado, codigo, tabela)

    def verificarPeriodo(self, data_in, data_out, detalhado, codigo, tabela):
        try:
            if data_in >= dt.date(2017, 11, 1):
                con = fdb.connect(
                    host="172.16.1.11",
                    database=BANCO_ATUAL,
                    user="SYSDBA",
                    password="masterkey",
                )
                criterio = """AND T.CODGRUPO NOT LIKE '1.2.11%%'"""
            else:
                con = fdb.connect(
                    host="172.16.1.11",
                    database=BANCO_ANTIGO,
                    user="SYSDBA",
                    password="masterkey",
                )
                criterio = ""
            cur = con.cursor()
            agrup1 = "LEFT(P.GRUPO,6)"
            agrup2 = "LEFT(R.GRUPO,6)"
            agrup3 = "LEFT(P.GRUPO,6)"
            agrup4 = """'1.2.08'"""
            agrup5 = "LEFT(M.GRUPO,6)"
            if detalhado:
                agrup1 = "P.GRUPO"
                agrup2 = "R.GRUPO"
                agrup3 = "P.GRUPO"
                agrup4 = """IIF(R.COMAGT > 5, '1.2.08.02', '1.2.08.01')"""
                agrup5 = "M.GRUPO"
            cod = ""
            if codigo:
                cod = """AND T.CODGRUPO LIKE '%s%%'""" % (codigo)
            if len(codigo) < 7:
                consulta = """SELECT DISTINCT T.CODGRUPO, T.GRUPODESC, SUM(T.VALOR) FROM (
SELECT P.DESCRICAO, P.VALOR, G.CODGRUPO, P.EMISSAO, G.DESCRICAO GRUPODESC
FROM TABPAG P
INNER JOIN TABGRUPF G ON G.CODGRUPO = %s
WHERE (P.STATUS = 'F' OR P.STATUS = 'A') 
AND (SELECT COUNT(*) FROM TABRATEI R WHERE R.CHAVE = P.CHAVEPAG) = 0
UNION ALL
SELECT P.DESCRICAO, R.VALOR, G.CODGRUPO, P.EMISSAO, G.DESCRICAO GRUPODESC
FROM TABRATEI R
INNER JOIN TABPAG P ON P.CHAVEPAG = R.CHAVE
INNER JOIN TABGRUPF G ON G.CODGRUPO = %s
WHERE P.STATUS = 'F' OR P.STATUS = 'A'
UNION ALL
SELECT P.DESCRICAO, (SELECT P.VALOR - SUM(R.VALOR) FROM TABRATEI R WHERE R.CHAVE = P.CHAVEPAG) VALOR,
G.CODGRUPO, P.EMISSAO, G.DESCRICAO GRUPODESC
FROM TABPAG P
INNER JOIN TABGRUPF G ON G.CODGRUPO = %s
WHERE (P.STATUS = 'F' OR P.STATUS = 'A')
AND (SELECT COUNT(*) FROM TABRATEI R WHERE R.CHAVE = P.CHAVEPAG) > 0
AND (SELECT SUM(R.VALOR) FROM TABRATEI R WHERE R.CHAVE = P.CHAVEPAG) < P.VALOR
UNION ALL
SELECT R.DESCRICAO, R.VALCOM VALOR, G.CODGRUPO, R.EMISSAO, G.DESCRICAO GRUPODESC
FROM TABREC R
INNER JOIN TABEMPR E ON E.F_COD = R.CLIENTE
INNER JOIN TABGRUPF G ON G.CODGRUPO = %s
WHERE (R.STATUS = 'F' OR R.STATUS = 'A') AND R.VALCOM > 0
UNION ALL
SELECT M.OBS DESCRICAO, M.VALOR, G.CODGRUPO, CAST(M.COMPETENCIA AS DATE) EMISSAO, G.DESCRICAO GRUPODESC
FROM TABMOVB M
INNER JOIN TABGRUPF G ON G.CODGRUPO = %s
WHERE M.ORIGEM = 'B' AND M.TIPO = 'D' AND M.GRUPO <> '1.2.09.05' AND M.GRUPO NOT LIKE '1.1.07%%'
) T WHERE T.EMISSAO BETWEEN '%s' AND '%s' AND
T.CODGRUPO NOT LIKE '1.2.11%%' %s
GROUP BY T.CODGRUPO, T.GRUPODESC ORDER BY T.CODGRUPO""" % (
                    agrup1,
                    agrup2,
                    agrup3,
                    agrup4,
                    agrup5,
                    data_in.strftime("%m/%d/%y"),
                    data_out.strftime("%m/%d/%y"),
                    cod,
                )
                cur.execute(consulta)
                resultados = []
                despesa_total = 0
                for resultado in cur.fetchall():
                    resultados.append(resultado)
                    despesa_total += resultado[2]
                tabela.setColumnCount(4)
                tabela.setRowCount(len(resultados) + 1)
                tabela.setHorizontalHeaderLabels(["Codigo", "Grupo", "Total", "%"])
                aux = 0
                for r in resultados:
                    tabela.setItem(aux, 0, QTableWidgetItem(r[0]))
                    tabela.setItem(aux, 1, QTableWidgetItem(r[1]))
                    tabela.setItem(aux, 2, QTableWidgetItem("R$ " + str(r[2])))
                    tabela.setItem(
                        aux,
                        3,
                        QTableWidgetItem(str(round((r[2] / despesa_total) * 100, 2))),
                    )
                    aux += 1
                table_codigo = QTableWidgetItem("99")
                table_codigo.setFont(QFont("Segoe UI", weight=QFont.Bold))
                table_grupo = QTableWidgetItem("TOTAL")
                table_grupo.setFont(QFont("Segoe UI", weight=QFont.Bold))
                table_total = QTableWidgetItem("R$ " + str(despesa_total))
                table_total.setFont(QFont("Segoe UI", weight=QFont.Bold))
                table_percentual = QTableWidgetItem("100.00")
                table_percentual.setFont(QFont("Segoe UI", weight=QFont.Bold))
                tabela.setItem(aux, 0, table_codigo)
                tabela.setItem(aux, 1, table_grupo)
                tabela.setItem(aux, 2, table_total)
                tabela.setItem(aux, 3, table_percentual)
                tabela.resizeColumnsToContents()
            else:
                consulta = """SELECT T.CODIGO, T.FORNECEDOR, T.DESCRICAO, T.VALOR, T.EMISSAO FROM (
SELECT P.CHAVEPAG CODIGO, F.FANTASIA FORNECEDOR, P.DESCRICAO, P.VALOR, G.CODGRUPO, P.EMISSAO
FROM TABPAG P
INNER JOIN TABGRUPF G ON G.CODGRUPO = %s
INNER JOIN TABFOR F ON F.CODIGO = P.FORNECEDOR
WHERE (P.STATUS = 'F' OR P.STATUS = 'A') 
AND (SELECT COUNT(*) FROM TABRATEI R WHERE R.CHAVE = P.CHAVEPAG) = 0
UNION ALL
SELECT P.CHAVEPAG CODIGO, F.FANTASIA FORNECEDOR, P.DESCRICAO, R.VALOR, G.CODGRUPO, P.EMISSAO
FROM TABRATEI R
INNER JOIN TABPAG P ON P.CHAVEPAG = R.CHAVE
INNER JOIN TABGRUPF G ON G.CODGRUPO = %s
INNER JOIN TABFOR F ON F.CODIGO = P.FORNECEDOR
WHERE P.STATUS = 'F' OR P.STATUS = 'A'
UNION ALL
SELECT P.CHAVEPAG CODIGO, F.FANTASIA FORNECEDOR, P.DESCRICAO, (SELECT P.VALOR - SUM(R.VALOR) FROM TABRATEI R WHERE R.CHAVE = P.CHAVEPAG) VALOR,
G.CODGRUPO, P.EMISSAO
FROM TABPAG P
INNER JOIN TABGRUPF G ON G.CODGRUPO = %s
INNER JOIN TABFOR F ON F.CODIGO = P.FORNECEDOR
WHERE (P.STATUS = 'F' OR P.STATUS = 'A')
AND (SELECT COUNT(*) FROM TABRATEI R WHERE R.CHAVE = P.CHAVEPAG) > 0
AND (SELECT SUM(R.VALOR) FROM TABRATEI R WHERE R.CHAVE = P.CHAVEPAG) < P.VALOR
UNION ALL
SELECT R.CHAVEREC CODIGO, E.F_NOME FORNECEDOR, R.DESCRICAO, R.VALCOM VALOR, G.CODGRUPO, R.EMISSAO
FROM TABREC R
INNER JOIN TABEMPR E ON E.F_COD = R.CLIENTE
INNER JOIN TABGRUPF G ON G.CODGRUPO = %s
WHERE (R.STATUS = 'F' OR R.STATUS = 'A') AND R.VALCOM > 0
UNION ALL
SELECT M.SEQUENCIAL CODIGO, 'NAO INFORMADO' FORNECEDOR, M.OBS DESCRICAO, M.VALOR, G.CODGRUPO, CAST(M.COMPETENCIA AS DATE) EMISSAO
FROM TABMOVB M
INNER JOIN TABGRUPF G ON G.CODGRUPO = %s
WHERE M.ORIGEM = 'B' AND M.TIPO = 'D'
) T WHERE T.EMISSAO BETWEEN '%s' AND '%s' %s ORDER BY T.EMISSAO""" % (
                    agrup1,
                    agrup2,
                    agrup3,
                    agrup4,
                    agrup5,
                    data_in.strftime("%m/%d/%y"),
                    data_out.strftime("%m/%d/%y"),
                    cod,
                )
                cur.execute(consulta)
                resultados = []
                for resultado in cur.fetchall():
                    resultados.append(resultado)
                tabela.setColumnCount(5)
                tabela.setRowCount(len(resultados))
                tabela.setHorizontalHeaderLabels(
                    ["Codigo", "Fornecedor", "Descricao", "Valor", "Emissao"]
                )
                aux = 0
                for r in resultados:
                    tabela.setItem(aux, 0, QTableWidgetItem(str(r[0])))
                    tabela.setItem(aux, 1, QTableWidgetItem(r[1]))
                    tabela.setItem(aux, 2, QTableWidgetItem(r[2]))
                    tabela.setItem(aux, 3, QTableWidgetItem("R$ " + str(r[3])))
                    tabela.setItem(aux, 4, QTableWidgetItem(r[4].strftime("%d/%m/%Y")))
                    aux += 1
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
    acd = AppComparativoDespesas()
    acd.show()
    return app.exec_()


if __name__ == "__main__":
    main()
