# 📋 RELATÓRIO DE AUDITORIA FISCAL
**NF-e Validator MVP** - Setor Sucroalcooleiro  
*Versão: 1.0.0-mvp*  
*Gerado em: 14/10/2025 09:45:07*

---

## 📄 Informações da NF-e

**Chave de Acesso:** `26250423456789000190550010000004234567890126`  
**Número:** 456789 | **Série:** 1  
**Data de Emissão:** 04/10/2025

### Emitente
- **CNPJ:** 12.345.678/0001-90
- **Razão Social:** USINA AÇÚCAR SP LTDA
- **UF:** SP

### Destinatário
- **CNPJ:** 11.122.233/0001-44
- **Razão Social:** SUPERMERCADO NORDESTE LTDA
- **UF:** PE

### Operação
- **Tipo:** 🌍 INTERESTADUAL (SP → PE)
- **CFOP:** 5101
- **Natureza:** Venda de mercadoria

---

## 📊 RESUMO DA VALIDAÇÃO

### Status: ❌ PENDING

**Total de Problemas Encontrados:** 1

| Severidade | Quantidade |
|------------|------------|
| 🔴 **CRÍTICO** | 1 |
| 🟠 **ERRO** | 0 |
| 🟡 **AVISO** | 0 |
| 🔵 **INFO** | 0 |

---

## 🔍 DETALHAMENTO DOS ERROS

### 🔴 ERROS CRÍTICOS
*Requer ação IMEDIATA*

#### 1. Operação interestadual (SP→PE) com CFOP interno (5101)

**Código:** `CFOP_003`  
**Campo:** `cfop`  
**Item:** #1  
**Valor Atual:** `5101`  
**Valor Esperado:** `6101 (interestadual)`  

📚 **Base Legal:** Tabela CFOP - Ajuste SINIEF 07/05

💡 **Sugestão:** Use CFOP 6101 para operação interestadual


---

## 📦 ANÁLISE POR ITEM

### Item 1: Açúcar cristal tipo 1 - saco 50kg

- **Código:** ACS-004
- **NCM:** 1701.99.00
- **CFOP:** 5101
- **Quantidade:** 150 KG
- **Valor Unitário:** R$ 2.50
- **Valor Total:** R$ 375.00

**Tributação:**
- PIS: CST 01 | 1.65% | R$ 6.19
- COFINS: CST 01 | 7.60% | R$ 28.50

**⚠️ 1 problema(s) encontrado(s) neste item**

---

## 💡 RECOMENDAÇÕES

1. ⚠️ Foram encontrados erros CRÍTICOS que podem resultar em autuação fiscal. Recomendamos ação imediata.

---

## 💰 TOTAIS DA NF-e

| Descrição | Valor |
|-----------|------:|
| Valor dos Produtos | R$ 375.00 |
| PIS | R$ 6.19 |
| COFINS | R$ 28.50 |
| ICMS | R$ 67.50 |
| **Valor Total da Nota** | **R$ 375.00** |

---

## 📌 Notas

- Este relatório foi gerado automaticamente pelo **NF-e Validator MVP**
- Validações baseadas na legislação federal vigente
- Estados validados neste MVP: **SP** e **PE**
- Setor: **Sucroalcooleiro** (Açúcar)
- Versão do validador: `1.0.0-mvp`

---

*Desenvolvido com ❤️ para o setor sucroalcooleiro brasileiro*