# -*- coding: utf-8 -*-
"""
Dataset Repository Interface - Interface para repositório de datasets

Define o contrato para persistência e recuperação de datasets,
permitindo diferentes implementações de armazenamento.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
import pandas as pd
from src.domain.entities import DatasetInfo


class IDatasetRepository(ABC):
    """Interface para repositório de datasets"""

    @abstractmethod
    def save_dataset(self, data: pd.DataFrame, info: DatasetInfo) -> str:
        """
        Salva um dataset

        Args:
            data: DataFrame com os dados
            info: Informações do dataset

        Returns:
            ID único do dataset salvo
        """
        pass

    @abstractmethod
    def load_dataset(self, dataset_id: str) -> Optional[pd.DataFrame]:
        """
        Carrega um dataset pelo ID

        Args:
            dataset_id: ID do dataset

        Returns:
            DataFrame ou None se não encontrado
        """
        pass

    @abstractmethod
    def get_dataset_info(self, dataset_id: str) -> Optional[DatasetInfo]:
        """
        Obtém informações de um dataset

        Args:
            dataset_id: ID do dataset

        Returns:
            Informações do dataset ou None
        """
        pass

    @abstractmethod
    def list_datasets(self) -> List[DatasetInfo]:
        """
        Lista todos os datasets disponíveis

        Returns:
            Lista de informações dos datasets
        """
        pass

    @abstractmethod
    def delete_dataset(self, dataset_id: str) -> bool:
        """
        Remove um dataset

        Args:
            dataset_id: ID do dataset

        Returns:
            True se removido com sucesso
        """
        pass

    @abstractmethod
    def update_dataset_info(self, dataset_id: str, info: DatasetInfo) -> bool:
        """
        Atualiza informações de um dataset

        Args:
            dataset_id: ID do dataset
            info: Novas informações

        Returns:
            True se atualizado com sucesso
        """
        pass

    @abstractmethod
    def search_datasets(self, query: str) -> List[DatasetInfo]:
        """
        Busca datasets por nome ou descrição

        Args:
            query: Termo de busca

        Returns:
            Lista de datasets encontrados
        """
        pass

    @abstractmethod
    def get_dataset_metadata(self, dataset_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtém metadados estendidos de um dataset

        Args:
            dataset_id: ID do dataset

        Returns:
            Metadados ou None
        """
        pass

    @abstractmethod
    def cleanup_expired_datasets(self, max_age_hours: int = 24) -> int:
        """
        Remove datasets expirados

        Args:
            max_age_hours: Idade máxima em horas

        Returns:
            Número de datasets removidos
        """
        pass