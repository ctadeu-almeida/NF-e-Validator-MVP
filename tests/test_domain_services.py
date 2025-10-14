# -*- coding: utf-8 -*-
"""
Tests for Domain Services - Testes dos serviços de domínio

Este módulo testa a lógica de negócio principal da aplicação,
incluindo análise de dados e processamento de queries.
"""

import pytest
import pandas as pd
import numpy as np
from src.domain.services import DataAnalysisService, QueryAnalysisService
from src.domain.entities import DatasetInfo, AnalysisResult, OutlierInfo


class TestDataAnalysisService:
    """Testes para DataAnalysisService"""

    def setup_method(self):
        """Setup para cada teste"""
        self.service = DataAnalysisService()

    def test_create_dataset_info(self, sample_numeric_data):
        """Teste criação de informações do dataset"""
        info = self.service.create_dataset_info(
            sample_numeric_data,
            "test_dataset",
            "csv"
        )

        assert isinstance(info, DatasetInfo)
        assert info.name == "test_dataset"
        assert info.rows == 100
        assert info.columns == 4
        assert info.source == "csv"
        assert 'id' in info.column_types
        assert info.size_bytes > 0

    def test_descriptive_statistics(self, sample_numeric_data):
        """Teste análise estatística descritiva"""
        result = self.service.analyze_descriptive_statistics(sample_numeric_data)

        assert isinstance(result, AnalysisResult)
        assert result.analysis_type == "descriptive_statistics"
        assert "descriptive_stats" in result.result_data
        assert "skewness" in result.result_data
        assert "kurtosis" in result.result_data

        # Verificar se as estatísticas estão corretas
        desc_stats = result.result_data["descriptive_stats"]["value"]
        assert "value_1" in desc_stats
        assert "count" in desc_stats["value_1"]
        assert desc_stats["value_1"]["count"] == 100

    def test_descriptive_statistics_with_categorical(self, sample_mixed_data):
        """Teste estatísticas com dados categóricos"""
        result = self.service.analyze_descriptive_statistics(sample_mixed_data)

        assert "categorical_analysis" in result.result_data
        cat_analysis = result.result_data["categorical_analysis"]["value"]
        assert "category" in cat_analysis
        assert cat_analysis["category"]["unique_values"] <= 4

    def test_outlier_detection_iqr(self, sample_numeric_data):
        """Teste detecção de outliers com método IQR"""
        outliers = self.service.detect_outliers(
            sample_numeric_data,
            method='iqr',
            columns=['outlier_col']
        )

        assert 'outlier_col' in outliers
        outlier_info = outliers['outlier_col']
        assert isinstance(outlier_info, OutlierInfo)
        assert outlier_info.method == "IQR"
        assert outlier_info.count > 0  # Deve detectar os outliers intencionais
        assert len(outlier_info.outlier_indices) == outlier_info.count

    def test_outlier_detection_zscore(self, sample_numeric_data):
        """Teste detecção de outliers com Z-score"""
        outliers = self.service.detect_outliers(
            sample_numeric_data,
            method='zscore',
            columns=['outlier_col']
        )

        assert 'outlier_col' in outliers
        outlier_info = outliers['outlier_col']
        assert outlier_info.method == "Z-Score"

    def test_outlier_detection_modified_zscore(self, sample_numeric_data):
        """Teste detecção de outliers com Z-score modificado"""
        outliers = self.service.detect_outliers(
            sample_numeric_data,
            method='modified_zscore',
            columns=['outlier_col']
        )

        assert 'outlier_col' in outliers
        outlier_info = outliers['outlier_col']
        assert outlier_info.method == "Modified Z-Score"

    def test_correlation_analysis(self, sample_correlation_data):
        """Teste análise de correlação"""
        analysis = self.service.analyze_correlations(
            sample_correlation_data,
            threshold=0.5
        )

        assert analysis.threshold == 0.5
        assert len(analysis.correlation_matrix) > 0

        # Verificar correlações fortes
        strong_corrs = analysis.get_strong_correlations()
        assert len(strong_corrs) > 0

        # Deve encontrar correlação forte entre x e y_strong_pos
        found_strong_pos = any(
            ('x' in pair[:2] and 'y_strong_pos' in pair[:2] and abs(pair[2]) > 0.5)
            for pair in strong_corrs
        )
        assert found_strong_pos

    def test_correlation_analysis_insufficient_data(self, sample_mixed_data):
        """Teste correlação com dados insuficientes"""
        # Usar apenas colunas não-numéricas
        cat_data = sample_mixed_data[['category', 'text']]
        analysis = self.service.analyze_correlations(cat_data)

        assert len(analysis.correlation_matrix) == 0
        assert len(analysis.strong_correlations) == 0

    def test_data_quality_assessment(self, sample_data_with_nulls):
        """Teste avaliação de qualidade dos dados"""
        dataset_info = self.service.create_dataset_info(
            sample_data_with_nulls,
            "test_nulls"
        )

        report = self.service.assess_data_quality(sample_data_with_nulls, dataset_info)

        assert report.missing_data_percentage > 0
        assert report.quality_score <= 100
        assert len(report.recommendations) > 0

        # Verificar se detectou problemas de dados faltantes
        assert any("faltantes" in rec for rec in report.recommendations)

    def test_data_quality_perfect_data(self, sample_numeric_data):
        """Teste qualidade com dados perfeitos"""
        dataset_info = self.service.create_dataset_info(
            sample_numeric_data,
            "perfect_data"
        )

        report = self.service.assess_data_quality(sample_numeric_data, dataset_info)

        assert report.missing_data_percentage == 0
        assert report.duplicate_percentage == 0
        assert report.quality_score > 80  # Deve ter boa qualidade


class TestQueryAnalysisService:
    """Testes para QueryAnalysisService"""

    def setup_method(self):
        """Setup para cada teste"""
        self.service = QueryAnalysisService()

    def test_query_intent_classification(self, sample_numeric_data):
        """Teste classificação de intenção de queries"""
        test_cases = [
            ("Mostre a média dos dados", "statistical"),
            ("Crie um gráfico de distribuição", "visualization"),
            ("Existem outliers nos dados?", "outliers"),
            ("Compare as colunas A e B", "comparison"),
            ("Qual a qualidade dos dados?", "quality")
        ]

        for query_text, expected_intent in test_cases:
            query = self.service.analyze_query(query_text, sample_numeric_data)
            assert query.intent == expected_intent

    def test_column_extraction(self, sample_mixed_data):
        """Teste extração de colunas mencionadas"""
        query_text = "Analise a coluna numeric e compare com category"
        query = self.service.analyze_query(query_text, sample_mixed_data)

        assert 'numeric' in query.required_columns
        assert 'category' in query.required_columns

    def test_analysis_type_determination(self, sample_numeric_data):
        """Teste determinação do tipo de análise"""
        query_text = "Mostre estatísticas descritivas"
        query = self.service.analyze_query(query_text, sample_numeric_data)

        query.classify_intent()
        analysis_type = self.service._determine_analysis_type(query)

        assert analysis_type in [
            'descriptive_statistics',
            'visualization',
            'outlier_detection',
            'exploratory_analysis',
            'data_quality',
            'comparative_analysis',
            'general_analysis'
        ]

    def test_empty_query(self, sample_numeric_data):
        """Teste com query vazia"""
        query = self.service.analyze_query("", sample_numeric_data)

        assert query.text == ""
        assert query.intent == "general"
        assert len(query.required_columns) == 0

    def test_query_with_keywords(self, sample_mixed_data):
        """Teste com palavras-chave específicas"""
        # Adicionar coluna que deve ser detectada por palavra-chave
        test_data = sample_mixed_data.copy()
        test_data['amount'] = range(len(test_data))

        query_text = "Analise os valores de amount"
        query = self.service.analyze_query(query_text, test_data)

        # Deve detectar 'amount' por palavra-chave
        assert len(query.required_columns) > 0