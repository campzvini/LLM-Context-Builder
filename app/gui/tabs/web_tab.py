"""
Web Tab Widget - V3.0
Aba Web isolada como componente autônomo
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QCheckBox, QSplitter,
    QProgressBar, QGroupBox, QTextEdit, QListWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtCore import pyqtSignal

from app.converters.web_converter import WebToMarkdownConverter
from app.gui.workers import WebScanWorker, WebCrawlWorker
from app.gui.dialogs import PageSelectionDialog
from app.converters.web_engine.logger import (
    log_button_click, log_worker_start, log_worker_finished,
    log_conversion_start, log_conversion_finished, log_spider_decision,
    log_scan_results
)
from app.utils.token_counter import TokenCounter
from pathlib import Path

# ===========================================
# 1. WEB TAB WIDGET
# ===========================================

class WebTab(QWidget):
    """Aba Web como componente isolado"""

    # Signals para comunicar com janela principal
    status_message_emitted = pyqtSignal(str)
    conversion_started = pyqtSignal()
    conversion_finished = pyqtSignal(bool, str)

    def __init__(self, parent=None):
        """Inicializa aba Web

        Args:
            parent: Janela pai (para acessar métodos da main window)
        """
        super().__init__(parent)
        self.parent_window = parent  # Reference to main window for file dialogs
        self.scan_worker = None
        self.crawl_worker = None

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Configura interface da aba Web com painel de controle profissional"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # === SEÇÃO 1: CONFIGURAÇÃO (TOPO) ===
        config_group = QGroupBox("Configuração da Missão")
        config_layout = QVBoxLayout(config_group)

        # Campo URL
        url_layout = QHBoxLayout()
        self.lbl_url = QLabel("URL:")
        self.txt_url = QLineEdit()
        self.txt_url.setPlaceholderText("https://exemplo.com/pagina")
        url_layout.addWidget(self.lbl_url)
        url_layout.addWidget(self.txt_url)

        # Campo Nome Arquivo e Pasta Destino
        file_layout = QHBoxLayout()
        self.lbl_filename = QLabel("Arquivo:")
        self.txt_filename = QLineEdit()
        self.txt_filename.setPlaceholderText("docs_v1.md")
        self.txt_filename.setText("output.md")
        self.lbl_folder = QLabel("Pasta:")
        self.txt_folder = QLineEdit()
        self.txt_folder.setPlaceholderText("Selecione pasta...")
        self.btn_folder = QPushButton("Selecionar")
        self.btn_folder.setFixedWidth(100)
        file_layout.addWidget(self.lbl_filename)
        file_layout.addWidget(self.txt_filename)
        file_layout.addWidget(self.lbl_folder)
        file_layout.addWidget(self.txt_folder)
        file_layout.addWidget(self.btn_folder)

        # Opções e Botão
        action_layout = QHBoxLayout()
        self.chk_spider = QCheckBox("🕷️ Spider Mode")
        self.chk_spider.setToolTip("Baixar página atual e todos os links internos da documentação")
        self.btn_convert_web = QPushButton("🚀 Iniciar Missão")
        self.btn_convert_web.setFixedHeight(35)
        self._apply_green_button_style(self.btn_convert_web)
        action_layout.addWidget(self.chk_spider)
        action_layout.addStretch()
        action_layout.addWidget(self.btn_convert_web)

        config_layout.addLayout(url_layout)
        config_layout.addLayout(file_layout)
        config_layout.addLayout(action_layout)

        # === SEÇÃO 2: DASHBOARD CENTRAL ===
        dashboard_group = QGroupBox("Progresso da Missão")
        dashboard_layout = QVBoxLayout(dashboard_group)

        # Splitter horizontal para dividir Links/Log
        self.splitter = QSplitter(Qt.Orientation.Horizontal)

        # Lista de Links (lado esquerdo)
        self.list_links = QListWidget()
        self.list_links.setMaximumWidth(300)  # Largura máxima
        self.list_links.addItem("🔍 Aguardando missão...")

        # Log de Execução (lado direito)
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #00ff00;
                font-family: Consolas;
                font-size: 12px;
                border: 1px solid #333;
            }
        """)

        # Adicionar ao splitter
        self.splitter.addWidget(self.list_links)
        self.splitter.addWidget(self.txt_log)
        self.splitter.setSizes([300, 500])  # Tamanhos iniciais

        dashboard_layout.addWidget(self.splitter)

        # === SEÇÃO 3: BARRA DE PROGRESSO (FUNDO) ===
        progress_group = QGroupBox("Status da Operação")
        progress_layout = QVBoxLayout(progress_group)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminado inicialmente
        self.progress_bar.setVisible(False)  # Escondido inicialmente

        self.lbl_status = QLabel("🎯 Pronto para missão")
        self.lbl_status.setStyleSheet("color: #666; font-weight: bold;")

        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.lbl_status)

        # === LAYOUT PRINCIPAL ===
        layout.addWidget(config_group)
        layout.addWidget(dashboard_group)
        layout.addWidget(progress_group)

    def _connect_signals(self):
        """Conecta sinais dos widgets"""
        self.btn_folder.clicked.connect(self._select_folder)
        self.btn_convert_web.clicked.connect(self._convert_web)

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
    # MÉTODOS DE ATUALIZAÇÃO DA INTERFACE
    # =======================================

    def add_log(self, message: str):
        """Adiciona mensagem ao log de execução"""
        timestamp = "[{:%H:%M:%S}]".format(__import__('datetime').datetime.now())
        self.txt_log.append(f"{timestamp} {message}")
        # Rola para o fim automaticamente
        scrollbar = self.txt_log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def add_link_to_list(self, url: str, title: str = "", status: str = "🔍"):
        """Adiciona link à lista de links encontrados"""
        item_text = f"{status} {title or 'Sem título'}"
        if url:
            item_text += f"\n   {url}"
        self.list_links.addItem(item_text)

    def add_error_log(self, message: str):
        """Adiciona mensagem de erro em vermelho no log"""
        timestamp = "[{:%H:%M:%S}]".format(__import__('datetime').datetime.now())
        # Usa HTML para cor vermelha
        self.txt_log.append(f'<span style="color:#ff5555;">{timestamp} 💥 {message}</span>')
        scrollbar = self.txt_log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def clear_dashboard(self):
        """Limpa o dashboard para nova missão"""
        self.list_links.clear()
        self.txt_log.clear()
        self.list_links.addItem("🔍 Aguardando missão...")
        self.progress_bar.setVisible(False)
        self.lbl_status.setText("🎯 Pronto para missão")

    # =======================================
    # HANDLERS DE EVENTOS
    # =======================================

    def _select_folder(self):
        """Seleciona pasta de destino via diálogo"""
        if not self.parent_window:
            return

        folder_path = self.parent_window.get_folder_dialog("Selecionar pasta de destino")

        if folder_path:
            self.txt_folder.setText(folder_path)

    def _convert_web(self):
        """Inicia fluxo de conversão Web"""
        url = self.txt_url.text().strip()
        filename = self.txt_filename.text().strip()
        folder = self.txt_folder.text().strip()
        spider_mode = self.chk_spider.isChecked()

        # Log do clique no botão
        log_button_click("Converter Web", {
            "url": url,
            "spider_mode": spider_mode,
            "arquivo_saida": filename,
            "pasta": folder
        })

        # Validações básicas
        if not url:
            self._show_error("Digite uma URL válida")
            return

        if not url.startswith(("http://", "https://")):
            self._show_error("URL deve começar com http:// ou https://")
            return

        if not filename:
            self._show_error("Digite o nome do arquivo de saída")
            return

        if not folder:
            self._show_error("Selecione a pasta de destino")
            return

        # Garantir extensão .md
        if not filename.endswith(".md"):
            filename += ".md"

        output_path = f"{folder}/{filename}"

        # Log da decisão do spider mode
        log_spider_decision(url, spider_mode)

        # Limpar dashboard para nova missão
        self.clear_dashboard()

        # Mostrar barra de progresso
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminado

        # Atualizar status
        self.lbl_status.setText("🚀 Missão iniciada...")
        self.lbl_status.setStyleSheet("color: blue; font-weight: bold;")

        # Emitir sinal de início
        self.conversion_started.emit()

        # Desabilitar controles
        self.btn_convert_web.setEnabled(False)
        self.btn_folder.setEnabled(False)

        if not spider_mode:
            # SINGLE PAGE MODE
            self.add_log("📄 MODO SINGLE PAGE: Baixando página única")
            self._run_single_page_web(url, output_path)
        else:
            # SPIDER MODE INTERATIVO
            self.add_log("🕷️ MODO SPIDER: Iniciando varredura inteligente")
            self._run_spider_mode_interactive(url, output_path)

    def _run_single_page_web(self, url: str, output_path: str):
        """Processa página única"""
        from app.gui.workers import WebConverterWorker

        # Criar worker para single page
        self.single_worker = WebConverterWorker(url, output_path, spider_mode=False)
        self.single_worker.progress.connect(self._on_worker_progress)
        self.single_worker.finished.connect(self._on_single_finished)
        self.single_worker.start()

        # Log de início
        log_worker_start("WebConverterWorker", {"url": url, "output": output_path})

    def _run_spider_mode_interactive(self, url: str, output_path: str):
        """Fluxo Spider com seleção interativa"""
        # Log de início do worker de scan
        log_worker_start("WebScanWorker", {"url": url, "output": output_path})

        # PASSO A: SCAN
        self.lbl_status.setText("Scanning: Identificando páginas...")
        self.btn_convert_web.setEnabled(False)
        self.btn_folder.setEnabled(False)

        self.scan_worker = WebScanWorker(url)
        self.scan_worker.progress.connect(self._on_worker_progress)
        self.scan_worker.scan_finished.connect(self._on_scan_finished)
        self.scan_worker.start()

    def _on_scan_finished(self, success: bool, pages: list[dict]):
        """Callback após Scan - Abre Dialog de Seleção"""
        # Log resultado do worker
        log_worker_finished("WebScanWorker", success, f"{len(pages)} páginas encontradas")

        if not success or not pages:
            self.add_log("❌ MISSÃO FALHADA: Nenhuma página encontrada")
            self._show_error("Nenhuma página encontrada")
            self._re_enable_controls()
            return

        # Atualizar lista de links na interface
        self.list_links.clear()
        self.add_log(f"📄 SCAN CONCLUÍDO: {len(pages)} páginas encontradas")

        for page in pages:
            self.add_link_to_list(page['url'], page['title'], "📄")

        # PASSO B: SELEÇÃO (DIALOG)
        self.lbl_status.setText(f"{len(pages)} páginas encontradas")

        dialog = PageSelectionDialog(pages, self.parent_window or self)
        result = dialog.exec()

        if result == dialog.DialogCode.Rejected:
            # Usuário cancelou
            self.lbl_status.setText("Cancelado")
            self._re_enable_controls()
            return

        # PASSO C: EXECUÇÃO (CRAWL)
        selected = dialog.get_selected_pages()

        # Configurar barra de progresso real
        self.progress_bar.setRange(0, len(selected))
        self.progress_bar.setValue(0)

        # Log das URLs selecionadas no terminal
        print(f"\n✅ PÁGINAS SELECIONADAS ({len(selected)}):")
        for i, page in enumerate(selected, 1):
            print(f"  {i}. {page['title']} - {page['url']}")
        print()

        # Log de início do worker de crawl
        log_worker_start("WebCrawlWorker", {
            "paginas_selecionadas": len(selected),
            "output": self._get_current_output_path()
        })

        self.lbl_status.setText(f"Crawling: {len(selected)} páginas selecionadas...")

        self.crawl_worker = WebCrawlWorker(selected, self._get_current_output_path())
        self.crawl_worker.progress.connect(self._on_worker_progress)
        self.crawl_worker.crawl_finished.connect(self._on_crawl_finished)
        self.crawl_worker.start()

    def _on_crawl_finished(self, success: bool, message: str):
        """Callback após Crawl"""
        # Log resultado do worker
        log_worker_finished("WebCrawlWorker", success, message)

        # Esconder barra de progresso
        self.progress_bar.setVisible(False)

        if success:
            # Contar tokens do arquivo gerado
            try:
                counter = TokenCounter()
                output_file = Path(self._get_current_output_path())
                if output_file.exists():
                    tokens = counter.count_tokens_in_file(output_file)
                    tokens_formatted = counter.format_token_count(tokens)
                    self.add_log(f"🔢 Total de Tokens Gerados: {tokens_formatted}")
                    self.lbl_status.setText(f"🎉 Sucesso! ({len(self.crawl_worker.selected_pages)} páginas | {tokens_formatted})")
                else:
                    self.lbl_status.setText("🎉 Missão concluída!")
            except Exception as e:
                self.lbl_status.setText("🎉 Missão concluída!")
            self.lbl_status.setStyleSheet("color: green; font-weight: bold;")
            self.add_log("✅ MISSÃO CONCLUÍDA COM SUCESSO!")
        else:
            self.add_error_log(f"ERRO CRÍTICO: {message}")
            self.lbl_status.setText("❌ Erro na missão")
            self.lbl_status.setStyleSheet("color: red; font-weight: bold;")

        self._re_enable_controls()

        # Emitir sinal de fim
        self.conversion_finished.emit(success, message)

    def _on_single_finished(self, success: bool, message: str):
        """Callback após conversão single page"""
        # Log resultado
        log_worker_finished("WebConverterWorker", success, message)

        self._re_enable_controls()

        if success:
            self.lbl_status.setText("Conversão concluída!")
        else:
            self.lbl_status.setText("Erro na conversão")

        # Emitir sinal de fim
        self.conversion_finished.emit(success, message)

    def _on_worker_progress(self, message: str):
        """Handler para progresso dos workers"""
        self.add_log(f"⚡ {message}")
        self.lbl_status.setText(message)
        self.status_message_emitted.emit(message)

        # Atualizar barra de progresso se detectar conclusão de página
        if "✓" in message and ("chars" in message or "CRAWL NOVO" in message):
            current_value = self.progress_bar.value()
            self.progress_bar.setValue(current_value + 1)

    def _re_enable_controls(self):
        """Reabilita controles da interface"""
        self.btn_convert_web.setEnabled(True)
        self.btn_folder.setEnabled(True)

    def _get_current_output_path(self) -> str:
        """Retorna o caminho de saída atual baseado nos campos da GUI"""
        filename = self.txt_filename.text().strip()
        folder = self.txt_folder.text().strip()

        if not filename.endswith(".md"):
            filename += ".md"

        return f"{folder}/{filename}"

    # =======================================
    # UTILITÁRIOS
    # =======================================

    def _show_error(self, message: str):
        """Exibe mensagem de erro"""
        if self.parent_window:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self.parent_window, "Erro", message)
        else:
            self.lbl_status.setText(f"Erro: {message}")

    # =======================================
    # GETTERS PARA JANELA PRINCIPAL
    # =======================================

    def get_url(self) -> str:
        """Retorna URL inserida"""
        return self.txt_url.text().strip()

    def get_filename(self) -> str:
        """Retorna nome do arquivo"""
        return self.txt_filename.text().strip()

    def get_folder(self) -> str:
        """Retorna pasta de destino"""
        return self.txt_folder.text().strip()

    def is_spider_mode(self) -> bool:
        """Retorna se Spider Mode está ativado"""
        return self.chk_spider.isChecked()

    def set_status_message(self, message: str):
        """Define mensagem de status"""
        self.lbl_status.setText(message)