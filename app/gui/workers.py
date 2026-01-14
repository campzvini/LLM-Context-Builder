"""
GUI Workers Module - V3.0
Workers Qt para operações assíncronas
"""

import asyncio
from PyQt6.QtCore import QThread, pyqtSignal

from app.converters.pdf_converter import PdfToMarkdownConverter
from app.converters.web_converter import WebToMarkdownConverter
from app.converters.web_engine.logger import (
    log_worker_start, log_worker_finished,
    log_conversion_start, log_conversion_finished, logger
)

# ===========================================
# 1. WORKER PDF
# ===========================================

class ConverterWorker(QThread):
    """Executa conversão PDF em thread separada"""

    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, pdf_path: str, output_path: str):
        """Inicializa worker

        Args:
            pdf_path: Caminho do PDF
            output_path: Caminho de destino do .md
        """
        super().__init__()
        self.converter = PdfToMarkdownConverter()
        self.pdf_path = pdf_path
        self.output_path = output_path

    def run(self):
        """Executa conversão e emite signals"""
        try:
            self.progress.emit("Iniciando conversão PDF...")
            success, message = self.converter.process(self.pdf_path, self.output_path)
            self.finished.emit(success, message)

        except Exception as e:
            logger.exception(f"Erro no ConverterWorker: {e}")
            self.finished.emit(False, f"Erro na thread: {e}")

# ===========================================
# 2. WORKER WEB LEGACY
# ===========================================

class WebConverterWorker(QThread):
    """Executa conversão Web em thread separada"""

    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, url: str, output_path: str, spider_mode: bool = False):
        """Inicializa worker web

        Args:
            url: URL da página web
            output_path: Caminho de destino do .md
            spider_mode: Se True, ativa modo spider
        """
        super().__init__()
        self.converter = WebToMarkdownConverter()
        self.url = url
        self.output_path = output_path
        self.spider_mode = spider_mode

    def run(self):
        """Executa conversão web e emite signals"""
        try:
            self.progress.emit("Iniciando crawler...")

            if self.spider_mode:
                self.progress.emit("Modo Spider ativado: Mapeando links...")
                success, message = self.converter.process_spider(self.url, self.output_path)
            else:
                self.progress.emit("Carregando página web...")
                success, message = self.converter.process_web(self.url, self.output_path)

            self.finished.emit(success, message)

        except Exception as e:
            logger.exception(f"Erro no WebConverterWorker: {e}")
            self.finished.emit(False, f"Erro na thread: {e}")

# ===========================================
# 3. WORKER WEB SCAN (NOVO V3.0)
# ===========================================

class WebScanWorker(QThread):
    """PASSO A: Worker que apenas SCANEIA páginas"""

    progress = pyqtSignal(str)
    scan_finished = pyqtSignal(bool, list)  # (sucesso, lista_de_paginas)

    def __init__(self, url: str):
        """Inicializa worker de scan

        Args:
            url: URL da seed para scan
        """
        super().__init__()
        self.converter = WebToMarkdownConverter()
        self.url = url

    def run(self):
        """Executa scan e emite signals"""
        try:
            self.progress.emit("Detectando tipo de renderização...")
            success, pages = asyncio.run(self.converter.scan_pages(self.url))
            self.scan_finished.emit(success, pages)
        except Exception as e:
            logger.exception(f"Erro no WebScanWorker: {e}")
            self.scan_finished.emit(False, [])

# ===========================================
# 4. WORKER WEB CRAWL (NOVO V3.0)
# ===========================================

class WebCrawlWorker(QThread):
    """PASSO C: Worker que CRAWLA páginas selecionadas"""

    progress = pyqtSignal(str)
    crawl_finished = pyqtSignal(bool, str)

    def __init__(self, selected_pages: list, output_path: str):
        """Inicializa worker de crawl

        Args:
            selected_pages: Páginas selecionadas pelo usuário
            output_path: Caminho do arquivo de saída
        """
        super().__init__()
        self.converter = WebToMarkdownConverter()
        self.selected_pages = selected_pages
        self.output_path = output_path

    def run(self):
        """Executa crawl e gera arquivo consolidado"""
        try:
            self.progress.emit("Baixando conteúdo das páginas selecionadas...")
            success, contents = asyncio.run(self.converter.crawl_selected_pages(self.selected_pages))

            if success and contents:
                success, message = self._generate_consolidated_markdown(contents)
                self.crawl_finished.emit(success, message)
            else:
                self.crawl_finished.emit(False, "Nenhum conteúdo baixado")
        except Exception as e:
            logger.exception(f"Erro no WebCrawlWorker: {e}")
            self.crawl_finished.emit(False, f"Erro: {e}")

    def _generate_consolidated_markdown(self, contents: list) -> tuple[bool, str]:
        """Gera arquivo consolidado (cabeçalho + índice + conteúdo)"""
        try:
            from datetime import datetime
            from pathlib import Path

            output_p = Path(self.output_path)

            documento = []
            documento.append("# Documentação\n")
            documento.append(f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")

            # Índice
            documento.append("## 📑 Índice\n")
            for i, page in enumerate(contents, 1):
                documento.append(f"{i}. {page['title']}")

            documento.append("\n---\n")

            # Conteúdo de cada página
            for page in contents:
                documento.append(f"\n## 📄 {page['title']}\n")
                documento.append(f"> Fonte: {page['url']}\n")
                documento.append(page['markdown'])
                documento.append("\n---\n")

            # Salvar
            texto_final = "\n".join(documento)
            output_p.write_text(texto_final, encoding='utf-8')

            return True, f"Arquivo salvo: {self.output_path}\n{len(contents)} páginas"

        except Exception as e:
            logger.exception(f"Erro ao gerar arquivo consolidado: {e}")
            return False, f"Erro ao gerar arquivo: {e}"