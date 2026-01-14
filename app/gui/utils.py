"""
GUI Utils Module - V3.0
Utilitários para interface gráfica
"""

import sys
import os

def resource_path(relative_path):
    """Retorna caminho absoluto para recursos empacotados"""
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)