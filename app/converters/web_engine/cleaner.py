"""
╔══════════════════════════════════════════════════════════════════════════════╗
║ Web Cleaner Module - V3.0                                                  ║
║ Limpeza e processamento de texto Markdown                                ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from .logger import logger
import re

# ===========================================
# CLASSE WEB CLEANER
# ===========================================

class WebCleaner:
    """Limpa e processa texto Markdown removendo lixo de navegação"""

    def __init__(self):
        logger.info("WebCleaner inicializado")

    def limpar_markdown_google(self, texto_bruto: str) -> str:
        """Remove lixo de navegação do Markdown gerado

        Args:
            texto_bruto: Markdown bruto do crawler

        Returns:
            Markdown limpo sem menus/rodapés
        """
        logger.info("Iniciando limpeza do Markdown...")
        logger.debug(f"Tamanho do texto bruto: {len(texto_bruto)} caracteres")

        # ✅ CORREÇÃO P5: Remove tags <script> e <style> antes de qualquer processamento
        texto_sem_scripts = re.sub(r'<script.*?>.*?</script>', '', texto_bruto, flags=re.DOTALL | re.IGNORECASE)
        texto_sem_scripts = re.sub(r'<style.*?>.*?</style>', '', texto_sem_scripts, flags=re.DOTALL | re.IGNORECASE)
        logger.debug(f"Após remover <script>/<style>: {len(texto_sem_scripts)} caracteres")

        linhas = texto_sem_scripts.split('\n')
        logger.debug(f"Total de linhas: {len(linhas)}")

        # Palavras que indicam lixo de navegação
        lixo_nav = [
            # Existentes
            "keyboard_arrow", "expand_more", "side_navigation",
            "On this Page", "Edit this page", "menu", "download",
            "Stay up-to-date", "Edit this page", "Next page", "Previous page",

            # Novos: Menus de navegação do site
            "Product", "Pricing", "Blog", "Use Cases", "Resources", "Documentation",
            "Changelog", "Support", "Press", "Built for developers", "Everything you need",
            "Review Changes", "Source Control", "Conversation View", "Separate Chrome Profile",
            "workspaces Professional", "code_blocks Frontend", "stacks Fullstack"
        ]

        linhas_ignoradas = 0
        primeiro_heading = None
        linhas_limpas = []

        for i, linha in enumerate(linhas):
            l = linha.strip()

            # O conteúdo útil geralmente começa em um heading (# ## ### ####)
            if not linhas_limpas and l.startswith("#"):
                primeiro_heading = l[:50] + "..." if len(l) > 50 else l
                logger.info(f"Início do conteúdo encontrado na linha {i+1}: {primeiro_heading}")

            # Remove links soltos de navegação lateral (curtos e com "docs")
            if l.startswith("[") and "docs" in l.lower() and len(l) < 80:
                if "](" in l and l.count("[") == 1:
                    logger.debug(f"Linha {i+1} removida (link de navegação): {l[:60]}")
                    continue

            # ✅ CORREÇÃO: Limpeza inteligente com zona de segurança
            if any(x in l.lower() for x in lixo_nav):
                # ZONA DE SEGURANÇA: Não remove se linha longa (>60 chars)
                if len(l) > 60:
                    logger.debug(f"Linha {i+1} PRESERVADA (zona de segurança >60 chars): {l[:60]}")
                    linhas_limpas.append(linha)
                    continue

                # Não remove se for texto corrido (não link isolado)
                if not l.startswith('[') and ']' not in l:
                    # Verifica se tem contexto (mais de 3 palavras)
                    words = l.split()
                    if len(words) > 3:
                        logger.debug(f"Linha {i+1} PRESERVADA (texto corrido): {l[:60]}")
                        linhas_limpas.append(linha)
                        continue

                # Caso contrário, remove (é lixo de navegação verdadeiro)
                logger.debug(f"Linha {i+1} removida (palavra proibida): {l[:60]}")
                continue

            linhas_limpas.append(linha)

        # ✅ FILTRO DE RUÍDO DE DENSIDADE: Remove sequências de linhas curtas com links
        # (menus laterais esquerdo e direito que aparecem como blocos de links)
        linhas_filtradas = []
        i = 0
        while i < len(linhas_limpas):
            linha_atual = linhas_limpas[i].strip()

            # Verifica se é uma linha curta com link (possível item de menu)
            eh_link_curto = (linha_atual.startswith('[') and
                           '](' in linha_atual and
                           len(linha_atual) < 80 and
                           linha_atual.count('[') == 1)

            if eh_link_curto:
                # Conta quantas linhas consecutivas são links curtos
                count_consecutivos = 1
                j = i + 1
                while j < len(linhas_limpas):
                    prox_linha = linhas_limpas[j].strip()
                    eh_prox_link = (prox_linha.startswith('[') and
                                  '](' in prox_linha and
                                  len(prox_linha) < 80 and
                                  prox_linha.count('[') == 1)
                    if eh_prox_link:
                        count_consecutivos += 1
                        j += 1
                    else:
                        break

                # Se encontrou 3+ linhas consecutivas de links curtos, remove o bloco
                if count_consecutivos >= 3:
                    logger.debug(f"Removido bloco de {count_consecutivos} links consecutivos (menu lateral) nas linhas {i+1}-{j}")
                    i = j  # Pula todo o bloco
                    continue
                else:
                    # Menos de 3, mantém (pode ser lista de referências legítima)
                    linhas_filtradas.append(linhas_limpas[i])

            else:
                # Linha normal, mantém
                linhas_filtradas.append(linhas_limpas[i])

            i += 1

        texto = "\n".join(linhas_filtradas)
        texto_limpo = re.sub(r'\n{3,}', '\n\n', texto)

        # ✅ CORREÇÃO P5: Fallback threshold ajustado para 90% ao invés de 100%
        if len(texto_limpo) < len(texto_sem_scripts) * 0.1:  # Se removeu >90%
            logger.warning("ATENÇÃO: Limpeza removeu >90% do conteúdo!")
            logger.info("Usando fallback: removendo apenas lixo extremo...")

            # Fallback: remove apenas linhas muito curtas de navegação
            linhas_fallback = []
            for linha in linhas:
                l = linha.strip()
                if len(l) < 3:
                    continue
                if l in ["menu", "download", "search", "close"]:
                    continue
                linhas_fallback.append(linha)

            texto_limpo = "\n".join(linhas_fallback)
            texto_limpo = re.sub(r'\n{3,}', '\n\n', texto_limpo)
            logger.info(f"Linhas após fallback: {len(linhas_fallback)}")

        logger.info(f"Tamanho final do texto limpo: {len(texto_limpo)} caracteres")
        return texto_limpo


# ===========================================
# TESTE DO MÓDULO
# ===========================================

if __name__ == "__main__":
    cleaner = WebCleaner()

    # Teste com texto de exemplo
    texto_teste = """
# Documentação

## Menu de Navegação

Clique aqui para acessar o menu principal.

<script>alert('teste')</script>

## Conteúdo Útil

Este é um texto corrido sobre o menu de configurações que deve ser preservado.
"""

    limpo = cleaner.limpar_markdown_google(texto_teste)
    print("TEXTO LIMPO:")
    print(limpo)