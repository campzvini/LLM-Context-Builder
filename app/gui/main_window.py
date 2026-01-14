"""
╔══════════════════════════════════════════════════════════════════════════════╗
║ Pdf2md Converter V3.0 - Main Window Module                                ║
║ Janela principal PyQt6 - Container para widgets modulares                 ║
╚══════════════════════════════════════════════════════════════════════════════╝
Taller Dev - 2026
VAI CORINTHIANS!!
═══════════════════════════════════════════════════════════════════════════════
"""

# ===========================================
# 1. IMPORTS
# ===========================================

import sys
from PyQt6.QtWidgets import (
    QMainWindow, QVBoxLayout, QWidget, QTabWidget,
    QLabel, QStatusBar
)
from PyQt6.QtCore import Qt

# Importações dos widgets modulares
from app.gui.tabs.pdf_tab import PdfTab
from app.gui.tabs.web_tab import WebTab
from app.converters.web_engine.logger import log_app_startup, log_app_shutdown_by_user

# ===========================================
# 2. CLASSE JANELA PRINCIPAL
# ===========================================

class Pdf2mdWindow(QMainWindow):
    """Janela principal - Container para widgets das abas"""

    def __init__(self):
        """Inicializa janela principal"""
        super().__init__()

        # Configurações básicas da janela
        self.setWindowTitle("LLM Context Builder V3.0")
        self.setGeometry(100, 100, 900, 700)
        self.setMinimumSize(800, 600)

        # Inicializar componentes
        self.pdf_tab = None
        self.web_tab = None

        # Log de inicialização da GUI
        log_app_startup()

        # Configurar interface
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Configura interface principal"""
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout principal
        layout = QVBoxLayout(central_widget)

        # Título
        title = QLabel("LLM Context Builder")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Tab Widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # Instanciar abas modulares
        self.pdf_tab = PdfTab(self)
        self.web_tab = WebTab(self)

        # Adicionar abas
        self.tab_widget.addTab(self.pdf_tab, "📄 PDF")
        self.tab_widget.addTab(self.web_tab, "🌐 Web")

        # Status Bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Pronto")

        # Contador de tokens na status bar
        self.lbl_token_count = QLabel("Tokens: --")
        self.lbl_token_count.setStyleSheet("color: #666; font-size: 10px;")
        self.status_bar.addWidget(self.lbl_token_count)

    def _connect_signals(self):
        """Conecta sinais das abas à janela principal"""
        if self.pdf_tab:
            self.pdf_tab.status_message_emitted.connect(self._update_status)
            self.pdf_tab.conversion_started.connect(self._on_conversion_started)
            self.pdf_tab.conversion_finished.connect(self._on_conversion_finished)

        if self.web_tab:
            self.web_tab.status_message_emitted.connect(self._update_status)
            self.web_tab.conversion_started.connect(self._on_conversion_started)
            self.web_tab.conversion_finished.connect(self._on_conversion_finished)

    # =======================================
    # HANDLERS DE SINAIS DAS ABAS
    # =======================================

    def _update_status(self, message: str):
        """Atualiza status bar com mensagens das abas"""
        self.status_bar.showMessage(message)

        # Se for mensagem de tokens, atualizar contador
        if message.startswith("Tokens"):
            self.lbl_token_count.setText(message)

    def _on_conversion_started(self):
        """Handler quando conversão inicia"""
        self.status_bar.showMessage("🔄 Conversão em andamento...")

    def _on_conversion_finished(self, success: bool, message: str):
        """Handler quando conversão finaliza"""
        if success:
            self.status_bar.showMessage("✅ Conversão concluída")
            # Mostrar resultado em dialog
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self, "Sucesso", message)
        else:
            self.status_bar.showMessage("❌ Erro na conversão")
            # Mostrar erro em dialog
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Erro", message)

    # =======================================
    # MÉTODOS UTILITÁRIOS PARA AS ABAS
    # =======================================

    def get_file_dialog(self, filter_str: str, title: str) -> tuple[str, str]:
        """Abre diálogo para seleção de arquivo (usado pelas abas)"""
        from PyQt6.QtWidgets import QFileDialog
        return QFileDialog.getOpenFileName(self, title, "", filter_str)

    def get_save_file_dialog(self, filter_str: str, title: str) -> tuple[str, str]:
        """Abre diálogo para salvar arquivo (usado pelas abas)"""
        from PyQt6.QtWidgets import QFileDialog
        return QFileDialog.getSaveFileName(self, title, "", filter_str)

    def get_folder_dialog(self, title: str) -> str:
        """Abre diálogo para seleção de pasta (usado pelas abas)"""
        from PyQt6.QtWidgets import QFileDialog
        folder = QFileDialog.getExistingDirectory(self, title)
        return folder

    # =======================================
    # EVENTOS DA JANELA
    # =======================================

    def closeEvent(self, event):
        """Evento chamado quando a aplicação é fechada pelo usuário"""
        log_app_shutdown_by_user()
        event.accept()