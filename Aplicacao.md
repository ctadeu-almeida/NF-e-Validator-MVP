# Aplicação NF-e Validator MVP

## 📋 Visão Geral

Sistema de validação automatizada de Notas Fiscais Eletrônicas (NF-e) focado no setor sucroalcooleiro (açúcar) para os estados de São Paulo e Pernambuco. Implementa validação fiscal multi-camadas com capacidade de análise via IA.

---

## 🏗️ Arquitetura

### Stack Tecnológico

**Core:**
- Python 3.10+
- Streamlit 1.32+ (Framework Web)
- Pandas 2.x (Processamento de dados)
- SQLite 3 (Base de conhecimento fiscal)

**IA/ML:**
- Google Gemini 2.5 Flash (LLM via API)
- LangChain (Orquestração de agentes)

**Validação:**
- Decimal (Precisão financeira)
- Regex (Normalização de dados)

---

## 📊 Fluxo de Dados

### 1. Ingestão de Dados

```
CSV Upload → Detecção de Encoding → Pipeline de Limpeza → Parser NF-e
```

**Componentes:**
- `src/data_processing/csv_pipeline.py`: Detecção automática de separador e encoding
- `src/nfe_validator/infrastructure/parsers/csv_parser.py`: Parsing e normalização

**Transformações:**
- NCM: 8 dígitos (zero-padding à direita)
- CFOP: 4 dígitos (zero-padding à esquerda)
- CST: 2 dígitos (zero-padding à esquerda)
- CNPJ: 14 dígitos numéricos
- Chave NF-e: String (evita notação científica)

### 2. Validação em Camadas

```
Layer 1: CSV Local (base_validacao.csv)
    ↓ (cache miss)
Layer 2: SQLite (rules.db)
    ↓ (não encontrado)
Layer 3: LLM Gemini (fallback opcional)
```

**Repositório:**
- `src/repositories/fiscal_repository.py`: Query em camadas
- `src/repositories/local_csv_repository.py`: Cache local

### 3. Motor de Validação

```
NFeEntity → Validators → ValidationError[] → AuditReport
```

**Validadores:**
- `NCMValidator`: Código NCM válido e compatível com descrição
- `PISCOFINSValidator`: CST válido + alíquotas corretas (1.65% / 7.60%)
- `CFOPValidator`: CFOP compatível com operação (interna/interestadual)
- `StateRulesValidator`: Regras específicas SP/PE (ICMS, ST)

**Severidade:**
- `CRITICAL`: Bloqueio de operação
- `ERROR`: Incorreção fiscal
- `WARNING`: Atenção necessária
- `INFO`: Informativo

### 4. Agentes de IA

```
UserRequest → OrquestradorAgente → [AgenteFiscal, AgenteNCM, AgenteCalculo]
                                          ↓
                                    Gemini 2.5 Flash API
```

**Agentes Implementados:**
- `AgenteFiscal`: Análise tributária geral
- `AgenteNCM`: Classificação NCM via descrição do produto
- `AgenteCalculo`: Validação de cálculos fiscais

**Configuração:**
- `src/agents/base_agent.py`: Classe base LangChain
- `src/config/agents_config.py`: Configuração de prompts

---

## 🗄️ Modelo de Dados

### Entidades Principais

```python
NFeEntity
├── chave_acesso: str
├── emitente: Empresa
├── destinatario: Empresa
├── items: List[NFeItem]
│   ├── ncm: str
│   ├── cfop: str
│   ├── impostos: ImpostoItem
│   │   ├── pis_cst: str
│   │   ├── pis_aliquota: Decimal
│   │   ├── cofins_cst: str
│   │   └── cofins_aliquota: Decimal
│   └── valor_total: Decimal
├── totais: TotaisNFe
└── validation_errors: List[ValidationError]
```

### Schema SQLite (`rules.db`)

**Tabelas:**
- `ncm_rules`: NCMs válidos com regime PIS/COFINS
- `pis_cofins_rules`: CSTs e alíquotas padrão
- `cfop_rules`: CFOPs válidos por tipo de operação
- `state_overrides`: Regras específicas SP/PE
- `legal_refs`: Base legal de referências

**Views:**
- `v_sugar_ncms`: NCMs do setor sucroalcooleiro
- `v_sugar_cfops`: CFOPs comuns para açúcar

---

## 🔄 Pipeline de Processamento

### ETL (Extract, Transform, Load)

```python
# 1. Extract
df = pd.read_csv(file, dtype={'chave_acesso': str, 'pis_cst': str})

# 2. Transform
df = normalize_columns(df)  # Rename colunas
df = remove_duplicates(df)
df['ncm'] = df['ncm'].apply(normalize_ncm)  # 8 dígitos
df['pis_cst'] = df['pis_cst'].apply(normalize_cst)  # 01 → "01"

# 3. Load
for group in df.groupby('chave_acesso'):
    nfe = parse_nfe_group(group)
    nfes.append(nfe)
```

### Validação

```python
# Validação local
validator = NFeValidator(repo=FiscalRepository())
nfe = validator.validate(nfe_entity)

# Validação com IA (opcional)
if user_requests_ai:
    ai_result = validate_with_gemini(nfe, item_numero)
    nfe.apply_ai_suggestions(ai_result)
```

### Geração de Relatórios

```python
generator = ReportGenerator()
markdown = generator.generate_markdown_report(nfe)
json_report = generator.generate_json_report(nfe)
```

---

## 📦 Estrutura de Diretórios

```
progfinal/
├── app.py                          # Streamlit UI principal
├── src/
│   ├── agents/                     # Agentes LLM
│   │   ├── base_agent.py
│   │   ├── fiscal_agent.py
│   │   └── ncm_agent.py
│   ├── config/
│   │   ├── agents_config.py        # Configuração de agentes
│   │   └── settings.py
│   ├── data_processing/
│   │   └── csv_pipeline.py         # ETL de CSV
│   ├── database/
│   │   ├── rules.db                # SQLite fiscal
│   │   └── schema.sql
│   ├── nfe_validator/
│   │   ├── domain/
│   │   │   └── entities/
│   │   │       └── nfe_entity.py   # Modelo de domínio
│   │   ├── infrastructure/
│   │   │   ├── parsers/
│   │   │   │   └── csv_parser.py   # Parser NF-e
│   │   │   └── validators/
│   │   │       ├── ncm_validator.py
│   │   │       ├── pis_cofins_validator.py
│   │   │       ├── cfop_validator.py
│   │   │       ├── state_rules_validator.py
│   │   │       └── report_generator.py
│   │   └── use_cases/
│   │       └── validate_nfe.py     # Caso de uso principal
│   └── repositories/
│       ├── fiscal_repository.py    # Acesso SQLite
│       └── local_csv_repository.py # Cache CSV
└── test_data/
    ├── nfe_teste_controlado.csv    # Dataset de testes
    └── RESULTADOS_ESPERADOS.md     # Casos de teste documentados
```

---

## 🔌 Integrações

### Google Gemini API

```python
import google.generativeai as genai

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

response = model.generate_content(prompt)
```

**Rate Limits:**
- 15 RPM (requests por minuto)
- 1M TPM (tokens por minuto)
- 1500 RPD (requests por dia)

### Streamlit Session State

```python
# Cache de validações
st.session_state.validation_results = {}
st.session_state.ai_suggestions = {}
st.session_state.current_nfe = None
```

---

## 🧪 Testes

### Dataset Controlado

`test_data/nfe_teste_controlado.csv` - 20 NF-es sintéticas:

- ✅ 5 notas corretas
- ⚠️ 5 notas com dados faltantes
- 🔴 5 notas com impostos pagos a mais
- 🟡 5 notas com impostos pagos a menos

### Validação de Resultados

Comparação automática com `RESULTADOS_ESPERADOS.md`:
- Assertividade de detecção de erros
- Precisão de cálculos tributários
- Impacto financeiro estimado

---

## ⚡ Otimizações

### Performance

1. **Lazy Loading:** Validação sob demanda por item
2. **Cache em Camadas:** CSV → SQLite → LLM
3. **Batch Processing:** Validação em lote com progress bar
4. **Conexão Persistente:** SQLite com `check_same_thread=False`

### Normalização de Dados

```python
# Evitar notação científica em chaves NF-e
dtype_spec = {'chave_acesso': str}
df = pd.read_csv(file, dtype=dtype_spec)
df['chave_acesso'] = df['chave_acesso'].str.replace('.0', '')

# Preservar zeros à esquerda em CST
df['pis_cst'] = df['pis_cst'].str.zfill(2)  # '1' → '01'
```

### JSON Serialization

```python
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.int64):
            return int(obj)
        elif isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)
```

---

## 📊 Métricas de Validação

### KPIs do Sistema

- **Taxa de Validação:** % de NF-es processadas com sucesso
- **Economia Identificada:** Soma de `financial_impact` positivo
- **Risco Fiscal:** Soma de `financial_impact` negativo
- **Cobertura de Regras:** NCMs/CFOPs na base vs. encontrados

### Auditoria

```python
AuditReport
├── total_errors: int
├── critical_count: int
├── error_count: int
├── warning_count: int
├── total_financial_impact: Decimal
└── recommendations: List[str]
```

---

## 🔐 Segurança

### API Keys

```python
# Variáveis de ambiente
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Validação
if not GEMINI_API_KEY:
    st.warning("⚠️ API Key do Gemini não configurada")
```

### Validação de Entrada

- Sanitização de CSV (encoding/separador)
- Validação de formato de CNPJ/NCM/CFOP
- Limite de tamanho de arquivo (100 MB)
- Timeout em chamadas LLM (60s)

---

## 📈 Escalabilidade

### Limitações Atuais

- **Processamento:** Single-thread (Streamlit)
- **Storage:** SQLite (até ~1M registros)
- **Concorrência:** 1 usuário por instância

### Melhorias Futuras

1. **Backend Assíncrono:** FastAPI + Celery
2. **Database:** PostgreSQL com índices GIN
3. **Cache Distribuído:** Redis
4. **Processamento:** Apache Spark para batch
5. **Deploy:** Docker + Kubernetes

---

## 📝 Logs e Debugging

### Logging

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info(f"✅ NF-e {chave} validada com {len(errors)} erros")
logger.warning(f"⚠️ NCM {ncm} não encontrado na base local")
logger.error(f"❌ Erro ao parsear NF-e: {exception}")
```

### Debug Mode

```python
# Streamlit debug
st.write("🐛 Debug:", nfe_entity.__dict__)
st.json(validation_result)
```

---

## 🚀 Deploy

### Requirements

```txt
streamlit>=1.32.0
pandas>=2.0.0
google-generativeai>=0.3.0
langchain>=0.1.0
python-dotenv>=1.0.0
```

### Execução Local

```bash
# Instalar dependências
pip install -r requirements.txt

# Configurar API key
export GEMINI_API_KEY="sua-chave-aqui"

# Executar aplicação
streamlit run app.py --server.port 8501
```

### Ambiente de Produção

```bash
streamlit run app.py \
    --server.port 80 \
    --server.address 0.0.0.0 \
    --server.maxUploadSize 100
```

---

## 📚 Base Legal Implementada

### Legislação Federal

- **Lei 10.637/2002:** PIS não-cumulativo
- **Lei 10.833/2003:** COFINS não-cumulativo
- **IN RFB 2.121/2022:** Tabela NCM/TIPI
- **Ajuste SINIEF 07/05:** Tabela CFOP

### Legislação Estadual

- **RICMS-SP (Decreto 45.490/2000):** Alíquota ICMS 18% (açúcar)
- **RICMS-PE:** Regras específicas Pernambuco

---

**Versão:** 1.0.0-mvp
**Última Atualização:** 17/10/2025
**Desenvolvido para:** Setor Sucroalcooleiro (Açúcar) - SP/PE
