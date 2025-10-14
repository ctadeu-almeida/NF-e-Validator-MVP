# -*- coding: utf-8 -*-
"""
File Processor Interface - Interface para processamento de arquivos

Define o contrato para processamento de diferentes tipos de arquivo,
permitindo extensibilidade para novos formatos.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, Union
from pathlib import Path
import pandas as pd


class IFileProcessor(ABC):
    """Interface para processamento de arquivos"""

    @abstractmethod
    def process_file(
        self,
        file_path: Union[str, Path],
        **kwargs
    ) -> Optional[pd.DataFrame]:
        """
        Processa um arquivo e retorna DataFrame

        Args:
            file_path: Caminho para o arquivo
            **kwargs: Parâmetros específicos do formato

        Returns:
            DataFrame processado ou None em caso de erro
        """
        pass

    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """
        Retorna lista de formatos suportados

        Returns:
            Lista de extensões suportadas (ex: ['.csv', '.xlsx'])
        """
        pass

    @abstractmethod
    def validate_file_format(self, file_path: Union[str, Path]) -> bool:
        """
        Valida se o formato do arquivo é suportado

        Args:
            file_path: Caminho para o arquivo

        Returns:
            True se formato é suportado
        """
        pass

    @abstractmethod
    def get_file_info(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Obtém informações básicas do arquivo

        Args:
            file_path: Caminho para o arquivo

        Returns:
            Dict com informações do arquivo
        """
        pass

    @abstractmethod
    def detect_encoding(self, file_path: Union[str, Path]) -> str:
        """
        Detecta encoding do arquivo

        Args:
            file_path: Caminho para o arquivo

        Returns:
            Encoding detectado
        """
        pass

    @abstractmethod
    def detect_delimiter(self, file_path: Union[str, Path]) -> str:
        """
        Detecta delimitador para arquivos CSV

        Args:
            file_path: Caminho para o arquivo

        Returns:
            Delimitador detectado
        """
        pass

    @abstractmethod
    def preview_file(
        self,
        file_path: Union[str, Path],
        rows: int = 5
    ) -> Optional[pd.DataFrame]:
        """
        Gera preview do arquivo com primeiras linhas

        Args:
            file_path: Caminho para o arquivo
            rows: Número de linhas para preview

        Returns:
            DataFrame com preview ou None
        """
        pass

    @abstractmethod
    def process_multiple_files(
        self,
        file_paths: List[Union[str, Path]],
        **kwargs
    ) -> Dict[str, Optional[pd.DataFrame]]:
        """
        Processa múltiplos arquivos

        Args:
            file_paths: Lista de caminhos
            **kwargs: Parâmetros de processamento

        Returns:
            Dict com resultado de cada arquivo
        """
        pass

    @abstractmethod
    def extract_metadata(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Extrai metadados do arquivo

        Args:
            file_path: Caminho para o arquivo

        Returns:
            Dict com metadados extraídos
        """
        pass