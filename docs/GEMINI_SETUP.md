# 🤖 Configuração do Google Gemini 2.5

**Guia para configurar o Agente IA com Google Gemini 2.5**

---

## 📋 Pré-requisitos

- Conta Google
- Python 3.10+
- NF-e Validator MVP instalado

---

## 🔑 Passo 1: Obter API Key

### 1.1. Acessar Google AI Studio

Visite: **https://aistudio.google.com/app/apikey**

### 1.2. Criar API Key

1. Faça login com sua conta Google
2. Clique em "Get API Key" ou "Create API Key"
3. Selecione um projeto existente ou crie um novo
4. Copie a API key gerada (formato: `AIza...`)

⚠️ **IMPORTANTE:** Guarde sua API key em local seguro. Não compartilhe publicamente.

---

## ⚙️ Passo 2: Configurar API Key

### Opção A: Variável de Ambiente (Recomendado)

**Windows PowerShell:**
```powershell
$env:GOOGLE_API_KEY = "AIza..."
```

**Windows CMD:**
```cmd
set GOOGLE_API_KEY=AIza...
```

**Linux/Mac:**
```bash
export GOOGLE_API_KEY="AIza..."
```

**Permanente (Linux/Mac):**

Adicione ao `~/.bashrc` ou `~/.zshrc`:
```bash
echo 'export GOOGLE_API_KEY="AIza..."' >> ~/.bashrc
source ~/.bashrc
```

**Permanente (Windows):**

1. Painel de Controle → Sistema → Configurações Avançadas
2. Variáveis de Ambiente
3. Nova variável de usuário:
   - Nome: `GOOGLE_API_KEY`
   - Valor: `AIza...`

### Opção B: Passar via Parâmetro

```python
from agents.ncm_agent import create_ncm_agent

agent = create_ncm_agent(repo, api_key="AIza...")
```

---

## 🧪 Passo 3: Testar Configuração

### Teste 1: Via Script

```bash
python tests/test_agent.py
```

**Output esperado:**
```
[OK] API Key encontrada: AIza...
[OK] Agente criado com sucesso
[OK] Classificação correta!
[SUCCESS] Todos os testes passaram! ✅
```

### Teste 2: Via Python

```python
import os
from repositories.fiscal_repository import FiscalRepository
from agents.ncm_agent import create_ncm_agent

# Verificar API key
print(f"API Key: {os.getenv('GOOGLE_API_KEY')[:10]}...")

# Criar agente
repo = FiscalRepository()
agent = create_ncm_agent(repo)

# Testar classificação
result = agent.classify_ncm("Açúcar cristal tipo 1", "17019900")

print(f"NCM Sugerido: {result['suggested_ncm']}")
print(f"Confiança: {result['confidence']}%")
print(f"Correto: {result['is_correct']}")
```

### Teste 3: Via Streamlit

```bash
python run_streamlit.py
```

1. Marque "Usar Agente para NCM"
2. Insira sua API Key no campo de senha
3. Deve aparecer "✅ API Key configurada"
4. Upload de CSV e valide
5. Veja sugestões na aba "🤖 Sugestões IA"

---

## 🔧 Troubleshooting

### Erro: "Google API key required"

**Causa:** API key não configurada

**Solução:**
```bash
# Verificar se variável existe
echo $GOOGLE_API_KEY  # Linux/Mac
echo %GOOGLE_API_KEY%  # Windows CMD
$env:GOOGLE_API_KEY  # Windows PowerShell

# Se não existir, configure:
export GOOGLE_API_KEY="your-key-here"
```

### Erro: "Invalid API key"

**Causa:** API key incorreta ou expirada

**Solução:**
1. Acesse https://aistudio.google.com/app/apikey
2. Verifique se a key está ativa
3. Se necessário, gere uma nova key
4. Atualize a variável de ambiente

### Erro: "Quota exceeded"

**Causa:** Limite de uso da API atingido

**Solução:**
1. Acesse Google Cloud Console
2. Verifique quotas e limites
3. Aguarde reset (geralmente 24h)
4. Ou habilite billing para quotas maiores

### Erro: "Model not found: gemini-2.5-pro"

**Causa:** Modelo Gemini 2.5 não disponível na sua região/conta

**Solução Temporária:**

Edite `src/agents/ncm_agent.py` linha 60:
```python
# Tente um dos modelos alternativos:
model="gemini-1.5-pro"      # Gemini 1.5 Pro
# ou
model="gemini-2.0-flash-exp"  # Gemini 2.0 Flash
```

**Modelos Disponíveis:**
- `gemini-2.5-pro` - Mais recente, melhor performance ⭐
- `gemini-1.5-pro` - Produção estável
- `gemini-2.0-flash-exp` - Rápido, experimental
- `gemini-1.5-flash` - Rápido, menor custo

### Erro SQLite Thread (Streamlit)

**Causa:** SQLite não permite conexões de múltiplas threads

**Solução:** Já corrigido! (`check_same_thread=False` no repository)

Se persistir:
```python
# src/repositories/fiscal_repository.py linha 46
self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
```

---

## 💰 Custos

### Free Tier (Sem Billing)

**Gemini 2.5 Pro:**
- **15 requests/minuto** (RPM)
- **1 milhão tokens/dia**
- **1.500 requests/dia**

Para o MVP (validar poucas NF-es), o free tier é suficiente.

### Pricing (Com Billing)

**Gemini 2.5 Pro:**
- Input: $0.00075 / 1k tokens
- Output: $0.003 / 1k tokens

**Estimativa para MVP:**
- 1 classificação NCM ≈ 500 tokens
- 1000 classificações ≈ $1.50

---

## 🔒 Segurança

### Melhores Práticas

✅ **FAZER:**
- Usar variáveis de ambiente
- Rotacionar keys regularmente
- Limitar quotas no Google Cloud
- Monitorar uso

❌ **NÃO FAZER:**
- Commitar keys no Git
- Hardcodar keys no código
- Compartilhar keys publicamente
- Usar mesma key para dev/prod

### .gitignore

Certifique-se de ter no `.gitignore`:
```
# API Keys
.env
*.key
credentials.json

# Streamlit secrets
.streamlit/secrets.toml
```

---

## 📊 Monitorar Uso

### Via Google Cloud Console

1. Acesse: https://console.cloud.google.com
2. APIs & Services → Dashboard
3. Selecione "Generative Language API"
4. Veja gráficos de uso

### Via Streamlit

O agente já mostra feedback:
- ✅ API Key configurada
- ⚠️ Agente IA não disponível: [erro]
- 🔄 Inicializando Agente IA...
- 🔄 Classificando NCMs com IA...

---

## 🎯 Validar Configuração Completa

**Checklist:**

- [ ] API Key obtida no Google AI Studio
- [ ] Variável `GOOGLE_API_KEY` configurada
- [ ] `test_agent.py` executado com sucesso
- [ ] Streamlit mostra "✅ API Key configurada"
- [ ] Sugestões IA aparecem na aba "🤖 Sugestões IA"
- [ ] Modelo: `gemini-2.5-pro` (verifique em `ncm_agent.py:60`)

---

## 📚 Referências

- **Google AI Studio:** https://aistudio.google.com
- **Gemini API Docs:** https://ai.google.dev/docs
- **Pricing:** https://ai.google.dev/pricing
- **LangChain Google:** https://python.langchain.com/docs/integrations/chat/google_generative_ai

---

## 🆘 Suporte

**Erros persistentes?**

1. Verifique logs: `streamlit run --server.enableXsrfProtection false src/interface/streamlit_app.py`
2. Execute `test_agent.py` para diagnóstico
3. Consulte `README_MVP.md` seção "Agente IA"

---

**✅ Configuração Completa!**

Agora você pode usar o Agente IA para classificação inteligente de NCM com Google Gemini 2.5.

*Última atualização: 13/10/2025*
