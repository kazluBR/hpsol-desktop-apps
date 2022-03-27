import firebirdsql as fdb
import traceback

from PyQt5.QtWidgets import QMainWindow, QApplication, QTableWidgetItem
from PyQt5.QtCore import QDate
from decouple import config
from interface import Ui_MainWindow


class AppAniversariantes(QMainWindow):
    def __init__(self, parent=None):
        super(AppAniversariantes, self).__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.conectarSinais()

    def conectarSinais(self):
        self.ui.dateEditAniversario.setDate(QDate.currentDate())
        self.ui.pushButtonPesquisar.clicked.connect(self.pesquisar)

    def pesquisar(self):
        data = self.ui.dateEditAniversario.date().toPyDate()
        tabela = self.ui.tableWidgetAniversariantes
        self.buscarAniversariantes(data, tabela)

    def buscarAniversariantes(self, data, tabela):
        try:
            con = fdb.connect(
                host=config("HOST"),
                database=config("BANCO_ATUAL"),
                user=config("USER"),
                password=config("PASSWORD"),
                charset="UTF8",
            )
            cur = con.cursor()
            consulta = """SELECT * FROM (
SELECT H.F_NOME, H.F_NASCIM, H.EMAIL, H.F_ULTIMA,
(SELECT SUM(IIF(R.F_ENTRADA = R.F_SAIDA, 1, DATEDIFF(DAY FROM R.F_ENTRADA TO R.F_SAIDA)))
    FROM TABRESER R WHERE R.F_HOSPEDE = H.F_COD AND R.F_STATUS = 'SAI') PERNOITES
FROM TABHOSPE H
WHERE EXTRACT(DAY FROM H.F_NASCIM) = %s AND
EXTRACT(MONTH FROM H.F_NASCIM) = %s AND
H.EMAIL IS NOT NULL
) T ORDER BY T.PERNOITES DESC""" % (
                data.strftime("%d"),
                data.strftime("%m"),
            )
            cur.execute(consulta)
            resultados = []
            for resultado in cur.fetchall():
                resultados.append(resultado)
            tabela.setColumnCount(5)
            tabela.setRowCount(len(resultados) + 1)
            tabela.setHorizontalHeaderLabels(
                [
                    "Hospede",
                    "Data Nascimento",
                    "Email",
                    "Ultima Hospedagem",
                    "Total Pernoites",
                ]
            )
            aux = 0
            for r in resultados:
                tabela.setItem(aux, 0, QTableWidgetItem(r[0]))
                tabela.setItem(aux, 1, QTableWidgetItem(str(r[1].strftime("%d/%m/%Y"))))
                tabela.setItem(aux, 2, QTableWidgetItem(r[2]))
                if r[3] is None:
                    tabela.setItem(aux, 3, QTableWidgetItem("-"))
                else:
                    tabela.setItem(
                        aux, 3, QTableWidgetItem(str(r[3].strftime("%d/%m/%Y")))
                    )
                if r[4] is None:
                    tabela.setItem(aux, 4, QTableWidgetItem("-"))
                else:
                    tabela.setItem(aux, 4, QTableWidgetItem(str(r[4])))
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
    aa = AppAniversariantes()
    aa.show()
    return app.exec_()


if __name__ == "__main__":
    main()
