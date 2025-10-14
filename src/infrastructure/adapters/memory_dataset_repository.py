# -*- coding: utf-8 -*-
"""
Memory Dataset Repository - Repositório de datasets em memória

Implementa a interface IDatasetRepository armazenando datasets
temporariamente em memória para prototipagem e desenvolvimento.
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import pandas as pd

from src.application.interfaces.dataset_repository import IDatasetRepository
from src.domain.entities import DatasetInfo


class MemoryDatasetRepository(IDatasetRepository):
    """Repositório de datasets em memória"""

    def __init__(self):
        self._datasets: Dict[str, pd.DataFrame] = {}
        self._dataset_info: Dict[str, DatasetInfo] = {}
        self._metadata: Dict[str, Dict[str, Any]] = {}
        self._timestamps: Dict[str, datetime] = {}

    def save_dataset(self, data: pd.DataFrame, info: DatasetInfo) -> str:
        """Salva um dataset"""
        dataset_id = str(uuid.uuid4())

        # Criar cópia dos dados para evitar modificações externas
        self._datasets[dataset_id] = data.copy()
        self._dataset_info[dataset_id] = info
        self._timestamps[dataset_id] = datetime.now()

        # Metadados básicos
        self._metadata[dataset_id] = {
            'created_at': datetime.now().isoformat(),
            'access_count': 0,
            'last_accessed': None
        }

        return dataset_id

    def load_dataset(self, dataset_id: str) -> Optional[pd.DataFrame]:
        """Carrega um dataset pelo ID"""
        if dataset_id not in self._datasets:
            return None

        # Atualizar contadores de acesso
        self._metadata[dataset_id]['access_count'] += 1
        self._metadata[dataset_id]['last_accessed'] = datetime.now().isoformat()

        # Retornar cópia para evitar modificações
        return self._datasets[dataset_id].copy()

    def get_dataset_info(self, dataset_id: str) -> Optional[DatasetInfo]:
        """Obtém informações de um dataset"""
        return self._dataset_info.get(dataset_id)

    def list_datasets(self) -> List[DatasetInfo]:
        """Lista todos os datasets disponíveis"""
        return list(self._dataset_info.values())

    def delete_dataset(self, dataset_id: str) -> bool:
        """Remove um dataset"""
        if dataset_id not in self._datasets:
            return False

        del self._datasets[dataset_id]
        del self._dataset_info[dataset_id]
        del self._timestamps[dataset_id]
        if dataset_id in self._metadata:
            del self._metadata[dataset_id]

        return True

    def update_dataset_info(self, dataset_id: str, info: DatasetInfo) -> bool:
        """Atualiza informações de um dataset"""
        if dataset_id not in self._dataset_info:
            return False

        self._dataset_info[dataset_id] = info
        return True

    def search_datasets(self, query: str) -> List[DatasetInfo]:
        """Busca datasets por nome ou descrição"""
        query_lower = query.lower()
        results = []

        for info in self._dataset_info.values():
            if (query_lower in info.name.lower() or
                (info.description and query_lower in info.description.lower())):
                results.append(info)

        return results

    def get_dataset_metadata(self, dataset_id: str) -> Optional[Dict[str, Any]]:
        """Obtém metadados estendidos de um dataset"""
        if dataset_id not in self._metadata:
            return None

        metadata = self._metadata[dataset_id].copy()

        # Adicionar informações de dataset
        if dataset_id in self._dataset_info:
            info = self._dataset_info[dataset_id]
            metadata['dataset_info'] = {
                'name': info.name,
                'rows': info.rows,
                'columns': info.columns,
                'size_bytes': info.size_bytes,
                'source': info.source
            }

        # Adicionar estatísticas de uso
        if dataset_id in self._timestamps:
            age = datetime.now() - self._timestamps[dataset_id]
            metadata['age_hours'] = age.total_seconds() / 3600

        return metadata

    def cleanup_expired_datasets(self, max_age_hours: int = 24) -> int:
        """Remove datasets expirados"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        expired_ids = []

        for dataset_id, timestamp in self._timestamps.items():
            if timestamp < cutoff_time:
                expired_ids.append(dataset_id)

        removed_count = 0
        for dataset_id in expired_ids:
            if self.delete_dataset(dataset_id):
                removed_count += 1

        return removed_count

    def get_memory_usage(self) -> Dict[str, Any]:
        """Obtém informações sobre uso de memória"""
        total_datasets = len(self._datasets)
        total_rows = sum(df.shape[0] for df in self._datasets.values())
        total_columns = sum(df.shape[1] for df in self._datasets.values())

        # Estimativa de uso de memória (não é exata)
        estimated_memory_mb = sum(
            df.memory_usage(deep=True).sum() / (1024 * 1024)
            for df in self._datasets.values()
        )

        return {
            'total_datasets': total_datasets,
            'total_rows': total_rows,
            'total_columns': total_columns,
            'estimated_memory_mb': round(estimated_memory_mb, 2),
            'dataset_ids': list(self._datasets.keys())
        }

    def clear_all(self) -> int:
        """Remove todos os datasets"""
        count = len(self._datasets)
        self._datasets.clear()
        self._dataset_info.clear()
        self._metadata.clear()
        self._timestamps.clear()
        return count