"""
╔══════════════════════════════════════════════════════════════════════════════╗
║ Web Crawler Module - V3.0                                                  ║
║ Core do sistema de crawling web com cache e paralelização                ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import asyncio
import time
import uuid
from pathlib import Path
from urllib.parse import urlparse
from datetime import datetime

from .logger import logger
from .analyzer import WebAnalyzer
from .cleaner import WebCleaner

# ===========================================
# FIX: EVENT LOOP PARA WINDOWS
# ===========================================
# Evita conflitos entre asyncio e Qt event loop no Windows
import sys
if sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Importações crawl4ai
try:
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
    from crawl4ai.async_configs import BrowserConfig as CrawlerBrowserConfig, CrawlerRunConfig as CrawlerRunConfigClass
except ImportError as e:
    logger.critical(f"ERRO FATAL: Dependência crawl4ai não encontrada: {e}")
    raise e

# ===========================================
# CLASSE WEB CRAWLER SERVICE
# ===========================================

class WebCrawlerService:
    """Serviço core de crawling web com cache e paralelização"""

    def __init__(self):
        self.analyzer = WebAnalyzer()
        self.cleaner = WebCleaner()

        # Cache de páginas
        self._cache = {}  # {url_normalizada: (html, markdown, timestamp)}
        self._cache_ttl = 3600  # 1 hora em segundos

        logger.info("WebCrawlerService inicializado")

    # =======================================
    # CACHE DE PÁGINAS
    # =======================================

    def _get_from_cache(self, url: str) -> tuple[str, str] | None:
        """Retorna (html, markdown) do cache se válido"""
        normalized = self._normalize_url(url)

        if normalized in self._cache:
            cached_data, timestamp = self._cache[normalized]
            if time.time() - timestamp < self._cache_ttl:
                logger.debug(f"  Cache HIT: {url}")
                return cached_data
            else:
                # Remove cache expirado
                del self._cache[normalized]
                logger.debug(f"  Cache EXPIRADO: {url}")

        logger.debug(f"  Cache MISS: {url}")
        return None

    def _save_to_cache(self, url: str, html: str, markdown: str):
        """Salva no cache"""
        normalized = self._normalize_url(url)
        self._cache[normalized] = ((html, markdown), time.time())

    def _normalize_url(self, url: str) -> str:
        """Normaliza URL removendo query strings e fragments"""
        parsed = urlparse(url)
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        return normalized.rstrip('/')

    # =======================================
    # EXTRAÇÃO DE LINKS
    # =======================================

    def extract_internal_links(self, html: str, base_url: str) -> set[str]:
        """Extrai links internos do HTML

        Args:
            html: Conteúdo HTML da página
            base_url: URL base para resolver links relativos

        Returns:
            Set de URLs internas
        """
        from bs4 import BeautifulSoup
        import re

        links = []  # Lista para preservar ordem
        seen = set()  # Set auxiliar para evitar duplicatas
        parsed_base = urlparse(base_url)
        base_domain = f"{parsed_base.scheme}://{parsed_base.netloc}"

        # ✅ PASSO 1: Filtro RELAXADO - apenas domínio (sem path_prefix)
        # REMOVIDO: Verificações de path_prefix para deixar o usuário filtrar depois
        path_prefix = ''  # Não filtra por path, apenas domínio

        try:
            soup = BeautifulSoup(html, 'html.parser')

            # Extrair de diferentes atributos
            selectors = [
                ('a', 'href'),
                ('link', 'href'),
                ('area', 'href'),
                ('form', 'action'),
                ('iframe', 'src'),
                ('script', 'src'),
                ('img', 'src'),
            ]

            for tag_name, attr in selectors:
                for element in soup.find_all(tag_name, {attr: True}):
                    full_url = element[attr]
                    if not full_url:
                        continue

                    try:
                        # Resolver URLs relativas
                        if not full_url.startswith(('http://', 'https://')):
                            if full_url.startswith('/'):
                                full_url = f"{base_domain}{full_url}"
                            else:
                                full_url = f"{base_domain}/{full_url}"

                        # Normaliza (remove query string, etc)
                        normalized = self._normalize_url(full_url)
                        seed_normalized = self._normalize_url(base_url)

                        # ✅ PASSO 1: Filtro RELAXADO - apenas domínio
                        parsed = urlparse(normalized)
                        extensions_ignorar = {'.css', '.js', '.svg', '.png', '.jpg', '.jpeg', '.gif',
                                             '.xml', '.json', '.woff', '.woff2', '.ttf', '.ico'}

                        path_lower = parsed.path.lower()
                        if (any(path_lower.endswith(ext) for ext in extensions_ignorar) or
                            '_astro/' in path_lower or
                            'sitemap' in path_lower or
                            'robots' in path_lower):
                            continue

                        # Filtra: APENAS mesmo domínio (removido path_prefix)
                        if (parsed.netloc == parsed_base.netloc and
                            normalized != seed_normalized and
                            normalized not in seen):
                            seen.add(normalized)
                            links.append(normalized)

                    except Exception as e:
                        logger.debug(f"Erro ao processar link {full_url}: {e}")
                        continue

        except Exception as e:
            logger.exception(f"Erro ao extrair links do HTML: {e}")

        return links

    # =======================================
    # UTILITÁRIOS PARA SCAN
    # =======================================

    def _extract_title_from_html(self, html: str, url: str) -> str:
        """Extrai título de <title> ou <meta property="og:title">"""
        try:
            soup = BeautifulSoup(html, 'html.parser')

            # Tenta <title>
            if soup.title and soup.title.string:
                return soup.title.string.strip()

            # Tenta og:title
            og_title = soup.find('meta', property='og:title')
            if og_title and og_title.get('content'):
                return og_title['content'].strip()

        except Exception as e:
            logger.debug(f"Erro ao extrair título: {e}")

        # Fallback: última parte da URL
        path_parts = urlparse(url).path.strip('/').split('/')
        return path_parts[-1].replace('-', ' ').title() if path_parts else "Sem Título"

    async def _get_page_title(self, crawler, url: str) -> str:
        """Extrai título via lightweight crawl"""
        try:
            # Crawl rápido (somente head, 5s timeout)
            quick_config = CrawlerRunConfig(
                wait_until="networkidle",
                page_timeout=5000,
                magic=True,
                verbose=False
            )

            result = await crawler.arun(url=url, config=quick_config)

            if result.success:
                return self._extract_title_from_html(str(result.html or ""), url)

        except Exception as e:
            logger.debug(f"Erro ao obter título de {url}: {e}")

        return "Sem Título"

    # =======================================
    # MÉTODOS DE CRAWLING
    # =======================================

    async def scan_pages(self, seed_url: str) -> tuple[bool, list[dict]]:
        """PASSO A (SCAN): Identifica páginas elegíveis SEM baixar conteúdo"""
        logger.info(f"SCAN INICIADO: {seed_url}")

        # 1. Detectar tipo de renderização para config otimizada
        render_type = await self.analyzer.detect_render_type(seed_url)
        crawler_config = self.analyzer.get_crawler_config(render_type)

        # 2. Configuração Blindada (Anti-Bloqueio) + Config Crawler
        browser_cfg = BrowserConfig(
            headless=True,
            verbose=True, # Verbose para debug no console
            ignore_https_errors=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
            }
        )
        # Usar config otimizada com JS para expansão de menus (se CSR)
        run_cfg = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            page_timeout=crawler_config.page_timeout or 30000,
            js_code=crawler_config.js_code,
            wait_until=crawler_config.wait_until,
            wait_for=crawler_config.wait_for
        )

        pages = []

        try: # Try/Except interno para garantir log de erro no arquivo
            async with AsyncWebCrawler(config=browser_cfg) as crawler:

                # 2. Smart Retry (Resgatado da V2)
                urls_to_try = [seed_url]
                if seed_url.endswith('/'):
                    urls_to_try.append(seed_url.rstrip('/'))
                else:
                    urls_to_try.append(seed_url + '/')

                # Adiciona variações comuns
                clean = seed_url.rstrip('/')
                if not clean.endswith(('home', 'docs', 'intro')):
                    urls_to_try.append(f"{clean}/home")
                    urls_to_try.append(f"{clean}/docs")

                valid_seed_result = None
                valid_url = ""

                logger.info(f"Tentando acessar seed com variações: {urls_to_try}")

                for try_url in urls_to_try:
                    logger.info(f"Tentando Crawl em: {try_url}")
                    result = await crawler.arun(url=try_url, config=run_cfg)

                    if result.success and "404" not in result.markdown[:100]:
                        valid_seed_result = result
                        valid_url = try_url
                        logger.info(f"Seed válida encontrada: {valid_url}")
                        break
                    else:
                        logger.warning(f"Falha ao acessar {try_url}: {result.error_message}")

                if not valid_seed_result:
                    logger.error("TODAS as tentativas de Seed falharam.")
                    return False, []

                # 3. Adiciona a Seed Garantida (Correção da Lista Vazia)
                title_seed = self._extract_title_from_html(str(valid_seed_result.html or ""), valid_url)
                pages.append({
                    "url": valid_url,
                    "title": title_seed,
                    "selected": True
                })

                # 4. Extrai Links (Com filtro relaxado do Passo 1)
                links = self.extract_internal_links(str(valid_seed_result.html or ""), valid_url)
                logger.info(f"Links extraídos: {len(links)}")

                # Crawl leve para títulos dos links
                for link in links:
                    title = await self._get_page_title(crawler, link)
                    pages.append({
                        "url": link,
                        "title": title,
                        "selected": True
                    })

            return True, pages

        except Exception as e:
            logger.exception(f"ERRO FATAL NO SCAN_PAGES: {e}")
            return False, []

    async def crawl_selected_pages(self, selected_pages: list[dict]) -> tuple[bool, list[dict]]:
        """PASSO C (EXECUTAR): Baixa apenas páginas selecionadas pelo usuário"""
        logger.info("CRAWLING: Baixando páginas selecionadas...")
        logger.info(f"Páginas selecionadas: {len(selected_pages)}")

        if not selected_pages:
            logger.warning("Nenhuma página selecionada")
            return False, []

        try:
            # Detectar renderização da primeira página
            render_type = await self.analyzer.detect_render_type(selected_pages[0]["url"])
            crawler_config = self.analyzer.get_crawler_config(render_type)



            contents = []
            seen_hashes = set()  # Deduplicação de conteúdo

            # Browser configuration
            browser_cfg = BrowserConfig(
                headless=True,
                verbose=False
            )

            async with AsyncWebCrawler(config=browser_cfg) as crawler:
                # ✅ PARALELIZAÇÃO: Processar em chunks de 5 URLs (seguro)
                chunk_size = 5

                for i in range(0, len(selected_pages), chunk_size):
                    chunk = selected_pages[i:i+chunk_size]
                    logger.info(f"  Chunk {i//chunk_size + 1}: {len(chunk)} URLs")

                    # Paralelizar downloads
                    tasks = [self.crawl_page_async(crawler, crawler_config, p["url"])
                             for p in chunk]
                    chunk_results = await asyncio.gather(*tasks, return_exceptions=True)

                    # Processar resultados
                    for result in chunk_results:
                        if isinstance(result, Exception):
                            logger.error(f"Exceção no chunk: {result}")
                            continue

                        url, title, markdown = result
                        if markdown.strip():
                            # ✅ DEDUPLICAÇÃO: Evitar salvar conteúdo repetido
                            content_hash = hash(markdown)
                            if content_hash in seen_hashes:
                                logger.warning(f"⚠️ Conteúdo duplicado detectado para {url} - IGNORADO.")
                                continue
                            seen_hashes.add(content_hash)

                            contents.append({
                                "url": url,
                                "title": title,
                                "markdown": markdown
                            })
                            logger.info(f"    ✓ {title} ({len(markdown)} chars)")
                        else:
                            logger.warning(f"    ✗ {url} - conteúdo vazio")

                    # Pequena pausa entre chunks
                    await asyncio.sleep(0.5)

            logger.info(f"CRAWL CONCLUÍDO: {len(contents)} páginas baixadas")

            return True, contents

        except Exception as e:
            logger.exception(f"Erro no crawl_selected_pages: {e}")
            return False, []

    async def crawl_page_async(self, crawler, crawler_config, url: str) -> tuple[str, str, str]:
        """Faz crawl de uma única página e retorna título + conteúdo"""
        try:
            # ✅ CACHE: Verifica cache primeiro
            cached = self._get_from_cache(url)
            if cached:
                html, md_from_cache = cached
                md_limpo = self.cleaner.limpar_markdown_google(md_from_cache)

                titulo = "Sem Título"
                for linha in md_limpo.split('\n'):
                    if linha.startswith('# '):
                        titulo = linha[2:].strip()
                        break
                    elif linha.startswith('## '):
                        titulo = linha[3:].strip()
                        break

                logger.info(f"  ✓ CACHE HIT - {len(md_limpo)} chars - {titulo[:50]}")
                return url, titulo, md_limpo

            # Se não está no cache, faz o crawl normal
            logger.info(f"  Crawling: {url}")

            # ✅ ISOLAMENTO DE SESSÃO: Força contexto novo por URL
            session_id = str(uuid.uuid4())

            # ✅ CSS SELECTOR STRATEGY: Seletor restritivo para evitar vazamento de menus
            css_selector = "main, article, [role='main']"
            result = await crawler.arun(
                url=url,
                config=crawler_config,
                css_selector=css_selector,  # Extrai apenas o miolo, elimina menus/headers
                session_id=session_id  # Isolamento total por página
            )

            if result.success:
                # ✅ CACHE: Salva no cache
                self._save_to_cache(url, str(result.html or ""), result.markdown)

                # Limpa o markdown
                md_limpo = self.cleaner.limpar_markdown_google(result.markdown)

                # Extrai título (primeiro H1 ou H2)
                titulo = "Sem Título"
                for linha in md_limpo.split('\n'):
                    if linha.startswith('# '):
                        titulo = linha[2:].strip()
                        break
                    elif linha.startswith('## '):
                        titulo = linha[3:].strip()
                        break

                logger.info(f"  ✓ CRAWL NOVO - {len(md_limpo)} chars - {titulo[:50]}")
                return url, titulo, md_limpo
            else:
                logger.warning(f"    ✗ Falha: {result.error_message}")
                return url, "Erro", ""

        except Exception as e:
            logger.exception(f"    ✗ Exceção: {e}")
            return url, "Erro", ""


# ===========================================
# TESTE DO MÓDULO
# ===========================================

if __name__ == "__main__":
    import asyncio

    async def test():
        service = WebCrawlerService()

        # Teste scan (descomentado para teste real)
        # success, pages = await service.scan_pages("https://example.com")
        # print(f"Scan: {success}, {len(pages)} páginas")

        print("✅ WebCrawlerService inicializado")

    asyncio.run(test())