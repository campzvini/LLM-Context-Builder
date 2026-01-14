"""
╔══════════════════════════════════════════════════════════════════════════════╗
║ LLM Context Builder V2.0 - PDF Converter Module                              ║
║ Lógica de conversão PDF → Markdown (sem GUI)                                 ║
╚══════════════════════════════════════════════════════════════════════════════╝
Taller Dev - 2026
VAI CORINTHIANS!!
═══════════════════════════════════════════════════════════════════════════════
"""

# ===========================================
# 1. IMPORTS E CONFIGURAÇÕES
# ===========================================

from pathlib import Path
import pymupdf4llm


# ===========================================
# 2. CLASSE PRINCIPAL
# ===========================================

class PdfToMarkdownConverter:
    """Converte PDF para Markdown usando pymupdf4llm"""

    # =======================================
    # 2.1: INICIALIZAÇÃO
    # =======================================

    def __init__(self):
        """Inicializa conversor"""
        pass

    # =======================================
    # 2.2: VALIDAÇÃO
    # =======================================

    def validate_pdf_path(self, pdf_path: Path) -> bool:
        """Valida se o arquivo PDF existe
        
        Args:
            pdf_path: Caminho do arquivo PDF
            
        Returns:
            True se arquivo existe, False caso contrário
        """
        try:
            if not pdf_path.exists():
                return False
            
            if pdf_path.suffix.lower() != '.pdf':
                return False
            
            return True
            
        except Exception as e:
            return False

    # =======================================
    # 2.3: CONVERSÃO
    # =======================================

    def convert_pdf_to_markdown(self, pdf_path: Path) -> str:
        """Executa conversão usando pymupdf4llm
        
        Args:
            pdf_path: Caminho do arquivo PDF
            
        Returns:
            Conteúdo Markdown gerado
            
        Raises:
            Exception: Caso conversão falhe
        """
        try:
            md_text = pymupdf4llm.to_markdown(str(pdf_path))
            return md_text
            
        except Exception as e:
            raise Exception(f"Falha na conversão: {e}")

    # =======================================
    # 2.4: SALVAR ARQUIVO
    # =======================================

    def save_markdown(self, content: str, output_path: Path) -> None:
        """Salva conteúdo Markdown em arquivo
        
        Args:
            content: Conteúdo Markdown
            output_path: Caminho de destino do arquivo .md
            
        Raises:
            Exception: Caso salvamento falhe
        """
        try:
            output_path.write_text(content, encoding='utf-8')
            
        except Exception as e:
            raise Exception(f"Falha ao salvar arquivo: {e}")

    # =======================================
    # 2.5: PROCESSO PRINCIPAL
    # =======================================

    def process(self, pdf_path: str, output_path: str) -> tuple[bool, str]:
        """Executa conversão completa
        
        Args:
            pdf_path: Caminho do PDF (string)
            output_path: Caminho de destino do .md (string)
            
        Returns:
            Tupla (sucesso: bool, mensagem: str)
        """
        try:
            pdf_p = Path(pdf_path)
            output_p = Path(output_path)
            
            # 2.5.1: VALIDAR ENTRADA
            if not self.validate_pdf_path(pdf_p):
                return False, f"Arquivo PDF inválido ou não encontrado: {pdf_path}"
            
            # 2.5.2: CONVERTER
            md_content = self.convert_pdf_to_markdown(pdf_p)
            
            # 2.5.3: SALVAR
            self.save_markdown(md_content, output_p)
            
            return True, f"Conversão concluída com sucesso!\nArquivo salvo: {output_path}"
            
        except Exception as e:
            return False, f"Erro: {e}"


# ===========================================
# 9. TESTE DO MÓDULO
# ===========================================

if __name__ == "__main__":
    print("Teste do módulo converter_pdf")
    print("-" * 40)
    
    converter = PdfToMarkdownConverter()
    
    # Teste básico
    print(f"Conversor instanciado: {converter is not None}")
    print("OK - Módulo funcionando")
