# -*- coding: utf-8 -*-
"""
Domain Package - Camada de domínio da aplicação CSVEDA

Este pacote contém as entidades de negócio e serviços de domínio,
implementando a lógica central da aplicação separada da infraestrutura.
"""

from .entities import (
    DatasetInfo,
    AnalysisResult,
    Visualization,
    OutlierInfo,
    CorrelationAnalysis,
    DataQualityReport,
    AnalysisSession,
    AgentQuery,
    ModelResponse
)

from .services import (
    DataAnalysisService,
    QueryAnalysisService
)

__all__ = [
    # Entities
    'DatasetInfo',
    'AnalysisResult',
    'Visualization',
    'OutlierInfo',
    'CorrelationAnalysis',
    'DataQualityReport',
    'AnalysisSession',
    'AgentQuery',
    'ModelResponse',

    # Services
    'DataAnalysisService',
    'QueryAnalysisService'
]