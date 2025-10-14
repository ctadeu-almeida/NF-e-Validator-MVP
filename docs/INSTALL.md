# Guia de Instalação - NF-e Validator MVP

**Versão:** 1.0.0-mvp
**Tempo estimado:** 5-10 minutos

---

## 📋 Pré-requisitos

- **Python 3.10+** instalado
- **pip** atualizado (`python -m pip install --upgrade pip`)
- **(Opcional)** Google API Key para usar o Agente IA

---

## 🚀 Instalação Rápida (MVP)

### 1. Clonar/Baixar o Projeto

```bash
cd C:\app\ProgFinal
```

### 2. Criar Ambiente Virtual (Recomendado)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

### 3. Instalar Dependências

**Opção A: Instalação Mínima (MVP)**
```bash
pip install -r requirements-mvp.txt
```

**Opção B: Instalação Completa (com dev tools)**
```bash
pip install -r requirements.txt
```

### 4. Popular o Database

```bash
python scripts/populate_db.py
```

**Saída esperada:**
```
[*] Populando Database - NF-e Validator MVP
[OK] 5 NCMs inseridos
[OK] 7 CSTs inseridos
[OK] 7 CFOPs inseridos
[OK] 3 regras estaduais inseridas
[OK] 5 referências legais inseridas
[STATS] Total de registros: 27
```

### 5. Verificar Instalação

```bash
python tests/test_integration.py
```

**Resultado esperado:**
```
Passed: 5/5
[SUCCESS] All tests passed!
```

---

## 🎯 Executando o MVP

### Opção 1: Interface Streamlit (Recomendado)

```bash
python run_streamlit.py
```

Acesse: **http://localhost:8501**

### Opção 2: CLI (Testes)

```bash
python tests/test_integration.py
```

Relatórios gerados em `tests/output/`

### Opção 3: Python API

```python
from repositories.fiscal_repository import FiscalRepository
from nfe_validator.infrastructure.parsers.csv_parser import NFeCSVParser
from nfe_validator.domain.services.federal_validators_v2 import NCMValidator

# Inicializar
repo = FiscalRepository()
parser = NFeCSVParser()

# Parsear CSV
nfes = parser.parse_csv('tests/data/nfe_valid.csv')

# Validar
validator = NCMValidator(repo)
for item in nfes[0].items:
    errors = validator.validate(item, nfes[0])
    print(f"Erros: {len(errors)}")
```

---

## 🤖 Configurar Agente IA (Opcional)

### 1. Obter Google API Key

1. Acesse: https://makersuite.google.com/app/apikey
2. Crie uma nova API key
3. Copie a key

### 2. Configurar Variável de Ambiente

**Windows (PowerShell):**
```powershell
$env:GOOGLE_API_KEY = "YOUR_API_KEY_HERE"
```

**Windows (CMD):**
```cmd
set GOOGLE_API_KEY=YOUR_API_KEY_HERE
```

**Linux/Mac:**
```bash
export GOOGLE_API_KEY="YOUR_API_KEY_HERE"
```

### 3. Testar Agente

```python
from repositories.fiscal_repository import FiscalRepository
from agents.ncm_agent import create_ncm_agent

repo = FiscalRepository()
agent = create_ncm_agent(repo)  # Usa GOOGLE_API_KEY env var

result = agent.classify_ncm("Açúcar cristal tipo 1")
print(result)
```

---

## 📦 Estrutura de Arquivos

Após instalação, você terá:

```
C:\app\ProgFinal\
├── src/
│   ├── nfe_validator/        # Validadores
│   ├── repositories/         # Database access
│   ├── database/
│   │   └── rules.db          # Database populado ✅
│   ├── agents/               # LangChain agents
│   └── interface/            # Streamlit UI
├── tests/
│   ├── data/                 # CSVs de teste
│   └── output/               # Relatórios gerados
├── scripts/
│   └── populate_db.py        # Popula database
├── requirements.txt          # Dependências completas
├── requirements-mvp.txt      # Dependências mínimas
├── run_streamlit.py          # Launcher Streamlit
└── README_MVP.md             # Documentação completa
```

---

## 🔧 Troubleshooting

### Erro: "No module named 'langchain'"

**Solução:**
```bash
pip install langchain langchain-core langchain-google-genai
```

### Erro: "GOOGLE_API_KEY not found"

**Solução:**
- Configure a variável de ambiente (ver seção "Configurar Agente IA")
- Ou passe a key diretamente: `create_ncm_agent(repo, api_key="YOUR_KEY")`

### Erro: "Database not found"

**Solução:**
```bash
python scripts/populate_db.py
```

### Erro: Unicode/Encoding (Windows)

**Sintoma:** Caracteres estranhos em prints (ex: "A��car")

**Solução:** Adicione ao início do script:
```python
import sys
import locale
sys.stdout.reconfigure(encoding='utf-8')
```

### Porta 8501 já em uso

**Solução:**
```bash
streamlit run src/interface/streamlit_app.py --server.port=8502
```

---

## 📊 Verificar Instalação

### Database

```bash
python -c "from repositories.fiscal_repository import FiscalRepository; repo = FiscalRepository(); print(repo.get_statistics())"
```

**Saída esperada:**
```
{'ncm_rules': 5, 'pis_cofins_rules': 7, 'cfop_rules': 7, 'state_overrides': 3, 'legal_refs': 5}
```

### Validadores

```bash
python -c "from nfe_validator.domain.services.federal_validators_v2 import NCMValidator; from repositories.fiscal_repository import FiscalRepository; v = NCMValidator(FiscalRepository()); print('NCMValidator OK')"
```

### Streamlit

```bash
streamlit --version
```

---

## 🎓 Próximos Passos

1. ✅ **Ler documentação completa:** `README_MVP.md`
2. ✅ **Testar com CSVs de exemplo:** `tests/data/*.csv`
3. ✅ **Explorar interface Streamlit:** `python run_streamlit.py`
4. ✅ **Customizar validações:** Modificar `state_validators.py`
5. ✅ **Adicionar novos NCMs:** Editar `scripts/populate_db.py`

---

## 💡 Dicas

### Performance

- Use `@st.cache_resource` no Streamlit para cache do repository
- Database SQLite é rápido o suficiente para MVP (< 100 registros)
- Para produção, considere PostgreSQL

### Desenvolvimento

```bash
# Rodar testes
pytest tests/

# Formatar código
black src/

# Checar tipos
mypy src/
```

### Logs

```bash
# Ver logs do Streamlit
tail -f ~/.streamlit/logs/*.log
```

---

## 📞 Suporte

**Problemas comuns:** Consulte README_MVP.md seção "Troubleshooting"
**Issues:** https://github.com/[repo]/issues
**Documentação:** README_MVP.md

---

## ✅ Checklist de Instalação

- [ ] Python 3.10+ instalado
- [ ] Ambiente virtual criado e ativado
- [ ] Dependências instaladas (`requirements-mvp.txt` ou `requirements.txt`)
- [ ] Database populado (`python scripts/populate_db.py`)
- [ ] Testes passando (`python tests/test_integration.py`)
- [ ] Streamlit funcionando (`python run_streamlit.py`)
- [ ] (Opcional) Google API Key configurada para Agente IA

---

**🎉 Instalação Concluída!**

Você está pronto para validar NF-es do setor sucroalcooleiro.

*Tempo total: ~5 minutos*
