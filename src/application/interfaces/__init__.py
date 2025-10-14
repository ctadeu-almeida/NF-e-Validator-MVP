# -*- coding: utf-8 -*-
"""
Application Interfaces - Interfaces da camada de aplicação

Este pacote define as interfaces que a camada de aplicação
precisa da infraestrutura, implementando inversão de dependência.
"""

from .dataset_repository import IDatasetRepository
from .file_processor import IFileProcessor
from .analysis_presenter import IAnalysisPresenter
from .notification_service import INotificationService

__all__ = [
    'IDatasetRepository',
    'IFileProcessor',
    'IAnalysisPresenter',
    'INotificationService'
]