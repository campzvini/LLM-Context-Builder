"""
PDF Tab Widget - V3.0
Aba PDF isolada como componente autônomo
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QMainWindow
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap

from app.gui.utils import resource_path
from app.gui.workers import ConverterWorker
from app.converters.web_engine.logger import (
    log_button_click, log_worker_start, log_worker_finished,
    log_conversion_start, log_conversion_finished, log_file_operation
)

# ===========================================
# 1. PDF TAB WIDGET
# ===========================================

class PdfTab(QWidget):
    """Aba PDF como componente isolado"""

    # Signals para comunicar com janela principal
    status_message_emitted = pyqtSignal(str)
    conversion_started = pyqtSignal()
    conversion_finished = pyqtSignal(bool, str)

    def __init__(self, parent=None):
        """Inicializa aba PDF

        Args:
            parent: Janela pai (para acessar métodos da main window)
        """
        super().__init__(parent)
        self.parent_window = parent  # Reference to main window for file dialogs
        self.worker = None

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Configura interface da aba PDF"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Campo PDF
        pdf_file_layout = QHBoxLayout()
        self.lbl_pdf = QLabel("Arquivo PDF:")
        self.txt_pdf = QLineEdit()
        self.txt_pdf.setPlaceholderText("Selecione um arquivo PDF...")
        self.btn_pdf = QPushButton("Selecionar")
        self.btn_pdf.setFixedWidth(100)
        pdf_file_layout.addWidget(self.lbl_pdf)
        pdf_file_layout.addWidget(self.txt_pdf)
        pdf_file_layout.addWidget(self.btn_pdf)

        # Campo Destino
        output_layout = QHBoxLayout()
        self.lbl_output = QLabel("Destino .md:")
        self.txt_output = QLineEdit()
        self.txt_output.setPlaceholderText("Selecione destino ou deixe vazio para automático...")
        self.btn_output = QPushButton("Selecionar")
        self.btn_output.setFixedWidth(100)
        output_layout.addWidget(self.lbl_output)
        output_layout.addWidget(self.txt_output)
        output_layout.addWidget(self.btn_output)

        # Botão Converter
        self.btn_convert = QPushButton("Converter PDF")
        self.btn_convert.setFixedHeight(40)
        self.btn_convert.setEnabled(False)
        self._apply_green_button_style(self.btn_convert)

        # Área de Drop com Hitbox
        drop_container = QWidget()
        drop_container.setStyleSheet("""
            QWidget#drop_container {
                background-color: #f5f5f5;
                border: 3px dashed #aaa;
                border-radius: 12px;
                padding: 20px;
            }
        """)
        drop_container.setObjectName("drop_container")

        drop_container_layout = QVBoxLayout(drop_container)

        self.lbl_drop_icon = QLabel()
        self.lbl_drop_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        drop_pixmap = QPixmap(resource_path("imagens/drop-file.png"))
        self.lbl_drop_icon.setPixmap(drop_pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio))

        self.lbl_drop_text = QLabel("Arraste e solte um PDF aqui")
        self.lbl_drop_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_drop_text.setStyleSheet("color: #666; font-style: italic; font-size: 12px;")

        drop_container_layout.addWidget(self.lbl_drop_icon)
        drop_container_layout.addWidget(self.lbl_drop_text)

        drop_wrapper_layout = QHBoxLayout()
        drop_wrapper_layout.addWidget(drop_container)

        # Status PDF
        self.lbl_status = QLabel("Pronto")
        self.lbl_status.setStyleSheet("color: gray;")

        # Adicionar ao layout
        layout.addLayout(pdf_file_layout)
        layout.addLayout(output_layout)
        layout.addWidget(self.btn_convert)
        layout.addStretch()
        layout.addLayout(drop_wrapper_layout)
        layout.addWidget(self.lbl_status)

    def _connect_signals(self):
        """Conecta sinais dos widgets"""
        self.btn_pdf.clicked.connect(self._select_pdf_file)
        self.btn_output.clicked.connect(self._select_output_file)
        self.btn_convert.clicked.connect(self._convert_pdf)

        # Drag & Drop
        self.setAcceptDrops(True)

    def _apply_green_button_style(self, button: QPushButton):
        """Aplica estilo verde aos botões de conversão"""
        button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-weight: bold;
                font-size: 12px;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
            QPushButton:disabled {
                background-color: #6c757d;
                color: #ffffff;
            }
        """)

    # =======================================
    # HANDLERS DE EVENTOS
    # =======================================

    def _select_pdf_file(self):
        """Seleciona arquivo PDF via diálogo"""
        if not self.parent_window:
            return

        file_path, _ = self.parent_window.get_file_dialog("PDF Files (*.pdf)", "Selecionar PDF")

        if file_path:
            self.txt_pdf.setText(file_path)

            # Sugerir destino automático
            from pathlib import Path
            pdf_path = Path(file_path)
            suggested = pdf_path.parent / f"{pdf_path.stem}.md"
            self.txt_output.setText(str(suggested))

            # Contar tokens se disponível
            try:
                from app.utils.token_counter import count_pdf_tokens
                token_count = count_pdf_tokens(pdf_path)
                from app.utils.token_counter import TokenCounter
                token_counter = TokenCounter()
                token_display = token_counter.format_token_count(token_count)
                self.status_message_emitted.emit(f"Tokens estimados: {token_display}")
            except:
                pass

            self.btn_convert.setEnabled(True)
            self.lbl_status.setText("PDF selecionado")

    def _select_output_file(self):
        """Seleciona arquivo de saída via diálogo"""
        if not self.parent_window:
            return

        file_path, _ = self.parent_window.get_save_file_dialog("Markdown Files (*.md)", "Salvar como")

        if file_path:
            self.txt_output.setText(file_path)

    def _convert_pdf(self):
        """Inicia conversão PDF"""
        pdf_path = self.txt_pdf.text().strip()
        output_path = self.txt_output.text().strip()

        # Log do clique
        log_button_click("Converter PDF", {
            "arquivo_pdf": pdf_path,
            "arquivo_saida": output_path
        })

        # Validações
        if not pdf_path:
            self._show_error("Selecione um arquivo PDF")
            return

        if not output_path:
            self._show_error("Digite o nome do arquivo de saída")
            return

        # Garantir extensão .md
        if not output_path.endswith(".md"):
            output_path += ".md"

        # Log de início
        log_conversion_start("PDF", pdf_path, output_path)

        # Emitir sinal de início
        self.conversion_started.emit()

        # Desabilitar controles
        self.btn_convert.setEnabled(False)
        self.btn_pdf.setEnabled(False)

        # Criar e iniciar worker
        self.worker = ConverterWorker(pdf_path, output_path)
        self.worker.progress.connect(self._on_worker_progress)
        self.worker.finished.connect(self._on_worker_finished)
        self.worker.start()

        # Log de início do worker
        log_worker_start("ConverterWorker", {
            "pdf": pdf_path,
            "output": output_path
        })

    def _on_worker_progress(self, message: str):
        """Handler para progresso do worker"""
        self.lbl_status.setText(message)
        self.status_message_emitted.emit(message)

    def _on_worker_finished(self, success: bool, message: str):
        """Handler para finalização do worker"""
        # Reabilitar controles
        self.btn_convert.setEnabled(True)
        self.btn_pdf.setEnabled(True)

        # Log resultado
        log_worker_finished("ConverterWorker", success, message)

        if success:
            self.lbl_status.setText("Conversão concluída!")
            log_file_operation("CRIADO", self.txt_output.text(), True)
        else:
            self.lbl_status.setText("Erro na conversão")

        # Log conversão finalizada
        log_conversion_finished("PDF", success, message)

        # Emitir sinal de fim
        self.conversion_finished.emit(success, message)

    # =======================================
    # DRAG & DROP
    # =======================================

    def dragEnterEvent(self, event):
        """Evento de entrada de drag"""
        if event.mimeData().hasUrls():
            # Verificar se tem PDF
            for url in event.mimeData().urls():
                if url.toLocalFile().endswith('.pdf'):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event):
        """Evento de drop de arquivo"""
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.endswith('.pdf'):
                self.txt_pdf.setText(file_path)

                # Sugerir destino automático
                from pathlib import Path
                pdf_path = Path(file_path)
                suggested = pdf_path.parent / f"{pdf_path.stem}.md"
                self.txt_output.setText(str(suggested))

                self.btn_convert.setEnabled(True)
                self.lbl_status.setText("PDF carregado via drag & drop")

                # Contar tokens
                try:
                    from app.utils.token_counter import count_pdf_tokens, TokenCounter
                    token_count = count_pdf_tokens(pdf_path)
                    token_counter = TokenCounter()
                    token_display = token_counter.format_token_count(token_count)
                    self.status_message_emitted.emit(f"Tokens estimados: {token_display}")
                except:
                    pass

                break

    # =======================================
    # UTILITÁRIOS
    # =======================================

    def _show_error(self, message: str):
        """Exibe mensagem de erro"""
        if self.parent_window:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Erro", message)
        else:
            self.lbl_status.setText(f"Erro: {message}")

    # =======================================
    # GETTERS PARA JANELA PRINCIPAL
    # =======================================

    def get_pdf_path(self) -> str:
        """Retorna caminho do PDF selecionado"""
        return self.txt_pdf.text().strip()

    def get_output_path(self) -> str:
        """Retorna caminho de saída"""
        return self.txt_output.text().strip()

    def set_status_message(self, message: str):
        """Define mensagem de status"""
        self.lbl_status.setText(message)