# LLM Context Builder V3.0

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)
[![PyQt6](https://img.shields.io/badge/PyQt6-6.0+-green.svg)](https://pypi.org/project/PyQt6/)
[![crawl4ai](https://img.shields.io/badge/crawl4ai-0.7.8-orange.svg)](https://pypi.org/project/crawl4ai/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Conversor avançado PDF/Web → Markdown com arquitetura modular e multi-threading. Suporte completo a SPAs (Angular/React/Vue) com isolamento de sessão e deduplicação inteligente.

## ✨ Funcionalidades

- **Conversão PDF:** Processamento via PyMuPDF4LLM
- **Spider Mode:** Crawling interativo de sites SPA com detecção automática de tecnologia
- **Interface Gráfica:** PyQt6 profissional com progresso real e contagem de tokens
- **Limpeza Inteligente:** Remoção automática de menus, navegação e conteúdo duplicado
- **Logger Paranóico:** Diagnóstico forense completo com excepthook

## 🚀 Instalação

```bash
# Clone o repositório
git clone https://github.com/SEU_USERNAME/LLM-Context-Builder.git
cd LLM-Context-Builder

# Instale dependências
pip install -r requirements.txt

# Instale Playwright (para web crawling)
playwright install
```

## 📖 Uso

```bash
python main.py
```

1. Abra a interface gráfica
2. Escolha PDF ou Web
3. Configure opções (Spider Mode para sites)
4. Selecione páginas e converta

## 🏗️ Arquitetura

```
app/
├── gui/                 # Interface PyQt6
│   ├── main_window.py   # Janela principal
│   ├── tabs/            # Abas PDF/Web
│   └── workers.py       # QThreads para processamento
├── converters/          # Lógica de negócio
│   ├── pdf_converter.py # Conversão PDF
│   └── web_converter.py # Fachada Web
│       └── web_engine/  # Motor Web
│           ├── crawler.py   # Crawling + isolamento
│           ├── analyzer.py  # Detecção tecnologia
│           ├── cleaner.py   # Limpeza Markdown
│           └── logger.py    # Logging forense
└── utils/
    └── token_counter.py # Contagem tokens
```

## 🔧 Build para Produção

```bash
pyinstaller Pdf2mdConverter.spec
```

Gera executável standalone (.exe) na pasta `dist/`.

## 📋 Requisitos

- Python 3.12+
- PyQt6
- crawl4ai
- PyMuPDF4LLM
- BeautifulSoup4

## 📄 Licença

MIT License - veja [LICENSE](LICENSE) para detalhes.

## 🤝 Contribuições

Feito inteiro com Opencode! Veja [AGENTS.md](AGENTS.md) para arquitetura técnica.
