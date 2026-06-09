from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QComboBox, QPushButton, QListWidget,
    QListWidgetItem, QFrame, QSplitter, QProgressBar,
    QScrollArea, QSizePolicy
)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import Qt, QUrl, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QColor

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from data.grafo import DEPARTAMENTOS, ARISTAS, construir_grafo
from algoritmo.dijkstra import dijkstra
from ui.mapa_folium import generar_mapa


class DijkstraWorker(QThread):
    """Hilo separado para ejecutar Dijkstra sin bloquear la UI."""
    terminado = pyqtSignal(list, float, list)  # ruta, distancia, pasos
    error     = pyqtSignal(str)

    def __init__(self, grafo, origen, destino):
        super().__init__()
        self.grafo   = grafo
        self.origen  = origen
        self.destino = destino

    def run(self):
        try:
            ruta, distancia, pasos = dijkstra(self.grafo, self.origen, self.destino)
            self.terminado.emit(ruta, distancia, pasos)
        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🗺️ Rutas Perú — Dijkstra con OpenStreetMap")
        self.grafo = construir_grafo()
        self.ruta_actual  = []
        self.pasos_actual = []
        self.worker = None
        self._mapa_tmp = None

        self._build_ui()
        self._cargar_mapa_inicial()

    # ──────────────────────────────────────────
    #  CONSTRUCCIÓN DE LA UI
    # ──────────────────────────────────────────
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)
        root.addWidget(splitter)

        # ── Panel izquierdo ──────────────────
        panel = QWidget()
        panel.setFixedWidth(300)
        panel.setStyleSheet("background:#1E2532;")
        pv = QVBoxLayout(panel)
        pv.setContentsMargins(16, 20, 16, 16)
        pv.setSpacing(14)

        # Título
        titulo = QLabel("🗺️ Rutas del Perú")
        titulo.setFont(QFont("Arial", 16, QFont.Bold))
        titulo.setStyleSheet("color:#FFFFFF;")
        pv.addWidget(titulo)

        subtitulo = QLabel("Algoritmo de Dijkstra")
        subtitulo.setStyleSheet("color:#8892A4;font-size:12px;")
        pv.addWidget(subtitulo)

        sep = QFrame(); sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color:#2E3848;"); pv.addWidget(sep)

        # Selectores
        pv.addWidget(self._label("Departamento Origen"))
        self.cb_origen = self._combo()
        pv.addWidget(self.cb_origen)

        pv.addWidget(self._label("Departamento Destino"))
        self.cb_destino = self._combo()
        self.cb_destino.setCurrentIndex(5)
        pv.addWidget(self.cb_destino)

        # Botón buscar
        self.btn_buscar = QPushButton("▶  Encontrar Ruta")
        self.btn_buscar.setFixedHeight(40)
        self.btn_buscar.setStyleSheet("""
            QPushButton {
                background:#1D9E75; color:white; border-radius:8px;
                font-size:14px; font-weight:bold;
            }
            QPushButton:hover   { background:#0F6E56; }
            QPushButton:pressed { background:#0B5443; }
            QPushButton:disabled{ background:#3A4455; color:#6B7585; }
        """)
        self.btn_buscar.clicked.connect(self._ejecutar_dijkstra)
        pv.addWidget(self.btn_buscar)

        # Botón limpiar
        self.btn_limpiar = QPushButton("✕  Limpiar")
        self.btn_limpiar.setFixedHeight(34)
        self.btn_limpiar.setStyleSheet("""
            QPushButton {
                background:#2E3848; color:#8892A4; border-radius:8px;
                font-size:12px;
            }
            QPushButton:hover { background:#3A4455; color:white; }
        """)
        self.btn_limpiar.clicked.connect(self._limpiar)
        pv.addWidget(self.btn_limpiar)

        sep2 = QFrame(); sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet("color:#2E3848;"); pv.addWidget(sep2)

        # Resultado
        self.lbl_resultado = QLabel("Selecciona origen y destino,\nluego presiona ▶ Encontrar Ruta")
        self.lbl_resultado.setStyleSheet("color:#8892A4; font-size:12px;")
        self.lbl_resultado.setWordWrap(True)
        pv.addWidget(self.lbl_resultado)

        self.lbl_distancia = QLabel("")
        self.lbl_distancia.setFont(QFont("Arial", 18, QFont.Bold))
        self.lbl_distancia.setStyleSheet("color:#1D9E75;")
        pv.addWidget(self.lbl_distancia)

        sep3 = QFrame(); sep3.setFrameShape(QFrame.HLine)
        sep3.setStyleSheet("color:#2E3848;"); pv.addWidget(sep3)

        # Lista de ruta
        pv.addWidget(self._label("Ruta encontrada"))
        self.lista_ruta = QListWidget()
        self.lista_ruta.setStyleSheet("""
            QListWidget { background:#161C27; border:none; border-radius:6px; color:white; font-size:12px; }
            QListWidget::item { padding:6px 10px; border-bottom:1px solid #2E3848; }
            QListWidget::item:selected { background:#1D9E75; }
        """)
        self.lista_ruta.setFixedHeight(160)
        pv.addWidget(self.lista_ruta)

        # Log de pasos
        pv.addWidget(self._label("Log de pasos Dijkstra"))
        self.lista_pasos = QListWidget()
        self.lista_pasos.setStyleSheet("""
            QListWidget { background:#161C27; border:none; border-radius:6px; color:#8892A4; font-size:11px; }
            QListWidget::item { padding:4px 10px; border-bottom:1px solid #1E2532; }
        """)
        pv.addWidget(self.lista_pasos)

        pv.addStretch()

        # ── Mapa (derecha) ───────────────────
        self.webview = QWebEngineView()
        self.webview.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        splitter.addWidget(panel)
        splitter.addWidget(self.webview)
        splitter.setSizes([300, 900])

    def _label(self, texto):
        lbl = QLabel(texto)
        lbl.setStyleSheet("color:#C0C8D8; font-size:11px; font-weight:bold;")
        return lbl

    def _combo(self):
        cb = QComboBox()
        cb.setFixedHeight(34)
        cb.setStyleSheet("""
            QComboBox {
                background:#2E3848; color:white; border-radius:6px;
                padding:4px 10px; font-size:13px; border:none;
            }
            QComboBox::drop-down { border:none; }
            QComboBox QAbstractItemView {
                background:#2E3848; color:white; selection-background-color:#1D9E75;
            }
        """)
        for dep in sorted(DEPARTAMENTOS.keys()):
            cb.addItem(dep)
        return cb

    # ──────────────────────────────────────────
    #  LÓGICA
    # ──────────────────────────────────────────
    def _cargar_mapa_inicial(self):
        html = generar_mapa(
            departamentos=DEPARTAMENTOS,
            aristas=ARISTAS
        )
        if html:
            self._mapa_tmp = html
            self.webview.load(QUrl.fromLocalFile(html))

    def _ejecutar_dijkstra(self):
        origen  = self.cb_origen.currentText()
        destino = self.cb_destino.currentText()

        if origen == destino:
            self.lbl_resultado.setText("⚠️ Origen y destino deben ser diferentes.")
            return

        self.btn_buscar.setEnabled(False)
        self.btn_buscar.setText("⏳ Calculando...")
        self.lista_ruta.clear()
        self.lista_pasos.clear()
        self.lbl_distancia.setText("")
        self.lbl_resultado.setText("Ejecutando Dijkstra...")

        self.worker = DijkstraWorker(self.grafo, origen, destino)
        self.worker.terminado.connect(self._on_dijkstra_done)
        self.worker.error.connect(self._on_dijkstra_error)
        self.worker.start()

    def _on_dijkstra_done(self, ruta, distancia, pasos):
        self.ruta_actual  = ruta
        self.pasos_actual = pasos
        self.btn_buscar.setEnabled(True)
        self.btn_buscar.setText("▶  Encontrar Ruta")

        if not ruta or distancia == float('inf'):
            self.lbl_resultado.setText("❌ No se encontró ruta entre estos departamentos.")
            return

        origen  = self.cb_origen.currentText()
        destino = self.cb_destino.currentText()

        # Panel resultado
        self.lbl_resultado.setText(f"📍 {origen}  →  {destino}")
        self.lbl_distancia.setText(f"{distancia:,.0f} km")

        # Lista de ruta
        self.lista_ruta.clear()
        for i, dep in enumerate(ruta):
            icono = "🟡" if dep == origen else ("🔴" if dep == destino else "●")
            item  = QListWidgetItem(f"  {icono}  {i+1}. {dep}")
            item.setForeground(QColor("#1D9E75") if dep in (origen, destino) else QColor("white"))
            self.lista_ruta.addItem(item)

        # Log pasos
        self.lista_pasos.clear()
        for i, (nodo, dist, _) in enumerate(pasos):
            item = QListWidgetItem(f"  Paso {i+1}: {nodo}  ({dist:,.0f} km)")
            self.lista_pasos.addItem(item)
        self.lista_pasos.scrollToBottom()

        # Actualizar mapa
        visitados_final = pasos[-1][2] if pasos else set()
        html = generar_mapa(
            ruta=ruta,
            visitados=visitados_final,
            origen=origen,
            destino=destino,
            departamentos=DEPARTAMENTOS,
            aristas=ARISTAS
        )
        if html:
            if self._mapa_tmp and os.path.exists(self._mapa_tmp):
                try: os.unlink(self._mapa_tmp)
                except: pass
            self._mapa_tmp = html
            self.webview.load(QUrl.fromLocalFile(html))

    def _on_dijkstra_error(self, msg):
        self.btn_buscar.setEnabled(True)
        self.btn_buscar.setText("▶  Encontrar Ruta")
        self.lbl_resultado.setText(f"❌ Error: {msg}")

    def _limpiar(self):
        self.lista_ruta.clear()
        self.lista_pasos.clear()
        self.lbl_resultado.setText("Selecciona origen y destino,\nluego presiona ▶ Encontrar Ruta")
        self.lbl_distancia.setText("")
        self._cargar_mapa_inicial()
