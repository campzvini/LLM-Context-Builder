"""
╔══════════════════════════════════════════════════════════════════════════════╗
║ LLM Context Builder V2.0 - Main Entry Point                                  ║
║ Inicialização da aplicação (PDF + Web → Markdown)                            ║
╚══════════════════════════════════════════════════════════════════════════════╝
Taller Dev - 2026
VAI CORINTHIANS!!
═══════════════════════════════════════════════════════════════════════════════
"""

# ===========================================
# 1. IMPORTS E CONFIGURAÇÕES
# ===========================================

import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from app.gui.main_window import Pdf2mdWindow
from app.converters.web_engine.logger import log_app_startup


def resource_path(relative_path):
    """Retorna caminho absoluto para recursos empacotados"""
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# ===========================================
# 2. FUNÇÃO MAIN
# ===========================================

def main():
    """Inicializa aplicação e inicia loop de eventos"""
    # Log de inicialização da aplicação
    log_app_startup()

    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(resource_path("imagens/icone_principal.png")))
    window = Pdf2mdWindow()
    window.show()
    sys.exit(app.exec())


# ===========================================
# 9. TESTE DO MÓDULO
# ===========================================

if __name__ == "__main__":
    main()
