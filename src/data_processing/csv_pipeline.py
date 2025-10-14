# -*- coding: utf-8 -*-
"""
Pipeline de Tratamento Automático de CSV

Este módulo implementa um pipeline genérico para tratamento automático de arquivos CSV,
incluindo detecção de separadores, normalização de dados e limpeza automática.
"""

import pandas as pd
import numpy as np
import re
from typing import Dict, Any, Tuple, Optional, List
from io import StringIO
import chardet


class CSVPipeline:
    """
    Pipeline completo para tratamento automático de arquivos CSV
    """

    def __init__(self):
        """Inicializa o pipeline de tratamento de CSV"""
        self.original_data = None
        self.processed_data = None
        self.metadata = {}

    def process_csv(self, file_path: str) -> pd.DataFrame:
        """
        Processa um arquivo CSV completo: detecção, limpeza e normalização

        Args:
            file_path (str): Caminho para o arquivo CSV

        Returns:
            pd.DataFrame: DataFrame limpo e normalizado
        """
        print("Iniciando pipeline de tratamento automatico...")

        # Etapa 1: Detectar encoding
        encoding = self._detect_encoding(file_path)
        print(f"   Encoding detectado: {encoding}")

        # Etapa 2: Detectar separador e ler arquivo
        separator, data = self._detect_separator_and_read(file_path, encoding)
        print(f"   Separador detectado: '{separator}'")

        # Etapa 3: Limpeza inicial
        data = self._initial_cleanup(data)
        print(f"   Limpeza inicial: {data.shape[0]} linhas, {data.shape[1]} colunas")

        # Etapa 4: Normalização de tipos
        data = self._normalize_data_types(data)
        print(f"   Tipos normalizados")

        # Etapa 5: Limpeza de valores ausentes
        data = self._handle_missing_values(data)
        print(f"   Valores ausentes tratados")

        # Etapa 6: Validação final
        data = self._final_validation(data)
        print(f"   Validacao final: {data.shape[0]} linhas, {data.shape[1]} colunas")

        # Armazenar dados processados
        self.processed_data = data
        self._generate_metadata()

        print("Pipeline concluido com sucesso!")
        return data

    def _detect_encoding(self, file_path: str) -> str:
        """
        Detecta o encoding do arquivo automaticamente

        Args:
            file_path (str): Caminho do arquivo

        Returns:
            str: Encoding detectado
        """
        try:
            with open(file_path, 'rb') as file:
                raw_data = file.read(10000)  # Lê primeiros 10KB
                result = chardet.detect(raw_data)
                encoding = result['encoding']

                # Fallback para encodings comuns se confiança for baixa
                if result['confidence'] < 0.7:
                    return 'utf-8'

                return encoding if encoding else 'utf-8'
        except:
            return 'utf-8'

    def _detect_separator_and_read(self, file_path: str, encoding: str) -> Tuple[str, pd.DataFrame]:
        """
        Detecta o separador correto e lê o arquivo com tratamento avançado para CSVs problemáticos

        Args:
            file_path (str): Caminho do arquivo
            encoding (str): Encoding do arquivo

        Returns:
            Tuple[str, pd.DataFrame]: Separador detectado e DataFrame
        """
        print("   Analisando estrutura do arquivo...")

        # Primeiro, vamos analisar o arquivo linha por linha
        with open(file_path, 'r', encoding=encoding) as file:
            lines = [line.strip() for line in file.readlines()[:20] if line.strip()]

        if not lines:
            raise ValueError("Arquivo vazio ou sem conteúdo válido")

        # Analisar contagem de vírgulas por linha
        comma_counts = [line.count(',') for line in lines]
        most_common_comma_count = max(set(comma_counts), key=comma_counts.count) if comma_counts else 0

        print(f"      • Contagem de vírgulas mais comum: {most_common_comma_count}")
        print(f"      • Colunas esperadas: {most_common_comma_count + 1}")

        # Se temos vírgulas consistentes, forçar separação por vírgula
        if most_common_comma_count > 0:
            expected_columns = most_common_comma_count + 1

            # Tentar diferentes abordagens para ler o CSV
            reading_strategies = [
                # Estratégia 1: Leitura padrão com vírgula
                {
                    'sep': ',',
                    'encoding': encoding,
                    'low_memory': False,
                    'skipinitialspace': True
                },
                # Estratégia 2: Sem quotes
                {
                    'sep': ',',
                    'encoding': encoding,
                    'low_memory': False,
                    'quoting': 3,  # QUOTE_NONE
                    'skipinitialspace': True
                },
                # Estratégia 3: Todas as quotes
                {
                    'sep': ',',
                    'encoding': encoding,
                    'low_memory': False,
                    'quoting': 1,  # QUOTE_ALL
                    'skipinitialspace': True
                },
                # Estratégia 4: Engine Python (mais robusto)
                {
                    'sep': ',',
                    'encoding': encoding,
                    'low_memory': False,
                    'engine': 'python',
                    'skipinitialspace': True,
                    'error_bad_lines': False,
                    'warn_bad_lines': False
                }
            ]

            for i, params in enumerate(reading_strategies):
                try:
                    print(f"      • Tentativa {i+1}: {list(params.keys())}")
                    data = pd.read_csv(file_path, **params)

                    print(f"      • Resultado: {data.shape[1]} colunas")

                    # Verificar se conseguimos o número esperado de colunas
                    if data.shape[1] == expected_columns:
                        print(f"      Sucesso! {data.shape[1]} colunas como esperado")
                        return ',', data
                    elif data.shape[1] > 1:  # Pelo menos alguma separação aconteceu
                        print(f"      Parcial: {data.shape[1]} colunas (esperado: {expected_columns})")
                        best_data = data

                except Exception as e:
                    print(f"      Estrategia {i+1} falhou: {str(e)[:50]}")
                    continue

            # Se chegou até aqui, usar a melhor tentativa ou forçar parsing manual
            if 'best_data' in locals() and best_data.shape[1] > 1:
                return ',', best_data
            else:
                # Parsing manual como último recurso
                print("      Forcando parsing manual...")
                return self._force_comma_parsing(file_path, encoding, expected_columns)

        # Se não há vírgulas ou padrão não detectado, tentar outros separadores
        print("      Testando outros separadores...")
        separators = [';', '\t', '|']

        for sep in separators:
            try:
                data = pd.read_csv(file_path, sep=sep, encoding=encoding, low_memory=False, nrows=100)
                if data.shape[1] > 1:
                    # Ler arquivo completo
                    full_data = pd.read_csv(file_path, sep=sep, encoding=encoding, low_memory=False)
                    print(f"      Separador '{sep}' funcionou: {full_data.shape[1]} colunas")
                    return sep, full_data
            except Exception:
                continue

        # Se tudo falhou, retornar dados como estão
        print("      Usando fallback: leitura simples")
        fallback_data = pd.read_csv(file_path, encoding=encoding, low_memory=False)
        return ',', fallback_data

    def _force_comma_parsing(self, file_path: str, encoding: str, expected_columns: int) -> Tuple[str, pd.DataFrame]:
        """
        Força o parsing por vírgulas quando métodos normais falham

        Args:
            file_path (str): Caminho do arquivo
            encoding (str): Encoding do arquivo
            expected_columns (int): Número esperado de colunas

        Returns:
            Tuple[str, pd.DataFrame]: Separador e DataFrame
        """
        print("      Executando parsing manual por virgulas...")

        with open(file_path, 'r', encoding=encoding) as file:
            lines = file.readlines()

        # Processar linha por linha
        processed_lines = []
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            # Dividir por vírgula e limpar valores
            values = [val.strip().strip('"').strip("'") for val in line.split(',')]

            # Garantir que temos o número correto de colunas
            if len(values) < expected_columns:
                # Preencher com valores vazios
                values.extend([''] * (expected_columns - len(values)))
            elif len(values) > expected_columns:
                # Truncar valores extras
                values = values[:expected_columns]

            processed_lines.append(values)

        if not processed_lines:
            raise ValueError("Nenhuma linha válida processada")

        # Criar DataFrame
        # Primeira linha como header se parecer com nomes de colunas
        first_line = processed_lines[0]
        if self._looks_like_header(first_line):
            columns = [self._clean_column_name(col) for col in first_line]
            data_lines = processed_lines[1:]
        else:
            # Gerar nomes de colunas automáticos
            columns = [f'column_{i}' for i in range(len(first_line))]
            data_lines = processed_lines

        if not data_lines:
            raise ValueError("Nenhuma linha de dados após processar header")

        # Criar DataFrame
        df = pd.DataFrame(data_lines, columns=columns)

        print(f"      Parsing manual concluido: {df.shape[0]} linhas, {df.shape[1]} colunas")
        return ',', df

    def _looks_like_header(self, values: list) -> bool:
        """
        Verifica se uma linha parece ser um cabeçalho

        Args:
            values (list): Lista de valores da linha

        Returns:
            bool: True se parece ser cabeçalho
        """
        # Se a maioria dos valores não são números, provavelmente é header
        non_numeric_count = 0
        for val in values:
            try:
                float(val.replace(',', '.'))
            except (ValueError, AttributeError):
                non_numeric_count += 1

        return non_numeric_count > len(values) * 0.7

    def _clean_column_name(self, name: str) -> str:
        """
        Limpa um nome de coluna individual

        Args:
            name (str): Nome original da coluna

        Returns:
            str: Nome limpo
        """
        if not name or name.strip() == '':
            return 'unnamed_column'

        # Limpar e normalizar
        clean_name = str(name).strip()
        clean_name = re.sub(r'[^\w\s]', '', clean_name)
        clean_name = re.sub(r'\s+', '_', clean_name)
        clean_name = clean_name.strip('_')

        return clean_name if clean_name else 'unnamed_column'

    def _initial_cleanup(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Limpeza inicial dos dados

        Args:
            data (pd.DataFrame): Dados brutos

        Returns:
            pd.DataFrame: Dados com limpeza inicial
        """
        # Fazer cópia para não modificar original
        cleaned_data = data.copy()

        # 1. Limpar nomes das colunas
        cleaned_data.columns = self._clean_column_names(cleaned_data.columns)

        # 2. Remover linhas completamente vazias
        cleaned_data = cleaned_data.dropna(how='all')

        # 3. Remover colunas completamente vazias
        cleaned_data = cleaned_data.dropna(axis=1, how='all')

        # 4. Limpar espaços em branco
        for col in cleaned_data.columns:
            if cleaned_data[col].dtype == 'object':
                cleaned_data[col] = cleaned_data[col].astype(str).str.strip()
                # Substituir strings vazias por NaN
                cleaned_data[col] = cleaned_data[col].replace(['', 'nan', 'NaN', 'NULL', 'null'], np.nan)

        return cleaned_data

    def _clean_column_names(self, columns: List[str]) -> List[str]:
        """
        Limpa e normaliza nomes das colunas

        Args:
            columns (List[str]): Lista de nomes de colunas

        Returns:
            List[str]: Nomes de colunas limpos
        """
        cleaned_columns = []

        for col in columns:
            # Converter para string e limpar
            col = str(col).strip()

            # Remover aspas
            col = col.strip('"').strip("'")

            # Remover caracteres especiais problemáticos
            col = re.sub(r'[^\w\s]', '', col)

            # Substituir espaços por underscore
            col = re.sub(r'\s+', '_', col)

            # Remover underscores consecutivos
            col = re.sub(r'_+', '_', col)

            # Remover underscore no início/fim
            col = col.strip('_')

            # Se ficou vazio, dar um nome genérico
            if not col:
                col = f'column_{len(cleaned_columns)}'

            # Evitar nomes duplicados
            original_col = col
            counter = 1
            while col in cleaned_columns:
                col = f"{original_col}_{counter}"
                counter += 1

            cleaned_columns.append(col)

        return cleaned_columns

    def _normalize_data_types(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Normaliza tipos de dados automaticamente

        Args:
            data (pd.DataFrame): Dados com tipos brutos

        Returns:
            pd.DataFrame: Dados com tipos normalizados
        """
        normalized_data = data.copy()

        for col in normalized_data.columns:
            # Tentar converter para numérico
            if normalized_data[col].dtype == 'object':
                # Limpar dados antes da conversão
                cleaned_series = normalized_data[col].astype(str)

                # Remover aspas
                cleaned_series = cleaned_series.str.replace('"', '').str.replace("'", "")

                # Substituir vírgula por ponto para decimais
                cleaned_series = cleaned_series.str.replace(',', '.')

                # Remover espaços
                cleaned_series = cleaned_series.str.strip()

                # Tentar conversão numérica
                try:
                    numeric_series = pd.to_numeric(cleaned_series, errors='coerce')

                    # Se mais de 70% dos valores foram convertidos com sucesso, usar versão numérica
                    conversion_rate = numeric_series.notna().sum() / len(numeric_series)
                    if conversion_rate > 0.7:
                        normalized_data[col] = numeric_series
                        continue
                except:
                    pass

                # Tentar conversão para datetime
                try:
                    if self._looks_like_datetime(cleaned_series):
                        datetime_series = pd.to_datetime(cleaned_series, errors='coerce', infer_datetime_format=True)
                        conversion_rate = datetime_series.notna().sum() / len(datetime_series)
                        if conversion_rate > 0.7:
                            normalized_data[col] = datetime_series
                            continue
                except:
                    pass

                # Se não converteu, manter como string limpa
                normalized_data[col] = cleaned_series.replace('nan', np.nan)

        return normalized_data

    def _looks_like_datetime(self, series: pd.Series) -> bool:
        """
        Verifica se uma série parece conter datas

        Args:
            series (pd.Series): Série para verificar

        Returns:
            bool: True se parece com datetime
        """
        # Pegar uma amostra para testar
        sample = series.dropna().head(10)

        datetime_patterns = [
            r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
            r'\d{2}/\d{2}/\d{4}',  # DD/MM/YYYY ou MM/DD/YYYY
            r'\d{2}-\d{2}-\d{4}',  # DD-MM-YYYY
            r'\d{4}/\d{2}/\d{2}',  # YYYY/MM/DD
        ]

        for value in sample:
            value_str = str(value)
            for pattern in datetime_patterns:
                if re.search(pattern, value_str):
                    return True

        return False

    def _handle_missing_values(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Trata valores ausentes de forma inteligente

        Args:
            data (pd.DataFrame): Dados com valores ausentes

        Returns:
            pd.DataFrame: Dados com valores ausentes tratados
        """
        treated_data = data.copy()

        for col in treated_data.columns:
            missing_percentage = treated_data[col].isnull().sum() / len(treated_data)

            # Se mais de 90% ausente, considerar remover coluna
            if missing_percentage > 0.9:
                print(f"      Coluna '{col}' tem {missing_percentage:.1%} valores ausentes")
                continue

            # Tratamento baseado no tipo de dados
            if treated_data[col].dtype in ['int64', 'float64']:
                # Para numéricos: usar mediana se distribuição não é muito skewed
                if missing_percentage > 0 and missing_percentage < 0.5:
                    skewness = abs(treated_data[col].skew())
                    if skewness < 2:  # Distribuição relativamente normal
                        fill_value = treated_data[col].median()
                    else:  # Distribuição muito skewed
                        fill_value = treated_data[col].mode().iloc[0] if not treated_data[col].mode().empty else 0

                    treated_data[col] = treated_data[col].fillna(fill_value)

            elif treated_data[col].dtype == 'object':
                # Para categóricos: usar moda ou 'Unknown'
                if missing_percentage > 0 and missing_percentage < 0.5:
                    mode_value = treated_data[col].mode()
                    fill_value = mode_value.iloc[0] if not mode_value.empty else 'Unknown'
                    treated_data[col] = treated_data[col].fillna(fill_value)

            elif pd.api.types.is_datetime64_any_dtype(treated_data[col]):
                # Para datas: não preencher automaticamente
                pass

        return treated_data

    def _final_validation(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Validação final e ajustes

        Args:
            data (pd.DataFrame): Dados tratados

        Returns:
            pd.DataFrame: Dados validados
        """
        validated_data = data.copy()

        # Remover duplicatas exatas
        original_rows = len(validated_data)
        validated_data = validated_data.drop_duplicates()
        removed_duplicates = original_rows - len(validated_data)

        if removed_duplicates > 0:
            print(f"      Removidas {removed_duplicates} linhas duplicadas")

        # Resetar index
        validated_data = validated_data.reset_index(drop=True)

        return validated_data

    def _generate_metadata(self):
        """Gera metadados sobre o processamento"""
        if self.processed_data is None:
            return

        self.metadata = {
            'shape': self.processed_data.shape,
            'columns': list(self.processed_data.columns),
            'dtypes': self.processed_data.dtypes.to_dict(),
            'missing_values': self.processed_data.isnull().sum().to_dict(),
            'numeric_columns': list(self.processed_data.select_dtypes(include=[np.number]).columns),
            'categorical_columns': list(self.processed_data.select_dtypes(include=['object']).columns),
            'datetime_columns': list(self.processed_data.select_dtypes(include=['datetime64']).columns),
            'memory_usage': self.processed_data.memory_usage(deep=True).sum(),
        }

    def get_summary(self) -> Dict[str, Any]:
        """
        Retorna resumo do processamento

        Returns:
            Dict[str, Any]: Resumo dos dados processados
        """
        if not self.metadata:
            return {}

        summary = {
            'total_rows': self.metadata['shape'][0],
            'total_columns': self.metadata['shape'][1],
            'numeric_columns_count': len(self.metadata['numeric_columns']),
            'categorical_columns_count': len(self.metadata['categorical_columns']),
            'datetime_columns_count': len(self.metadata['datetime_columns']),
            'total_missing_values': sum(self.metadata['missing_values'].values()),
            'memory_usage_mb': round(self.metadata['memory_usage'] / (1024 * 1024), 2),
            'columns_by_type': {
                'numeric': self.metadata['numeric_columns'],
                'categorical': self.metadata['categorical_columns'],
                'datetime': self.metadata['datetime_columns']
            }
        }

        return summary


def process_csv_file(file_path: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Função utilitária para processar um arquivo CSV

    Args:
        file_path (str): Caminho para o arquivo CSV

    Returns:
        Tuple[pd.DataFrame, Dict[str, Any]]: DataFrame tratado e resumo
    """
    pipeline = CSVPipeline()
    df_tratado = pipeline.process_csv(file_path)
    summary = pipeline.get_summary()

    return df_tratado, summary


# Exemplo de uso
if __name__ == "__main__":
    # Exemplo de como usar
    # df_tratado, resumo = process_csv_file("caminho/para/arquivo.csv")
    # print(f"Dados processados: {df_tratado.shape}")
    # print(f"Resumo: {resumo}")
    pass