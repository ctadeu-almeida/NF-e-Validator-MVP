# -*- coding: utf-8 -*-
"""
LangChain ReAct Agent - NCM Classification

Agente inteligente para classificação semântica de NCM quando:
- Descrição do produto é ambígua
- NCM não está no database
- Múltiplos NCMs possíveis

Usa ReAct (Reasoning + Acting) pattern com Google Gemini
"""

from typing import Dict, List, Optional, Any
from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import Tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
import os

# Import FiscalRepository
import sys
from pathlib import Path
if True:
    project_root = Path(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from repositories.fiscal_repository import FiscalRepository


class NCMReActAgent:
    """
    Agente ReAct para classificação inteligente de NCM

    Capabilities:
    - Buscar NCMs no database por palavras-chave
    - Analisar descrição do produto semanticamente
    - Sugerir NCM mais apropriado com confidence score
    - Explicar raciocínio (reasoning trace)
    """

    def __init__(self, repository: FiscalRepository, api_key: str = None):
        """
        Inicializar agente NCM

        Args:
            repository: FiscalRepository para consultas
            api_key: Google AI API key (ou usar GOOGLE_API_KEY env var)
        """
        self.repo = repository

        # Initialize Gemini model
        if api_key is None:
            api_key = os.getenv('GOOGLE_API_KEY')

        if not api_key:
            raise ValueError("Google API key required (set GOOGLE_API_KEY env var or pass api_key)")

        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-pro",  # Gemini 2.5
            google_api_key=api_key,
            temperature=0.1,  # Low temperature for consistency
            max_output_tokens=2000
        )

        # Define tools
        self.tools = self._create_tools()

        # Create ReAct agent
        self.agent = self._create_agent()

        # Create executor
        self.executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            max_iterations=5,
            handle_parsing_errors=True
        )

    def _create_tools(self) -> List[Tool]:
        """
        Criar ferramentas (tools) para o agente

        Returns:
            Lista de Tools
        """

        def search_ncm_by_keywords(query: str) -> str:
            """Buscar NCMs que contenham palavras-chave na descrição ou keywords"""
            query_lower = query.lower()

            # Get all sugar NCMs
            ncms = self.repo.get_all_sugar_ncms()

            results = []
            for ncm_data in ncms:
                # Check description
                if query_lower in ncm_data['description'].lower():
                    results.append(ncm_data)
                    continue

                # Check keywords
                keywords = self.repo.get_ncm_keywords(ncm_data['ncm'])
                if any(query_lower in kw.lower() for kw in keywords):
                    results.append(ncm_data)

            if not results:
                return f"Nenhum NCM encontrado para: {query}"

            # Format results
            output = f"NCMs encontrados ({len(results)}):\n\n"
            for ncm_data in results:
                output += f"- NCM: {ncm_data['ncm']}\n"
                output += f"  Descrição: {ncm_data['description']}\n"
                output += f"  Tipo: {ncm_data.get('product_type', 'N/A')}\n"

                keywords = self.repo.get_ncm_keywords(ncm_data['ncm'])
                output += f"  Keywords: {', '.join(keywords)}\n\n"

            return output

        def get_ncm_details(ncm: str) -> str:
            """Obter detalhes completos de um NCM específico"""
            ncm_clean = ncm.replace('.', '').replace('-', '')

            ncm_rule = self.repo.get_ncm_rule(ncm_clean)

            if not ncm_rule:
                return f"NCM {ncm} não encontrado no database"

            # Format details
            output = f"NCM: {ncm_rule['ncm']}\n"
            output += f"Descrição: {ncm_rule['description']}\n"
            output += f"Categoria: {ncm_rule.get('category', 'N/A')}\n"
            output += f"Tipo de Produto: {ncm_rule.get('product_type', 'N/A')}\n"
            output += f"Setor: {ncm_rule.get('sector', 'N/A')}\n"
            output += f"IPI: {ncm_rule.get('ipi_rate', 0)}% (Isento: {ncm_rule.get('is_ipi_exempt', False)})\n"
            output += f"Regime PIS/COFINS: {ncm_rule.get('pis_cofins_regime', 'STANDARD')}\n"

            keywords = self.repo.get_ncm_keywords(ncm_rule['ncm'])
            output += f"Keywords: {', '.join(keywords)}\n"

            if ncm_rule.get('notes'):
                output += f"\nNotas: {ncm_rule['notes']}\n"

            return output

        def list_all_sugar_ncms(query: str = "") -> str:
            """Listar todos os NCMs de açúcar disponíveis"""
            # Ignora o argumento query (LangChain sempre passa, mesmo vazio)
            ncms = self.repo.get_all_sugar_ncms()

            output = f"Total de NCMs de açúcar: {len(ncms)}\n\n"

            for ncm_data in ncms:
                output += f"- {ncm_data['ncm']}: {ncm_data['description']}"
                if ncm_data.get('product_type'):
                    output += f" ({ncm_data['product_type']})"
                output += "\n"

            return output

        # Define tools
        tools = [
            Tool(
                name="search_ncm_by_keywords",
                func=search_ncm_by_keywords,
                description=(
                    "Buscar NCMs que contenham palavras-chave específicas. "
                    "Use esta ferramenta para encontrar NCMs relacionados a um produto. "
                    "Input: palavra-chave ou frase (ex: 'refinado', 'cristal', 'bruto')"
                )
            ),
            Tool(
                name="get_ncm_details",
                func=get_ncm_details,
                description=(
                    "Obter detalhes completos de um NCM específico. "
                    "Use quando precisar de informações detalhadas sobre um NCM. "
                    "Input: código NCM (8 dígitos, ex: '17019900')"
                )
            ),
            Tool(
                name="list_all_sugar_ncms",
                func=list_all_sugar_ncms,
                description=(
                    "Listar todos os NCMs de açúcar disponíveis no MVP. "
                    "Use para ter uma visão geral dos NCMs possíveis. "
                    "Input: não requer input (use string vazia)"
                )
            )
        ]

        return tools

    def _create_agent(self):
        """
        Criar agente ReAct com prompt personalizado

        Returns:
            ReAct Agent
        """

        template = """Você é um especialista em classificação fiscal de produtos do setor sucroalcooleiro (açúcar).
Sua tarefa é determinar o NCM (Nomenclatura Comum do Mercosul) mais apropriado para produtos de açúcar.

Você tem acesso às seguintes ferramentas:

{tools}

Use o seguinte formato OBRIGATORIAMENTE:

Question: a pergunta de entrada que você deve responder
Thought: você deve sempre pensar sobre o que fazer
Action: a ação a tomar, deve ser uma de [{tool_names}]
Action Input: o input para a ação
Observation: o resultado da ação
... (este Thought/Action/Action Input/Observation pode repetir N vezes)
Thought: Agora sei a resposta final
Final Answer: a resposta final para a pergunta original

IMPORTANTE:
- Açúcar CRISTAL → NCM 17019900 (mais comum)
- Açúcar REFINADO → NCM 17019100 (com aromatizante) ou 17019900
- Açúcar BRUTO → NCM 17011100 (cana) ou 17011200 (beterraba)
- Use as ferramentas para verificar keywords e descrições
- Seja específico e justifique sua escolha
- Forneça confidence score (0-100%)

Comece!

Question: {input}
Thought: {agent_scratchpad}"""

        prompt = PromptTemplate(
            template=template,
            input_variables=["input", "agent_scratchpad"],
            partial_variables={
                "tools": "\n".join([f"- {tool.name}: {tool.description}" for tool in self.tools]),
                "tool_names": ", ".join([tool.name for tool in self.tools])
            }
        )

        return create_react_agent(self.llm, self.tools, prompt)

    def classify_ncm(self, product_description: str, current_ncm: str = None) -> Dict[str, Any]:
        """
        Classificar NCM para um produto

        Args:
            product_description: Descrição do produto
            current_ncm: NCM atual na NF-e (opcional, para comparação)

        Returns:
            Dict com:
            - suggested_ncm: NCM sugerido
            - confidence: Confiança (0-100)
            - reasoning: Raciocínio do agente
            - is_correct: Se NCM atual está correto (se fornecido)
        """

        # Build query
        query = f"Qual o NCM correto para o produto: '{product_description}'"

        if current_ncm:
            query += f"\nNCM atual na nota: {current_ncm}"
            query += "\nO NCM atual está correto? Se não, qual deveria ser?"

        try:
            # Run agent
            result = self.executor.invoke({"input": query})

            # Parse result
            answer = result.get('output', '')

            # Extract suggested NCM (simple parsing)
            suggested_ncm = self._extract_ncm_from_answer(answer)

            # Determine if current NCM is correct
            is_correct = None
            if current_ncm:
                is_correct = (current_ncm == suggested_ncm)

            return {
                'suggested_ncm': suggested_ncm,
                'confidence': self._extract_confidence(answer),
                'reasoning': answer,
                'is_correct': is_correct,
                'query': query
            }

        except Exception as e:
            return {
                'suggested_ncm': None,
                'confidence': 0,
                'reasoning': f"Erro ao processar: {str(e)}",
                'is_correct': None,
                'query': query,
                'error': str(e)
            }

    def _extract_ncm_from_answer(self, answer: str) -> Optional[str]:
        """
        Extrair NCM da resposta do agente

        Args:
            answer: Resposta do agente

        Returns:
            NCM (8 dígitos) ou None
        """
        import re

        # Look for 8-digit NCM patterns
        patterns = [
            r'NCM[:\s]+(\d{8})',
            r'(\d{4}\.\d{2}\.\d{2})',
            r'(\d{8})'
        ]

        for pattern in patterns:
            match = re.search(pattern, answer)
            if match:
                ncm = match.group(1).replace('.', '')
                if len(ncm) == 8:
                    return ncm

        return None

    def _extract_confidence(self, answer: str) -> int:
        """
        Extrair confidence score da resposta

        Args:
            answer: Resposta do agente

        Returns:
            Confidence (0-100)
        """
        import re

        # Look for confidence patterns
        patterns = [
            r'confidence[:\s]+(\d+)%',
            r'confiança[:\s]+(\d+)%',
            r'(\d+)%\s+de confiança'
        ]

        for pattern in patterns:
            match = re.search(pattern, answer.lower())
            if match:
                return int(match.group(1))

        # Default confidence
        return 80


# =====================================================
# Factory Functions
# =====================================================

def create_ncm_agent(repository: FiscalRepository, api_key: str = None) -> NCMReActAgent:
    """
    Factory para criar agente NCM

    Args:
        repository: FiscalRepository
        api_key: Google AI API key (opcional)

    Returns:
        NCMReActAgent instanciado
    """
    return NCMReActAgent(repository, api_key)
