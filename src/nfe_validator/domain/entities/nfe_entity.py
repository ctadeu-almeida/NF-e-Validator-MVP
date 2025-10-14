# -*- coding: utf-8 -*-
"""
Entidade NF-e para MVP Sucroalcooleiro

Foco: Açúcar (cristal/refinado) - SP + PE
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
from enum import Enum


class TipoOperacao(Enum):
    """Tipo de operação da NF-e"""
    ENTRADA = "ENTRADA"
    SAIDA = "SAIDA"
    DEVOLUCAO = "DEVOLUCAO"


class ValidationStatus(Enum):
    """Status de validação"""
    PENDING = "PENDING"
    VALIDATING = "VALIDATING"
    VALID = "VALID"
    INVALID = "INVALID"
    ERROR = "ERROR"


class Severity(Enum):
    """Severidade do erro"""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class Empresa:
    """Dados de empresa (emitente/destinatário)"""
    cnpj: str
    razao_social: str
    nome_fantasia: Optional[str] = None
    ie: Optional[str] = None  # Inscrição Estadual
    uf: str = ""
    municipio: str = ""

    # Regime tributário
    crt: Optional[str] = None  # Código Regime Tributário


@dataclass
class ImpostoItem:
    """Impostos de um item da NF-e"""

    # ICMS
    icms_cst: str = ""
    icms_base: Decimal = Decimal('0')
    icms_aliquota: Decimal = Decimal('0')
    icms_valor: Decimal = Decimal('0')

    # IPI
    ipi_cst: str = ""
    ipi_base: Decimal = Decimal('0')
    ipi_aliquota: Decimal = Decimal('0')
    ipi_valor: Decimal = Decimal('0')

    # PIS
    pis_cst: str = ""
    pis_base: Decimal = Decimal('0')
    pis_aliquota: Decimal = Decimal('0')
    pis_valor: Decimal = Decimal('0')

    # COFINS
    cofins_cst: str = ""
    cofins_base: Decimal = Decimal('0')
    cofins_aliquota: Decimal = Decimal('0')
    cofins_valor: Decimal = Decimal('0')


@dataclass
class NFeItem:
    """Item de uma NF-e"""

    # Identificação
    numero_item: int
    codigo_produto: str
    descricao: str

    # Classificação fiscal
    ncm: str
    cest: Optional[str] = None
    cfop: str = ""

    # Quantidades e valores
    unidade: str = ""
    quantidade: Decimal = Decimal('0')
    valor_unitario: Decimal = Decimal('0')
    valor_total: Decimal = Decimal('0')
    valor_desconto: Decimal = Decimal('0')
    valor_frete: Decimal = Decimal('0')

    # Tributação
    impostos: ImpostoItem = field(default_factory=ImpostoItem)

    # Validação
    validation_errors: List['ValidationError'] = field(default_factory=list)

    # Metadados para setor sucroalcooleiro
    tipo_acucar: Optional[str] = None  # cristal, refinado, etc
    icumsa: Optional[str] = None  # índice de cor do açúcar


@dataclass
class TotaisNFe:
    """Totais da NF-e"""

    # Base de cálculo
    base_calculo_icms: Decimal = Decimal('0')

    # Valores de impostos
    valor_icms: Decimal = Decimal('0')
    valor_icms_desonerado: Decimal = Decimal('0')
    valor_ipi: Decimal = Decimal('0')
    valor_pis: Decimal = Decimal('0')
    valor_cofins: Decimal = Decimal('0')

    # Totais
    valor_produtos: Decimal = Decimal('0')
    valor_frete: Decimal = Decimal('0')
    valor_seguro: Decimal = Decimal('0')
    valor_desconto: Decimal = Decimal('0')
    valor_outras_despesas: Decimal = Decimal('0')
    valor_total_nota: Decimal = Decimal('0')


@dataclass
class ValidationError:
    """Erro de validação fiscal"""

    # Identificação
    code: str
    field: str
    message: str
    severity: Severity

    # Detalhes
    expected_value: Optional[str] = None
    actual_value: Optional[str] = None
    suggestion: Optional[str] = None

    # Base legal
    legal_reference: str = ""
    legal_article: Optional[str] = None

    # Impacto financeiro
    financial_impact: Optional[Decimal] = None

    # Item afetado (se aplicável)
    item_numero: Optional[int] = None

    # Correção automática
    can_auto_correct: bool = False
    corrected_value: Optional[str] = None


@dataclass
class NFeEntity:
    """
    Entidade NF-e para MVP Sucroalcooleiro

    Foco: Validação de tributação de açúcar (cristal/refinado)
    Estados: SP + PE
    """

    # Identificação
    chave_acesso: str  # 44 dígitos
    numero: str
    serie: str
    data_emissao: datetime

    # Partes
    emitente: Empresa
    destinatario: Empresa

    # Itens
    items: List[NFeItem] = field(default_factory=list)

    # Totais
    totais: TotaisNFe = field(default_factory=TotaisNFe)

    # Operação
    tipo_operacao: TipoOperacao = TipoOperacao.SAIDA
    natureza_operacao: str = ""
    cfop_nota: str = ""  # CFOP predominante da nota

    # Validação
    validation_status: ValidationStatus = ValidationStatus.PENDING
    validation_errors: List[ValidationError] = field(default_factory=list)
    validation_timestamp: Optional[datetime] = None

    # Metadados MVP
    setor: str = "sucroalcooleiro"
    produto_principal: str = "acucar"  # açúcar
    uf_origem: str = ""
    uf_destino: str = ""

    # Original
    csv_source: Optional[Dict[str, Any]] = None

    def add_validation_error(self, error: ValidationError):
        """Adicionar erro de validação"""
        self.validation_errors.append(error)

        # Atualizar status baseado na severidade
        if error.severity == Severity.CRITICAL:
            self.validation_status = ValidationStatus.INVALID

    def get_errors_by_severity(self, severity: Severity) -> List[ValidationError]:
        """Obter erros por severidade"""
        return [e for e in self.validation_errors if e.severity == severity]

    def get_total_financial_impact(self) -> Decimal:
        """Calcular impacto financeiro total dos erros"""
        return sum(
            (e.financial_impact or Decimal('0'))
            for e in self.validation_errors
            if e.financial_impact
        )

    def is_sugar_product(self, item: NFeItem) -> bool:
        """Verificar se item é açúcar"""
        # NCM do açúcar: 1701 (açúcares de cana ou beterraba)
        return item.ncm.startswith('1701')

    def get_sugar_items(self) -> List[NFeItem]:
        """Obter apenas itens de açúcar"""
        return [item for item in self.items if self.is_sugar_product(item)]

    def is_interstate(self) -> bool:
        """Verificar se operação é interestadual"""
        return self.uf_origem != self.uf_destino

    def get_validation_summary(self) -> Dict[str, Any]:
        """Obter resumo da validação"""
        return {
            'status': self.validation_status.value,
            'total_errors': len(self.validation_errors),
            'critical_errors': len(self.get_errors_by_severity(Severity.CRITICAL)),
            'errors': len(self.get_errors_by_severity(Severity.ERROR)),
            'warnings': len(self.get_errors_by_severity(Severity.WARNING)),
            'financial_impact': float(self.get_total_financial_impact()),
            'validated_at': self.validation_timestamp.isoformat() if self.validation_timestamp else None
        }


@dataclass
class AuditReport:
    """Relatório de auditoria fiscal"""

    # NF-e analisada
    nfe: NFeEntity

    # Resumo
    total_errors: int = 0
    critical_count: int = 0
    error_count: int = 0
    warning_count: int = 0
    info_count: int = 0

    # Impacto financeiro
    total_financial_impact: Decimal = Decimal('0')

    # Erros agrupados
    errors_by_type: Dict[str, List[ValidationError]] = field(default_factory=dict)
    errors_by_item: Dict[int, List[ValidationError]] = field(default_factory=dict)

    # Metadados
    generated_at: datetime = field(default_factory=datetime.now)
    validator_version: str = "1.0.0-mvp"

    # Recomendações
    recommendations: List[str] = field(default_factory=list)

    def generate_summary(self):
        """Gerar resumo do relatório"""
        self.total_errors = len(self.nfe.validation_errors)
        self.critical_count = len(self.nfe.get_errors_by_severity(Severity.CRITICAL))
        self.error_count = len(self.nfe.get_errors_by_severity(Severity.ERROR))
        self.warning_count = len(self.nfe.get_errors_by_severity(Severity.WARNING))
        self.info_count = len(self.nfe.get_errors_by_severity(Severity.INFO))
        self.total_financial_impact = self.nfe.get_total_financial_impact()

        # Agrupar erros
        self._group_errors()

        # Gerar recomendações
        self._generate_recommendations()

    def _group_errors(self):
        """Agrupar erros por tipo e item"""
        for error in self.nfe.validation_errors:
            # Por tipo
            error_type = error.code.split('_')[0]
            if error_type not in self.errors_by_type:
                self.errors_by_type[error_type] = []
            self.errors_by_type[error_type].append(error)

            # Por item
            if error.item_numero:
                if error.item_numero not in self.errors_by_item:
                    self.errors_by_item[error.item_numero] = []
                self.errors_by_item[error.item_numero].append(error)

    def _generate_recommendations(self):
        """Gerar recomendações baseadas nos erros"""
        if self.critical_count > 0:
            self.recommendations.append(
                "⚠️ Foram encontrados erros CRÍTICOS que podem resultar em autuação fiscal. "
                "Recomendamos ação imediata."
            )

        if self.total_financial_impact > 0:
            self.recommendations.append(
                f"💰 Impacto financeiro estimado: R$ {self.total_financial_impact:,.2f}. "
                "Considere solicitar retificação da nota fiscal."
            )

        # Recomendações por tipo de erro
        if 'NCM' in self.errors_by_type:
            self.recommendations.append(
                "📋 Encontrados erros de classificação NCM. "
                "Verifique a Tabela NCM/TIPI atualizada."
            )

        if 'PIS' in self.errors_by_type or 'COFINS' in self.errors_by_type:
            self.recommendations.append(
                "💼 Encontrados erros em PIS/COFINS. "
                "Consulte legislação federal (Lei 10.833/2003 e Lei 10.637/2002)."
            )
