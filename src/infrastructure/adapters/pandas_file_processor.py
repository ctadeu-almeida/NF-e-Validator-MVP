# -*- coding: utf-8 -*-
"""
Pandas File Processor - Implementação do processador de arquivos com Pandas

Implementa a interface IFileProcessor usando Pandas para processar
diferentes formatos de arquivo (CSV, Excel, JSON, etc.).
"""

import chardet
import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
import zipfile
import io

from src.application.interfaces.file_processor import IFileProcessor


class PandasFileProcessor(IFileProcessor):
    """Processador de arquivos usando Pandas"""

    def __init__(self):
        self.supported_formats = ['.csv', '.xlsx', '.xls', '.json', '.parquet', '.zip']

    def process_file(
        self,
        file_path: Union[str, Path],
        **kwargs
    ) -> Optional[pd.DataFrame]:
        """Processa um arquivo e retorna DataFrame"""
        try:
            path = Path(file_path)
            extension = path.suffix.lower()

            if extension == '.csv':
                return self._process_csv(path, **kwargs)
            elif extension in ['.xlsx', '.xls']:
                return self._process_excel(path, **kwargs)
            elif extension == '.json':
                return self._process_json(path, **kwargs)
            elif extension == '.parquet':
                return self._process_parquet(path, **kwargs)
            elif extension == '.zip':
                return self._process_zip(path, **kwargs)
            else:
                raise ValueError(f"Formato não suportado: {extension}")

        except Exception as e:
            print(f"Erro ao processar arquivo {file_path}: {str(e)}")
            return None

    def _process_csv(self, file_path: Path, **kwargs) -> pd.DataFrame:
        """Processa arquivo CSV"""
        encoding = kwargs.get('encoding') or self.detect_encoding(file_path)
        delimiter = kwargs.get('delimiter') or self.detect_delimiter(file_path)

        return pd.read_csv(
            file_path,
            encoding=encoding,
            delimiter=delimiter,
            **{k: v for k, v in kwargs.items() if k not in ['encoding', 'delimiter']}
        )

    def _process_excel(self, file_path: Path, **kwargs) -> pd.DataFrame:
        """Processa arquivo Excel"""
        sheet_name = kwargs.get('sheet_name', 0)
        return pd.read_excel(file_path, sheet_name=sheet_name, **kwargs)

    def _process_json(self, file_path: Path, **kwargs) -> pd.DataFrame:
        """Processa arquivo JSON"""
        return pd.read_json(file_path, **kwargs)

    def _process_parquet(self, file_path: Path, **kwargs) -> pd.DataFrame:
        """Processa arquivo Parquet"""
        return pd.read_parquet(file_path, **kwargs)

    def _process_zip(self, file_path: Path, **kwargs) -> pd.DataFrame:
        """Processa arquivo ZIP contendo CSVs"""
        dataframes = []

        with zipfile.ZipFile(file_path, 'r') as zip_file:
            csv_files = [f for f in zip_file.namelist() if f.endswith('.csv')]

            if not csv_files:
                raise ValueError("Nenhum arquivo CSV encontrado no ZIP")

            for csv_file in csv_files:
                with zip_file.open(csv_file) as file:
                    content = file.read()
                    encoding = chardet.detect(content)['encoding'] or 'utf-8'

                    df = pd.read_csv(
                        io.StringIO(content.decode(encoding)),
                        **kwargs
                    )
                    df['source_file'] = csv_file
                    dataframes.append(df)

        if len(dataframes) == 1:
            return dataframes[0]
        else:
            return pd.concat(dataframes, ignore_index=True)

    def get_supported_formats(self) -> List[str]:
        """Retorna formatos suportados"""
        return self.supported_formats.copy()

    def validate_file_format(self, file_path: Union[str, Path]) -> bool:
        """Valida se o formato é suportado"""
        extension = Path(file_path).suffix.lower()
        return extension in self.supported_formats

    def get_file_info(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Obtém informações básicas do arquivo"""
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")

        stat = path.stat()
        return {
            'name': path.name,
            'size_bytes': stat.st_size,
            'size_mb': round(stat.st_size / (1024 * 1024), 2),
            'extension': path.suffix.lower(),
            'created': stat.st_ctime,
            'modified': stat.st_mtime
        }

    def detect_encoding(self, file_path: Union[str, Path]) -> str:
        """Detecta encoding do arquivo"""
        try:
            with open(file_path, 'rb') as file:
                sample = file.read(10000)  # Lê amostra de 10KB
                result = chardet.detect(sample)
                return result['encoding'] or 'utf-8'
        except Exception:
            return 'utf-8'

    def detect_delimiter(self, file_path: Union[str, Path]) -> str:
        """Detecta delimitador para CSV"""
        try:
            with open(file_path, 'r', encoding=self.detect_encoding(file_path)) as file:
                sample = file.read(1024)

            # Testa delimitadores comuns
            delimiters = [',', ';', '\t', '|']
            delimiter_counts = {}

            for delimiter in delimiters:
                count = sample.count(delimiter)
                if count > 0:
                    delimiter_counts[delimiter] = count

            if delimiter_counts:
                return max(delimiter_counts, key=delimiter_counts.get)
            else:
                return ','  # Padrão

        except Exception:
            return ','

    def preview_file(
        self,
        file_path: Union[str, Path],
        rows: int = 5
    ) -> Optional[pd.DataFrame]:
        """Gera preview do arquivo"""
        try:
            path = Path(file_path)
            extension = path.suffix.lower()

            if extension == '.csv':
                encoding = self.detect_encoding(path)
                delimiter = self.detect_delimiter(path)
                return pd.read_csv(path, encoding=encoding, delimiter=delimiter, nrows=rows)
            elif extension in ['.xlsx', '.xls']:
                return pd.read_excel(path, nrows=rows)
            elif extension == '.json':
                df = pd.read_json(path)
                return df.head(rows)
            else:
                return self.process_file(path).head(rows) if self.process_file(path) is not None else None

        except Exception as e:
            print(f"Erro ao gerar preview: {str(e)}")
            return None

    def process_multiple_files(
        self,
        file_paths: List[Union[str, Path]],
        **kwargs
    ) -> Dict[str, Optional[pd.DataFrame]]:
        """Processa múltiplos arquivos"""
        results = {}

        for file_path in file_paths:
            path = Path(file_path)
            results[str(path)] = self.process_file(path, **kwargs)

        return results

    def extract_metadata(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Extrai metadados do arquivo"""
        file_info = self.get_file_info(file_path)

        metadata = {
            'file_info': file_info,
            'format_specific': {}
        }

        try:
            extension = Path(file_path).suffix.lower()

            if extension == '.csv':
                metadata['format_specific'] = {
                    'encoding': self.detect_encoding(file_path),
                    'delimiter': self.detect_delimiter(file_path)
                }
            elif extension in ['.xlsx', '.xls']:
                # Para Excel, podemos detectar sheets
                try:
                    excel_file = pd.ExcelFile(file_path)
                    metadata['format_specific'] = {
                        'sheet_names': excel_file.sheet_names,
                        'total_sheets': len(excel_file.sheet_names)
                    }
                except Exception:
                    pass

        except Exception as e:
            metadata['extraction_error'] = str(e)

        return metadata