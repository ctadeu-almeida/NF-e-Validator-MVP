# Sistema EDA + NF-e Validator

**Versão:** 1.0.0
**Módulos:**
- **CSVEDA** - Análise Exploratória de Dados com IA (Gemini 2.5)
- **NF-e Validator** - Validação Fiscal Automatizada para Setor Sucroalcooleiro

Sistema integrado que combina análise exploratória de dados CSV com validação fiscal automatizada de NF-e, utilizando agentes de IA com Google Gemini 2.5.

---

## 🎯 Visão Geral

Este sistema oferece **duas funcionalidades complementares** em uma única aplicação Streamlit:

### 📊 Módulo CSVEDA (Original)
- Análise exploratória de dados CSV/ZIP
- Agentes de IA especializados com Google Gemini 2.5
- Geração automática de gráficos e insights
- Pipeline de processamento de dados
- Mesclagem de múltiplos arquivos CSV
- Chat inteligente para análise de dados

### 🧾 Módulo NF-e Validator (Complementar)
- Validação fiscal automatizada de Notas Fiscais Eletrônicas
- Foco no setor sucroalcooleiro (açúcar)
- Validações federais e estaduais (SP + PE)
- Agente IA para classificação NCM (opcional)
- Relatórios detalhados em JSON e Markdown
- Detecção de tributação indevida

---

## 📋 Escopo - NF-e Validator

### ✅ Validações Implementadas

**Federal (Brasil todo):**
- ✅ NCM × Descrição do produto
- ✅ PIS/COFINS (CST, alíquotas, valores)
- ✅ CFOP (interno vs interestadual)
- ✅ Cálculos e somatórios

**Estadual (SP + PE):**
- ✅ ICMS alíquota padrão (18%)
- ✅ Substituição tributária (SP)
- ✅ Benefícios fiscais (PE)
- ⚠️ Retorna apenas warnings (não-bloqueantes)

**Inteligência Artificial:**
- ✅ Agente LangChain ReAct para classificação NCM
- ✅ Google Gemini 2.5 Pro (atualizado)
- ✅ Raciocínio explicável (reasoning trace)
- ✅ Reutilização automática da API key do EDA

---

## 🏗️ Arquitetura

### Clean Architecture (DDD)

```
src/
├── nfe_validator/
│   ├── domain/              # Entidades e regras de negócio
│   │   ├── entities/        # NFeEntity, ValidationError, etc.
│   │   └── services/        # Validadores (Federal + Estadual)
│   ├── application/         # Casos de uso
│   └── infrastructure/      # Parsers, Generators
├── repositories/            # Acesso ao database
├── database/                # SQLite rules.db
├── agents/                  # LangChain ReAct agents
└── interface/               # Streamlit web UI
```

### Stack Tecnológico

- **Python 3.10+**
- **SQLite** (rules.db - 27 regras fiscais para NF-e)
- **LangChain** (ReAct agent pattern para ambos os módulos)
- **Google Gemini 2.5** (LLM - atualizado)
- **Streamlit** (Interface web unificada com tabs)
- **Pandas** (CSV processing completo, sem limites de linhas)

---

## 🚀 Instalação

### 1. Clonar Repositório

```bash
git clone <repo-url>
cd ProgFinal
```

### 2. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 3. Popular Database

```bash
python scripts/populate_db.py
```

**Resultado esperado:**
```
[*] Populando Database - NF-e Validator MVP
[*] Database: C:\app\ProgFinal\src\database\rules.db
[INFO] Populando NCM Rules...
[OK] 5 NCMs inseridos
[INFO] Populando PIS/COFINS Rules...
[OK] 7 CSTs inseridos
[INFO] Populando CFOP Rules...
[OK] 7 CFOPs inseridos
[INFO] Populando State Overrides...
[OK] 3 regras estaduais inseridas
[INFO] Populando Legal References...
[OK] 5 referências legais inseridas
[STATS] Database populado com sucesso!
Total de registros: 27
```

---

## 📖 Uso

### Interface Streamlit Unificada

```bash
streamlit run app.py
```

Ou use o script helper:

```bash
python run_streamlit.py
```

Acesse: **http://localhost:8501**

A aplicação abrirá com **duas tabs**:

---

### 📊 Tab 1: Análise de Dados (EDA)

**Passo a passo:**

1. **Configurar API Gemini** (sidebar):
   - Insira sua chave da API do Google Gemini
   - Clique em "🚀 Inicializar Modelo"

2. **Upload de Dados** (sidebar):
   - Selecione arquivo CSV ou ZIP
   - Sistema detecta automaticamente o separador (`,`, `;`, `\t`, `|`)
   - Arquivos ZIP são extraídos e mesclados automaticamente
   - **Sem limite de linhas** - arquivo completo é processado

3. **Analisar com Agentes** (área principal):
   - Visualize preview dos dados
   - Faça perguntas no chat: "Analise a correlação entre variáveis"
   - Agentes geram gráficos automaticamente
   - Respostas detalhadas com insights

**Features EDA:**
- ✅ CSV/ZIP upload com mesclagem automática
- ✅ Detecção inteligente de separador
- ✅ Pipeline de normalização de dados
- ✅ Agentes especializados para análise
- ✅ Chat com memória contextual
- ✅ Geração automática de gráficos
- ✅ Análises estatísticas avançadas

---

### 🧾 Tab 2: Validação de NF-e

**Passo a passo:**

1. **Carregar Base Fiscal** (sidebar):
   - Clique em "📚 Carregar Base Fiscal"
   - Sistema carrega 27 regras fiscais do SQLite

2. **(Opcional) Ativar Agente IA para NCM** (sidebar):
   - Marque "🤖 Usar Agente IA para NCM"
   - Se já inicializou Gemini no EDA, a chave é reutilizada automaticamente
   - Caso contrário, insira a chave da API Google

3. **Upload de NF-es** (tab NF-e):
   - Selecione arquivo CSV com notas fiscais
   - Clique em "🔍 Validar NF-es"
   - **Arquivo completo é processado** (sem limites)
   - Sistema valida todas as NF-es encontradas

4. **Visualizar Resultados**:
   - **📋 Relatório**: Visualização formatada em Markdown
   - **📄 JSON**: Estrutura completa para integração
   - **🤖 Sugestões IA**: Recomendações do agente NCM (se ativado)
   - **💾 Downloads**: Baixe relatórios em MD ou JSON

**Features NF-e:**
- ✅ Validação federal (NCM, PIS/COFINS, CFOP, Totais)
- ✅ Validação estadual (SP + PE)
- ✅ Agente IA opcional para NCM (reutiliza API do EDA)
- ✅ Relatórios detalhados (JSON + Markdown)
- ✅ Impacto financeiro calculado
- ✅ Múltiplas NF-es em lote
- ✅ Downloads de relatórios

---

### Validação via CLI (Testes)

Para testar apenas o módulo NF-e sem interface:

```bash
python tests/test_integration.py
```

**Output:**
```
================================================================================
TEST SUMMARY
================================================================================
[OK] test_01_valid
[OK] test_02_ncm_error
[OK] test_03_pis_cofins_error
[OK] test_04_cfop_error
[OK] test_05_totals_error

Passed: 5/5
```

---

## 📁 Formato CSV

### Para Análise EDA

**Qualquer formato CSV:**
- Separadores suportados: `,` `;` `\t` `|` (detecção automática)
- Sem requisitos específicos de colunas
- Processamento completo sem limites de linhas
- Suporte a múltiplos arquivos via ZIP
- Normalização automática de tipos de dados

### Para Validação de NF-e

**Colunas obrigatórias:**

```csv
chave_acesso,numero_nfe,serie,data_emissao,
cnpj_emitente,razao_social_emitente,uf_emitente,
cnpj_destinatario,razao_social_destinatario,uf_destinatario,
numero_item,codigo_produto,descricao,ncm,cfop,
quantidade,unidade,valor_unitario,valor_total,
pis_cst,pis_aliquota,pis_valor,
cofins_cst,cofins_aliquota,cofins_valor,
icms_aliquota,icms_valor,ipi_aliquota,ipi_valor
```

**Exemplo (CSV válido):**

```csv
35250123456789000190550010000001234567890123,123456,1,2025-10-01,
12345678000190,USINA AÇÚCAR SP LTDA,SP,
98765432000110,DISTRIBUIDORA ALIMENTOS LTDA,SP,
1,ACS-001,Açúcar cristal tipo 1 - saco 50kg,17019900,5101,
100,KG,2.50,250.00,
01,1.65,4.13,
01,7.60,19.00,
18.00,45.00,0.00,0.00
```

**CSVs de teste disponíveis:**
- `tests/data/nfe_valid.csv` - NF-e 100% conforme
- `tests/data/nfe_erro_ncm.csv` - Erro de NCM × descrição
- `tests/data/nfe_erro_pis_cofins.csv` - Erro de alíquota PIS/COFINS
- `tests/data/nfe_erro_cfop.csv` - Erro CFOP interno/interestadual
- `tests/data/nfe_erro_totais.csv` - Erro de cálculo

---

## 🔍 Validadores

### Federal Validators (src/nfe_validator/domain/services/federal_validators.py)

#### 1. NCMValidator
- ✅ Verifica se NCM existe no database
- ✅ Valida keywords na descrição do produto
- ⚠️ Severity: WARNING (descrição não contém palavras-chave esperadas)

**NCMs válidos no MVP:**
- `17011100` - Açúcar de cana, em bruto
- `17011200` - Açúcar de beterraba, em bruto
- `17019100` - Açúcar refinado, adicionado de aromatizante
- `17019900` - Outros açúcares de cana ou beterraba (MAIS COMUM)
- `17021100` - Lactose e xarope de lactose

#### 2. PISCOFINSValidator
- ✅ Valida CST PIS/COFINS
- ✅ Verifica alíquotas (1.65% PIS, 7.6% COFINS padrão)
- ✅ Calcula divergência de valores
- 🔴 Severity: CRITICAL (alíquota incorreta = tributação indevida)

**CSTs válidos:**
- `01` - Operação Tributável com Alíquota Básica
- `04` - Tributação Monofásica
- `06` - Alíquota Zero (exportação)
- `07` - Isenta da Contribuição
- `08` - Sem Incidência da Contribuição
- `49` - Outras Operações de Saída
- `50` - Operação com Direito a Crédito

#### 3. CFOPValidator
- ✅ Valida CFOP contra database
- ✅ Verifica consistência interno/interestadual
- 🔴 Severity: CRITICAL (CFOP errado = natureza da operação incorreta)

**CFOPs válidos:**
- `5101` / `6101` - Venda de produção (interno/interestadual)
- `5102` / `6102` - Venda de mercadoria adquirida
- `7101` - Venda de produção para o exterior (exportação)
- `1101` / `2101` - Compra (interno/interestadual)

#### 4. TotalsValidator
- ✅ Valida soma de PIS/COFINS/ICMS dos itens
- ✅ Verifica consistência de cálculos
- 🟠 Severity: ERROR (cálculo incorreto)

### State Validators (src/nfe_validator/domain/services/state_validators.py)

#### SPValidator (São Paulo)
- ⚠️ Alíquota ICMS padrão: 18%
- ⚠️ Substituição Tributária para açúcar
- 🟡 Severity: WARNING (não-bloqueante)

#### PEValidator (Pernambuco)
- ⚠️ Alíquota ICMS padrão: 18%
- ⚠️ Benefícios fiscais disponíveis
- 🔵 Severity: INFO (apenas informativo)

---

## 🤖 Agente IA (LangChain ReAct)

### Uso do Agente NCM

**Arquivo:** `src/agents/ncm_agent.py`

```python
from repositories.fiscal_repository import FiscalRepository
from agents.ncm_agent import create_ncm_agent

# Inicializar
repo = FiscalRepository()
agent = create_ncm_agent(repo, api_key="YOUR_GOOGLE_API_KEY")

# Classificar NCM
result = agent.classify_ncm(
    product_description="Açúcar cristal tipo 1 - saco 50kg",
    current_ncm="17019900"
)

print(result)
# {
#     'suggested_ncm': '17019900',
#     'confidence': 95,
#     'reasoning': 'Thought: ...\nAction: ...\nFinal Answer: ...',
#     'is_correct': True
# }
```

**Tools disponíveis para o agente:**
1. `search_ncm_by_keywords` - Buscar NCMs por palavras-chave
2. `get_ncm_details` - Obter detalhes de NCM específico
3. `list_all_sugar_ncms` - Listar todos os NCMs de açúcar

**Quando usar:**
- ✅ Descrição ambígua (ex: "Açúcar especial")
- ✅ NCM não encontrado no database
- ✅ Múltiplos NCMs possíveis
- ✅ Validação de NCM atual

**Configuração:**

Defina a variável de ambiente:
```bash
export GOOGLE_API_KEY="your-api-key-here"
```

Ou passe via parâmetro:
```python
agent = create_ncm_agent(repo, api_key="your-key")
```

---

## 📊 Relatórios

### JSON Report (Estruturado)

```json
{
  "metadata": {
    "report_version": "1.0.0-mvp",
    "generated_at": "2025-10-13T16:47:37",
    "validator": "NF-e Validator MVP - Setor Sucroalcooleiro"
  },
  "nfe_info": {
    "chave_acesso": "35250...",
    "numero": "123456",
    "emitente": {...},
    "destinatario": {...}
  },
  "validation_summary": {
    "status": "INVALID",
    "total_errors": 2,
    "by_severity": {
      "CRITICAL": 2,
      "ERROR": 0,
      "WARNING": 0,
      "INFO": 0
    }
  },
  "financial_impact": {
    "total": 30.00,
    "currency": "BRL"
  },
  "errors": [
    {
      "code": "PIS_002",
      "field": "pis_aliquota",
      "severity": "CRITICAL",
      "expected": "1.65",
      "actual": "3.00",
      "legal_reference": "Lei 10.637/2002",
      "financial_impact": 10.80
    }
  ]
}
```

### Markdown Report (Legível)

```markdown
# 📋 RELATÓRIO DE AUDITORIA FISCAL

**NF-e Validator MVP** - Setor Sucroalcooleiro

## 📊 RESUMO DA VALIDAÇÃO

**Status:** ❌ INVALID

| Severidade | Quantidade |
|------------|------------|
| 🔴 CRÍTICO | 2          |
| 🟠 ERRO    | 0          |
| 🟡 AVISO   | 0          |

### 💰 IMPACTO FINANCEIRO
**Economia Potencial:** R$ 30.00

## 🔍 DETALHAMENTO DOS ERROS

### 1. Alíquota PIS incorreta: 3.00%

📚 **Base Legal:** Lei 10.637/2002
💡 **Sugestão:** Alíquota correta: 1.65%
```

---

## 🗄️ Database (rules.db)

### Schema

**5 Tabelas:**
1. `ncm_rules` - Regras de NCM (5 registros)
2. `pis_cofins_rules` - Regras PIS/COFINS (7 registros)
3. `cfop_rules` - Regras CFOP (7 registros)
4. `state_overrides` - Regras estaduais SP/PE (3 registros)
5. `legal_refs` - Referências legais (5 registros)

**Total:** 27 registros

### Consultas Úteis

```sql
-- Listar todos os NCMs de açúcar
SELECT * FROM v_sugar_ncms;

-- Buscar alíquotas PIS/COFINS para CST 01
SELECT pis_rate_standard, cofins_rate_standard
FROM pis_cofins_rules
WHERE cst = '01';

-- Verificar regras de SP
SELECT * FROM state_overrides WHERE state = 'SP';
```

---

## 🧪 Testes

### Integration Tests (tests/test_integration.py)

**5 cenários de teste:**

1. ✅ **test_01_valid** - NF-e 100% conforme
2. ⚠️ **test_02_ncm_error** - NCM × descrição incompatível
3. 🔴 **test_03_pis_cofins_error** - Alíquotas PIS/COFINS incorretas
4. 🔴 **test_04_cfop_error** - CFOP interno usado em operação interestadual
5. 🟠 **test_05_totals_error** - Erro de cálculo (valor_total ≠ qtd × valor_unit)

**Rodar testes:**

```bash
python tests/test_integration.py
```

**Resultado esperado:** Passed: 5/5

**Outputs gerados:**
- `tests/output/test_XX_report.json`
- `tests/output/test_XX_report.md`

---

## 📚 Base Legal

### Legislação Federal

1. **Lei 10.637/2002** - Lei do PIS não-cumulativo
2. **Lei 10.833/2003** - Lei da COFINS não-cumulativa
3. **IN RFB 2.121/2022** - Normas sobre PIS/COFINS
4. **TIPI Capítulo 17** - Tabela de IPI para açúcares
5. **SINIEF 07/05** - Tabela de CFOP

### Legislação Estadual

**São Paulo:**
- RICMS/SP - Alíquota padrão 18%
- Decreto XX/YYYY - Substituição tributária

**Pernambuco:**
- RICMS/PE - Alíquota padrão 18%
- Decreto YY/ZZZZ - Benefícios fiscais

---

## 🔄 Integração dos Módulos

### Características da Integração

**Independência:**
- Cada módulo funciona independentemente
- NF-e Validator não requer inicialização do EDA
- EDA funciona normalmente sem carregar base fiscal

**Compartilhamento Inteligente:**
- ✅ API Key do Gemini reutilizada entre módulos
- ✅ Mesmo ambiente Streamlit
- ✅ Interface unificada com tabs
- ✅ Sessão compartilhada (mas estados separados)

**Processamento de Arquivos:**
- ✅ **Leitura completa** sem limites de linhas em ambos os módulos
- ✅ EDA: múltiplos CSVs via ZIP com mesclagem automática
- ✅ NF-e: processamento em lote de múltiplas notas
- ✅ Detecção automática de formato (EDA)
- ✅ Normalização específica por domínio

**Agentes de IA:**
- EDA: Agentes especializados em análise exploratória
- NF-e: Agente opcional para classificação NCM
- Ambos usam Google Gemini 2.5 Pro
- ReAct pattern (Reasoning + Acting)

---

## 🛣️ Roadmap Pós-MVP

### Fase 2 (Expansão)

- [ ] Suporte a etanol (NCMs 2207.10.00, 2207.20.00)
- [ ] Validações para MG, RJ, PR
- [ ] ICMS-ST detalhado (MVA, redução de BC)
- [ ] Upload de XML (layout oficial NF-e)

### Fase 3 (Avançado)

- [ ] Dashboard analytics (Power BI / Metabase)
- [ ] API REST para integração
- [ ] Batch processing (múltiplas NF-es)
- [ ] Histórico de validações

### Fase 4 (Escalabilidade)

- [ ] PostgreSQL (substituir SQLite)
- [ ] Cache Redis
- [ ] Kubernetes deployment
- [ ] Multi-tenant

---

## 🤝 Contribuindo

### Guidelines

1. Seguir Clean Architecture
2. Testes obrigatórios para novos validadores
3. Documentar base legal para todas as regras
4. Manter database atualizado

### Estrutura de Commits

```
feat: adicionar validador de IPI
fix: corrigir cálculo de ICMS-ST
docs: atualizar README com novos NCMs
test: adicionar test_06_ipi_error
```

---

## 📞 Suporte

**Issues:** https://github.com/[repo]/issues
**Docs:** https://docs.[projeto].com

---

## 📄 Licença

MIT License

---

## 👥 Autores

**Desenvolvido para o setor sucroalcooleiro brasileiro** ❤️

*Version 1.0.0 - Outubro 2025*

---

## 📝 Changelog

### v1.0.0 (Atual)
- ✅ Integração completa CSVEDA + NF-e Validator
- ✅ Interface unificada com tabs independentes
- ✅ Atualização para Google Gemini 2.5 Pro
- ✅ Remoção de limites de linhas no processamento CSV
- ✅ Reutilização automática de API key entre módulos
- ✅ SQLite com thread safety para Streamlit (`check_same_thread=False`)
- ✅ Suporte a Windows (temp directory cross-platform)
- ✅ Processamento completo de arquivos (sem `max_rows`)
- ✅ Documentação atualizada com guia de uso integrado
