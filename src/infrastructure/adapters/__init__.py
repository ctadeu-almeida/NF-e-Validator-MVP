# -*- coding: utf-8 -*-
"""
Infrastructure Adapters - Adaptadores da camada de infraestrutura

Este pacote contém adaptadores que implementam as interfaces definidas
na camada de aplicação, conectando a lógica de negócio com frameworks
e bibliotecas externas.
"""

from .streamlit_presenter import StreamlitPresenter
from .pandas_file_processor import PandasFileProcessor
from .memory_dataset_repository import MemoryDatasetRepository

__all__ = [
    'StreamlitPresenter',
    'PandasFileProcessor',
    'MemoryDatasetRepository'
]