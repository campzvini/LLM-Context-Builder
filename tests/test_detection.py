import asyncio
import sys
from converter_web import WebToMarkdownConverter

async def test_detection():
    """Testa detecção de renderização em sites diferentes"""

    urls = [
        ("Antigravity (Angular SPA CSR)", "https://antigravity.google/docs"),
        ("OpenCode (Astro SSR)", "https://opencode.ai/docs"),
    ]

    converter = WebToMarkdownConverter()

    for name, url in urls:
        print(f"\n{'='*60}")
        print(f"Testando: {name}")
        print(f"URL: {url}")
        print(f"{'='*60}")

        render_type = await converter.detect_render_type(url)
        print(f"Tipo detectado: {render_type}")

        config = converter.get_crawler_config(render_type)
        print(f"Configuração: timeout={config.page_timeout}s, delay={config.delay_before_return_html}s")

if __name__ == "__main__":
    asyncio.run(test_detection())
