import firebirdsql as fdb
import traceback
import os

from PyQt5.QtWidgets import QMainWindow, QApplication, QTableWidgetItem
from interface import Ui_MainWindow

BANCO_ATUAL = "C:\\nethotel\POUSADA_SOL.FB"


class AppSaldosEstoque(QMainWindow):
    def __init__(self, parent=None):
        super(AppSaldosEstoque, self).__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.conectarSinais()

    def conectarSinais(self):
        self.ui.pushButtonBar.clicked.connect(self.saldoEstoqueBar)
        self.ui.pushButtonCozinha.clicked.connect(self.saldoEstoqueCozinha)
        self.ui.pushButtonImprimir.clicked.connect(self.imprimir)

    def saldoEstoqueBar(self):
        self.saldoEstoque(0)

    def saldoEstoqueCozinha(self):
        self.saldoEstoque(1)

    def saldoEstoque(self, subal):
        try:
            con = fdb.connect(
                host="172.16.1.11",
                database=BANCO_ATUAL,
                user="SYSDBA",
                password="masterkey",
            )
            cur = con.cursor()
            criterio = (
                """((I.GRUPO BETWEEN '02.01' AND '02.05') OR (I.GRUPO = '01.17'))"""
            )
            if subal == 1:
                criterio = """I.GRUPO BETWEEN '01.19' AND '01.20'"""
            consulta = """SELECT T.DESCRICAO, (T.SALDOINICIAL + T.ENTRADAS - T.SAIDAS) AS SALDO FROM (
SELECT I.GRUPO, I.CODIGO, I.DESCRICAO,
(SELECT COALESCE(SUM(E.SALDO),0) FROM TABE5 E
INNER JOIN TABITENS I2 ON I2.CODIGO = E.ITEM
WHERE E.SUBAL = 2 AND
EXTRACT(MONTH FROM E.DATA) = EXTRACT(MONTH FROM CURRENT_DATE) AND
EXTRACT(YEAR FROM E.DATA) = EXTRACT(YEAR FROM CURRENT_DATE) AND
I2.CODIGO = I.CODIGO) SALDOINICIAL,
(SELECT COALESCE(SUM(E.QTD),0) FROM TABE4 E
INNER JOIN TABITENS I2 ON I2.CODIGO = E.ITEM
WHERE E.DESTINO = 2 AND
EXTRACT(MONTH FROM E.DATA) = EXTRACT(MONTH FROM CURRENT_DATE) AND
EXTRACT(YEAR FROM E.DATA) = EXTRACT(YEAR FROM CURRENT_DATE) AND
I2.CODIGO = I.CODIGO) AS ENTRADAS,
(SELECT COALESCE(SUM(E.QTD),0) FROM TABE8 E
INNER JOIN TABITENS I2 ON I.CODIGO = E.ITEM
WHERE E.SUBAL = 2 AND
EXTRACT(MONTH FROM E.DATA) = EXTRACT(MONTH FROM CURRENT_DATE) AND
EXTRACT(YEAR FROM E.DATA) = EXTRACT(YEAR FROM CURRENT_DATE) AND
E.ESTORNO = 'N' AND I2.CODIGO = I.CODIGO) AS SAIDAS FROM TABITENS I
INNER JOIN TABCARD2 C ON C.ITEM = I.CODIGO
WHERE C.CHAVECARD1 = 1 AND I.ESTOQUE = 'S' AND %s
) T ORDER BY T.GRUPO, T.CODIGO""" % (
                criterio
            )
            cur.execute(consulta)
            self.resultados = []
            tabela = self.ui.tableWidgetSaldos
            for resultado in cur.fetchall():
                self.resultados.append(resultado)
            tabela.setColumnCount(2)
            tabela.setRowCount(len(self.resultados))
            tabela.setHorizontalHeaderLabels(["Item", "Qtde"])
            aux = 0
            for r in self.resultados:
                tabela.setItem(aux, 0, QTableWidgetItem(str(r[0])))
                tabela.setItem(aux, 1, QTableWidgetItem(str(r[1])))
                aux += 1
            tabela.resizeColumnsToContents()
            con.close()
        except Exception as e:
            with open("log.txt", "a") as f:
                print(str(e))
                print(traceback.format_exc())
                f.write(str(e))
                f.write(traceback.format_exc())

    def imprimir(self):
        try:
            filePrint = open("print.html", "w")
            filePrint.write(
                "<table><tr><td><font size='1'>{0}</font></td><td><font size='1'>{1}</font></td></tr>".format(
                    "Item", "Qtde"
                )
            )
            for r in self.resultados:
                filePrint.write(
                    "<tr><td><font size='1'>{0}</font></td><td><font size='1'>{1}</font></td></tr>".format(
                        str(r[0]), int(r[1])
                    )
                )
            filePrint.write("</table>")
            filePrint.close()
            os.startfile("print.html", "print")
        except Exception as e:
            with open("log.txt", "a") as f:
                print(str(e))
                print(traceback.format_exc())
                f.write(str(e))
                f.write(traceback.format_exc())


def main():
    app = QApplication([])
    ase = AppSaldosEstoque()
    ase.show()
    return app.exec_()


if __name__ == "__main__":
    main()
