# 🔍 CSVEDA - Análise Exploratória de Dados com IA

Sistema moderno de análise de dados usando agentes autônomos, Clean Architecture e boas práticas de engenharia.

## ⚡ Funcionalidades

- **Interface Chat**: WhatsApp-style com histórico persistente
- **Agentes IA**: LangChain + Google Gemini
- **Análise Completa**: Estatísticas, correlações, outliers, visualizações
- **Arquitetura Limpa**: Domain-driven design, DI container, testes

## 🚀 Quick Start

```bash
# 1. Clone e instale
git clone <repo>
cd CSVEDA
pip install -r requirements.txt

# 2. Configure (copie .env.example para .env)
cp .env.example .env
# Adicione sua GEMINI_API_KEY

# 3. Execute
streamlit run app.py
```

## 🛠️ Desenvolvimento

```bash
# Testes
pytest

# Qualidade de código
black src/ tests/
ruff check src/ tests/
mypy src/

# CI/CD
# GitHub Actions configurado automaticamente
```

## 📁 Arquitetura

```
src/
├── domain/           # Entidades e serviços de negócio
├── application/      # Casos de uso e interfaces
├── infrastructure/   # Adaptadores e DI container
├── interfaces/       # Abstrações LLM/Agent
└── utils/           # Logger estruturado
```

## 🔧 Stack Técnica

- **Framework**: Streamlit + Pandas
- **IA**: LangChain + Google Gemini
- **Arquitetura**: Clean Architecture + DDD
- **DI**: Container customizado thread-safe
- **Logging**: Estruturado JSON (Loguru)
- **Testes**: Pytest + Coverage
- **CI/CD**: GitHub Actions

---
**Análise de dados com IA e engenharia moderna** 🤖