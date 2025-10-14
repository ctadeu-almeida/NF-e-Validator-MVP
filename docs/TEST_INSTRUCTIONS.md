# 🧪 Instruções de Teste - NF-e Validator MVP

**Como testar todas as funcionalidades do sistema**

---

## ⚡ Quick Start (5 minutos)

```bash
# 1. Instalar
pip install -r requirements-mvp.txt

# 2. Popular database
python scripts/populate_db.py

# 3. Testar validações
python tests/test_integration.py

# 4. Testar interface
python run_streamlit.py
```

---

## 📋 Testes Detalhados

### Teste 1: Database & Repository ✅

**Objetivo:** Verificar se database foi populado corretamente

```bash
python -c "from repositories.fiscal_repository import FiscalRepository; repo = FiscalRepository(); stats = repo.get_statistics(); print(f'Total registros: {sum(stats.values())}'); print(stats)"
```

**Resultado esperado:**
```
Total registros: 27
{'ncm_rules': 5, 'pis_cofins_rules': 7, 'cfop_rules': 7, 'state_overrides': 3, 'legal_refs': 5}
```

**Status:** ✅ PASSOU

---

### Teste 2: Validadores Federais ✅

**Objetivo:** Testar validadores NCM, PIS/COFINS, CFOP, Totals

```bash
python tests/test_integration.py
```

**Resultado esperado:**
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

[SUCCESS] All tests passed!
```

**Verifica:**
- ✅ CSV parsing
- ✅ Validações federais (NCM, PIS/COFINS, CFOP, Totals)
- ✅ Validações estaduais (SP + PE)
- ✅ Geração de relatórios (JSON + Markdown)
- ✅ Cálculo de impacto financeiro

**Status:** ✅ PASSOU (5/5)

---

### Teste 3: Thread Safety (Streamlit) ✅

**Objetivo:** Verificar se SQLite funciona com múltiplas threads

```bash
python run_streamlit.py
```

**Verificar:**
1. ✅ Streamlit inicia sem erros
2. ✅ Sidebar mostra "Database Status"
3. ✅ Métricas carregam (Regras Carregadas: 27)
4. ✅ Não aparece erro de thread

**Erro corrigido:**
```
❌ ANTES: sqlite3.ProgrammingError: SQLite objects created in a thread...
✅ DEPOIS: Funciona perfeitamente!
```

**Status:** ✅ PASSOU

---

### Teste 4: Agente IA (Google Gemini 2.5) 🤖

**Pré-requisito:** Google API Key configurada

#### 4.1. Configurar API Key

```bash
# Obter key: https://aistudio.google.com/app/apikey

# Windows PowerShell
$env:GOOGLE_API_KEY = "AIza..."

# Linux/Mac
export GOOGLE_API_KEY="AIza..."
```

#### 4.2. Testar Agente via Script

```bash
python tests/test_agent.py
```

**Resultado esperado:**
```
[OK] API Key encontrada: AIza...
[1/3] Inicializando Repository...
      Database version: 1.0.0
[2/3] Inicializando Agente IA (Gemini 2.5)...
      [OK] Agente criado com sucesso
[3/3] Testando Classificações...

   Test 1/3: Açúcar cristal tipo 1 - saco 50kg
   NCM Atual: 17019900
   NCM Sugerido: 17019900
   Confiança: 95%
   Correto: True
   [OK] Classificação correta!

   Test 2/3: Açúcar refinado especial
   NCM Atual: 17019100
   NCM Sugerido: 17019100
   Confiança: 90%
   Correto: True
   [OK] Classificação correta!

   Test 3/3: Computador desktop Intel i7
   NCM Atual: 17019900
   NCM Sugerido: 8471XXXX (ou similar)
   Confiança: 85%
   Correto: False
   [OK] Classificação correta!

Sucesso: 3/3
[SUCCESS] Todos os testes passaram! ✅
```

**Status:** ⏳ PENDENTE (requer API Key)

#### 4.3. Testar Agente via Streamlit

```bash
python run_streamlit.py
```

**Passos:**
1. ✅ Marcar checkbox "Usar Agente para NCM"
2. ✅ Inserir API Key no campo de senha
3. ✅ Verificar mensagem "✅ API Key configurada"
4. ✅ Upload de CSV (`tests/data/nfe_erro_ncm.csv`)
5. ✅ Clicar "Validar NF-e"
6. ✅ Aguardar spinners:
   - "Inicializando Agente IA..."
   - "Classificando NCMs com IA..."
7. ✅ Ir para aba "🤖 Sugestões IA"
8. ✅ Verificar sugestões do agente

**Verificar:**
- ✅ NCM sugerido
- ✅ Confiança (0-100%)
- ✅ Correto (Sim/Não)
- ✅ Raciocínio do agente

**Status:** ⏳ PENDENTE (requer API Key)

---

### Teste 5: Interface Streamlit Completa 🖥️

**Objetivo:** Testar fluxo completo da interface

```bash
python run_streamlit.py
# Acesse: http://localhost:8501
```

#### 5.1. Teste Básico (Sem IA)

**Passos:**
1. ✅ Upload: `tests/data/nfe_valid.csv`
2. ✅ Clicar "Validar NF-e"
3. ✅ Verificar resultados:
   - Métricas: 🔴0 🟠0 🟡0 💰R$ 0,00
   - Status: ✅ NF-e VÁLIDA
4. ✅ Aba "📋 Relatório": Ver Markdown
5. ✅ Aba "📄 JSON": Ver JSON estruturado
6. ✅ Aba "💾 Downloads": Baixar relatórios

**Status:** ✅ PASSOU

#### 5.2. Teste com Erros

**Arquivo:** `tests/data/nfe_erro_pis_cofins.csv`

**Resultado esperado:**
- Métricas: 🔴2 🟠0 🟡0 💰R$ 30,00
- Status: ❌ NF-e INVÁLIDA - Requer correção
- Erros detalhados:
  - PIS: 3.00% (deveria ser 1.65%) - R$ 10.80
  - COFINS: 10.00% (deveria ser 7.6%) - R$ 19.20

**Status:** ✅ PASSOU

#### 5.3. Teste com IA

**Arquivo:** `tests/data/nfe_erro_ncm.csv`

**Com API Key configurada:**
- ✅ Aba "🤖 Sugestões IA" deve mostrar:
  - NCM Sugerido: diferente de 17019900
  - Confiança: ~80-95%
  - NCM Correto: ❌ Não
  - Raciocínio completo do agente

**Status:** ⏳ PENDENTE (requer API Key)

---

## 🎯 Checklist Completo

### Funcionalidades Core

- [x] Database populado (27 registros)
- [x] Repository pattern funcionando
- [x] CSV parser (normalização)
- [x] NCM Validator
- [x] PIS/COFINS Validator
- [x] CFOP Validator
- [x] Totals Validator
- [x] SP Validator (estadual)
- [x] PE Validator (estadual)
- [x] Report Generator (JSON)
- [x] Report Generator (Markdown)
- [x] Integration tests (5/5)

### Interface Streamlit

- [x] Upload CSV
- [x] Parsing + Validation
- [x] Dashboard de métricas
- [x] Aba Relatório (Markdown)
- [x] Aba JSON
- [x] Aba Downloads
- [x] Thread safety (SQLite)
- [ ] Aba Sugestões IA (requer API Key)

### Agente IA

- [x] Implementado (LangChain ReAct)
- [x] Model: Gemini 2.5 Pro
- [x] 3 tools (search, details, list)
- [ ] Testado com API Key
- [ ] Integrado com Streamlit

---

## 📊 Relatório de Testes

### Testes Automatizados

| Teste | Status | Resultado |
|-------|--------|-----------|
| Database Population | ✅ | 27/27 registros |
| Repository Queries | ✅ | Todas funcionando |
| CSV Parser | ✅ | 5/5 CSVs |
| Federal Validators | ✅ | 4/4 validadores |
| State Validators | ✅ | 2/2 validadores |
| Report Generation | ✅ | JSON + MD |
| Integration Tests | ✅ | 5/5 passed |
| Thread Safety | ✅ | Corrigido |

### Testes Manuais (Streamlit)

| Teste | Status | Observação |
|-------|--------|------------|
| UI Load | ✅ | Carrega sem erros |
| Database Info | ✅ | Mostra stats |
| CSV Upload | ✅ | Aceita arquivos |
| Validação Básica | ✅ | Funciona |
| Relatórios | ✅ | JSON + MD |
| Downloads | ✅ | Funciona |
| AI Agent (sem key) | ✅ | Warning correto |
| AI Agent (com key) | ⏳ | Pendente teste |

### Testes de Agente IA

| Teste | Status | Pré-requisito |
|-------|--------|---------------|
| Script test_agent.py | ⏳ | API Key |
| Streamlit integration | ⏳ | API Key |
| Gemini 2.5 Pro | ✅ | Configurado |

---

## 🐛 Issues Conhecidos

### ✅ Resolvidos

1. ✅ **SQLite Thread Error** - Corrigido com `check_same_thread=False`
2. ✅ **Gemini Model** - Atualizado para `gemini-2.5-pro`
3. ✅ **Unicode Encoding** - Emojis removidos de prints

### ⏳ Pendentes

1. ⏳ **Agente IA** - Requer teste com API Key real
2. ⏳ **Performance** - Testar com CSVs grandes (>1000 linhas)
3. ⏳ **Export XLSX** - Ainda não implementado (apenas JSON/MD)

---

## 🚀 Como Rodar Todos os Testes

```bash
# 1. Setup
pip install -r requirements-mvp.txt
python scripts/populate_db.py

# 2. Testes Unitários
python tests/test_integration.py

# 3. Teste Agente (se tiver API key)
export GOOGLE_API_KEY="your-key"
python tests/test_agent.py

# 4. Teste Interface
python run_streamlit.py
```

---

## 📞 Reportar Problemas

**Encontrou um bug?**

1. Verifique `BUGFIX_SUMMARY.md` (bugs já corrigidos)
2. Verifique `GEMINI_SETUP.md` (problemas com IA)
3. Consulte `README_MVP.md` seção "Troubleshooting"
4. Abra issue no GitHub (se aplicável)

---

## ✅ Conclusão

**Status Geral:** ✅ **SISTEMA FUNCIONAL**

- ✅ Core validation: 100% testado (5/5)
- ✅ Thread safety: Corrigido
- ✅ Gemini 2.5: Configurado
- ⏳ AI Agent: Requer API Key para teste final

**Pronto para uso em MVP!**

---

*Última atualização: 13/10/2025*
*Versão: 1.0.0-mvp (patched)*
