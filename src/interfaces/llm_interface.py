# -*- coding: utf-8 -*-
"""
LLM Interface - Interfaces para Large Language Models

Este módulo define abstrações para diferentes provedores de LLM,
permitindo troca fácil entre modelos sem alterar a lógica de negócio.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum


class ModelType(Enum):
    """Tipos de modelos suportados"""
    GEMINI = "gemini"
    MISTRAL = "mistral"
    OPENAI = "openai"
    CLAUDE = "claude"


@dataclass
class ModelConfig:
    """Configuração de um modelo"""
    model_name: str
    temperature: float = 0.1
    max_tokens: int = 4096
    timeout: int = 30
    api_key: Optional[str] = None
    additional_params: Dict[str, Any] = None

    def __post_init__(self):
        if self.additional_params is None:
            self.additional_params = {}


@dataclass
class ModelResponse:
    """Resposta de um modelo"""
    content: str
    model_name: str
    tokens_used: Optional[int] = None
    execution_time: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ILanguageModel(ABC):
    """Interface base para modelos de linguagem"""

    @abstractmethod
    def initialize(self, config: ModelConfig) -> bool:
        """Inicializar o modelo com configurações"""
        pass

    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> ModelResponse:
        """Gerar resposta para um prompt"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Verificar se o modelo está disponível"""
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Obter informações sobre o modelo"""
        pass

    @abstractmethod
    def estimate_tokens(self, text: str) -> int:
        """Estimar número de tokens de um texto"""
        pass


class IChatModel(ILanguageModel):
    """Interface para modelos de chat/conversação"""

    @abstractmethod
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> ModelResponse:
        """Manter conversa com histórico de mensagens"""
        pass

    @abstractmethod
    def clear_history(self):
        """Limpar histórico de conversa"""
        pass

    @abstractmethod
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Obter histórico da conversa"""
        pass


class ICodeGenerationModel(ILanguageModel):
    """Interface para modelos especializados em geração de código"""

    @abstractmethod
    def generate_code(self, description: str, language: str = "python", **kwargs) -> ModelResponse:
        """Gerar código baseado em descrição"""
        pass

    @abstractmethod
    def explain_code(self, code: str, **kwargs) -> ModelResponse:
        """Explicar código fornecido"""
        pass

    @abstractmethod
    def optimize_code(self, code: str, **kwargs) -> ModelResponse:
        """Otimizar código fornecido"""
        pass


class IAnalysisModel(IChatModel, ICodeGenerationModel):
    """Interface para modelos especializados em análise de dados"""

    @abstractmethod
    def analyze_data_structure(self, data_info: Dict[str, Any], **kwargs) -> ModelResponse:
        """Analisar estrutura de dados"""
        pass

    @abstractmethod
    def suggest_analysis(self, data_info: Dict[str, Any], user_goal: str, **kwargs) -> ModelResponse:
        """Sugerir análises baseadas nos dados e objetivo"""
        pass

    @abstractmethod
    def interpret_results(self, analysis_results: Dict[str, Any], **kwargs) -> ModelResponse:
        """Interpretar resultados de análise"""
        pass


class IModelProvider(ABC):
    """Interface para provedores de modelos"""

    @abstractmethod
    def get_available_models(self) -> List[str]:
        """Listar modelos disponíveis"""
        pass

    @abstractmethod
    def create_model(self, model_name: str, config: ModelConfig) -> ILanguageModel:
        """Criar instância de um modelo"""
        pass

    @abstractmethod
    def get_default_config(self, model_name: str) -> ModelConfig:
        """Obter configuração padrão para um modelo"""
        pass

    @abstractmethod
    def validate_config(self, config: ModelConfig) -> bool:
        """Validar configuração do modelo"""
        pass


class ModelError(Exception):
    """Exceção base para erros de modelo"""

    def __init__(self, message: str, model_name: str = None, error_code: str = None):
        self.message = message
        self.model_name = model_name
        self.error_code = error_code
        super().__init__(self.message)


class ModelInitializationError(ModelError):
    """Erro na inicialização do modelo"""
    pass


class ModelGenerationError(ModelError):
    """Erro na geração de resposta"""
    pass


class ModelTimeoutError(ModelError):
    """Timeout na requisição ao modelo"""
    pass


class ModelQuotaExceededError(ModelError):
    """Cota do modelo excedida"""
    pass


class ModelConfigurationError(ModelError):
    """Erro de configuração do modelo"""
    pass