# 📋 RELATÓRIO DE AUDITORIA FISCAL
**NF-e Validator MVP** - Setor Sucroalcooleiro  
*Versão: 1.0.0-mvp*  
*Gerado em: 14/10/2025 09:45:07*

---

## 📄 Informações da NF-e

**Chave de Acesso:** `35250223456789000190550010000002234567890124`  
**Número:** 234567 | **Série:** 1  
**Data de Emissão:** 02/10/2025

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

**Total de Problemas Encontrados:** 1

| Severidade | Quantidade |
|------------|------------|
| 🔴 **CRÍTICO** | 0 |
| 🟠 **ERRO** | 0 |
| 🟡 **AVISO** | 1 |
| 🔵 **INFO** | 0 |

---

## 🔍 DETALHAMENTO DOS ERROS

### 🟡 AVISOS
*Verificação recomendada*

#### 1. Descrição "Computador desktop Intel i7" pode não corresponder ao NCM 17019900 (Outros açúcares de cana ou de beterraba e sacarose quimicamente pura, no estado sólido)

**Código:** `NCM_003`  
**Campo:** `descricao`  
**Item:** #1  
**Valor Atual:** `Computador desktop Intel i7`  
**Valor Esperado:** `Outros açúcares de cana ou de beterraba e sacarose quimicamente pura, no estado sólido`  

📚 **Base Legal:** Tabela NCM/TIPI - Posição 1701

💡 **Sugestão:** Descrição esperada para NCM 17019900: Outros açúcares de cana ou de beterraba e sacarose quimicamente pura, no estado sólido


---

## 📦 ANÁLISE POR ITEM

### Item 1: Computador desktop Intel i7

- **Código:** ACS-002
- **NCM:** 1701.99.00
- **CFOP:** 5101
- **Quantidade:** 50 KG
- **Valor Unitário:** R$ 3.00
- **Valor Total:** R$ 150.00

**Tributação:**
- PIS: CST 01 | 1.65% | R$ 2.48
- COFINS: CST 01 | 7.60% | R$ 11.40

**⚠️ 1 problema(s) encontrado(s) neste item**

---

## 💡 RECOMENDAÇÕES

1. 📋 Encontrados erros de classificação NCM. Verifique a Tabela NCM/TIPI atualizada.

---

## 💰 TOTAIS DA NF-e

| Descrição | Valor |
|-----------|------:|
| Valor dos Produtos | R$ 150.00 |
| PIS | R$ 2.48 |
| COFINS | R$ 11.40 |
| ICMS | R$ 27.00 |
| **Valor Total da Nota** | **R$ 150.00** |

---

## 📌 Notas

- Este relatório foi gerado automaticamente pelo **NF-e Validator MVP**
- Validações baseadas na legislação federal vigente
- Estados validados neste MVP: **SP** e **PE**
- Setor: **Sucroalcooleiro** (Açúcar)
- Versão do validador: `1.0.0-mvp`

---

*Desenvolvido com ❤️ para o setor sucroalcooleiro brasileiro*