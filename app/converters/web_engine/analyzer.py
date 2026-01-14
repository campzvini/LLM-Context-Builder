"""
╔══════════════════════════════════════════════════════════════════════════════╗
║ Web Analyzer Module - V3.0                                                 ║
║ Detecção de tecnologias e configuração de crawler                         ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from .logger import logger

# Importações crawl4ai necessárias
try:
    from crawl4ai import AsyncWebCrawler
    from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
    from collections import Counter
except ImportError as e:
    logger.critical(f"ERRO FATAL: Dependência crawl4ai não encontrada: {e}")
    raise e

# ===========================================
# CLASSE WEB ANALYZER
# ===========================================

class WebAnalyzer:
    """Analisador de tecnologias web para configuração otimizada"""

    def __init__(self):
        logger.info("WebAnalyzer inicializado")

    async def detect_render_type(self, url: str) -> str:
        """Detecta se site é SSR ou CSR com majority vote

        Retorna:
            "SSR" - Server-Side Rendering (conteúdo no HTML inicial)
            "CSR_ANGULAR" - Angular SPA (Client-Side Rendering)
            "CSR_REACT" - React SPA
        """
        logger.info("Detectando tipo de renderização...")

        try:
            browser_config = BrowserConfig(headless=True, verbose=False)
            quick_config = CrawlerRunConfig(
                wait_until="networkidle",
                page_timeout=10000,
                magic=True,
                verbose=False
            )

            # Tenta 2x + majority vote
            resultados = []
            for tentativa in range(2):
                logger.debug(f"  Tentativa {tentativa + 1}/2")
                async with AsyncWebCrawler(config=browser_config) as crawler:
                    result = await crawler.arun(url=url, config=quick_config)

                    if result.success:
                        html = str(result.html or "")
                        html_lower = html.lower()

                        # Detecta Angular (verifica primeiro por ser mais específico)
                        if "<app-root" in html or "ng-version" in html or "ng-app" in html_lower:
                            resultados.append("CSR_ANGULAR")

                        # Detecta React
                        elif ('div id="root"' in html or 'div id="app"' in html or
                              "_reactFiber" in html or "react-root" in html):
                            resultados.append("CSR_REACT")

                        # Detecta conteúdo SSR (se não achou placeholders de SPA)
                        elif len(html) > 5000 and ("<h1" in html or "<main" in html):
                            # Verifica se não é um skeleton de SPA muito curto
                            if html_lower.count("<") > 50:
                                resultados.append("SSR")
                            else:
                                resultados.append("SSR")
                        else:
                            resultados.append("SSR")
                    else:
                        logger.warning(f"    Tentativa {tentativa + 1} falhou: {result.error_message}")
                        resultados.append("SSR")  # Falha → assume SSR

            # Majority vote
            contador = Counter(resultados)
            tipo_final = contador.most_common(1)[0][0]
            logger.info(f"  ✓ Tipo detectado: {tipo_final} (votação: {resultados})")
            return tipo_final

        except Exception as e:
            logger.exception(f"Erro ao detectar renderização: {e}")
            return "SSR"

    def get_crawler_config(self, render_type: str) -> CrawlerRunConfig:
        """Retorna configuração otimizada por tipo de renderização

        Args:
            render_type: Tipo detectado ("SSR", "CSR_ANGULAR", "CSR_REACT")

        Returns:
            CrawlerRunConfig otimizada
        """
        if render_type == "CSR_ANGULAR":
            logger.info("Usando configuração Angular SPA (robusta)")
            js_code = """
                // Delay simples para Angular estabilizar
                await new Promise(r => setTimeout(r, 3000));
            """
            return CrawlerRunConfig(
                js_code=js_code,
                wait_until="networkidle",
                wait_for="main, article, [role='main'], .content",  # ✅ CSS SELECTOR STRATEGY
                page_timeout=60000,
                magic=False,  # Desativar automação mágica para isolamento
                verbose=False
            )

        elif render_type == "CSR_REACT":
            logger.info("Usando configuração React SPA (otimizada)")
            js_code = """
                // Scroll completo para carregar conteúdo lazy
                window.scrollTo(0, document.body.scrollHeight);
                await new Promise(resolve => setTimeout(resolve, 1500));
            """
            return CrawlerRunConfig(
                js_code=js_code,
                wait_until="networkidle",
                wait_for="main, article, [role='main'], .content",  # ✅ CSS SELECTOR STRATEGY
                page_timeout=20000,
                magic=True,
                verbose=False
            )

        else:  # SSR
            logger.info("Usando configuração SSR (rápida)")
            return CrawlerRunConfig(
                wait_until="networkidle",
                page_timeout=10000,
                magic=True,
                verbose=False
            )


# ===========================================
# TESTE DO MÓDULO
# ===========================================

if __name__ == "__main__":
    import asyncio

    async def test():
        analyzer = WebAnalyzer()

        # Teste configuração
        config = analyzer.get_crawler_config("SSR")
        print(f"✅ Config SSR criada: {config}")

        # Teste detecção (comentado para não fazer requests reais)
        # tipo = await analyzer.detect_render_type("https://example.com")
        # print(f"Tipo detectado: {tipo}")

    asyncio.run(test())