# -*- coding: utf-8 -*-
"""
Load Dataset Use Case - Caso de uso para carregamento de datasets

Este módulo implementa o caso de uso responsável por carregar
e validar datasets de diferentes formatos.
"""

from typing import Union, Dict, Any, Optional
import pandas as pd
from pathlib import Path

from src.domain.entities import DatasetInfo
from src.domain.services import DataAnalysisService
from src.application.interfaces.dataset_repository import IDatasetRepository
from src.application.interfaces.file_processor import IFileProcessor
from src.utils.logger import StructuredLogger


class LoadDatasetUseCase:
    """Caso de uso para carregamento de datasets"""

    def __init__(
        self,
        dataset_repository: IDatasetRepository,
        file_processor: IFileProcessor,
        analysis_service: DataAnalysisService,
        logger: StructuredLogger
    ):
        self.dataset_repository = dataset_repository
        self.file_processor = file_processor
        self.analysis_service = analysis_service
        self.logger = logger

    def execute(
        self,
        file_path: Union[str, Path],
        dataset_name: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Executa o carregamento de um dataset

        Args:
            file_path: Caminho para o arquivo
            dataset_name: Nome opcional para o dataset
            **kwargs: Parâmetros adicionais para carregamento

        Returns:
            Dict contendo dataset, informações e status
        """
        try:
            self.logger.log_user_action(
                "load_dataset_start",
                file_path=str(file_path),
                dataset_name=dataset_name
            )

            # Validar arquivo
            if not Path(file_path).exists():
                raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")

            # Processar arquivo
            data = self.file_processor.process_file(file_path, **kwargs)

            if data is None or data.empty:
                raise ValueError("Dataset vazio ou inválido")

            # Criar informações do dataset
            file_extension = Path(file_path).suffix.lower()
            name = dataset_name or Path(file_path).stem

            dataset_info = self.analysis_service.create_dataset_info(
                data, name, file_extension.replace('.', '')
            )

            # Salvar no repositório
            dataset_id = self.dataset_repository.save_dataset(data, dataset_info)

            # Avaliar qualidade dos dados
            quality_report = self.analysis_service.assess_data_quality(data, dataset_info)

            self.logger.log_user_action(
                "load_dataset_success",
                dataset_id=dataset_id,
                rows=dataset_info.rows,
                columns=dataset_info.columns,
                quality_score=quality_report.quality_score
            )

            return {
                'success': True,
                'dataset_id': dataset_id,
                'dataset_info': dataset_info,
                'data': data,
                'quality_report': quality_report,
                'message': f"Dataset '{name}' carregado com sucesso"
            }

        except Exception as e:
            self.logger.log_error(
                f"Erro ao carregar dataset: {str(e)}",
                file_path=str(file_path),
                error_type=type(e).__name__
            )

            return {
                'success': False,
                'error': str(e),
                'message': f"Falha ao carregar dataset: {str(e)}"
            }

    def get_supported_formats(self) -> list:
        """Retorna formatos suportados"""
        return self.file_processor.get_supported_formats()

    def validate_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Valida um arquivo antes do carregamento

        Args:
            file_path: Caminho para o arquivo

        Returns:
            Dict com resultado da validação
        """
        try:
            path = Path(file_path)

            if not path.exists():
                return {
                    'valid': False,
                    'error': 'Arquivo não encontrado'
                }

            if not path.is_file():
                return {
                    'valid': False,
                    'error': 'Caminho não é um arquivo'
                }

            if path.suffix.lower() not in self.get_supported_formats():
                return {
                    'valid': False,
                    'error': f'Formato não suportado: {path.suffix}'
                }

            # Verificar tamanho (limite de 100MB)
            size_mb = path.stat().st_size / (1024 * 1024)
            if size_mb > 100:
                return {
                    'valid': False,
                    'error': f'Arquivo muito grande: {size_mb:.1f}MB (máximo 100MB)'
                }

            return {
                'valid': True,
                'size_mb': size_mb,
                'format': path.suffix.lower()
            }

        except Exception as e:
            return {
                'valid': False,
                'error': f'Erro na validação: {str(e)}'
            }