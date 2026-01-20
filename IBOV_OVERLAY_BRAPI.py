# -*- coding: utf-8 -*-
"""
Created on Tue Jan 20 13:52:17 2026

# IBOV OVERLAY – SPYDER / PYQT5
# API: BRAPI.DEV (OFICIAL, FUNCIONAL)
# Atualização: 5 segundos (criar token)

conda install requests pyqt5 matplotlib

@author: k

"""
# ==========================================================
# IBOV OVERLAY – SPYDER / PYQT5
# API: BRAPI.DEV
# Atualização: 5 segundos
# ==========================================================

import sys
import requests
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QGridLayout, QDialog
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
import matplotlib.pyplot as plt

# ==============================
# CONFIGURAÇÕES GERAIS
# ==============================

TICKERS = [
    "VALE3","PETR4","ITUB4","BBDC4","ABEV3",
    "B3SA3","BBAS3","WEGE3","RENT3","SUZB3",
    "JBSS3","RADL3","EQTL3","LREN3","PRIO3",
    "CSNA3","GGBR4","ENGI11","VIVT3","CPFE3",
    "KLBN11","ELET3","ELET6","RAIL3","BRFS3",
    "CMIN3","MULT3"
]

API_BASE = "https://brapi.dev/api/quote/{}" # crie aqui
TIMEOUT = 5
UPDATE_INTERVAL = 5000  # ms

# ==============================
# FUNÇÕES DE API
# ==============================

def get_quotes():
    ativos = ",".join(TICKERS)
    r = requests.get(API_BASE.format(ativos), timeout=TIMEOUT)
    r.raise_for_status()
    return r.json().get("results", [])


def get_history(ticker):
    r = requests.get(
        API_BASE.format(ticker),
        params={"range": "5d", "interval": "5m"},
        timeout=TIMEOUT
    )
    r.raise_for_status()
    hist = r.json()["results"][0].get("historicalDataPrice", [])
    return [h["close"] for h in hist if h.get("close")]

# ==============================
# JANELA DE GRÁFICO
# ==============================

class ChartDialog(QDialog):
    def __init__(self, ticker):
        super().__init__()
        self.setWindowTitle(f"{ticker} – VWAP + Volatilidade")
        self.resize(760, 460)

        from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
        from matplotlib.figure import Figure
        import numpy as np

        prices = get_history(ticker)
        if not prices:
            return

        prices = np.array(prices)
        volumes = np.arange(1, len(prices) + 1)  # proxy de volume (API não fornece intraday volume confiável)

        # ===== VWAP =====
        vwap = np.cumsum(prices * volumes) / np.cumsum(volumes)

        # ===== VOLATILIDADE =====
        vol = np.std(prices)
        upper = vwap + vol
        lower = vwap - vol

        # ===== FIGURA EMBUTIDA (EVITA BUG DO SPYDER) =====
        fig = Figure(figsize=(7.5, 4.5))
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)

        # Fundo preto
        fig.patch.set_facecolor("black")
        ax.set_facecolor("black")
        ax.tick_params(colors="white")
        ax.spines["bottom"].set_color("white")
        ax.spines["top"].set_color("white")
        ax.spines["left"].set_color("white")
        ax.spines["right"].set_color("white")

        # Direção do VWAP
        vwap_color = "#00ff66" if vwap[-1] >= vwap[0] else "#ff3333"

        # Plots
        ax.plot(prices, label="Preço", color="white", linewidth=2)
        ax.plot(vwap, label="VWAP", color=vwap_color, linestyle="--", linewidth=2)
        ax.fill_between(range(len(prices)), lower, upper, color=vwap_color, alpha=0.18, label="Volatilidade")

        last = prices[-1]
        pct = ((last / prices[0]) - 1) * 100

        ax.set_title(
            f"{ticker} | Último: {last:.2f} | %Período: {pct:.2f}% | σ: {vol:.2f}",
            fontsize=10,
            color="white"
        )
        ax.grid(alpha=0.25, color="gray")
        ax.legend(facecolor="black", labelcolor="white")

        layout = QGridLayout()
        layout.addWidget(canvas, 0, 0)
        self.setLayout(layout)

        canvas.draw()

# ==============================
# OVERLAY PRINCIPAL
# ==============================

class Overlay(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("IBOV Overlay – BRAPI")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setWindowOpacity(0.4)
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(0,0,0,180);
                border-radius: 22px;
                color: white;
            }
        """)

        self.layout = QGridLayout()
        self.layout.setSpacing(8)
        self.setLayout(self.layout)

        self.labels = {}
        self.font = QFont("Arial", 9, QFont.Bold)

        self._build_cards()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_data)
        self.timer.start(UPDATE_INTERVAL)

        self.update_data()

    def _build_cards(self):
        for i, ticker in enumerate(TICKERS):
            lbl = QLabel(ticker)
            lbl.setFont(self.font)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(
                "padding:8px; background: rgba(255,255,255,40); border-radius:14px;"
            )
            lbl.mousePressEvent = lambda e, t=ticker: self.open_chart(t)
            self.layout.addWidget(lbl, i // 4, i % 4)
            self.labels[ticker] = lbl

    def update_data(self):
        try:
            data = get_quotes()
            for d in data:
                sym = d.get("symbol")
                price = d.get("regularMarketPrice")
                chg = d.get("regularMarketChangePercent", 0)

                lbl = self.labels.get(sym)
                if lbl and price is not None:
                    color = "#00ff99" if chg >= 0 else "#ff6b6b"
                    lbl.setText(f"{sym}\n{price:.2f}")
                    lbl.setStyleSheet(
                        f"padding:8px; background: rgba(255,255,255,40);"
                        f"border-radius:14px; color:{color};"
                    )
        except Exception as e:
            print("Erro ao atualizar dados:", e)

    def open_chart(self, ticker):
        dlg = ChartDialog(ticker)
        dlg.exec_()

# ==============================
# EXECUÇÃO (SPYDER)
# ==============================

if __name__ == "__main__":
    app = QApplication(sys.argv)
    overlay = Overlay()
    overlay.resize(440, 560)
    overlay.show()
    sys.exit(app.exec_())
