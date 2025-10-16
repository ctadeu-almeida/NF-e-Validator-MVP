# 📋 RELATÓRIO DE AUDITORIA FISCAL
**NF-e Validator MVP** - Setor Sucroalcooleiro  
*Versão: 1.0.0-mvp*  
*Gerado em: 14/10/2025 09:45:07*

---

## 📄 Informações da NF-e

**Chave de Acesso:** `35250323456789000190550010000003234567890125`  
**Número:** 345678 | **Série:** 1  
**Data de Emissão:** 03/10/2025

### Emitente
- **CNPJ:** 12.345.678/0001-90
- **Razão Social:** USINA AÇÚCAR SP LTDA
- **UF:** SP

### Destinatário
- **CNPJ:** 98.765.432/0001-10
- **Razão Social:** DISTRIBUIDORA ALIMENTOS LTDA
- **UF:** SP

### Operação
- **Tipo:** 🏠 INTERNA (SP → SP)
- **CFOP:** 5101
- **Natureza:** Venda de mercadoria

---

## 📊 RESUMO DA VALIDAÇÃO

### Status: ❌ PENDING

**Total de Problemas Encontrados:** 2

| Severidade | Quantidade |
|------------|------------|
| 🔴 **CRÍTICO** | 2 |
| 🟠 **ERRO** | 0 |
| 🟡 **AVISO** | 0 |
| 🔵 **INFO** | 0 |

### 💰 IMPACTO FINANCEIRO

**Economia Potencial:** R$ 30.00

*Valor total que pode ser economizado corrigindo os erros identificados.*

---

## 🔍 DETALHAMENTO DOS ERROS

### 🔴 ERROS CRÍTICOS
*Requer ação IMEDIATA*

#### 1. Alíquota PIS incorreta: 3.00%

**Código:** `PIS_002`  
**Campo:** `pis_aliquota`  
**Item:** #1  
**Valor Atual:** `3.00`  
**Valor Esperado:** `1.65`  
**💵 Impacto:** R$ 10.80  

📚 **Base Legal:** Lei 10.637/2002 e Lei 10.833/2003
 - Art. 2º - Alíquotas de 1,65% (PIS) e 7,6% (COFINS)

💡 **Sugestão:** Alíquota correta: 1.65%


#### 2. Alíquota COFINS incorreta: 10.00%

**Código:** `COFINS_002`  
**Campo:** `cofins_aliquota`  
**Item:** #1  
**Valor Atual:** `10.00`  
**Valor Esperado:** `7.6`  
**💵 Impacto:** R$ 19.20  

📚 **Base Legal:** Lei 10.637/2002 e Lei 10.833/2003
 - Art. 2º - Alíquotas de 1,65% (PIS) e 7,6% (COFINS)

💡 **Sugestão:** Alíquota correta: 7.6%


---

## 📦 ANÁLISE POR ITEM

### Item 1: Açúcar refinado especial - saco 1kg

- **Código:** ACS-003
- **NCM:** 1701.91.00
- **CFOP:** 5101
- **Quantidade:** 200 KG
- **Valor Unitário:** R$ 4.00
- **Valor Total:** R$ 800.00

**Tributação:**
- PIS: CST 01 | 3.00% | R$ 24.00
- COFINS: CST 01 | 10.00% | R$ 80.00

**⚠️ 2 problema(s) encontrado(s) neste item**

---

## 💡 RECOMENDAÇÕES

1. ⚠️ Foram encontrados erros CRÍTICOS que podem resultar em autuação fiscal. Recomendamos ação imediata.
2. 💰 Impacto financeiro estimado: R$ 30.00. Considere solicitar retificação da nota fiscal.
3. 💼 Encontrados erros em PIS/COFINS. Consulte legislação federal (Lei 10.833/2003 e Lei 10.637/2002).

---

## 💰 TOTAIS DA NF-e

| Descrição | Valor |
|-----------|------:|
| Valor dos Produtos | R$ 800.00 |
| PIS | R$ 24.00 |
| COFINS | R$ 80.00 |
| ICMS | R$ 144.00 |
| **Valor Total da Nota** | **R$ 800.00** |

---

## 📌 Notas

- Este relatório foi gerado automaticamente pelo **NF-e Validator MVP**
- Validações baseadas na legislação federal vigente
- Estados validados neste MVP: **SP** e **PE**
- Setor: **Sucroalcooleiro** (Açúcar)
- Versão do validador: `1.0.0-mvp`

---

*Desenvolvido com ❤️ para o setor sucroalcooleiro brasileiro*