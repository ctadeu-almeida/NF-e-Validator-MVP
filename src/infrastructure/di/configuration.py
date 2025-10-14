# -*- coding: utf-8 -*-
"""
DI Configuration - Configuração do container de injeção de dependências

Centraliza toda a configuração das dependências da aplicação,
seguindo o padrão Composition Root.
"""

from src.infrastructure.di.container import DIContainer
from src.infrastructure.adapters.pandas_file_processor import PandasFileProcessor
from src.infrastructure.adapters.memory_dataset_repository import MemoryDatasetRepository
from src.application.interfaces.file_processor import IFileProcessor
from src.application.interfaces.dataset_repository import IDatasetRepository
from src.application.use_cases.load_dataset_use_case import LoadDatasetUseCase
from src.domain.services import DataAnalysisService, QueryAnalysisService
from src.utils.logger import StructuredLogger


def configure_dependencies() -> DIContainer:
    """
    Configura todas as dependências da aplicação

    Returns:
        Container configurado com todas as dependências
    """
    container = DIContainer()

    # Utilitários (Singletons)
    container.register_singleton(StructuredLogger, StructuredLogger)

    # Serviços de domínio (Singletons)
    container.register_singleton(DataAnalysisService, DataAnalysisService)
    container.register_singleton(QueryAnalysisService, QueryAnalysisService)

    # Adaptadores de infraestrutura (Singletons)
    container.register_singleton(IFileProcessor, PandasFileProcessor)
    container.register_singleton(IDatasetRepository, MemoryDatasetRepository)

    # Casos de uso (Factory - podem ter estado)
    container.register_factory(LoadDatasetUseCase, LoadDatasetUseCase)

    return container


def configure_test_dependencies() -> DIContainer:
    """
    Configura dependências para testes (com mocks quando necessário)

    Returns:
        Container configurado para ambiente de teste
    """
    container = DIContainer()

    # Para testes, usar as mesmas implementações por enquanto
    # Em cenários reais, aqui usaríamos mocks
    container.register_singleton(StructuredLogger, StructuredLogger)
    container.register_singleton(DataAnalysisService, DataAnalysisService)
    container.register_singleton(QueryAnalysisService, QueryAnalysisService)
    container.register_singleton(IFileProcessor, PandasFileProcessor)
    container.register_singleton(IDatasetRepository, MemoryDatasetRepository)
    container.register_factory(LoadDatasetUseCase, LoadDatasetUseCase)

    return container


def configure_production_dependencies() -> DIContainer:
    """
    Configura dependências para produção

    Returns:
        Container configurado para ambiente de produção
    """
    container = configure_dependencies()

    # Em produção, poderíamos trocar implementações:
    # - MemoryDatasetRepository por DatabaseDatasetRepository
    # - Adicionar configurações específicas de produção
    # - Configurar logging para produção

    return container


def configure_development_dependencies() -> DIContainer:
    """
    Configura dependências para desenvolvimento

    Returns:
        Container configurado para ambiente de desenvolvimento
    """
    container = configure_dependencies()

    # Em desenvolvimento, podemos adicionar:
    # - Logging mais verboso
    # - Ferramentas de debug
    # - Implementações com mais validações

    return container


# Container global da aplicação
_app_container: DIContainer = None


def get_app_container() -> DIContainer:
    """
    Obtém o container da aplicação

    Returns:
        Container configurado da aplicação
    """
    global _app_container
    if _app_container is None:
        _app_container = configure_dependencies()
    return _app_container


def set_app_container(container: DIContainer):
    """
    Define o container da aplicação

    Args:
        container: Container a ser usado pela aplicação
    """
    global _app_container
    _app_container = container


def reset_app_container():
    """Reseta o container da aplicação"""
    global _app_container
    _app_container = None


# Funções de conveniência para casos de uso comuns
def resolve_load_dataset_use_case() -> LoadDatasetUseCase:
    """Resolve o caso de uso de carregamento de dataset"""
    return get_app_container().resolve(LoadDatasetUseCase)


def resolve_data_analysis_service() -> DataAnalysisService:
    """Resolve o serviço de análise de dados"""
    return get_app_container().resolve(DataAnalysisService)


def resolve_query_analysis_service() -> QueryAnalysisService:
    """Resolve o serviço de análise de queries"""
    return get_app_container().resolve(QueryAnalysisService)


def resolve_file_processor() -> IFileProcessor:
    """Resolve o processador de arquivos"""
    return get_app_container().resolve(IFileProcessor)


def resolve_dataset_repository() -> IDatasetRepository:
    """Resolve o repositório de datasets"""
    return get_app_container().resolve(IDatasetRepository)


def resolve_logger() -> StructuredLogger:
    """Resolve o logger estruturado"""
    return get_app_container().resolve(StructuredLogger)