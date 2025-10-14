# 🚀 Quick Reference - NF-e Validator MVP

**Guia rápido de comandos e exemplos mais usados**

---

## ⚡ Comandos Rápidos

### Instalação

```bash
pip install -r requirements-mvp.txt
python scripts/populate_db.py
```

### Executar

```bash
# Interface Web
python run_streamlit.py

# Testes
python tests/test_integration.py
```

---

## 📝 Exemplos de Código

### 1. Validar CSV Completo

```python
from repositories.fiscal_repository import FiscalRepository
from nfe_validator.infrastructure.parsers.csv_parser import NFeCSVParser
from nfe_validator.domain.services.federal_validators_v2 import *
from nfe_validator.domain.services.state_validators import *

# Setup
repo = FiscalRepository()
parser = NFeCSVParser()

# Parse
nfes = parser.parse_csv('path/to/file.csv')
nfe = nfes[0]

# Validate Federal
for validator in [NCMValidator(repo), PISCOFINSValidator(repo), CFOPValidator(repo)]:
    for item in nfe.items:
        nfe.validation_errors.extend(validator.validate(item, nfe))

# Validate State (SP)
if nfe.emitente.uf == 'SP':
    sp_validator = SPValidator(repo)
    for item in nfe.items:
        nfe.validation_errors.extend(sp_validator.validate(item, nfe))

# Results
print(f"Errors: {len(nfe.validation_errors)}")
print(f"Impact: R$ {nfe.get_total_financial_impact()}")
```

### 2. Gerar Relatório

```python
from nfe_validator.infrastructure.validators.report_generator import ReportGenerator

generator = ReportGenerator()

# Markdown
md = generator.generate_markdown_report(nfe)
with open('report.md', 'w', encoding='utf-8') as f:
    f.write(md)

# JSON
json_report = generator.generate_json_report(nfe)
import json
with open('report.json', 'w', encoding='utf-8') as f:
    json.dump(json_report, f, ensure_ascii=False, indent=2)
```

### 3. Usar Agente IA

```python
from agents.ncm_agent import create_ncm_agent

agent = create_ncm_agent(repo, api_key="YOUR_KEY")

result = agent.classify_ncm(
    product_description="Açúcar cristal tipo 1 - saco 50kg",
    current_ncm="17019900"
)

print(f"NCM Sugerido: {result['suggested_ncm']}")
print(f"Confiança: {result['confidence']}%")
print(f"Correto: {result['is_correct']}")
```

### 4. Consultar Database

```python
# NCMs de açúcar
ncms = repo.get_all_sugar_ncms()
for ncm in ncms:
    print(f"{ncm['ncm']}: {ncm['description']}")

# Alíquotas PIS/COFINS
rates = repo.get_pis_cofins_rates('01', regime='STANDARD')
print(f"PIS: {rates['pis']}%")  # 1.65
print(f"COFINS: {rates['cofins']}%")  # 7.6

# Regras SP
sp_rules = repo.get_state_rules('SP')
for rule in sp_rules:
    print(f"{rule['rule_name']}: {rule['icms_rate']}%")
```

---

## 📊 NCMs Válidos (Açúcar)

| NCM | Descrição | Tipo |
|-----|-----------|------|
| 17011100 | Açúcar de cana, em bruto | bruto |
| 17011200 | Açúcar de beterraba, em bruto | bruto |
| 17019100 | Açúcar refinado, adicionado de aromatizante | refinado |
| **17019900** | **Outros açúcares de cana ou beterraba** | **cristal** ⭐ |
| 17021100 | Lactose e xarope de lactose | lactose |

⭐ **Mais comum para açúcar cristal**

---

## 🔢 CSTs PIS/COFINS

| CST | Descrição | PIS | COFINS |
|-----|-----------|-----|--------|
| **01** | **Operação Tributável (Alíquota Básica)** | **1.65%** | **7.60%** |
| 04 | Tributação Monofásica | - | - |
| 06 | Alíquota Zero (Exportação) | 0% | 0% |
| 07 | Isenta da Contribuição | 0% | 0% |
| 08 | Sem Incidência | 0% | 0% |
| 49 | Outras Operações de Saída | varia | varia |
| 50 | Operação com Direito a Crédito | varia | varia |

---

## 📦 CFOPs Comuns

| CFOP | Descrição | Escopo |
|------|-----------|--------|
| **5101** | **Venda de produção própria** | **Interno** |
| 5102 | Venda de mercadoria adquirida | Interno |
| **6101** | **Venda de produção própria** | **Interestadual** |
| 6102 | Venda de mercadoria adquirida | Interestadual |
| 7101 | Venda para o exterior | Exportação |
| 1101 | Compra para industrialização | Interno |
| 2101 | Compra para industrialização | Interestadual |

---

## 🏛️ ICMS Estadual

| UF | Alíquota Padrão | ST Açúcar |
|----|-----------------|-----------|
| SP | 18% | Sim |
| PE | 18% | Não |

---

## ⚠️ Severidades

| Severity | Cor | Ação |
|----------|-----|------|
| CRITICAL | 🔴 | Correção IMEDIATA (tributação indevida) |
| ERROR | 🟠 | Correção necessária (cálculo errado) |
| WARNING | 🟡 | Revisão recomendada (inconsistência) |
| INFO | 🔵 | Informativo (sugestão) |

---

## 🗄️ SQL Úteis

```sql
-- Verificar NCM
SELECT * FROM ncm_rules WHERE ncm = '17019900';

-- Listar todos açúcares
SELECT * FROM v_sugar_ncms;

-- CST PIS/COFINS
SELECT * FROM pis_cofins_rules WHERE cst = '01';

-- CFOPs
SELECT * FROM cfop_rules WHERE operation_scope = 'INTERNO';

-- Regras SP
SELECT * FROM state_overrides WHERE state = 'SP';

-- Stats
SELECT
    (SELECT COUNT(*) FROM ncm_rules) as ncms,
    (SELECT COUNT(*) FROM pis_cofins_rules) as csts,
    (SELECT COUNT(*) FROM cfop_rules) as cfops,
    (SELECT COUNT(*) FROM state_overrides) as states,
    (SELECT COUNT(*) FROM legal_refs) as refs;
```

---

## 🐛 Troubleshooting

### Erro: ModuleNotFoundError

```bash
pip install -r requirements-mvp.txt
```

### Erro: Database not found

```bash
python scripts/populate_db.py
```

### Erro: Google API Key

```bash
# Windows PowerShell
$env:GOOGLE_API_KEY = "your-key"

# Linux/Mac
export GOOGLE_API_KEY="your-key"
```

### Porta 8501 ocupada

```bash
streamlit run src/interface/streamlit_app.py --server.port=8502
```

---

## 📁 Arquivos Importantes

| Arquivo | Descrição |
|---------|-----------|
| `src/nfe_validator/domain/services/federal_validators_v2.py` | Validadores federais |
| `src/nfe_validator/domain/services/state_validators.py` | Validadores SP/PE |
| `src/repositories/fiscal_repository.py` | Acesso ao database |
| `src/database/rules.db` | Database SQLite |
| `src/agents/ncm_agent.py` | Agente LangChain |
| `src/interface/streamlit_app.py` | Interface web |
| `tests/test_integration.py` | Testes |
| `tests/data/*.csv` | CSVs de exemplo |

---

## 🔗 Links Úteis

- **README Completo:** `README_MVP.md`
- **Instalação:** `INSTALL.md`
- **Entrega:** `DELIVERY_SUMMARY.md`
- **Este Guia:** `QUICK_REFERENCE.md`

---

## 💡 Dicas

### Performance

```python
# Cache repository no Streamlit
@st.cache_resource
def load_repository():
    return FiscalRepository()
```

### Batch Processing

```python
# Validar múltiplas NF-es
for nfe in nfes:
    # ... validar cada uma
    pass
```

### Custom Validators

```python
class MyCustomValidator:
    def __init__(self, repository):
        self.repo = repository

    def validate(self, item, nfe):
        errors = []
        # ... sua lógica
        return errors
```

---

## 📞 Ajuda Rápida

```bash
# Ver versão do Python
python --version

# Ver versão do Streamlit
streamlit --version

# Testar database
python -c "from repositories.fiscal_repository import FiscalRepository; print(FiscalRepository().get_statistics())"

# Ver estrutura CSV
head -n 2 tests/data/nfe_valid.csv
```

---

**🎯 MVP Ready!**

*Para documentação completa, consulte `README_MVP.md`*
