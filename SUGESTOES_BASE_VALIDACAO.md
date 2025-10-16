# Sugestões para Expandir base_validacao.csv

**Objetivo:** Aumentar a cobertura de validação PIS/COFINS para reduzir warnings "sem regra cadastrada"

---

## 1. NCMs PRIORITÁRIOS (Setor Sucroalcooleiro)

### 1.1 Etanol e Subprodutos

```csv
# Etanol (álcool etílico)
22071000,Álcool etílico não desnaturado com teor alcoólico >= 80% vol,06,0.00,06,0.00,50,1.65,50,7.60,5101|5102|5405|6101|6102|6404,1101|1556|2101|2556,SIM,9,Lei 10925/2004 Art.1 VIII; RICMS/SP,Alíquota Zero na saída (combustível). Manter créditos de entrada. SP: RBC ICMS. PE: Crédito presumido 9%

22072000,Álcool etílico desnaturado qualquer teor,06,0.00,06,0.00,50,1.65,50,7.60,5101|5102|5405|6101|6102|6404,1101|1556|2101|2556,SIM,9,Lei 10925/2004 Art.1 VIII,Alíquota Zero na saída. Manter créditos de entrada.

# Bagaço de cana
23032000,Polpas e resíduos da extração do açúcar de beterraba e cana,50,1.65,50,7.60,50,1.65,50,7.60,5101|5102|6101|6102,1101|2101,NAO,0,Lei 10925/2004 Art.8 XXV,Suspensão PIS/COFINS (insumo agropecuário). Regime especial de créditos (STJ REsp 1221170)
```

### 1.2 Melaço e Derivados

```csv
17031000,Melaços resultantes da extração ou refinação do açúcar de cana,50,1.65,50,7.60,50,1.65,50,7.60,5101|5102|6101|6102,1101|2101,NAO,0,Lei 10925/2004 Art.8 XXV,Suspensão PIS/COFINS. Subproduto do açúcar usado na alimentação animal

17039000,Outros melaços,50,1.65,50,7.60,50,1.65,50,7.60,5101|5102|6101|6102,1101|2101,NAO,0,Lei 10925/2004 Art.8 XXV,Suspensão PIS/COFINS
```

---

## 2. INSUMOS COMPLEMENTARES (Expandir Cobertura)

### 2.1 Embalagens (Industrialização)

```csv
# Sacos de papel/plástico para açúcar
48195000,Embalagens de papel/cartão para produtos,01,1.65,01,7.60,50,1.65,50,7.60,5101|5102|5401|6101|6102|6401,1101|1556|2101|2556,NAO,0,Lei 10637/2002 e 10833/2003,Tributado normalmente. Crédito na entrada (insumo industrial)

39232100,Sacos de polímeros de etileno,01,1.65,01,7.60,50,1.65,50,7.60,5101|5102|5401|6101|6102|6401,1101|1556|2101|2556,NAO,0,Lei 10637/2002 e 10833/2003,Tributado normalmente. Crédito na entrada
```

### 2.2 Peças de Reposição e Manutenção

```csv
# Peças para máquinas agrícolas
84329000,Partes de máquinas/aparelhos de uso agrícola,01,1.65,01,7.60,50,1.65,50,7.60,5101|5102|5401|6101|6102|6401,1101|1556|2101|2556,NAO,0,Lei 10637/2002 e 10833/2003,Tributado normalmente. Crédito na entrada

# Correias/correntes
40101900,Correias transportadoras/transmissão de borracha,01,1.65,01,7.60,50,1.65,50,7.60,5101|5102|5401|6101|6102|6401,1101|1556|2101|2556,NAO,0,Lei 10637/2002 e 10833/2003,Tributado normalmente. Crédito na entrada
```

### 2.3 Produtos Químicos

```csv
# Cal (tratamento de caldo)
25221000,Cal viva,01,1.65,01,7.60,50,1.65,50,7.60,5101|5102|5401|6101|6102|6401,1101|1556|2101|2556,NAO,0,Lei 10637/2002 e 10833/2003,Tributado normalmente. Crédito na entrada (insumo industrial)

# Ácido fosfórico
28092010,Ácido fosfórico de pureza >= 75%,01,1.65,01,7.60,50,1.65,50,7.60,5101|5102|5401|6101|6102|6401,1101|1556|2101|2556,NAO,0,Lei 10637/2002 e 10833/2003,Tributado normalmente. Crédito na entrada (clarificação)

# Antiespumantes
38249099,Outros produtos químicos,01,1.65,01,7.60,50,1.65,50,7.60,5101|5102|5401|6101|6102|6401,1101|1556|2101|2556,NAO,0,Lei 10637/2002 e 10833/2003,Tributado normalmente. Crédito na entrada
```

---

## 3. OPERAÇÕES ESPECIAIS (CSTs Menos Comuns)

### 3.1 Simples Nacional

```csv
# Qualquer NCM com Simples Nacional
<NCM>,<Descrição>,99,0.00,99,0.00,49,0.00,49,0.00,5101|5102|6101|6102,1101|2101,NAO,NAO,Lei Complementar 123/2006,CST 99 (Simples Nacional - isenção). Não gera crédito
```

**Como usar:** Para empresas do Simples Nacional, **qualquer NCM** deve ter:
- PIS CST: 99 (Outras Operações)
- COFINS CST: 99 (Outras Operações)
- Alíquota: 0% (não há destaque separado)

### 3.2 Zona Franca de Manaus (ZFM)

```csv
# Produtos para/de ZFM
<NCM>,<Descrição>,06,0.00,06,0.00,73,0.00,73,0.00,6109|6110|6111|6152,2152|2153,NAO,NAO,Decreto-Lei 288/1967,CST 06 saída para ZFM (alíquota zero). CST 73 entrada de ZFM (suspensão)
```

### 3.3 Exportação

```csv
# Qualquer NCM para exportação
<NCM>,<Descrição>,06,0.00,06,0.00,73,0.00,73,0.00,7101|7102,<vazio>,NAO,NAO,Lei 10637/2002 Art.5; Lei 10833/2003 Art.6,Exportação: CST 06 (alíquota zero). Mantém créditos da entrada (imunidade)
```

---

## 4. REGRA GENÉRICA (Fallback)

Para NCMs não cadastrados, sugerimos adicionar uma **regra padrão**:

```csv
# Regra genérica - Regime Cumulativo (saída)
99999999,Produtos em geral - Regime Padrão,01,1.65,01,7.60,50,1.65,50,7.60,5101|5102|5401|6101|6102|6401,1101|1556|2101|2556,NAO,0,Lei 10637/2002 e 10833/2003,Tributação padrão - PIS 1.65% COFINS 7.6%. Crédito na entrada (não-cumulativo)

# Regra genérica - Regime Cumulativo (empresas menores)
99999998,Produtos em geral - Regime Cumulativo,02,0.65,02,3.00,49,0.00,49,0.00,5101|5102|6101|6102,1101|2101,NAO,0,Lei 9715/1998 e 9718/1998,Tributação cumulativa - PIS 0.65% COFINS 3%. Sem crédito na entrada
```

---

## 5. COMO ADICIONAR NOVAS REGRAS

### Passo 1: Identificar NCMs Ausentes

Quando aparecer warning `PIS_999` ou `COFINS_999`, anote:
- NCM reportado
- Descrição do produto
- CST informado na nota

### Passo 2: Consultar Legislação

- **Açúcar e derivados (1701, 2207, 1703):** Lei 10.925/2004 (alíquota zero)
- **Insumos agrícolas (31xx, 38xx):** Lei 10.925/2004 Art. 8 (suspensão)
- **Produtos industrializados gerais:** Lei 10.637/2002 e 10.833/2003
- **Simples Nacional:** Lei Complementar 123/2006 (CST 99)

### Passo 3: Adicionar em base_validacao.csv

**Formato:**
```csv
NCM,descrição,pis_cst_saida,pis_aliq_saida,cofins_cst_saida,cofins_aliq_saida,pis_cst_entrada,pis_aliq_entrada,cofins_cst_entrada,cofins_aliq_entrada,cfop_saida,cfop_entrada,icms_sp_reducao,icms_pe_credito,base_legal,observacoes
```

**Exemplo Real:**
```csv
22071000,Álcool etílico >= 80% vol,06,0.00,06,0.00,50,1.65,50,7.60,5101|5102|6101|6102,1101|2101,SIM,9,Lei 10925/2004 Art.1 VIII,Combustível - Alíquota Zero
```

### Passo 4: Validar

1. Salvar `base_validacao.csv`
2. Recarregar aplicação
3. Executar validação novamente
4. Verificar se warning desapareceu

---

## 6. TABELA RÁPIDA DE CSTs

### PIS/COFINS - Principais CSTs

| CST | Descrição | Alíquota PIS | Alíquota COFINS | Quando Usar |
|-----|-----------|--------------|-----------------|-------------|
| **01** | Tributável | 1.65% | 7.60% | Regime não-cumulativo (padrão) |
| **02** | Tributável | 0.65% | 3.00% | Regime cumulativo |
| **04** | Monofásica | 0% | 0% | Combustíveis (retido anteriormente) |
| **06** | Alíquota Zero | 0% | 0% | Açúcar, etanol, exportação |
| **07** | Isenta | 0% | 0% | Produtos isentos por lei |
| **08** | Sem Incidência | 0% | 0% | Não-incidência legal |
| **49** | Outras Operações (Entrada) | 0% | 0% | Entrada sem direito a crédito |
| **50** | Operação com Direito a Crédito | 1.65% | 7.60% | Entrada - regime não-cumulativo |
| **73** | Suspensão | 0% | 0% | Insumos agropecuários, ZFM |
| **99** | Outras Operações | Variável | Variável | Simples Nacional, casos especiais |

---

## 7. CHECKLIST DE EXPANSÃO

Use este checklist para priorizar quais NCMs adicionar:

### Alta Prioridade (Adicionar AGORA)
- [ ] 22071000 - Etanol (álcool etílico)
- [ ] 17031000 - Melaço
- [ ] 23032000 - Bagaço de cana
- [ ] 48195000 - Embalagens de papel
- [ ] 39232100 - Sacos plásticos

### Média Prioridade
- [ ] 84329000 - Peças de máquinas
- [ ] 25221000 - Cal
- [ ] 28092010 - Ácido fosfórico
- [ ] 40101900 - Correias

### Baixa Prioridade (Conforme Necessidade)
- [ ] NCMs de transporte e frete
- [ ] NCMs de serviços
- [ ] NCMs de produtos químicos específicos

---

## 8. EXEMPLO PRÁTICO

**Cenário:** Aparecem 10 warnings `PIS_999` para NCM `22071000` (Etanol)

**Ação:**

1. Abrir `base_validacao.csv`
2. Adicionar linha:
```csv
22071000,Álcool etílico não desnaturado >= 80% vol,06,0.00,06,0.00,50,1.65,50,7.60,5101|5102|5405|6101|6102|6404,1101|1556|2101|2556,SIM,9,Lei 10925/2004 Art.1 VIII,Combustível - Alíquota Zero saída. Manter créditos entrada
```
3. Salvar arquivo
4. Recarregar validação
5. **Resultado:** 0 warnings para NCM 22071000

---

## 9. FONTES DE CONSULTA

### Legislação Federal
- **Lei 10.925/2004:** Suspensão PIS/COFINS para insumos agropecuários
- **Lei 10.637/2002:** PIS não-cumulativo
- **Lei 10.833/2003:** COFINS não-cumulativo
- **Lei 11.033/2004 Art. 17:** Manutenção de créditos (tese STJ)

### Legislação Estadual
- **RICMS/SP Anexo II:** Redução BC ICMS açúcar (cesta básica)
- **RICMS/PE:** Crédito presumido 9% (regime substitutivo)

### Jurisprudência
- **STJ REsp 1.221.170:** Manutenção de créditos para insumos
- **STF Tema 69:** Exclusão ICMS da BC de PIS/COFINS

### Tabelas Oficiais
- **TIPI (Tabela de Incidência do IPI):** Descrições NCM
- **Receita Federal:** Tabela de CST PIS/COFINS

---

## 10. AUTOMATIZAÇÃO (FUTURO)

Para facilitar a expansão contínua, considerar:

1. **Log de NCMs Desconhecidos:**
   - Salvar automaticamente NCMs que geraram warning
   - Exportar lista para análise

2. **Sugestão Automática:**
   - LLM consulta legislação
   - Sugere regra baseada em NCM similar

3. **Importação em Lote:**
   - Carregar planilha com múltiplos NCMs
   - Validar e adicionar à `base_validacao.csv`

---

**Conclusão:** Comece adicionando os NCMs de **Alta Prioridade** (etanol, melaço, bagaço, embalagens). Isso deve cobrir 80% dos casos do setor sucroalcooleiro.
