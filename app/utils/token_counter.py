"""
╔══════════════════════════════════════════════════════════════════════════════╗
║ LLM Context Builder V2.1 - Token Counter Module                            ║
║ Contador de tokens usando tiktoken para textos e PDFs                      ║
╚══════════════════════════════════════════════════════════════════════════════╝
Taller Dev - 2026
VAI CORINTHIANS!!
═══════════════════════════════════════════════════════════════════════════════
"""

# ===========================================
# 1. IMPORTS E CONFIGURAÇÕES
# ===========================================

import tiktoken
from pathlib import Path
import logging

# Configuração de logging
LOG_FILE = Path(__file__).parent / "token_counter.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ===========================================
# 2. CLASSE PRINCIPAL
# ===========================================

class TokenCounter:
    """Contador de tokens usando tiktoken

    Suporte para diferentes modelos:
    - gpt-3.5-turbo
    - gpt-4
    - gpt-4o
    """

    # =======================================
    # 2.1: INICIALIZAÇÃO
    # =======================================

    def __init__(self, model: str = "gpt-4"):
        """Inicializa contador de tokens

        Args:
            model: Modelo tiktoken (default: gpt-4)
        """
        self.model = model
        self.encoding = None

        try:
            self.encoding = tiktoken.encoding_for_model(model)
            logger.info(f"TokenCounter inicializado com modelo: {model}")
        except Exception as e:
            logger.warning(f"Modelo {model} não encontrado, usando cl100k_base: {e}")
            self.encoding = tiktoken.get_encoding("cl100k_base")

    # =======================================
    # 2.2: CONTAGEM DE TOKENS
    # =======================================

    def count_tokens(self, text: str) -> int:
        """Conta tokens em um texto

        Args:
            text: Texto para contar tokens

        Returns:
            Número de tokens
        """
        try:
            if not text:
                return 0

            tokens = self.encoding.encode(text)
            count = len(tokens)

            logger.debug(f"Texto com {len(text)} chars → {count} tokens")
            return count

        except Exception as e:
            logger.exception(f"Erro ao contar tokens: {e}")
            return 0

    def count_tokens_in_file(self, file_path: Path) -> int:
        """Conta tokens em um arquivo

        Args:
            file_path: Caminho do arquivo

        Returns:
            Número de tokens ou 0 se erro
        """
        try:
            if not file_path.exists():
                logger.warning(f"Arquivo não encontrado: {file_path}")
                return 0

            # Lê arquivo com encoding UTF-8
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            return self.count_tokens(content)

        except Exception as e:
            logger.exception(f"Erro ao ler arquivo {file_path}: {e}")
            return 0

    def format_token_count(self, count: int) -> str:
        """Formata contagem de tokens para display

        Args:
            count: Número de tokens

        Returns:
            String formatada (ex: "1,234 tokens")
        """
        if count >= 1000:
            return f"{count:,} tokens"
        else:
            return f"{count} tokens"

    # =======================================
    # 2.3: UTILITÁRIOS
    # =======================================

    def estimate_cost(self, token_count: int, model: str = None) -> dict:
        """Estima custo aproximado de uso da API

        Args:
            token_count: Número de tokens
            model: Modelo (usa self.model se None)

        Returns:
            Dict com custos aproximados
        """
        model = model or self.model

        # Custos aproximados por 1K tokens (em USD)
        costs = {
            "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-4o": {"input": 0.005, "output": 0.015}
        }

        if model not in costs:
            return {"error": f"Modelo {model} não tem custos definidos"}

        cost_input = (token_count / 1000) * costs[model]["input"]
        cost_output = (token_count / 1000) * costs[model]["output"]

        return {
            "model": model,
            "tokens": token_count,
            "cost_input": round(cost_input, 4),
            "cost_output": round(cost_output, 4),
            "cost_total": round(cost_input + cost_output, 4)
        }


# ===========================================
# 3. FUNÇÕES UTILITÁRIAS GLOBAIS
# ===========================================

def count_pdf_tokens(pdf_path: Path, model: str = "gpt-4") -> int:
    """Conta tokens estimados de um PDF (baseado no tamanho do arquivo)

    Args:
        pdf_path: Caminho do PDF
        model: Modelo tiktoken

    Returns:
        Número estimado de tokens
    """
    try:
        if not pdf_path.exists():
            return 0

        # Estimativa simples: ~4 tokens por KB de arquivo
        # Isso é aproximado pois PDFs têm overhead de formatação
        file_size_kb = pdf_path.stat().st_size / 1024
        estimated_tokens = int(file_size_kb * 4)

        logger.info(f"PDF {pdf_path.name}: {file_size_kb:.1f} KB → ~{estimated_tokens} tokens estimados")
        return estimated_tokens

    except Exception as e:
        logger.exception(f"Erro ao estimar tokens do PDF: {e}")
        return 0


def count_md_tokens(md_path: Path, model: str = "gpt-4") -> int:
    """Conta tokens reais em um arquivo Markdown

    Args:
        md_path: Caminho do arquivo .md
        model: Modelo tiktoken

    Returns:
        Número de tokens
    """
    counter = TokenCounter(model)
    return counter.count_tokens_in_file(md_path)


# ===========================================
# 4. TESTE DO MÓDULO
# ===========================================

if __name__ == "__main__":
    # Teste básico
    counter = TokenCounter()

    test_text = "Olá mundo! Este é um teste de contagem de tokens."
    tokens = counter.count_tokens(test_text)

    print(f"Texto: {test_text}")
    print(f"Tokens: {tokens}")
    print(f"Formatado: {counter.format_token_count(tokens)}")

    # Teste de custo
    cost = counter.estimate_cost(tokens)
    print(f"Custo estimado: ${cost['cost_total']} (input: ${cost['cost_input']}, output: ${cost['cost_output']})")