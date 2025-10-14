# -*- coding: utf-8 -*-
"""
Domain Services - Serviços de domínio da aplicação

Este módulo contém a lógica de negócio para análise exploratória de dados,
separada da infraestrutura e interface.
"""

from typing import List, Dict, Tuple, Optional, Any
import pandas as pd
import numpy as np
from scipy import stats
from .entities import (
    DatasetInfo, AnalysisResult, OutlierInfo, CorrelationAnalysis,
    DataQualityReport, AgentQuery
)


class DataAnalysisService:
    """Serviço principal para análise de dados"""

    def __init__(self):
        self.outlier_methods = {
            'iqr': self._detect_outliers_iqr,
            'zscore': self._detect_outliers_zscore,
            'modified_zscore': self._detect_outliers_modified_zscore
        }

    def create_dataset_info(self, data: pd.DataFrame, name: str,
                           source: str = "csv") -> DatasetInfo:
        """Criar informações sobre o dataset"""
        return DatasetInfo(
            name=name,
            size_bytes=data.memory_usage(deep=True).sum(),
            rows=len(data),
            columns=len(data.columns),
            column_types={col: str(dtype) for col, dtype in data.dtypes.items()},
            missing_values=data.isnull().sum().to_dict(),
            source=source
        )

    def analyze_descriptive_statistics(self, data: pd.DataFrame) -> AnalysisResult:
        """Realizar análise estatística descritiva"""
        result = AnalysisResult(
            analysis_type="descriptive_statistics",
            summary="Análise estatística descritiva dos dados"
        )

        numeric_cols = data.select_dtypes(include=[np.number]).columns

        if len(numeric_cols) > 0:
            desc_stats = data[numeric_cols].describe()
            result.add_insight(
                "descriptive_stats",
                desc_stats.to_dict(),
                "Estatísticas descritivas das colunas numéricas"
            )

            # Análise de assimetria e curtose
            skewness = data[numeric_cols].skew()
            kurtosis = data[numeric_cols].kurtosis()

            result.add_insight(
                "skewness",
                skewness.to_dict(),
                "Medida de assimetria das distribuições"
            )

            result.add_insight(
                "kurtosis",
                kurtosis.to_dict(),
                "Medida de curtose das distribuições"
            )

        # Análise de dados categóricos
        categorical_cols = data.select_dtypes(include=['object', 'category']).columns
        if len(categorical_cols) > 0:
            cat_analysis = {}
            for col in categorical_cols:
                value_counts = data[col].value_counts()
                cat_analysis[col] = {
                    "unique_values": data[col].nunique(),
                    "top_values": value_counts.head(5).to_dict(),
                    "mode": value_counts.index[0] if len(value_counts) > 0 else None
                }

            result.add_insight(
                "categorical_analysis",
                cat_analysis,
                "Análise das variáveis categóricas"
            )

        return result

    def detect_outliers(self, data: pd.DataFrame, method: str = 'iqr',
                       columns: Optional[List[str]] = None) -> Dict[str, OutlierInfo]:
        """Detectar outliers nos dados"""
        if columns is None:
            columns = data.select_dtypes(include=[np.number]).columns.tolist()

        outliers = {}

        for col in columns:
            if col in data.columns:
                if method in self.outlier_methods:
                    outlier_info = self.outlier_methods[method](data, col)
                    outliers[col] = outlier_info

        return outliers

    def _detect_outliers_iqr(self, data: pd.DataFrame, column: str) -> OutlierInfo:
        """Detectar outliers usando método IQR"""
        series = data[column].dropna()
        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)
        IQR = Q3 - Q1

        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR

        outlier_mask = (series < lower_bound) | (series > upper_bound)
        outlier_indices = series[outlier_mask].index.tolist()

        return OutlierInfo(
            column=column,
            method="IQR",
            outlier_indices=outlier_indices,
            threshold_lower=lower_bound,
            threshold_upper=upper_bound,
            percentage=(len(outlier_indices) / len(series)) * 100
        )

    def _detect_outliers_zscore(self, data: pd.DataFrame, column: str) -> OutlierInfo:
        """Detectar outliers usando Z-score"""
        series = data[column].dropna()
        z_scores = np.abs(stats.zscore(series))
        threshold = 3

        outlier_mask = z_scores > threshold
        outlier_indices = series[outlier_mask].index.tolist()

        return OutlierInfo(
            column=column,
            method="Z-Score",
            outlier_indices=outlier_indices,
            threshold_lower=-threshold,
            threshold_upper=threshold,
            percentage=(len(outlier_indices) / len(series)) * 100
        )

    def _detect_outliers_modified_zscore(self, data: pd.DataFrame, column: str) -> OutlierInfo:
        """Detectar outliers usando Z-score modificado (MAD)"""
        series = data[column].dropna()
        median = np.median(series)
        mad = np.median(np.abs(series - median))
        modified_z_scores = 0.6745 * (series - median) / mad
        threshold = 3.5

        outlier_mask = np.abs(modified_z_scores) > threshold
        outlier_indices = series[outlier_mask].index.tolist()

        return OutlierInfo(
            column=column,
            method="Modified Z-Score",
            outlier_indices=outlier_indices,
            threshold_lower=-threshold,
            threshold_upper=threshold,
            percentage=(len(outlier_indices) / len(series)) * 100
        )

    def analyze_correlations(self, data: pd.DataFrame,
                           threshold: float = 0.5) -> CorrelationAnalysis:
        """Analisar correlações entre variáveis numéricas"""
        numeric_data = data.select_dtypes(include=[np.number])

        if numeric_data.shape[1] < 2:
            return CorrelationAnalysis(threshold=threshold)

        corr_matrix = numeric_data.corr()

        # Converter para dicionário
        corr_dict = {}
        for col1 in corr_matrix.columns:
            corr_dict[col1] = {}
            for col2 in corr_matrix.columns:
                corr_dict[col1][col2] = float(corr_matrix.loc[col1, col2])

        analysis = CorrelationAnalysis(
            correlation_matrix=corr_dict,
            threshold=threshold
        )

        analysis.strong_correlations = analysis.get_strong_correlations()
        return analysis

    def assess_data_quality(self, data: pd.DataFrame,
                           dataset_info: DatasetInfo) -> DataQualityReport:
        """Avaliar qualidade dos dados"""
        report = DataQualityReport(dataset_info=dataset_info)

        # Calcular percentual de dados faltantes
        total_cells = data.shape[0] * data.shape[1]
        missing_cells = data.isnull().sum().sum()
        report.missing_data_percentage = (missing_cells / total_cells) * 100

        # Detectar duplicatas
        report.duplicate_rows = data.duplicated().sum()
        report.duplicate_percentage = (report.duplicate_rows / len(data)) * 100

        # Problemas de tipos de dados
        for col in data.columns:
            # Verificar se colunas numéricas têm strings
            if data[col].dtype == 'object':
                try:
                    pd.to_numeric(data[col], errors='raise')
                except:
                    # Verificar se parece numérico mas não é
                    numeric_like = data[col].str.replace(r'[,.]', '', regex=True).str.isnumeric()
                    if numeric_like.sum() > len(data) * 0.8:  # 80% parecem numéricos
                        report.data_types_issues.append(
                            f"Coluna '{col}' parece numérica mas está como texto"
                        )

        # Análise de outliers
        outliers = self.detect_outliers(data)
        report.outliers_summary = outliers

        # Gerar recomendações
        report.recommendations = self._generate_quality_recommendations(report)

        # Calcular score de qualidade
        report.calculate_quality_score()

        return report

    def _generate_quality_recommendations(self, report: DataQualityReport) -> List[str]:
        """Gerar recomendações baseadas na qualidade dos dados"""
        recommendations = []

        if report.missing_data_percentage > 10:
            recommendations.append(
                "Considere tratar dados faltantes (>10% dos dados estão ausentes)"
            )

        if report.duplicate_percentage > 5:
            recommendations.append(
                "Remova linhas duplicadas que podem afetar a análise"
            )

        if report.data_types_issues:
            recommendations.append(
                "Corrija tipos de dados para melhorar a análise"
            )

        # Recomendações para outliers
        high_outlier_cols = [
            col for col, info in report.outliers_summary.items()
            if info.percentage > 5
        ]
        if high_outlier_cols:
            recommendations.append(
                f"Investigue outliers nas colunas: {', '.join(high_outlier_cols)}"
            )

        if not recommendations:
            recommendations.append("Dados parecem estar em boa qualidade!")

        return recommendations


class QueryAnalysisService:
    """Serviço para análise de queries do usuário"""

    def __init__(self):
        self.column_keywords = {
            'time': ['tempo', 'data', 'time', 'date', 'timestamp'],
            'amount': ['valor', 'quantidade', 'amount', 'price', 'preço'],
            'category': ['categoria', 'tipo', 'class', 'grupo']
        }

    def analyze_query(self, query_text: str, data: pd.DataFrame) -> AgentQuery:
        """Analisar query do usuário"""
        query = AgentQuery(text=query_text)

        # Classificar intenção
        query.classify_intent()

        # Identificar colunas mencionadas
        query.required_columns = self._extract_mentioned_columns(query_text, data)

        # Determinar tipo de análise necessária
        query.analysis_type = self._determine_analysis_type(query)

        return query

    def _extract_mentioned_columns(self, text: str, data: pd.DataFrame) -> List[str]:
        """Extrair colunas mencionadas no texto"""
        text_lower = text.lower()
        mentioned_columns = []

        # Procurar por nomes de colunas exatos
        for col in data.columns:
            if col.lower() in text_lower:
                mentioned_columns.append(col)

        # Procurar por palavras-chave que mapeiam para colunas
        for category, keywords in self.column_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    # Encontrar colunas que podem corresponder a esta categoria
                    matching_cols = [
                        col for col in data.columns
                        if any(kw in col.lower() for kw in keywords)
                    ]
                    mentioned_columns.extend(matching_cols)

        return list(set(mentioned_columns))  # Remover duplicatas

    def _determine_analysis_type(self, query: AgentQuery) -> str:
        """Determinar tipo de análise baseado na query"""
        intent_to_analysis = {
            'statistical': 'descriptive_statistics',
            'visualization': 'visualization',
            'outliers': 'outlier_detection',
            'exploration': 'exploratory_analysis',
            'quality': 'data_quality',
            'comparison': 'comparative_analysis'
        }

        return intent_to_analysis.get(query.intent, 'general_analysis')