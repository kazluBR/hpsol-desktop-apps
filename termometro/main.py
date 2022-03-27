from __future__ import division
import firebirdsql as fdb
import datetime as dt
import traceback

from PyQt5.QtWidgets import QMainWindow, QApplication
from decouple import config
from interface import Ui_MainWindow


class Termometro(QMainWindow):
    def __init__(self, parent=None):
        super(Termometro, self).__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.conectarSinais()
        self.operador = None
        self.parametro = None
        self.consultaReceita = """SELECT SUM(T.VALOR) TOTAL FROM (
    SELECT (L.F_VALOR - L.F_DESCONTO) VALOR, R.F_SAIDA DATA, 0 PREVISAO
        FROM TABLANCA L
        INNER JOIN TABRESER R ON R.F_RES = L.F_RES
        INNER JOIN TABHISTO H ON H.F_COD = L.F_CODHISTOR
        WHERE ((H.F_TIPO = 'C' AND H.RECEITA = 'S' AND H.TIPOREC <= 2) OR (H.F_COD = 109))
        AND L.F_ESTORNO <> 'S' AND L.F_ESTORNO <> 'P'
        AND (R.F_STATUS = 'SAI' OR R.F_STATUS = 'PAR' OR R.F_STATUS = 'PEN')
    UNION ALL
    SELECT IIF(TS.FLUT = 0, CAST(((TS.F_DIARIA - (TS.F_DIARIA * TS.DESCONTO)) * TS.DIAS) AS DECIMAL(10,2)),
        (SELECT SUM(R2.VALOR) FROM TABRES1 R2 WHERE R2.RES = TS.F_RES)) VALOR, TS.F_SAIDA DATA, 1 PREVISAO FROM (
            SELECT R.F_RES, IIF(R.F_ENTRADA = R.F_SAIDA, 1, DATEDIFF(DAY FROM R.F_ENTRADA TO R.F_SAIDA)) DIAS,
            R.F_DIARIA, CAST(R.F_DESCONTO / 100 AS NUMERIC(5,4)) DESCONTO, R.F_SAIDA,
            (SELECT COUNT(*) FROM TABRES1 R2 WHERE R2.RES = R.F_RES) FLUT
            FROM TABRESER R
            WHERE (R.F_STATUS = 'CON' OR R.F_STATUS = 'HOS')
            AND R.F_APTO IS NOT NULL AND R.F_DIARIA > 0
        ) TS
    UNION ALL
    SELECT E.TOTAL VALOR, E.DATA, 0 PREVISAO
        FROM TABE8 E
        WHERE E.RESERVA = 0 AND E.TOTAL > 0 AND E.TIPOLANCTO = 0
    UNION ALL
    SELECT R.VALOR, R.EMISSAO DATA, 0 PREVISAO
        FROM TABREC R
        WHERE (R.STATUS = 'F' OR R.STATUS = 'A') AND R.GRUPO = '1.1.06.03'
    UNION ALL
    SELECT M.VALOR, M.DATA, 0 PREVISAO
        FROM TABMOVB M
        WHERE M.GRUPO = '1.1.07.05'
    ) T WHERE EXTRACT(MONTH FROM T.DATA) %s AND EXTRACT(YEAR FROM T.DATA) = 2019 AND T.PREVISAO < %s"""
        self.consultaDespesa = """SELECT SUM(T.VALOR) TOTAL FROM (
    SELECT P.DESCRICAO, P.VALOR, G.CODGRUPO, P.EMISSAO
        FROM TABPAG P
        INNER JOIN TABGRUPF G ON G.CODGRUPO = P.GRUPO
        WHERE (P.STATUS = 'F' OR P.STATUS = 'A')
    UNION ALL
    SELECT R.DESCRICAO, R.VALCOM VALOR, G.CODGRUPO, R.EMISSAO
        FROM TABREC R
        INNER JOIN TABEMPR E ON E.F_COD = R.CLIENTE
        INNER JOIN TABGRUPF G ON G.CODGRUPO = '1.2.08'
        WHERE (R.STATUS = 'F' OR R.STATUS = 'A') AND R.VALCOM > 0
    UNION ALL
    SELECT M.OBS DESCRICAO, M.VALOR, G.CODGRUPO, CAST(M.COMPETENCIA AS DATE) EMISSAO
        FROM TABMOVB M
        INNER JOIN TABGRUPF G ON G.CODGRUPO = M.GRUPO
        WHERE M.ORIGEM = 'B' AND M.TIPO = 'D' AND M.GRUPO <> '1.2.09.05' AND M.GRUPO NOT LIKE '1.1.07%%'
) T WHERE EXTRACT(MONTH FROM T.EMISSAO) %s AND EXTRACT(YEAR FROM T.EMISSAO) = 2019 AND
T.DESCRICAO NOT CONTAINING '*' AND T.CODGRUPO NOT LIKE '1.2.11%%'"""

    def conectarSinais(self):
        self.ui.pushButtonJAN.clicked.connect(self.carregarJAN)
        self.ui.pushButtonFEV.clicked.connect(self.carregarFEV)
        self.ui.pushButtonMAR.clicked.connect(self.carregarMAR)
        self.ui.pushButtonABR.clicked.connect(self.carregarABR)
        self.ui.pushButtonMAI.clicked.connect(self.carregarMAI)
        self.ui.pushButtonJUN.clicked.connect(self.carregarJUN)
        self.ui.pushButtonJUL.clicked.connect(self.carregarJUL)
        self.ui.pushButtonAGO.clicked.connect(self.carregarAGO)
        self.ui.pushButtonSET.clicked.connect(self.carregarSET)
        self.ui.pushButtonOUT.clicked.connect(self.carregarOUT)
        self.ui.pushButtonNOV.clicked.connect(self.carregarNOV)
        self.ui.pushButtonDEZ.clicked.connect(self.carregarDEZ)
        self.ui.pushButtonSemestre1.clicked.connect(self.carregarSemestre1)
        self.ui.pushButtonSemestre2.clicked.connect(self.carregarSemestre2)
        self.ui.pushButtonAno.clicked.connect(self.carregarAno)
        self.ui.checkBoxPrevisao.stateChanged.connect(self.atualizarBarraProgresso)

    def carregarJAN(self):
        self.operador = "= "
        self.parametro = "1"
        self.metaRec = 500000
        self.limiteDes = 300000
        self.carregarBarraProgresso()
        self.ui.label.setText("JAN")

    def carregarFEV(self):
        self.operador = "= "
        self.parametro = "2"
        self.metaRec = 200000
        self.limiteDes = 200000
        self.carregarBarraProgresso()
        self.ui.label.setText("FEV")

    def carregarMAR(self):
        self.operador = "= "
        self.parametro = "3"
        self.metaRec = 300000
        self.limiteDes = 200000
        self.carregarBarraProgresso()
        self.ui.label.setText("MAR")

    def carregarABR(self):
        self.operador = "= "
        self.parametro = "4"
        self.metaRec = 200000
        self.limiteDes = 200000
        self.carregarBarraProgresso()
        self.ui.label.setText("ABR")

    def carregarMAI(self):
        self.operador = "= "
        self.parametro = "5"
        self.metaRec = 200000
        self.limiteDes = 200000
        self.carregarBarraProgresso()
        self.ui.label.setText("MAI")

    def carregarJUN(self):
        self.operador = "= "
        self.parametro = "6"
        self.metaRec = 200000
        self.limiteDes = 200000
        self.carregarBarraProgresso()
        self.ui.label.setText("JUN")

    def carregarJUL(self):
        self.operador = "= "
        self.parametro = "7"
        self.metaRec = 300000
        self.limiteDes = 200000
        self.carregarBarraProgresso()
        self.ui.label.setText("JUL")

    def carregarAGO(self):
        self.operador = "= "
        self.parametro = "8"
        self.metaRec = 220000
        self.limiteDes = 200000
        self.carregarBarraProgresso()
        self.ui.label.setText("AGO")

    def carregarSET(self):
        self.operador = "= "
        self.parametro = "9"
        self.metaRec = 220000
        self.limiteDes = 200000
        self.carregarBarraProgresso()
        self.ui.label.setText("SET")

    def carregarOUT(self):
        self.operador = "= "
        self.parametro = "10"
        self.metaRec = 220000
        self.limiteDes = 200000
        self.carregarBarraProgresso()
        self.ui.label.setText("OUT")

    def carregarNOV(self):
        self.operador = "= "
        self.parametro = "11"
        self.metaRec = 220000
        self.limiteDes = 200000
        self.carregarBarraProgresso()
        self.ui.label.setText("NOV")

    def carregarDEZ(self):
        self.operador = "= "
        self.parametro = "12"
        self.metaRec = 220000
        self.limiteDes = 200000
        self.carregarBarraProgresso()
        self.ui.label.setText("DEZ")

    def carregarSemestre1(self):
        self.operador = "< "
        self.parametro = "7"
        self.metaRec = 1600000
        self.limiteDes = 1300000
        self.carregarBarraProgresso()
        self.ui.label.setText("SEMESTRE 1")

    def carregarSemestre2(self):
        self.operador = "> "
        self.parametro = "6"
        self.metaRec = 1400000
        self.limiteDes = 1200000
        self.carregarBarraProgresso()
        self.ui.label.setText("SEMESTRE 2")

    def carregarAno(self):
        self.operador = "< "
        self.parametro = "13"
        self.metaRec = 3000000
        self.limiteDes = 2500000
        self.carregarBarraProgresso()
        self.ui.label.setText("ANO")

    def atualizarBarraProgresso(self):
        if self.operador is not None:
            self.carregarBarraProgresso()

    def carregarBarraProgresso(self):
        try:
            con = fdb.connect(
                host=config("HOST"),
                database=config("BANCO_ATUAL"),
                user=config("USER"),
                password=config("PASSWORD"),
                charset="UTF8",
            )
            cur = con.cursor()
            previsao = "1"
            if self.ui.checkBoxPrevisao.isChecked():
                previsao = "2"
            consulta_final = self.consultaReceita % (
                self.operador + self.parametro,
                previsao,
            )
            cur.execute(consulta_final)
            totalRec = cur.fetchone()[0]
            if totalRec is None:
                totalRec = 0
            percentualRec = int((totalRec / self.metaRec) * 100)
            self.ui.label_2.setText(str(percentualRec) + " %")
            self.ui.progressBar.setValue(percentualRec)
            template_css = """QProgressBar::chunk { background: %s; }"""
            if percentualRec > 100:
                css = template_css % "green"
            elif percentualRec > 50:
                css = template_css % "yellow"
            else:
                css = template_css % "red"
            self.ui.progressBar.setStyleSheet(css)
            consulta_final = self.consultaDespesa % (self.operador + self.parametro)
            cur.execute(consulta_final)
            totalDes = cur.fetchone()[0]
            if totalDes is None:
                totalDes = 0
            percentualDes = int((totalDes / self.limiteDes) * 100)
            self.ui.label_3.setText(str(percentualDes) + " %")
            self.ui.progressBar_2.setValue(percentualDes)
            if percentualDes > 100:
                css = template_css % "red"
            elif percentualDes > 50:
                css = template_css % "yellow"
            else:
                css = template_css % "green"
            self.ui.progressBar_2.setStyleSheet(css)
            percentualLucro = int(
                ((totalRec - totalDes - (self.metaRec - self.limiteDes)) / 100000) * 100
            )
            self.ui.label_4.setText(str(percentualLucro) + " %")
            self.ui.progressBar_3.setValue(percentualLucro)
            if percentualLucro > 0:
                css = template_css % "green"
            else:
                css = template_css % "red"
            self.ui.progressBar_3.setStyleSheet(css)
            con.close()
        except Exception as e:
            with open("log.txt", "a") as f:
                print(str(e))
                print(traceback.format_exc())
                f.write(str(e))
                f.write(traceback.format_exc())


def main():
    app = QApplication([])
    t = Termometro()
    t.show()
    return app.exec_()


if __name__ == "__main__":
    main()
