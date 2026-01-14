# ===========================================
# 2. CLASSE FACHADA (ORQUESTRADOR)
# ===========================================

class WebToMarkdownConverter:
    """Fachada para o sistema web modular - mantém compatibilidade com GUI"""

    def __init__(self):
        """Inicializa conversor web"""
        # Instancia os serviços modulares
        self.crawler_service = WebCrawlerService()

        logger.info("=" * 60)
        logger.info("WebToMarkdownConverter inicializado (V3.0 Modular)")
import asyncio
from pathlib import Path
from datetime import datetime

# Importações dos módulos modulares (imports relativos)
from .web_engine.logger import logger
from .web_engine.crawler import WebCrawlerService

# Importações crawl4ai necessárias para métodos internos
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig

logger.info("=" * 60)
logger.info("WebToMarkdownConverter inicializado (V3.0 Modular)")
logger.info("=" * 60)

# ===========================================
# 2. CLASSE FACHADA (ORQUESTRADOR)
# ===========================================

class WebToMarkdownConverter:
    """Fachada para o sistema web modular - mantém compatibilidade com GUI"""

    def __init__(self):
        """Inicializa conversor web"""
        # Instancia os serviços modulares
        self.crawler_service = WebCrawlerService()

        logger.info("=" * 60)
        logger.info("WebToMarkdownConverter inicializado (V3.0 Modular)")
        logger.info("=" * 60)

    # =======================================
    # MÉTODOS PÚBLICOS (COMPATIBILIDADE COM GUI)
    # =======================================

    def process_web(self, url: str, output_path: str, spider_mode: bool = False) -> tuple[bool, str]:
        """Processa URL web - wrapper para compatibilidade

        Args:
            url: URL da página
            output_path: Caminho do arquivo de saída
            spider_mode: Se True, faz spider mode

        Returns:
            (sucesso, mensagem)
        """
        try:
            if spider_mode:
                # Spider mode antigo - agora delega para scan + crawl
                return asyncio.run(self._process_spider_legacy(url, output_path))
            else:
                # Single page mode
                return asyncio.run(self._process_single_page(url, output_path))
        except Exception as e:
            logger.exception(f"Erro no process_web: {e}")
            return False, f"Erro: {e}"

    async def scan_pages(self, url: str) -> tuple[bool, list[dict]]:
        """Wrapper para scan_pages do crawler service"""
        return await self.crawler_service.scan_pages(url)

    async def crawl_selected_pages(self, selected_pages: list[dict]) -> tuple[bool, list[dict]]:
        """Wrapper para crawl_selected_pages do crawler service"""
        return await self.crawler_service.crawl_selected_pages(selected_pages)

    # =======================================
    # MÉTODOS PRIVADOS
    # =======================================

    async def _process_single_page(self, url: str, output_path: str) -> tuple[bool, str]:
        """Processa página única"""
        try:
            # Detectar renderização
            from .web_engine.analyzer import WebAnalyzer
            analyzer = WebAnalyzer()
            render_type = await analyzer.detect_render_type(url)
            crawler_config = analyzer.get_crawler_config(render_type)

            # Crawl da página
            browser_cfg = BrowserConfig(headless=True, verbose=False)
            async with AsyncWebCrawler(config=browser_cfg) as crawler:
                result = await crawler.arun(url=url, config=crawler_config)

                if not result.success:
                    return False, f"Falha ao baixar página: {result.error_message}"

                # Limpar markdown
                md_limpo = self.crawler_service.cleaner.limpar_markdown_google(result.markdown)

                # Salvar
                output_p = Path(output_path)
                output_p.write_text(md_limpo, encoding='utf-8')

                return True, f"Arquivo salvo: {output_path}"

        except Exception as e:
            logger.exception(f"Erro no single page: {e}")
            return False, f"Erro: {e}"

    async def _process_spider_legacy(self, url: str, output_path: str) -> tuple[bool, str]:
        """Processa spider mode legado (sem seleção interativa)"""
        try:
            # Scan de todas as páginas
            success, pages = await self.crawler_service.scan_pages(url)
            if not success:
                return False, "Falha no scan"

            # Crawl de todas as páginas encontradas
            success, contents = await self.crawler_service.crawl_selected_pages(pages)
            if not success:
                return False, "Falha no crawl"

            # Gerar arquivo consolidado
            documento = []
            documento.append("# Documentação\n")
            documento.append(f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")

            documento.append("## 📑 Índice\n")
            for i, page in enumerate(contents, 1):
                documento.append(f"{i}. {page['title']}")

            documento.append("\n---\n")

            for page in contents:
                documento.append(f"\n## 📄 {page['title']}\n")
                documento.append(f"> Fonte: {page['url']}\n")
                documento.append(page['markdown'])
                documento.append("\n---\n")

            texto_final = "\n".join(documento)
            output_p = Path(output_path)
            output_p.write_text(texto_final, encoding='utf-8')

            return True, f"Arquivo salvo: {output_path}\n{len(contents)} páginas"

        except Exception as e:
            logger.exception(f"Erro no spider legacy: {e}")
            return False, f"Erro: {e}"


# ===========================================
# TESTE DO MÓDULO
# ===========================================

if __name__ == "__main__":
    # Teste básico da fachada
    converter = WebToMarkdownConverter()
    print("✅ WebToMarkdownConverter (fachada) inicializado com sucesso!")