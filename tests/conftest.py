# -*- coding: utf-8 -*-
"""
Test Configuration - Fixtures e configurações para testes

Este módulo contém fixtures compartilhadas e configurações
para todos os testes da aplicação.
"""

import pytest
import pandas as pd
import numpy as np
from typing import Dict, Any
from pathlib import Path
import tempfile
import os


@pytest.fixture
def sample_numeric_data():
    """Dataset com dados numéricos para testes"""
    np.random.seed(42)
    return pd.DataFrame({
        'id': range(1, 101),
        'value_1': np.random.normal(100, 15, 100),
        'value_2': np.random.normal(50, 10, 100),
        'outlier_col': np.concatenate([
            np.random.normal(20, 5, 95),
            [100, 120, 150, 200, 300]  # Outliers intencionais
        ])
    })


@pytest.fixture
def sample_mixed_data():
    """Dataset com dados mistos para testes"""
    np.random.seed(42)
    categories = ['A', 'B', 'C', 'D']
    return pd.DataFrame({
        'id': range(1, 51),
        'numeric': np.random.normal(100, 20, 50),
        'category': np.random.choice(categories, 50),
        'boolean': np.random.choice([True, False], 50),
        'text': [f'item_{i}' for i in range(50)]
    })


@pytest.fixture
def sample_data_with_nulls():
    """Dataset com valores nulos para testes"""
    np.random.seed(42)
    data = pd.DataFrame({
        'complete': range(20),
        'with_nulls': [i if i % 3 != 0 else None for i in range(20)],
        'mostly_nulls': [i if i < 5 else None for i in range(20)]
    })
    return data


@pytest.fixture
def sample_correlation_data():
    """Dataset com correlações conhecidas para testes"""
    np.random.seed(42)
    x = np.random.normal(0, 1, 100)
    return pd.DataFrame({
        'x': x,
        'y_strong_pos': x * 0.9 + np.random.normal(0, 0.1, 100),  # Correlação forte positiva
        'y_strong_neg': -x * 0.8 + np.random.normal(0, 0.1, 100),  # Correlação forte negativa
        'y_weak': x * 0.2 + np.random.normal(0, 1, 100),  # Correlação fraca
        'y_none': np.random.normal(0, 1, 100)  # Sem correlação
    })


@pytest.fixture
def sample_csv_file(tmp_path, sample_numeric_data):
    """Arquivo CSV temporário para testes"""
    csv_path = tmp_path / "test_data.csv"
    sample_numeric_data.to_csv(csv_path, index=False)
    return str(csv_path)


@pytest.fixture
def sample_excel_file(tmp_path, sample_mixed_data):
    """Arquivo Excel temporário para testes"""
    excel_path = tmp_path / "test_data.xlsx"
    sample_mixed_data.to_excel(excel_path, index=False)
    return str(excel_path)


@pytest.fixture
def mock_api_key():
    """API key mock para testes"""
    return "AIzaSyDummy_Test_Key_123456789012345678901234"


@pytest.fixture
def test_config():
    """Configurações de teste"""
    return {
        'gemini': {
            'model': 'gemini-2.5-flash',
            'temperature': 0.1,
            'max_output_tokens': 1024,
            'max_retries': 1,
            'request_timeout': 10
        },
        'data': {
            'charts_dir': 'test_charts',
            'reports_dir': 'test_reports',
            'max_csv_size_mb': 10
        },
        'logging': {
            'level': 'DEBUG'
        }
    }


@pytest.fixture
def temp_directory():
    """Diretório temporário para testes"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture(autouse=True)
def cleanup_test_files():
    """Limpeza automática após cada teste"""
    yield
    # Cleanup após teste
    test_dirs = ['test_charts', 'test_reports', 'test_logs']
    for dir_name in test_dirs:
        if Path(dir_name).exists():
            import shutil
            shutil.rmtree(dir_name)


@pytest.fixture
def mock_visualization_data():
    """Dados para teste de visualizações"""
    return {
        'title': 'Test Chart',
        'chart_type': 'histogram',
        'file_path': 'test_charts/test_chart.png',
        'data_columns': ['value_1', 'value_2'],
        'metadata': {'bins': 20, 'color': 'blue'}
    }


class MockAgent:
    """Mock do agente para testes"""

    def __init__(self, api_available=True):
        self.api_available = api_available
        self.data = None
        self.filename = None

    def load_data(self, file_path):
        """Mock do carregamento de dados"""
        return True

    def ask_question(self, question):
        """Mock de pergunta ao agente"""
        return f"Mock response for: {question}"


@pytest.fixture
def mock_agent():
    """Agente mock para testes"""
    return MockAgent()


@pytest.fixture
def mock_failed_agent():
    """Agente mock que falha para testes"""
    return MockAgent(api_available=False)