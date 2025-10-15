# -*- coding: utf-8 -*-
"""
State Validators - Validadores Estaduais (SP + PE)

Validadores específicos para regras estaduais de SP e PE.
Retornam apenas warnings (não-bloqueantes) para o MVP.

Overlay sobre validações federais:
- SP: ICMS overlay, substituição tributária
- PE: ICMS overlay, benefícios fiscais
"""

from typing import List, Optional
from decimal import Decimal

from ..entities.nfe_entity import (
    NFeEntity,
    NFeItem,
    ValidationError,
    Severity
)

# Import FiscalRepository - absolute import
import sys
from pathlib import Path
if True:  # Always add to path
    project_root = Path(__file__).parent.parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from repositories.fiscal_repository import FiscalRepository


class SPValidator:
    """
    Validador de regras específicas do estado de São Paulo

    Validações:
    - ICMS: Alíquota padrão 18% (pode haver reduções)
    - Substituição Tributária para açúcar
    - Conformidade com RICMS/SP
    """

    def __init__(self, repository: FiscalRepository):
        """
        Inicializar validador SP

        Args:
            repository: FiscalRepository para consulta de regras estaduais
        """
        self.repo = repository
        self.uf = 'SP'

    def validate(self, item: NFeItem, nfe: NFeEntity) -> List[ValidationError]:
        """
        Validar item contra regras de SP

        Args:
            item: Item da NF-e
            nfe: NF-e completa (contexto)

        Returns:
            Lista de ValidationErrors (severity=WARNING)
        """
        errors = []

        # Apenas validar se operação envolve SP
        if not self._is_sp_operation(nfe):
            return errors

        # Obter regras estaduais para o NCM
        state_rules = self.repo.get_state_rules(self.uf, item.ncm)

        # Validação 1: ICMS Rate
        icms_errors = self._validate_icms_rate(item, state_rules)
        errors.extend(icms_errors)

        # Validação 2: Substituição Tributária
        st_errors = self._validate_substituicao_tributaria(item, state_rules)
        errors.extend(st_errors)

        return errors

    def _is_sp_operation(self, nfe: NFeEntity) -> bool:
        """
        Verificar se operação envolve SP

        Returns:
            True se emitente ou destinatário é de SP
        """
        return nfe.emitente.uf == 'SP' or nfe.destinatario.uf == 'SP'

    def _validate_icms_rate(
        self,
        item: NFeItem,
        state_rules: List[dict]
    ) -> List[ValidationError]:
        """
        Validar alíquota de ICMS para SP

        Args:
            item: Item da NF-e
            state_rules: Regras estaduais do repositório

        Returns:
            Lista de erros (warnings)
        """
        errors = []

        # Buscar regra de ICMS específica
        icms_rule = None
        for rule in state_rules:
            if rule['override_type'] == 'ICMS':
                icms_rule = rule
                break

        if not icms_rule:
            # Sem regra específica, retornar
            return errors

        # Obter alíquota esperada
        expected_rate = icms_rule.get('icms_rate')
        if expected_rate is None:
            return errors

        expected_rate = Decimal(str(expected_rate))

        # Verificar se item tem impostos
        if not item.impostos or not item.impostos.icms_aliquota:
            return errors

        actual_rate = item.impostos.icms_aliquota

        # Verificar divergência
        if abs(actual_rate - expected_rate) > Decimal('0.01'):
            # Calcular impacto financeiro (diferença no valor)
            base_calculo = item.impostos.icms_base or Decimal('0')

            expected_value = (base_calculo * expected_rate) / Decimal('100')
            actual_value = item.impostos.icms_valor or Decimal('0')
            impact = actual_value - expected_value

            # Montar referência legal
            legal_ref = icms_rule.get('legal_reference', 'RICMS/SP')
            decree = icms_rule.get('decree_number', '')
            if decree:
                legal_ref += f' - Decreto {decree}'

            errors.append(ValidationError(
                code='SP_ICMS_001',
                field=f'item[{item.numero_item}].impostos.icms_aliquota',
                message=f'Alíquota ICMS divergente da regra SP para NCM {item.ncm}. '
                       f'Regra: "{icms_rule.get("rule_name", "ICMS padrão")}"',
                severity=Severity.WARNING,  # Non-blocking
                expected_value=f'{expected_rate}%',
                actual_value=f'{actual_rate}%',
                legal_reference=legal_ref,
                legal_article=icms_rule.get('legal_article'),
                financial_impact=impact,
                can_auto_correct=False
            ))

        return errors

    def _validate_substituicao_tributaria(
        self,
        item: NFeItem,
        state_rules: List[dict]
    ) -> List[ValidationError]:
        """
        Validar substituição tributária (ICMS-ST)

        Args:
            item: Item da NF-e
            state_rules: Regras estaduais

        Returns:
            Lista de erros (warnings)
        """
        errors = []

        # Buscar regra de ST
        st_rule = None
        for rule in state_rules:
            if rule['override_type'] == 'SUBSTITUICAO_TRIBUTARIA' and rule.get('is_st'):
                st_rule = rule
                break

        if not st_rule:
            # Sem regra de ST aplicável
            return errors

        # Verificar se NCM está sujeito a ST
        # (SP tem ST para açúcar em algumas operações)

        # Se regra indica ST mas item não tem icms_st_valor
        if item.impostos and not item.impostos.icms_st_valor:
            mva = st_rule.get('st_mva')

            legal_ref = st_rule.get('legal_reference', 'RICMS/SP - Anexo ST')

            errors.append(ValidationError(
                code='SP_ST_001',
                field=f'item[{item.numero_item}].impostos.icms_st_valor',
                message=f'Item sujeito a Substituição Tributária em SP (NCM {item.ncm}). '
                       f'MVA aplicável: {mva}%. Regra: "{st_rule.get("rule_name")}"',
                severity=Severity.WARNING,
                expected_value=f'ICMS-ST calculado com MVA {mva}%',
                actual_value='Não informado',
                legal_reference=legal_ref,
                legal_article=st_rule.get('legal_article'),
                financial_impact=None,  # Difícil calcular sem base completa
                can_auto_correct=False
            ))

        return errors


class PEValidator:
    """
    Validador de regras específicas do estado de Pernambuco

    Validações:
    - ICMS: Alíquota padrão 18%
    - Benefícios fiscais estaduais
    - Conformidade com RICMS/PE
    """

    def __init__(self, repository: FiscalRepository):
        """
        Inicializar validador PE

        Args:
            repository: FiscalRepository para consulta de regras estaduais
        """
        self.repo = repository
        self.uf = 'PE'

    def validate(self, item: NFeItem, nfe: NFeEntity) -> List[ValidationError]:
        """
        Validar item contra regras de PE

        Args:
            item: Item da NF-e
            nfe: NF-e completa (contexto)

        Returns:
            Lista de ValidationErrors (severity=WARNING)
        """
        errors = []

        # Apenas validar se operação envolve PE
        if not self._is_pe_operation(nfe):
            return errors

        # Obter regras estaduais para o NCM
        state_rules = self.repo.get_state_rules(self.uf, item.ncm)

        # Validação 1: ICMS Rate
        icms_errors = self._validate_icms_rate(item, state_rules)
        errors.extend(icms_errors)

        # Validação 2: Benefícios Fiscais
        beneficio_errors = self._validate_beneficios_fiscais(item, state_rules)
        errors.extend(beneficio_errors)

        return errors

    def _is_pe_operation(self, nfe: NFeEntity) -> bool:
        """
        Verificar se operação envolve PE

        Returns:
            True se emitente ou destinatário é de PE
        """
        return nfe.emitente.uf == 'PE' or nfe.destinatario.uf == 'PE'

    def _validate_icms_rate(
        self,
        item: NFeItem,
        state_rules: List[dict]
    ) -> List[ValidationError]:
        """
        Validar alíquota de ICMS para PE

        Args:
            item: Item da NF-e
            state_rules: Regras estaduais do repositório

        Returns:
            Lista de erros (warnings)
        """
        errors = []

        # Buscar regra de ICMS específica
        icms_rule = None
        for rule in state_rules:
            if rule['override_type'] == 'ICMS':
                icms_rule = rule
                break

        if not icms_rule:
            # Sem regra específica, retornar
            return errors

        # Obter alíquota esperada
        expected_rate = icms_rule.get('icms_rate')
        if expected_rate is None:
            return errors

        expected_rate = Decimal(str(expected_rate))

        # Verificar se item tem impostos
        if not item.impostos or not item.impostos.icms_aliquota:
            return errors

        actual_rate = item.impostos.icms_aliquota

        # Verificar divergência
        if abs(actual_rate - expected_rate) > Decimal('0.01'):
            # Calcular impacto financeiro
            base_calculo = item.impostos.icms_base or Decimal('0')

            expected_value = (base_calculo * expected_rate) / Decimal('100')
            actual_value = item.impostos.icms_valor or Decimal('0')
            impact = actual_value - expected_value

            # Montar referência legal
            legal_ref = icms_rule.get('legal_reference', 'RICMS/PE')
            decree = icms_rule.get('decree_number', '')
            if decree:
                legal_ref += f' - Decreto {decree}'

            errors.append(ValidationError(
                code='PE_ICMS_001',
                field=f'item[{item.numero_item}].impostos.icms_aliquota',
                message=f'Alíquota ICMS divergente da regra PE para NCM {item.ncm}. '
                       f'Regra: "{icms_rule.get("rule_name", "ICMS padrão")}"',
                severity=Severity.WARNING,  # Non-blocking
                expected_value=f'{expected_rate}%',
                actual_value=f'{actual_rate}%',
                legal_reference=legal_ref,
                legal_article=icms_rule.get('legal_article'),
                financial_impact=impact,
                can_auto_correct=False
            ))

        return errors

    def _validate_beneficios_fiscais(
        self,
        item: NFeItem,
        state_rules: List[dict]
    ) -> List[ValidationError]:
        """
        Validar aplicação de benefícios fiscais de PE

        Args:
            item: Item da NF-e
            state_rules: Regras estaduais

        Returns:
            Lista de erros (warnings)
        """
        errors = []

        # Buscar regra de redução de base de cálculo
        reducao_rule = None
        for rule in state_rules:
            if rule['override_type'] == 'REDUCAO_BC':
                reducao_rule = rule
                break

        if not reducao_rule:
            # Sem benefício aplicável
            return errors

        # Verificar se item tem redução de BC aplicada
        reduction_rate = reducao_rule.get('icms_reduction_rate')
        if reduction_rate is None:
            return errors

        reduction_rate = Decimal(str(reduction_rate))

        # Se há benefício disponível mas não foi aplicado
        if item.impostos and item.impostos.icms_base:
            # Verificar se base de cálculo foi reduzida
            # (difícil saber sem valor original do produto, apenas informativo)

            legal_ref = reducao_rule.get('legal_reference', 'RICMS/PE')

            errors.append(ValidationError(
                code='PE_BENEFICIO_001',
                field=f'item[{item.numero_item}].impostos.icms_base',
                message=f'Benefício fiscal disponível para NCM {item.ncm} em PE: '
                       f'Redução de {reduction_rate}% na base de cálculo do ICMS. '
                       f'Regra: "{reducao_rule.get("rule_name")}"',
                severity=Severity.INFO,  # Apenas informativo
                expected_value=f'Redução de BC em {reduction_rate}%',
                actual_value='Verificar se foi aplicado',
                legal_reference=legal_ref,
                legal_article=reducao_rule.get('legal_article'),
                financial_impact=None,  # Não calcular sem contexto completo
                can_auto_correct=False
            ))

        return errors


# =====================================================
# Factory Functions
# =====================================================

def create_sp_validator(repository: FiscalRepository) -> SPValidator:
    """
    Factory para criar validador SP

    Args:
        repository: FiscalRepository

    Returns:
        SPValidator instanciado
    """
    return SPValidator(repository)


def create_pe_validator(repository: FiscalRepository) -> PEValidator:
    """
    Factory para criar validador PE

    Args:
        repository: FiscalRepository

    Returns:
        PEValidator instanciado
    """
    return PEValidator(repository)


def get_state_validator(uf: str, repository: FiscalRepository):
    """
    Factory para obter validador por UF

    Args:
        uf: UF (SP, PE)
        repository: FiscalRepository

    Returns:
        Validator correspondente ou None
    """
    validators = {
        'SP': lambda: SPValidator(repository),
        'PE': lambda: PEValidator(repository)
    }

    validator_factory = validators.get(uf.upper())
    return validator_factory() if validator_factory else None
