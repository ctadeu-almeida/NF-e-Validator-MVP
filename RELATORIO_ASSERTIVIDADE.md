# Relatório de Assertividade - NF-e Validator MVP

**Data:** 2025-10-15
**Objetivo:** Avaliar se a aplicação está capturando TODOS os erros possíveis nas validações de NF-e

---

## 1. VALIDAÇÕES IMPLEMENTADAS

### 1.1 Validações Federais (federal_validators.py)

#### **NCMValidator**
- ✅ NCM_001: Formato inválido (não tem 8 dígitos)
- ✅ NCM_002: NCM não é de açúcar (não começa com 1701)
- ✅ NCM_003: NCM não corresponde à descrição do produto
- ✅ NCM_004: NCM de açúcar não reconhecido na base MVP (INFO)

**Cobertura:**
- ✅ Valida TODOS os itens da NF-e (loop em `nfe.items`)
- ✅ Erros críticos impedem validações subsequentes
- ⚠️ **LIMITAÇÃO:** Apenas valida açúcar (1701xxxx) no MVP - outros NCMs geram INFO/WARNING

#### **PISCOFINSValidator**
- ✅ PIS_001: CST incorreto para o NCM
- ✅ PIS_002: Alíquota divergente da esperada
- ✅ PIS_003: Valor calculado difere do declarado (>1% de tolerância)
- ✅ COFINS_001: CST incorreto para o NCM
- ✅ COFINS_002: Alíquota divergente da esperada
- ✅ COFINS_003: Valor calculado difere do declarado (>1% de tolerância)
- ✅ PIS_COFINS_001: Lei 10.925/2004 - Suspensão para insumos agropecuários
- ✅ PIS_COFINS_002: REsp 1.221.170 STJ - Manutenção de créditos

**Cobertura:**
- ✅ Valida TODOS os itens da NF-e
- ✅ Calcula impacto financeiro em cada divergência
- ✅ Valida base de cálculo, alíquota E valor
- ✅ Aplica regras especiais (teses jurídicas) quando aplicável

#### **CFOPValidator**
- ✅ CFOP_001: Formato inválido (não tem 4 dígitos)
- ✅ CFOP_002: CFOP não reconhecido na base
- ✅ CFOP_003: Territorialidade incorreta (5xxx interno, 6xxx interestadual)
- ✅ CFOP_004: CFOP não aplicável ao tipo de produto

**Cobertura:**
- ✅ Valida TODOS os itens
- ✅ Verifica compatibilidade UF emitente × UF destinatário
- ✅ Valida tipo de operação (venda, transferência, etc.)

#### **TotaisValidator**
- ✅ TOTAIS_001: Valor total não bate com soma dos itens
- ✅ TOTAIS_002: Total de impostos divergente
- ✅ TOTAIS_003: Aplicação incorreta da tese Tema 69 STF (exclusão ICMS)

**Cobertura:**
- ✅ Valida somatórios gerais da NF-e
- ✅ Tolerância de R$ 0.01 para arredondamentos
- ⚠️ **LIMITAÇÃO:** Não valida frete, seguro, outras despesas (não estão no escopo MVP)

---

### 1.2 Validações Estaduais (state_validators.py)

#### **SPValidator (São Paulo)**
- ✅ SP_ICMS_001: Alíquota ICMS divergente da regra estadual
- ✅ SP_ST_001: Substituição tributária não aplicada (quando obrigatória)

**Cobertura:**
- ✅ Valida TODOS os itens quando NF-e envolve SP
- ⚠️ **SEVERIDADE:** Apenas WARNING (não-bloqueante)
- ⚠️ **LIMITAÇÃO:** Base estadual limitada no MVP (poucos NCMs cadastrados)

#### **PEValidator (Pernambuco)**
- ✅ PE_ICMS_001: Alíquota ICMS divergente da regra estadual
- ✅ PE_BENEFICIO_001: Benefício fiscal disponível não aplicado (INFO)

**Cobertura:**
- ✅ Valida TODOS os itens quando NF-e envolve PE
- ⚠️ **SEVERIDADE:** Apenas WARNING/INFO (não-bloqueante)
- ⚠️ **LIMITAÇÃO:** Base estadual limitada no MVP

---

## 2. FLUXO DE VALIDAÇÃO (app.py)

### Pipeline de Validação (validate_nfe_with_pipeline)

```python
# Para CADA NF-e:
for nfe in nfes:
    # 1. Validações Federais - Item por Item
    for item in nfe.items:
        NCMValidator.validate(item)         # Todos os itens
        PISCOFINSValidator.validate(item)   # Todos os itens
        CFOPValidator.validate(item)        # Todos os itens

    # 2. Validações de Totais (NF-e completa)
    TotaisValidator.validate(nfe)

    # 3. Validações Estaduais (se aplicável)
    if emitente.uf == 'SP' or destinatario.uf == 'SP':
        for item in nfe.items:
            SPValidator.validate(item)

    if emitente.uf == 'PE' or destinatario.uf == 'PE':
        for item in nfe.items:
            PEValidator.validate(item)
```

**Assertividade do Loop:**
- ✅ **TODOS** os itens são validados (não há break/continue que pule itens)
- ✅ **TODOS** os validadores são executados (não há if que ignore validadores)
- ✅ Erros são acumulados em `nfe.validation_errors` (não há sobrescrita)

---

## 3. POSSÍVEIS GAPS DE ASSERTIVIDADE

### 3.1 ⚠️ **NCMs Fora do Escopo MVP**

**Problema:**
Se o arquivo contém NCMs que NÃO são açúcar (1701xxxx) e NÃO estão em `base_validacao.csv`, as validações de PIS/COFINS podem não ocorrer corretamente.

**Exemplo:**
- NCM 2106909900 (Preparações alimentícias)
- NCM 3920109900 (Plásticos)

**Consequência:**
- NCMValidator → Gera NCM_002 (ERROR) "Não é açúcar"
- PISCOFINSValidator → Sem regra no repositório → **PODE NÃO VALIDAR ALÍQUOTA**

**Mitigação Atual:**
- Validador tenta buscar regra genérica
- Se não achar, **NÃO gera erro de PIS/COFINS** (assume que CST/alíquota estão corretos)

**Recomendação:**
- ✅ Adicionar regra genérica em `base_validacao.csv` para NCMs comuns
- ✅ Ou gerar WARNING quando não há regra disponível

---

### 3.2 ⚠️ **Valores NaN/Ausentes no CSV**

**Problema:**
Se o CSV possui células vazias em campos críticos (pis_cst, cofins_cst, valor_total), o parser agora aceita com valores padrão ('', 0.00).

**Consequência:**
- Item com `pis_cst = ''` → Validador compara com regra esperada → Gera erro
- Item com `valor_total = 0` → Cálculos ficam zerados → **PODE MASCARAR ERROS**

**Mitigação Atual:**
- Parser usa `safe_str()`, `safe_decimal()`, `safe_int()` (commit recente)
- Valores ausentes viram valores padrão

**Recomendação:**
- ⚠️ Considerar gerar WARNING quando campos fiscais críticos estão ausentes
- ⚠️ Exemplo: "Item sem PIS/COFINS informado - impossível validar"

---

### 3.3 ✅ **Validação Parcial (Colunas Ausentes)**

**Cenário:**
Arquivo CSV sem colunas de ICMS (icms_cst, icms_aliquota, icms_valor).

**Comportamento Atual:**
- ColumnMapper detecta ausência
- Mostra expander "📋 Colunas Ausentes" com lista
- Validações estaduais (SP/PE) **NÃO executam** se `item.impostos.icms_aliquota` for None
- **NÃO gera erros falsos**

**Assertividade:** ✅ CORRETO - Não gera falsos positivos

---

### 3.4 ⚠️ **Validação de Múltiplas NF-es**

**Cenário:**
Arquivo com 50 NF-es, sendo:
- 40 NF-es corretas
- 10 NF-es com erros

**Comportamento Atual:**
```python
for i, nfe in enumerate(nfes):
    validated_nfe = validate_nfe_with_pipeline(nfe, repo)
    validated_nfes.append(validated_nfe)
```

**Assertividade:**
- ✅ **TODAS** as NF-es são validadas (loop completo)
- ✅ Erros de uma NF-e **NÃO impedem** validação das outras
- ✅ Progress bar mostra andamento

**Possível Problema:**
- Se houver **exception não-tratada** dentro de `validate_nfe_with_pipeline()`, o loop pode **parar**
- Exemplo: `AttributeError`, `KeyError`, `TypeError`

**Mitigação Atual:**
- Parser tem try/except em `_parse_item()` (agora com safe_xxx)
- Validadores têm proteções contra None

**Recomendação:**
- ✅ Adicionar try/except em `validate_nfe_with_pipeline()` para capturar erros inesperados
- ✅ Registrar NF-e com erro e continuar loop

---

## 4. TESTE DE ASSERTIVIDADE

### 4.1 Casos de Teste Recomendados

Para garantir que **TODOS** os erros são capturados:

#### **Teste 1: Arquivo com Múltiplos Erros no Mesmo Item**
```csv
chave_acesso,numero_nfe,numero_item,ncm,cfop,pis_cst,pis_aliquota,cofins_cst,cofins_aliquota,valor_total
123,001,1,1701,510,01,1.65,01,7.60,1000.00
```

**Erros Esperados:**
- NCM_001: NCM com 4 dígitos (formato inválido)
- CFOP_001: CFOP com 3 dígitos (formato inválido)
- PIS_001: CST 01 incorreto (esperado 06 ou 50 para açúcar)
- COFINS_001: CST 01 incorreto

**Resultado Esperado:** 4 erros

---

#### **Teste 2: Arquivo com 10 NF-es, Erro na 5ª**
```csv
# NF-e 1-4: corretas
# NF-e 5: NCM inválido
# NF-e 6-10: corretas
```

**Comportamento Esperado:**
- Validação continua após erro na NF-e 5
- NF-es 6-10 são validadas normalmente
- Total: 10 NF-es processadas

---

#### **Teste 3: Arquivo com Campos Ausentes**
```csv
chave_acesso,numero_nfe,ncm,cfop,valor_total
# Sem pis_cst, cofins_cst, icms_cst
```

**Comportamento Esperado:**
- Mostra "Colunas Ausentes: pis_cst, cofins_cst, icms_cst..."
- Continua validação (formato NCM, CFOP, totais)
- **NÃO gera** erros de PIS/COFINS se regra não aplicável

---

## 5. ANÁLISE DE COBERTURA DE CÓDIGO

### 5.1 Validadores que SEMPRE Executam

| Validador | Condição | Cobertura |
|-----------|----------|-----------|
| NCMValidator | Sempre | ✅ 100% itens |
| PISCOFINSValidator | Se tem regra no repo | ⚠️ Depende da base |
| CFOPValidator | Sempre | ✅ 100% itens |
| TotaisValidator | Sempre | ✅ 1x por NF-e |
| SPValidator | Se UF=SP | ✅ 100% itens (quando aplicável) |
| PEValidator | Se UF=PE | ✅ 100% itens (quando aplicável) |

### 5.2 Validações que Podem Ser Puladas

| Validação | Motivo | Impacto |
|-----------|--------|---------|
| PIS/COFINS alíquota | NCM sem regra no repo | ⚠️ Erro pode não ser detectado |
| ICMS estadual | Coluna ausente no CSV | ✅ Correto (não gera falso positivo) |
| Substituição Tributária | NCM sem regra de ST | ⚠️ ST obrigatória pode passar |

---

## 6. CONCLUSÃO E RECOMENDAÇÕES

### 6.1 ✅ Assertividade CONFIRMADA

1. **Loop de Validação:** Todos os itens e todas as NF-es são validadas
2. **Acúmulo de Erros:** Erros não são sobrescritos (append em lista)
3. **Validação Parcial:** Não gera falsos positivos quando dados ausentes
4. **Progress Feedback:** Usuário vê andamento da validação

### 6.2 ⚠️ GAPS Identificados

1. **NCMs fora do MVP:** PIS/COFINS pode não validar se regra ausente
2. **Campos NaN:** Valores zerados podem mascarar erros de cálculo
3. **Exception não-tratada:** Erro inesperado pode interromper validação em lote

### 6.3 🔧 Melhorias Recomendadas

#### **Curto Prazo (Assertividade Imediata)**

1. **Adicionar try/except em validate_nfe_with_pipeline():**
```python
for i, nfe in enumerate(nfes):
    try:
        validated_nfe = validate_nfe_with_pipeline(nfe, repo)
        validated_nfes.append(validated_nfe)
    except Exception as e:
        # Registrar erro mas continuar
        st.warning(f"⚠️ Erro ao validar NF-e {nfe.numero}: {e}")
        nfe.validation_errors.append(ValidationError(
            code='SYSTEM_ERROR',
            message=f'Erro inesperado na validação: {str(e)}',
            severity=Severity.CRITICAL
        ))
        validated_nfes.append(nfe)
```

2. **Gerar WARNING quando regra fiscal ausente:**
```python
# Em PISCOFINSValidator
if not pis_cofins_rule:
    errors.append(ValidationError(
        code='PIS_COFINS_999',
        message=f'NCM {item.ncm} sem regra de PIS/COFINS cadastrada - validação não realizada',
        severity=Severity.WARNING
    ))
    return errors  # Não prossegue sem regra
```

3. **Adicionar validação de campos críticos ausentes:**
```python
# Em _parse_item()
if pd.isna(row.get('pis_cst')) or pd.isna(row.get('cofins_cst')):
    logging.warning(f"Item {numero_item}: PIS/COFINS ausentes - validação limitada")
```

#### **Médio Prazo (Expansão da Base)**

4. **Expandir base_validacao.csv:**
   - Adicionar NCMs comuns no setor (embalagens, insumos, etc.)
   - Regras genéricas para produtos não-açúcar

5. **Logs de Auditoria:**
   - Registrar quantas validações foram executadas vs. puladas
   - Exemplo: "50 itens validados NCM, 48 validados PIS/COFINS (2 sem regra)"

6. **Teste de Regressão:**
   - Criar suite de testes com casos extremos
   - Validar que 100% dos erros conhecidos são detectados

---

## 7. MÉTRICAS DE ASSERTIVIDADE

Para medir a assertividade real, sugerimos adicionar ao final da validação:

```python
# Métricas
total_items = sum(len(nfe.items) for nfe in validated_nfes)
items_validated_ncm = total_items  # Sempre 100%
items_validated_pis = sum(1 for nfe in validated_nfes for item in nfe.items if repo.get_pis_cofins_rule(item.ncm))
items_validated_cfop = total_items  # Sempre 100%

st.metric("Itens Validados (NCM)", f"{items_validated_ncm}/{total_items}")
st.metric("Itens Validados (PIS/COFINS)", f"{items_validated_pis}/{total_items}")
st.metric("Taxa de Cobertura", f"{items_validated_pis/total_items*100:.1f}%")
```

---

**Resumo Final:**
- ✅ Aplicação **ESTÁ** validando todos os itens corretamente
- ⚠️ **MAS** validações de PIS/COFINS dependem de regra no repositório
- 🔧 Recomenda-se adicionar **try/except** e **warnings** para melhorar visibilidade de gaps
