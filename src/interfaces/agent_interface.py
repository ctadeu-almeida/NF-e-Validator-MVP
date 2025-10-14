# -*- coding: utf-8 -*-
"""
Agent Interface - Interfaces para agentes de análise

Este módulo define abstrações para agentes de análise de dados,
permitindo diferentes implementações e facilitando testes.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
import pandas as pd
from .llm_interface import IAnalysisModel, ModelResponse


@dataclass
class AgentCapabilities:
    """Capacidades de um agente"""
    statistical_analysis: bool = True
    visualization: bool = True
    code_generation: bool = True
    data_cleaning: bool = True
    outlier_detection: bool = True
    correlation_analysis: bool = True
    predictive_analysis: bool = False
    natural_language_queries: bool = True


@dataclass
class AgentConfig:
    """Configuração de um agente"""
    name: str
    model: IAnalysisModel
    capabilities: AgentCapabilities
    max_iterations: int = 10
    timeout_seconds: int = 120
    memory_enabled: bool = True
    tools_enabled: List[str] = None

    def __post_init__(self):
        if self.tools_enabled is None:
            self.tools_enabled = []


@dataclass
class AnalysisRequest:
    """Requisição de análise"""
    query: str
    data: Optional[pd.DataFrame] = None
    context: Optional[Dict[str, Any]] = None
    preferred_output: Optional[str] = None  # text, visualization, code
    constraints: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.context is None:
            self.context = {}
        if self.constraints is None:
            self.constraints = {}


@dataclass
class AnalysisResponse:
    """Resposta de análise"""
    content: str
    request_id: str
    agent_name: str
    success: bool = True
    execution_time: Optional[float] = None
    generated_artifacts: List[str] = None  # Caminhos para gráficos, códigos, etc.
    intermediate_steps: List[Dict[str, Any]] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.generated_artifacts is None:
            self.generated_artifacts = []
        if self.intermediate_steps is None:
            self.intermediate_steps = []
        if self.metadata is None:
            self.metadata = {}


class IDataAgent(ABC):
    """Interface base para agentes de análise de dados"""

    @abstractmethod
    def initialize(self, config: AgentConfig) -> bool:
        """Inicializar o agente"""
        pass

    @abstractmethod
    def load_data(self, data: Union[pd.DataFrame, str], **kwargs) -> bool:
        """Carregar dados para análise"""
        pass

    @abstractmethod
    def analyze(self, request: AnalysisRequest) -> AnalysisResponse:
        """Realizar análise baseada na requisição"""
        pass

    @abstractmethod
    def get_capabilities(self) -> AgentCapabilities:
        """Obter capacidades do agente"""
        pass

    @abstractmethod
    def is_ready(self) -> bool:
        """Verificar se o agente está pronto para análise"""
        pass

    @abstractmethod
    def get_data_info(self) -> Optional[Dict[str, Any]]:
        """Obter informações sobre os dados carregados"""
        pass

    @abstractmethod
    def clear_memory(self):
        """Limpar memória do agente"""
        pass


class IStatisticalAgent(IDataAgent):
    """Interface para agentes especializados em análise estatística"""

    @abstractmethod
    def descriptive_statistics(self, columns: Optional[List[str]] = None) -> AnalysisResponse:
        """Gerar estatísticas descritivas"""
        pass

    @abstractmethod
    def correlation_analysis(self, method: str = "pearson") -> AnalysisResponse:
        """Análise de correlação"""
        pass

    @abstractmethod
    def outlier_detection(self, method: str = "iqr") -> AnalysisResponse:
        """Detecção de outliers"""
        pass

    @abstractmethod
    def hypothesis_testing(self, test_type: str, **kwargs) -> AnalysisResponse:
        """Testes de hipótese"""
        pass


class IVisualizationAgent(IDataAgent):
    """Interface para agentes especializados em visualização"""

    @abstractmethod
    def create_histogram(self, column: str, **kwargs) -> AnalysisResponse:
        """Criar histograma"""
        pass

    @abstractmethod
    def create_scatter_plot(self, x_col: str, y_col: str, **kwargs) -> AnalysisResponse:
        """Criar gráfico de dispersão"""
        pass

    @abstractmethod
    def create_correlation_heatmap(self, **kwargs) -> AnalysisResponse:
        """Criar heatmap de correlação"""
        pass

    @abstractmethod
    def create_custom_visualization(self, description: str, **kwargs) -> AnalysisResponse:
        """Criar visualização customizada baseada em descrição"""
        pass


class IConversationalAgent(IDataAgent):
    """Interface para agentes conversacionais"""

    @abstractmethod
    def ask_question(self, question: str, **kwargs) -> AnalysisResponse:
        """Fazer pergunta em linguagem natural"""
        pass

    @abstractmethod
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Obter histórico da conversa"""
        pass

    @abstractmethod
    def suggest_next_analysis(self) -> List[str]:
        """Sugerir próximas análises"""
        pass


class ICodeGenerationAgent(IDataAgent):
    """Interface para agentes de geração de código"""

    @abstractmethod
    def generate_analysis_code(self, description: str, **kwargs) -> AnalysisResponse:
        """Gerar código de análise"""
        pass

    @abstractmethod
    def execute_code(self, code: str, **kwargs) -> AnalysisResponse:
        """Executar código Python"""
        pass

    @abstractmethod
    def explain_analysis(self, results: Dict[str, Any], **kwargs) -> AnalysisResponse:
        """Explicar resultados de análise"""
        pass


class IEDAAgent(IStatisticalAgent, IVisualizationAgent,
                IConversationalAgent, ICodeGenerationAgent):
    """Interface completa para agentes EDA (Exploratory Data Analysis)"""

    @abstractmethod
    def comprehensive_analysis(self, **kwargs) -> AnalysisResponse:
        """Realizar análise exploratória completa"""
        pass

    @abstractmethod
    def data_quality_report(self, **kwargs) -> AnalysisResponse:
        """Gerar relatório de qualidade dos dados"""
        pass

    @abstractmethod
    def export_analysis(self, format: str = "html", **kwargs) -> str:
        """Exportar análise em formato específico"""
        pass


class IAgentFactory(ABC):
    """Interface para factory de agentes"""

    @abstractmethod
    def create_eda_agent(self, config: AgentConfig) -> IEDAAgent:
        """Criar agente EDA"""
        pass

    @abstractmethod
    def create_statistical_agent(self, config: AgentConfig) -> IStatisticalAgent:
        """Criar agente estatístico"""
        pass

    @abstractmethod
    def create_visualization_agent(self, config: AgentConfig) -> IVisualizationAgent:
        """Criar agente de visualização"""
        pass

    @abstractmethod
    def get_available_agents(self) -> List[str]:
        """Listar agentes disponíveis"""
        pass

    @abstractmethod
    def get_default_config(self, agent_type: str) -> AgentConfig:
        """Obter configuração padrão para tipo de agente"""
        pass


class AgentError(Exception):
    """Exceção base para erros de agente"""

    def __init__(self, message: str, agent_name: str = None, error_code: str = None):
        self.message = message
        self.agent_name = agent_name
        self.error_code = error_code
        super().__init__(self.message)


class AgentInitializationError(AgentError):
    """Erro na inicialização do agente"""
    pass


class AgentDataError(AgentError):
    """Erro relacionado aos dados do agente"""
    pass


class AgentAnalysisError(AgentError):
    """Erro durante análise"""
    pass


class AgentTimeoutError(AgentError):
    """Timeout na execução do agente"""
    pass