import asyncio
import logging
from converter_web import WebToMarkdownConverter

# Configura logger para ver no console
logging.basicConfig(level=logging.INFO)

async def main():
    print("--- INICIANDO TESTE ISOLADO ---")
    converter = WebToMarkdownConverter()
    url = "https://antigravity.google/docs/get-started"

    print(f"Tentando Scan em: {url}")
    # Isso vai testar se a importação global resolveu o travamento
    success, pages = await converter.scan_pages(url)

    if success:
        print(f"SUCESSO! Encontradas {len(pages)} páginas.")
        for p in pages:
            print(f" - {p['title']}")
    else:
        print("FALHA no Scan (mas pelo menos não travou silenciosamente).")

if __name__ == "__main__":
    asyncio.run(main())