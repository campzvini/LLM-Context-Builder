# LLM Context Builder V3.0 - Architecture Context

**Projeto:** Conversor PDF/Web → Markdown com arquitetura modular e multi-threading
**Stack:** Python 3.12+, PyQt6, pymupdf4llm, crawl4ai (Async/Playwright), BeautifulSoup4
**Versão:** 3.0 (Modular Refactored + SPA Fixes)
**Status:** Operacional com Mitigações SPA ✅
**Data:** 14/01/2026

---

## 📂 Estrutura de Diretórios (Novo Padrão)

O projeto segue uma arquitetura limpa, separando código fonte (`app`), testes e assets.

```text
raiz/
├── main.py                  # Entry Point (importa de app.gui.main_window)
├── AGENTS.md                # Documentação Técnica
├── requirements.txt         # Dependências
├── logs/                    # Logs Centralizados (Logger Paranóico)
│   └── debug_trace.log      # Logs Forenses (único arquivo)
├── app/                     # PACOTE PRINCIPAL MODULAR
│   ├── __init__.py
│   ├── gui/                 # COMPONENTES GUI ISOLADOS
│   │   ├── __init__.py
│   │   ├── main_window.py   # Container Janela Principal (150 linhas)
│   │   ├── utils.py         # resource_path
│   │   ├── workers.py       # TODOS os QThreads (ConverterWorker, etc)
│   │   ├── dialogs.py       # PageSelectionDialog
│   │   └── tabs/            # WIDGETS DAS ABAS AUTÔNOMOS
│   │       ├── __init__.py
│   │       ├── pdf_tab.py   # PdfTab(QWidget) - Drag & Drop + Workers
│   │       └── web_tab.py   # WebTab(QWidget) - Spider V3.0 + Dialogs
│   ├── converters/          # LÓGICA DE NEGÓCIO
│   │   ├── pdf_converter.py # Conversor PDF (PyMuPDF4LLM)
│   │   ├── web_converter.py # FACHADA (Orquestra o web_engine)
│   │   └── web_engine/      # MOTOR WEB (Modularizado)
│   │       ├── crawler.py   # Core (Rede, Browser, Cache, Proactor Fix)
│   │       ├── cleaner.py   # Limpeza (Regex, Zona de Segurança >60 chars)
│   │       ├── analyzer.py  # Detecção (SSR vs CSR - React/Angular)
│   │       └── logger.py    # Infra Logs Paranóica (UTF-8 + Excepthook)
│   └── utils/
│       └── token_counter.py # Contagem de Tokens (tiktoken)
├── tests/                   # Scripts de Validação
│   └── teste_driver.py      # Teste isolado do Crawler
└── assets/                  # Imagens e Ícones

## 🏗️ Arquitetura Modular

### 1. Fachada (app/converters/web_converter.py)
**Papel:** Atua como porteiro. A GUI só conversa com ele.

**Responsabilidades:**
- Instancia o `WebCrawlerService` e delega as chamadas
- Mantém compatibilidade com métodos antigos (`process_web`, `scan_pages`)
- Fornece wrappers para a GUI

### 2. Motor Web (app/converters/web_engine/)

O antigo "God Object" foi dividido em responsabilidades únicas:

#### 🕷️ crawler.py (O Navegador)
**Responsabilidades:**
- Gerencia o ciclo de vida do `AsyncWebCrawler`
- Implementa paralelização com `asyncio.gather()` (chunks de 5 URLs)
- Cache de páginas (TTL 1h)
- Extração de links internos (ordem preservada)
- **Isolamento de Sessão:** `session_id` único por página (evita cache cruzado)
- **Deduplicação:** Hash check para conteúdo repetido (descarta lixo)

**Configurações Críticas:**
- ✅ Fix `asyncio.WindowsProactorEventLoopPolicy()` para Windows
- ✅ Importações globais do `crawl4ai` (previne deadlocks)
- ✅ CSS Selector Strategy (`main, article, [role='main']`)
- ✅ Ordem de links preservada (lista em vez de set)
- ✅ Isolamento SPA: Sessão limpa por URL
- ✅ Deduplicação Inteligente: Evita salvar conteúdo fantasma

#### 🧹 cleaner.py (O Faxineiro)
**Responsabilidades:**
- Lógica de limpeza de Markdown
- Remove tags `<script>`, `<style>` e lixo de navegação
- **Zona de Segurança:** Linhas > 60 caracteres preservadas
- **Filtro de Densidade:** Remove blocos de 3+ links consecutivos
- **Limpeza Aprimorada:** Keywords expandidos (menus, headers de site)

#### 🔍 analyzer.py (O Detetive)
**Responsabilidades:**
- Detecta tecnologia: SSR vs CSR (Angular/React)
- Define estratégias de JS e timeouts otimizados
- **Expansão de Accordions:** JavaScript para abrir menus laterais
- **CSS Wait Strategy:** `wait_for="main, article, [role='main']"`

#### 📝 logger.py (O Escriba)
**Responsabilidades:**
- Configura logs rotativos UTF-8
- Detecção de modo compilado (.EXE) vs Dev
- **Diagnóstico Forense:** Ambiente, ciclo de vida, crashes
- **Excepthook Paranóico:** Captura exceptions não tratadas

## ⚙️ Fluxo de Execução (Spider Mode Interativo)

```mermaid
graph TD
    A[👤 Usuário] -->|URL + Spider Check| B[🖥️ GUI Window]
    B -->|Inicia| C[🔍 WebScanWorker]
    C -->|Chama| D[🏢 WebConverter Facade]
    D -->|Delega| E[🕷️ Crawler.scan_pages]
    E -->|Smart Retry + Headers| F[🌐 Internet]
    E -->|📋 Lista de Páginas| B
    B -->|Abre| G[📋 PageSelectionDialog]
    A -->|✅ Seleciona Páginas| G
    G -->|📋 Lista Filtrada| H[📥 WebCrawlWorker]
    H -->|Chama| I[🏢 WebConverter Facade]
    I -->|Delega| J[🕷️ Crawler.crawl_selected_pages]
    J -->|🔄 Asyncio Gather (Chunks 5)| F
    J -->|📄 Markdown Bruto| K[🧹 Cleaner]
    K -->|📄 Markdown Limpo| L[💾 Arquivo .md]
```
## ⚠️ Regras de Ouro (Configurações Críticas)

> **🚨 ALERTA CRÍTICO:** Estas configurações garantem a estabilidade do sistema. Não altere sem análise profunda!

### 🔧 Windows Proactor Loop
> **Local:** `crawler.py` (linha ~15)  
> **Por que:** Sem isso, o Playwright trava silenciosamente dentro de QThreads
> ```python
> if sys.platform.startswith('win'):
>     asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
> ```

### 🔧 Imports Globais
> **Local:** `crawler.py` (topo do arquivo)  
> **Por que:** Previna deadlocks de importação dinâmica em asyncio.run()
> ```python
> from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
> ```

### 🔧 UTF-8 Force
> **Local:** `logger.py` (linha ~10)  
> **Por que:** Títulos com emojis/setas quebram o app no Windows
> ```python
> if sys.platform.startswith('win'):
>     sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
> ```

### 🔧 Filtro Relaxado
> **Local:** `crawler.py` - método `extract_internal_links`  
> **Por que:** Descoberta completa de links válidos
> ```python
> # Filtra APENAS domínio (não path_prefix)
> if parsed.netloc == parsed_base.netloc:
>     links.add(normalized)
> ```

🛠️ Comandos de Manutenção
Instalação:

Bash

pip install -r requirements.txt
playwright install
Rodar em Dev:

Bash

python main.py
Build para Produção (.exe):

Bash

# Certifique-se de que os assets estão na pasta correta
pyinstaller Pdf2mdConverter.spec
## 🔍 Sistema de Logging Paranóico

### Arquitetura Centralizada
- **Pasta:** `logs/` (na raiz do projeto)
- **Arquivo Principal:** `logs/debug_trace.log`
- **Modo Duplo:** Console + Arquivo (persistência imediata)
- **Root Logger:** Captura logs de TODAS as bibliotecas (crawl4ai, asyncio, etc.)

### Diagnóstico Forense Completo
- **Inicialização:** Ambiente Python, sistema operacional, encodings
- **Ciclo de Vida:** Aplicação iniciada/fechada, cliques de botões, workers
- **Fluxo de Conversão:** Spider Mode decision, scan results, crawl progress
- **Captura de Crashes:** Excepthook personalizado para exceptions não tratadas
- **Persistência:** Flush imediato para capturar crashes súbitos

## ✅ Status V3.0 - SISTEMA OPERACIONAL
Arquitetura: Modular (App Package) - 5 pacotes coesos

Crawler: Asyncio + Paralelismo (Chunks 5) + CSS Selector Strategy + Isolamento SPA

UX: Painel Profissional + Scan → Seleção → Download

Interface: Painel de Controle + Progresso Real + Tokens Automáticos

Estabilidade: Blindado contra SSL/Encoding/Event Loops + Logger Paranóico

Logger: Forense Completo + Excepthook + Ciclo de Vida

Performance: Expansão Accordions + Conteúdo Limpo + Deduplicação Inteligente

## 🔬 O Que Falta Ser Testado
- End-to-End com sites SPA variados (Angular, React, Vue)
- Casos extremos: Timeouts, sites pesados, roteamento complexo
- Validação de limpeza: Confirmar remoção de menus sem perder conteúdo
- Stress Test: Múltiplas conversões simultâneas