# -*- coding: utf-8 -*-
"""
Domain Entities - Entidades de negócio da aplicação

Este módulo define as entidades centrais do domínio de análise exploratória
de dados, separando a lógica de negócio da infraestrutura.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Literal
from pathlib import Path
import pandas as pd
from datetime import datetime
import uuid


@dataclass
class DatasetInfo:
    """Informações sobre um dataset"""

    name: str
    file_path: Optional[str] = None
    size_bytes: int = 0
    rows: int = 0
    columns: int = 0
    column_types: Dict[str, str] = field(default_factory=dict)
    missing_values: Dict[str, int] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    source: Literal["csv", "zip", "excel"] = "csv"


@dataclass
class AnalysisResult:
    """Resultado de uma análise estatística"""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    analysis_type: str = ""
    result_data: Dict[str, Any] = field(default_factory=dict)
    summary: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    execution_time_seconds: float = 0.0

    def add_insight(self, key: str, value: Any, description: str = ""):
        """Adicionar insight ao resultado"""
        self.result_data[key] = {
            "value": value,
            "description": description,
            "timestamp": datetime.now()
        }


@dataclass
class Visualization:
    """Representação de uma visualização gerada"""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    chart_type: str = ""
    file_path: Optional[str] = None
    data_columns: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def exists(self) -> bool:
        """Verificar se o arquivo da visualização existe"""
        return self.file_path and Path(self.file_path).exists()


@dataclass
class OutlierInfo:
    """Informações sobre outliers detectados"""

    column: str
    method: str  # IQR, z-score, etc.
    outlier_indices: List[int] = field(default_factory=list)
    threshold_lower: Optional[float] = None
    threshold_upper: Optional[float] = None
    count: int = 0
    percentage: float = 0.0

    def __post_init__(self):
        """Calcular estatísticas após inicialização"""
        self.count = len(self.outlier_indices)


@dataclass
class CorrelationAnalysis:
    """Resultado de análise de correlação"""

    correlation_matrix: Dict[str, Dict[str, float]] = field(default_factory=dict)
    strong_correlations: List[tuple] = field(default_factory=list)  # [(col1, col2, value)]
    threshold: float = 0.5

    def get_strong_correlations(self, threshold: float = None) -> List[tuple]:
        """Obter correlações acima do threshold"""
        thresh = threshold or self.threshold
        strong = []

        for col1, correlations in self.correlation_matrix.items():
            for col2, value in correlations.items():
                if col1 != col2 and abs(value) >= thresh:
                    # Evitar duplicatas (A-B e B-A)
                    if (col2, col1, value) not in strong:
                        strong.append((col1, col2, value))

        return sorted(strong, key=lambda x: abs(x[2]), reverse=True)


@dataclass
class DataQualityReport:
    """Relatório de qualidade dos dados"""

    dataset_info: DatasetInfo
    missing_data_percentage: float = 0.0
    duplicate_rows: int = 0
    duplicate_percentage: float = 0.0
    data_types_issues: List[str] = field(default_factory=list)
    outliers_summary: Dict[str, OutlierInfo] = field(default_factory=dict)
    quality_score: float = 0.0  # 0-100
    recommendations: List[str] = field(default_factory=list)

    def calculate_quality_score(self) -> float:
        """Calcular score de qualidade dos dados"""
        score = 100.0

        # Penalizar dados faltantes
        score -= self.missing_data_percentage * 2

        # Penalizar duplicatas
        score -= self.duplicate_percentage * 1.5

        # Penalizar problemas de tipos
        score -= len(self.data_types_issues) * 5

        # Penalizar muitos outliers
        total_outliers = sum(info.percentage for info in self.outliers_summary.values())
        score -= min(total_outliers * 0.5, 20)  # Máximo 20 pontos

        self.quality_score = max(0.0, min(100.0, score))
        return self.quality_score


@dataclass
class AnalysisSession:
    """Sessão de análise com histórico"""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    dataset_info: Optional[DatasetInfo] = None
    analyses: List[AnalysisResult] = field(default_factory=list)
    visualizations: List[Visualization] = field(default_factory=list)
    quality_report: Optional[DataQualityReport] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def add_analysis(self, analysis: AnalysisResult):
        """Adicionar análise à sessão"""
        self.analyses.append(analysis)
        self.updated_at = datetime.now()

    def add_visualization(self, viz: Visualization):
        """Adicionar visualização à sessão"""
        self.visualizations.append(viz)
        self.updated_at = datetime.now()

    def get_recent_analyses(self, limit: int = 10) -> List[AnalysisResult]:
        """Obter análises mais recentes"""
        return sorted(self.analyses, key=lambda x: x.created_at, reverse=True)[:limit]

    def get_analysis_summary(self) -> Dict[str, Any]:
        """Obter resumo da sessão"""
        return {
            "session_id": self.id,
            "dataset": self.dataset_info.name if self.dataset_info else "Unknown",
            "total_analyses": len(self.analyses),
            "total_visualizations": len(self.visualizations),
            "duration_minutes": (self.updated_at - self.created_at).total_seconds() / 60,
            "quality_score": self.quality_report.quality_score if self.quality_report else None
        }


@dataclass
class AgentQuery:
    """Query feita pelo usuário ao agente"""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    text: str = ""
    intent: Optional[str] = None  # statistical, visualization, exploration, etc.
    required_columns: List[str] = field(default_factory=list)
    analysis_type: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def classify_intent(self) -> str:
        """Classificar intenção da query"""
        text_lower = self.text.lower()

        # Palavras-chave para cada tipo de intent
        intents = {
            "statistical": ["estatística", "média", "mediana", "desvio", "correlação", "distribuição"],
            "visualization": ["gráfico", "plot", "visualiz", "chart", "histograma", "scatter"],
            "outliers": ["outlier", "atípico", "anomalia", "extremo"],
            "exploration": ["explorar", "analisar", "entender", "resumo", "overview"],
            "quality": ["qualidade", "missing", "duplicata", "nulo", "vazio"],
            "comparison": ["comparar", "diferença", "versus", "vs", "entre"]
        }

        scores = {}
        for intent, keywords in intents.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                scores[intent] = score

        if scores:
            self.intent = max(scores, key=scores.get)
            return self.intent

        self.intent = "general"
        return self.intent


@dataclass
class ModelResponse:
    """Resposta de um modelo de IA"""

    query_id: str
    model_name: str
    response_text: str
    execution_time_seconds: float
    success: bool = True
    error_message: Optional[str] = None
    generated_artifacts: List[str] = field(default_factory=list)  # paths para gráficos, etc.
    timestamp: datetime = field(default_factory=datetime.now)

    def add_artifact(self, artifact_path: str):
        """Adicionar artefato gerado"""
        self.generated_artifacts.append(artifact_path)