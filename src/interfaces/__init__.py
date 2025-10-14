# -*- coding: utf-8 -*-
"""
Interfaces Package - Abstrações e contratos da aplicação

Este pacote contém todas as interfaces e abstrações que definem
os contratos para diferentes componentes da aplicação, promovendo
baixo acoplamento e alta testabilidade.
"""

from .llm_interface import (
    ILanguageModel,
    IChatModel,
    ICodeGenerationModel,
    IAnalysisModel,
    IModelProvider,
    ModelType,
    ModelConfig,
    ModelResponse,
    ModelError,
    ModelInitializationError,
    ModelGenerationError,
    ModelTimeoutError,
    ModelQuotaExceededError,
    ModelConfigurationError
)

from .agent_interface import (
    IDataAgent,
    IStatisticalAgent,
    IVisualizationAgent,
    IConversationalAgent,
    ICodeGenerationAgent,
    IEDAAgent,
    IAgentFactory,
    AgentCapabilities,
    AgentConfig,
    AnalysisRequest,
    AnalysisResponse,
    AgentError,
    AgentInitializationError,
    AgentDataError,
    AgentAnalysisError,
    AgentTimeoutError
)

__all__ = [
    # LLM Interfaces
    'ILanguageModel',
    'IChatModel',
    'ICodeGenerationModel',
    'IAnalysisModel',
    'IModelProvider',
    'ModelType',
    'ModelConfig',
    'ModelResponse',
    'ModelError',
    'ModelInitializationError',
    'ModelGenerationError',
    'ModelTimeoutError',
    'ModelQuotaExceededError',
    'ModelConfigurationError',

    # Agent Interfaces
    'IDataAgent',
    'IStatisticalAgent',
    'IVisualizationAgent',
    'IConversationalAgent',
    'ICodeGenerationAgent',
    'IEDAAgent',
    'IAgentFactory',
    'AgentCapabilities',
    'AgentConfig',
    'AnalysisRequest',
    'AnalysisResponse',
    'AgentError',
    'AgentInitializationError',
    'AgentDataError',
    'AgentAnalysisError',
    'AgentTimeoutError'
]