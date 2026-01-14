"""
╔══════════════════════════════════════════════════════════════════════════════╗
║ Web Logger Module - V3.0 (PARANÓICO)                                       ║
║ Infraestrutura de logging forense para diagnóstico de erros silenciosos  ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import sys
import io
import os
import logging
import traceback
from pathlib import Path

# ===========================================
# FIX: FORÇAR UTF-8 NO WINDOWS (PRESERVAR!)
# ===========================================
# CRÍTICO: Isso previne o erro 'charmap codec can't encode character' ao logar títulos com emojis/setas
if sys.platform.startswith('win'):
    # Reconfigura stdout/stderr para utf-8 e substitui caracteres incompatíveis
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# ===========================================
# LOGGER PARANÓICO - DIAGNÓSTICO FORENSE
# ===========================================

def get_log_dir():
    """Retorna o caminho da pasta de logs centralizada na raiz do projeto"""
    # Sempre retorna PROJECT_ROOT/logs/ independente de onde o código está sendo executado

    # Se estiver rodando como .exe (PyInstaller), usar o diretório do executável
    if getattr(sys, 'frozen', False):
        exe_dir = Path(sys.executable).parent
        logs_dir = exe_dir / 'logs'
    else:
        # Se estiver rodando como módulo Python, calcular da raiz do projeto
        # app/converters/web_engine/logger.py -> subir 3 níveis para raiz
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent.parent  # app -> raiz
        logs_dir = project_root / 'logs'

    # Garantir que a pasta existe
    logs_dir.mkdir(exist_ok=True)

    return logs_dir


def setup_paranoid_logger():
    """Configura logger paranóico para capturar TODOS os erros silenciosos"""

    # === 1. DIAGNÓSTICO DE AMBIENTE ===
    print("=" * 80)
    print("🔍 LOGGER PARANÓICO - DIAGNÓSTICO DE AMBIENTE")
    print("=" * 80)

    # Ambiente Python
    print(f"🐍 Python Version: {sys.version}")
    print(f"🖥️  Platform: {sys.platform}")
    print(f"🔤 Default Encoding: {sys.getdefaultencoding()}")
    print(f"💾 Filesystem Encoding: {sys.getfilesystemencoding()}")
    print(f"📁 Current Working Directory: {os.getcwd()}")

    # Estado do ambiente
    print(f"❄️  Frozen (PyInstaller): {getattr(sys, 'frozen', False)}")
    print(f"📦 Executable Path: {getattr(sys, 'executable', 'N/A')}")
    print(f"📂 Logs Directory: {get_log_dir()}")
    print("=" * 80)

    # === 2. CONFIGURAÇÃO DO ROOT LOGGER (CAPTURA GLOBAL) ===
    # Configurar ROOT logger para capturar logs de TODAS as bibliotecas
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Formato forense com arquivo e linha de origem
    formatter = logging.Formatter(
        '%(asctime)s | %(name)s | %(levelname)s | [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Verificar se está rodando em modo compilado (PyInstaller)
    is_compiled = getattr(sys, 'frozen', False)

    # === 3. CONFIGURAÇÃO DOS HANDLERS ===
    logs_dir = get_log_dir()

    # Definir arquivo de log
    debug_log_file = logs_dir / 'debug_trace.log'

    # Handler para arquivo (persistência imediata - buffer=0)
    file_handler = logging.FileHandler(
        debug_log_file,
        encoding='utf-8',
        delay=False  # Abrir arquivo imediatamente
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    # Forçar flush imediato para capturar crashes
    file_handler.flush()
    root_logger.addHandler(file_handler)

    # Handler para console (sempre ativo)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    print("📝 LOGGER CENTRALIZADO ATIVO")
    print(f"📄 Arquivo de debug: {debug_log_file}")
    if is_compiled:
        print("📦 Modo compilado (.EXE)")
    else:
        print("🐍 Modo desenvolvimento")

    # === 4. CONFIGURAÇÃO DE LOGGERS DE TERCEIROS ===
    # Capturar logs de bibliotecas críticas
    third_party_loggers = [
        'crawl4ai',
        'asyncio',
        'urllib3',
        'playwright',
        'pymupdf',
        'beautifulsoup4'
    ]

    for logger_name in third_party_loggers:
        third_logger = logging.getLogger(logger_name)
        third_logger.setLevel(logging.DEBUG)
        third_logger.addHandler(file_handler)  # Mesmo handler para consistência
        print(f"🔍 Logger '{logger_name}' configurado para DEBUG")

    print("=" * 80)

    # === 4. EXCEPT HOOK PARA CAPTURAR CRASHES SILENCIOSOS ===
    def paranoid_excepthook(exc_type, exc_value, exc_traceback):
        """Hook que captura TODAS as exceções não tratadas"""
        error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))

        # Log com CRITICAL para destacar
        root_logger.critical("=" * 80)
        root_logger.critical("💥 CRASH SILENCIOSO CAPTURADO!")
        root_logger.critical("=" * 80)
        root_logger.critical(error_msg)
        root_logger.critical("=" * 80)

        # Também imprimir no console para debug imediato
        print("\n" + "=" * 80, file=sys.stderr)
        print("💥 CRASH SILENCIOSO CAPTURADO!", file=sys.stderr)
        print("=" * 80, file=sys.stderr)
        print(error_msg, file=sys.stderr)
        print("=" * 80, file=sys.stderr)

        # Forçar flush de todos os handlers antes de morrer
        for handler in root_logger.handlers:
            handler.flush()

        # Chamar o hook original
        sys.__excepthook__(exc_type, exc_value, exc_traceback)

    # Instalar o hook paranóico
    sys.excepthook = paranoid_excepthook
    root_logger.info("🛡️  Excepthook paranóico instalado - capturando crashes silenciosos")

    print("🛡️  EXCEPT HOOK PARANÓICO INSTALADO")
    print("=" * 80)

    # === 6. LOGGER ESPECÍFICO DO MÓDULO ===
    web_logger = logging.getLogger('web_converter')
    web_logger.info("🎯 Logger paranóico inicializado com sucesso!")

    return web_logger


# ===========================================
# FUNÇÕES DE LOGGING DE CICLO DE VIDA
# ===========================================

def log_app_startup():
    """Loga inicialização da aplicação"""
    logger.info("=" * 80)
    logger.info("🚀 APLICAÇÃO INICIADA")
    logger.info("=" * 80)
    logger.info(f"Timestamp: {logging.time.time()}")
    logger.info("Estado: RUNNING")

def log_app_shutdown_by_user():
    """Loga fechamento normal pelo usuário"""
    logger.info("=" * 80)
    logger.info("👤 APLICAÇÃO FECHADA PELO USUÁRIO")
    logger.info("=" * 80)
    logger.info(f"Timestamp: {logging.time.time()}")
    logger.info("Estado: CLOSED_BY_USER")

def log_button_click(button_name: str, details: dict = None):
    """Loga clique em botão da GUI"""
    details_str = ""
    if details:
        details_str = " - " + ", ".join([f"{k}: {v}" for k, v in details.items()])

    logger.info(f"🔘 BOTÃO CLICADO: {button_name}{details_str}")

def log_worker_start(worker_type: str, params: dict = None):
    """Loga início de worker"""
    params_str = ""
    if params:
        params_str = " - " + ", ".join([f"{k}: {v}" for k, v in params.items()])

    logger.info(f"🔨 WORKER INICIADO: {worker_type}{params_str}")

def log_worker_finished(worker_type: str, success: bool, result: str = ""):
    """Loga finalização de worker"""
    status = "✅ SUCESSO" if success else "❌ FALHA"
    result_str = f" - {result}" if result else ""

    logger.info(f"🔨 WORKER FINALIZADO: {worker_type} {status}{result_str}")

def log_conversion_start(mode: str, source: str, destination: str):
    """Loga início de conversão"""
    logger.info(f"📄 CONVERSÃO INICIADA: {mode}")
    logger.info(f"   Origem: {source}")
    logger.info(f"   Destino: {destination}")

def log_conversion_finished(mode: str, success: bool, result: str = ""):
    """Loga finalização de conversão"""
    status = "✅ SUCESSO" if success else "❌ FALHA"
    result_str = f" - {result}" if result else ""

    logger.info(f"📄 CONVERSÃO FINALIZADA: {mode} {status}{result_str}")

def log_spider_decision(url: str, spider_mode: bool):
    """Loga decisão do modo spider"""
    logger.info(f"🕸️ DECISÃO SPIDER MODE: {spider_mode}")
    logger.info(f"   URL: {url}")
    if spider_mode:
        logger.info("   ROTA: Spider Mode Interativo (Scan + Seleção + Crawl)")
    else:
        logger.info("   ROTA: Single Page Mode (Página única)")

def log_scan_results(pages_count: int, selected_count: int = None):
    """Loga resultados do scan"""
    logger.info(f"🔍 SCAN CONCLUÍDO: {pages_count} páginas encontradas")
    if selected_count is not None:
        logger.info(f"   Selecionadas pelo usuário: {selected_count}")

def log_file_operation(operation: str, file_path: str, success: bool, details: str = ""):
    """Loga operações de arquivo"""
    status = "✅" if success else "❌"
    details_str = f" - {details}" if details else ""

    logger.info(f"💾 ARQUIVO {operation}: {status} {file_path}{details_str}")

# ===========================================
# LOGGER GLOBAL PARANÓICO
# ===========================================

logger = setup_paranoid_logger()

# ===========================================
# TESTE DO MÓDULO PARANÓICO
# ===========================================

if __name__ == "__main__":
    logger.info("🧪 Teste do Logger Paranóico")
    logger.debug("Mensagem de DEBUG (apenas em arquivo)")
    logger.info("Mensagem de INFO (console + arquivo)")
    logger.warning("Mensagem de WARNING")
    logger.error("Mensagem de ERROR")
    logger.critical("Mensagem de CRITICAL")

    # Teste de crash silencioso (descomentado para testar)
    # raise ValueError("Teste de crash controlado - deve ser capturado pelo excepthook")

    print("✅ Logger Paranóico configurado e testado!")