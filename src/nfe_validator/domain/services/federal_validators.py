# -*- coding: utf-8 -*-
"""
Validadores Federais - MVP Sucroalcooleiro (Versão 2 com Repository)

Validações federais (Brasil todo) integradas com Database:
1. NCM × Descrição
2. PIS/COFINS (CST, alíquota, valor)
3. CFOP (interno vs interestadual)
4. Cálculos e somatórios

Mudança: Todas as regras vêm do FiscalRepository (rules.db)
"""

from decimal import Decimal
from typing import List, Optional, Dict
import json

from ..entities.nfe_entity import NFeEntity, NFeItem, ValidationError, Severity

# Import FiscalRepository - absolute import
import sys
from pathlib import Path
if True:  # Always add to path
    project_root = Path(__file__).parent.parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from repositories.fiscal_repository import FiscalRepository


class NCMValidator:
    """
    Validador de NCM integrado com Database

    Usa FiscalRepository para buscar regras de NCM
    """

    def __init__(self, repository: FiscalRepository):
        """
        Inicializar validador com repository

        Args:
            repository: FiscalRepository para consultas
        """
        self.repo = repository

    def validate(self, item: NFeItem, nfe: NFeEntity) -> List[ValidationError]:
        """
        Validar NCM do item

        Args:
            item: Item da NF-e
            nfe: NF-e completa (contexto)

        Returns:
            Lista de erros de validação
        """
        errors = []

        # 1. Validar formato do NCM
        if not self._is_valid_format(item.ncm):
            legal_ref = self.repo.format_legal_citation('IN_2121')
            errors.append(ValidationError(
                code='NCM_001',
                field='ncm',
                message=f'NCM inválido: {item.ncm}. Deve ter 8 dígitos.',
                severity=Severity.CRITICAL,
                actual_value=item.ncm,
                expected_value='8 dígitos numéricos',
                legal_reference=legal_ref,
                item_numero=item.numero_item,
                financial_impact=Decimal('0')
            ))
            return errors

        # 2. Buscar NCM no database
        ncm_rule = self.repo.get_ncm_rule(item.ncm)

        if not ncm_rule:
            # NCM não reconhecido no MVP
            if item.ncm.startswith('1701'):
                # É açúcar mas não está na base MVP
                tipi_ref = self.repo.format_legal_citation('TIPI_17')
                errors.append(ValidationError(
                    code='NCM_004',
                    field='ncm',
                    message=f'NCM {item.ncm} de açúcar não reconhecido na base MVP',
                    severity=Severity.INFO,
                    actual_value=item.ncm,
                    legal_reference=tipi_ref,
                    item_numero=item.numero_item,
                    suggestion='Validar com Tabela NCM completa ou consultar despachante aduaneiro'
                ))
            else:
                # Não é açúcar
                errors.append(ValidationError(
                    code='NCM_002',
                    field='ncm',
                    message=f'NCM {item.ncm} não corresponde a açúcar (esperado: 1701xxxx)',
                    severity=Severity.ERROR,
                    actual_value=item.ncm,
                    expected_value='1701xxxx (açúcar)',
                    legal_reference='Tabela NCM/TIPI - Capítulo 17',
                    item_numero=item.numero_item,
                    suggestion='Verificar classificação fiscal do produto. MVP focado em açúcar.'
                ))
            return errors

        # 3. Validar descrição contra keywords do NCM
        desc_error = self._validate_description(item, ncm_rule)
        if desc_error:
            errors.append(desc_error)

        return errors

    def _validate_description(self, item: NFeItem, ncm_rule: Dict) -> Optional[ValidationError]:
        """
        Validar descrição do produto contra keywords do NCM

        Args:
            item: Item da NF-e
            ncm_rule: Regra do NCM do database

        Returns:
            ValidationError ou None
        """
        desc_lower = item.descricao.lower()

        # Obter keywords do NCM
        keywords_json = ncm_rule.get('keywords')
        if not keywords_json:
            return None

        try:
            keywords = json.loads(keywords_json)
        except:
            return None

        # Verificar se alguma keyword aparece na descrição
        if not any(kw.lower() in desc_lower for kw in keywords):
            return ValidationError(
                code='NCM_003',
                field='descricao',
                message=f'Descrição "{item.descricao}" pode não corresponder ao NCM {item.ncm} ({ncm_rule["description"]})',
                severity=Severity.WARNING,
                actual_value=item.descricao,
                expected_value=ncm_rule['description'],
                legal_reference='Tabela NCM/TIPI - Posição 1701',
                item_numero=item.numero_item,
                suggestion=f'Descrição esperada para NCM {item.ncm}: {ncm_rule["description"]}'
            )

        return None

    def _is_valid_format(self, ncm: str) -> bool:
        """Validar formato do NCM (8 dígitos)"""
        if not ncm:
            return False
        ncm_clean = ncm.replace('.', '').replace('-', '')
        return len(ncm_clean) == 8 and ncm_clean.isdigit()


class PISCOFINSValidator:
    """
    Validador de PIS e COFINS integrado com Database
    """

    def __init__(self, repository: FiscalRepository):
        """
        Inicializar validador

        Args:
            repository: FiscalRepository
        """
        self.repo = repository

    def validate(self, item: NFeItem, nfe: NFeEntity) -> List[ValidationError]:
        """Validar PIS e COFINS do item"""
        errors = []

        # Validar PIS
        errors.extend(self._validate_pis(item, nfe))

        # Validar COFINS
        errors.extend(self._validate_cofins(item, nfe))

        # Validar relação PIS/COFINS
        errors.extend(self._validate_pis_cofins_relation(item, nfe))

        return errors

    def _validate_pis(self, item: NFeItem, nfe: NFeEntity) -> List[ValidationError]:
        """Validar PIS"""
        errors = []
        pis = item.impostos

        # 1. Validar CST com database
        if not self.repo.is_cst_valid(pis.pis_cst):
            lei_ref = self.repo.format_legal_citation('LEI_10637')
            errors.append(ValidationError(
                code='PIS_001',
                field='pis_cst',
                message=f'CST PIS inválido: {pis.pis_cst}',
                severity=Severity.ERROR,
                actual_value=pis.pis_cst,
                expected_value='CST válido conforme base de dados',
                legal_reference=lei_ref,
                item_numero=item.numero_item
            ))
            return errors

        # Obter regra do CST
        pis_rule = self.repo.get_pis_cofins_rule(pis.pis_cst)
        if not pis_rule:
            # WARNING: Sem regra PIS no repositório
            errors.append(ValidationError(
                code='PIS_999',
                field='pis_cst',
                message=f'CST PIS {pis.pis_cst} sem regra cadastrada no repositório - validação de alíquota não realizada',
                severity=Severity.WARNING,
                actual_value=pis.pis_cst,
                expected_value='Regra cadastrada na base de dados',
                legal_reference='Sistema de Validação',
                item_numero=item.numero_item,
                suggestion='Verifique se o CST está correto ou adicione regra em base_validacao.csv'
            ))
            return errors

        # 2. Validar alíquota (se CST for tributado)
        if pis_rule['situation_type'] == 'TRIBUTADA':
            rates = self.repo.get_pis_cofins_rates(pis.pis_cst, regime='STANDARD')
            expected_aliquota = Decimal(str(rates['pis']))

            if pis.pis_aliquota != expected_aliquota:
                # Calcular impacto financeiro
                correct_value = (item.valor_total * expected_aliquota / Decimal('100')).quantize(Decimal('0.01'))
                financial_impact = abs(pis.pis_valor - correct_value)

                errors.append(ValidationError(
                    code='PIS_002',
                    field='pis_aliquota',
                    message=f'Alíquota PIS incorreta: {pis.pis_aliquota}%',
                    severity=Severity.CRITICAL,
                    actual_value=str(pis.pis_aliquota),
                    expected_value=str(expected_aliquota),
                    legal_reference=pis_rule.get('legal_reference', ''),
                    legal_article=pis_rule.get('legal_article', ''),
                    item_numero=item.numero_item,
                    financial_impact=financial_impact,
                    suggestion=f'Alíquota correta: {expected_aliquota}%',
                    corrected_value=str(expected_aliquota)
                ))

        # 3. Validar cálculo
        if pis.pis_aliquota > 0:
            calculated_pis = (pis.pis_base * pis.pis_aliquota / Decimal('100')).quantize(Decimal('0.01'))

            if abs(calculated_pis - pis.pis_valor) > Decimal('0.02'):
                errors.append(ValidationError(
                    code='PIS_003',
                    field='pis_valor',
                    message=f'Valor PIS incorreto. Calculado: {calculated_pis}, Informado: {pis.pis_valor}',
                    severity=Severity.ERROR,
                    actual_value=str(pis.pis_valor),
                    expected_value=str(calculated_pis),
                    legal_reference=pis_rule.get('legal_reference', ''),
                    item_numero=item.numero_item,
                    financial_impact=abs(calculated_pis - pis.pis_valor),
                    can_auto_correct=True,
                    corrected_value=str(calculated_pis)
                ))

        # 4. Validar exportação
        if self._is_export_operation(nfe):
            if pis_rule['situation_type'] not in ['ALIQUOTA_ZERO', 'NAO_INCIDENCIA']:
                lei_ref = self.repo.format_legal_citation('LEI_10637')
                errors.append(ValidationError(
                    code='PIS_004',
                    field='pis_cst',
                    message=f'Operação de exportação deve ter PIS com CST 06 ou 08',
                    severity=Severity.CRITICAL,
                    actual_value=pis.pis_cst,
                    expected_value='06 ou 08',
                    legal_reference=lei_ref,
                    legal_article='Art. 5º - Exportações com alíquota zero',
                    item_numero=item.numero_item,
                    financial_impact=pis.pis_valor,
                    suggestion='Exportações são isentas de PIS/COFINS'
                ))

        return errors

    def _validate_cofins(self, item: NFeItem, nfe: NFeEntity) -> List[ValidationError]:
        """Validar COFINS"""
        errors = []
        cofins = item.impostos

        # 1. Validar CST
        if not self.repo.is_cst_valid(cofins.cofins_cst):
            lei_ref = self.repo.format_legal_citation('LEI_10833')
            errors.append(ValidationError(
                code='COFINS_001',
                field='cofins_cst',
                message=f'CST COFINS inválido: {cofins.cofins_cst}',
                severity=Severity.ERROR,
                actual_value=cofins.cofins_cst,
                expected_value='CST válido conforme base de dados',
                legal_reference=lei_ref,
                item_numero=item.numero_item
            ))
            return errors

        # Obter regra
        cofins_rule = self.repo.get_pis_cofins_rule(cofins.cofins_cst)
        if not cofins_rule:
            # WARNING: Sem regra COFINS no repositório
            errors.append(ValidationError(
                code='COFINS_999',
                field='cofins_cst',
                message=f'CST COFINS {cofins.cofins_cst} sem regra cadastrada no repositório - validação de alíquota não realizada',
                severity=Severity.WARNING,
                actual_value=cofins.cofins_cst,
                expected_value='Regra cadastrada na base de dados',
                legal_reference='Sistema de Validação',
                item_numero=item.numero_item,
                suggestion='Verifique se o CST está correto ou adicione regra em base_validacao.csv'
            ))
            return errors

        # 2. Validar alíquota
        if cofins_rule['situation_type'] == 'TRIBUTADA':
            rates = self.repo.get_pis_cofins_rates(cofins.cofins_cst, regime='STANDARD')
            expected_aliquota = Decimal(str(rates['cofins']))

            if cofins.cofins_aliquota != expected_aliquota:
                correct_value = (item.valor_total * expected_aliquota / Decimal('100')).quantize(Decimal('0.01'))
                financial_impact = abs(cofins.cofins_valor - correct_value)

                errors.append(ValidationError(
                    code='COFINS_002',
                    field='cofins_aliquota',
                    message=f'Alíquota COFINS incorreta: {cofins.cofins_aliquota}%',
                    severity=Severity.CRITICAL,
                    actual_value=str(cofins.cofins_aliquota),
                    expected_value=str(expected_aliquota),
                    legal_reference=cofins_rule.get('legal_reference', ''),
                    legal_article=cofins_rule.get('legal_article', ''),
                    item_numero=item.numero_item,
                    financial_impact=financial_impact,
                    suggestion=f'Alíquota correta: {expected_aliquota}%',
                    corrected_value=str(expected_aliquota)
                ))

        # 3. Validar cálculo
        if cofins.cofins_aliquota > 0:
            calculated_cofins = (cofins.cofins_base * cofins.cofins_aliquota / Decimal('100')).quantize(Decimal('0.01'))

            if abs(calculated_cofins - cofins.cofins_valor) > Decimal('0.02'):
                errors.append(ValidationError(
                    code='COFINS_003',
                    field='cofins_valor',
                    message=f'Valor COFINS incorreto. Calculado: {calculated_cofins}, Informado: {cofins.cofins_valor}',
                    severity=Severity.ERROR,
                    actual_value=str(cofins.cofins_valor),
                    expected_value=str(calculated_cofins),
                    legal_reference=cofins_rule.get('legal_reference', ''),
                    item_numero=item.numero_item,
                    financial_impact=abs(calculated_cofins - cofins.cofins_valor),
                    can_auto_correct=True,
                    corrected_value=str(calculated_cofins)
                ))

        # 4. Validar exportação
        if self._is_export_operation(nfe):
            if cofins_rule['situation_type'] not in ['ALIQUOTA_ZERO', 'NAO_INCIDENCIA']:
                lei_ref = self.repo.format_legal_citation('LEI_10833')
                errors.append(ValidationError(
                    code='COFINS_004',
                    field='cofins_cst',
                    message=f'Operação de exportação deve ter COFINS com CST 06 ou 08',
                    severity=Severity.CRITICAL,
                    actual_value=cofins.cofins_cst,
                    expected_value='06 ou 08',
                    legal_reference=lei_ref,
                    legal_article='Art. 6º - Exportações com alíquota zero',
                    item_numero=item.numero_item,
                    financial_impact=cofins.cofins_valor,
                    suggestion='Exportações são isentas de PIS/COFINS'
                ))

        return errors

    def _validate_pis_cofins_relation(self, item: NFeItem, nfe: NFeEntity) -> List[ValidationError]:
        """Validar relação entre PIS e COFINS"""
        errors = []

        # PIS e COFINS devem ter CST compatíveis
        if item.impostos.pis_cst != item.impostos.cofins_cst:
            errors.append(ValidationError(
                code='PISCOFINS_001',
                field='pis_cst,cofins_cst',
                message=f'CST PIS ({item.impostos.pis_cst}) e COFINS ({item.impostos.cofins_cst}) divergentes',
                severity=Severity.WARNING,
                actual_value=f'PIS:{item.impostos.pis_cst}, COFINS:{item.impostos.cofins_cst}',
                legal_reference='Leis 10.637/2002 e 10.833/2003',
                item_numero=item.numero_item,
                suggestion='PIS e COFINS geralmente devem ter mesma situação tributária'
            ))

        return errors

    def _is_export_operation(self, nfe: NFeEntity) -> bool:
        """Verificar se é operação de exportação"""
        return nfe.cfop_nota.startswith('7')


class CFOPValidator:
    """
    Validador de CFOP integrado com Database
    """

    def __init__(self, repository: FiscalRepository):
        """
        Inicializar validador

        Args:
            repository: FiscalRepository
        """
        self.repo = repository

    def validate(self, item: NFeItem, nfe: NFeEntity) -> List[ValidationError]:
        """Validar CFOP do item"""
        errors = []

        # 1. Validar formato
        if not self._is_valid_format(item.cfop):
            sinief_ref = self.repo.format_legal_citation('SINIEF_0705')
            errors.append(ValidationError(
                code='CFOP_001',
                field='cfop',
                message=f'CFOP inválido: {item.cfop}. Deve ter 4 dígitos.',
                severity=Severity.CRITICAL,
                actual_value=item.cfop,
                expected_value='4 dígitos numéricos',
                legal_reference=sinief_ref,
                item_numero=item.numero_item
            ))
            return errors

        # 2. Buscar CFOP no database
        cfop_rule = self.repo.get_cfop_rule(item.cfop)

        if not cfop_rule:
            errors.append(ValidationError(
                code='CFOP_002',
                field='cfop',
                message=f'CFOP {item.cfop} não reconhecido para setor sucroalcooleiro (MVP)',
                severity=Severity.WARNING,
                actual_value=item.cfop,
                legal_reference='Tabela CFOP - Ajuste SINIEF 07/05',
                item_numero=item.numero_item,
                suggestion='Verificar Tabela CFOP completa. MVP focado em CFOPs comuns de açúcar.'
            ))
            # Continuar validação mesmo sem regra específica

        # 3. Validar consistência interno/interestadual
        is_interstate = nfe.is_interstate()

        # Validar com repository se possível
        if cfop_rule:
            scope = cfop_rule['operation_scope']

            if is_interstate and scope not in ['INTERESTADUAL', 'EXTERIOR']:
                errors.append(ValidationError(
                    code='CFOP_003',
                    field='cfop',
                    message=f'Operação interestadual ({nfe.uf_origem}→{nfe.uf_destino}) com CFOP interno ({item.cfop})',
                    severity=Severity.CRITICAL,
                    actual_value=item.cfop,
                    expected_value=f'6{item.cfop[1:]} (interestadual)',
                    legal_reference=cfop_rule.get('legal_reference', 'Tabela CFOP'),
                    item_numero=item.numero_item,
                    suggestion=f'Use CFOP 6{item.cfop[1:]} para operação interestadual'
                ))
            elif not is_interstate and scope != 'INTERNO':
                errors.append(ValidationError(
                    code='CFOP_004',
                    field='cfop',
                    message=f'Operação interna ({nfe.uf_origem}) com CFOP interestadual ({item.cfop})',
                    severity=Severity.CRITICAL,
                    actual_value=item.cfop,
                    expected_value=f'5{item.cfop[1:]} (interno)',
                    legal_reference=cfop_rule.get('legal_reference', 'Tabela CFOP'),
                    item_numero=item.numero_item,
                    suggestion=f'Use CFOP 5{item.cfop[1:]} para operação interna'
                ))
        else:
            # Validação básica por dígito inicial sem regra
            cfop_first_digit = item.cfop[0]

            if is_interstate and cfop_first_digit not in ['6', '7']:
                errors.append(ValidationError(
                    code='CFOP_003',
                    field='cfop',
                    message=f'Operação interestadual ({nfe.uf_origem}→{nfe.uf_destino}) com CFOP interno ({item.cfop})',
                    severity=Severity.CRITICAL,
                    actual_value=item.cfop,
                    expected_value='6xxx ou 7xxx',
                    legal_reference='Tabela CFOP',
                    item_numero=item.numero_item
                ))
            elif not is_interstate and cfop_first_digit != '5':
                errors.append(ValidationError(
                    code='CFOP_004',
                    field='cfop',
                    message=f'Operação interna ({nfe.uf_origem}) com CFOP interestadual ({item.cfop})',
                    severity=Severity.CRITICAL,
                    actual_value=item.cfop,
                    expected_value='5xxx',
                    legal_reference='Tabela CFOP',
                    item_numero=item.numero_item
                ))

        return errors

    def _is_valid_format(self, cfop: str) -> bool:
        """Validar formato do CFOP"""
        if not cfop:
            return False
        cfop_clean = cfop.replace('.', '')
        return len(cfop_clean) == 4 and cfop_clean.isdigit()


class TotalsValidator:
    """Validador de totais e somatórios da NF-e"""

    def __init__(self, repository: FiscalRepository = None):
        """
        Inicializar validador

        Args:
            repository: Opcional (totais não dependem do DB)
        """
        self.repo = repository

    def validate(self, nfe: NFeEntity) -> List[ValidationError]:
        """Validar totais da NF-e"""
        errors = []

        # 1. Somar valores dos itens
        total_items = sum(item.valor_total for item in nfe.items)

        # 2. Validar valor dos produtos
        if abs(total_items - nfe.totais.valor_produtos) > Decimal('0.02'):
            errors.append(ValidationError(
                code='TOTAL_001',
                field='valor_produtos',
                message=f'Valor total dos produtos divergente. Soma itens: {total_items}, Informado: {nfe.totais.valor_produtos}',
                severity=Severity.CRITICAL,
                actual_value=str(nfe.totais.valor_produtos),
                expected_value=str(total_items),
                legal_reference='Manual NF-e, Item 7.2',
                financial_impact=abs(total_items - nfe.totais.valor_produtos),
                can_auto_correct=True,
                corrected_value=str(total_items)
            ))

        # 3. Validar valor total da nota
        calculated_total = (
            nfe.totais.valor_produtos +
            nfe.totais.valor_frete +
            nfe.totais.valor_seguro +
            nfe.totais.valor_outras_despesas -
            nfe.totais.valor_desconto
        )

        if abs(calculated_total - nfe.totais.valor_total_nota) > Decimal('0.02'):
            errors.append(ValidationError(
                code='TOTAL_002',
                field='valor_total_nota',
                message=f'Valor total da nota incorreto. Calculado: {calculated_total}, Informado: {nfe.totais.valor_total_nota}',
                severity=Severity.CRITICAL,
                actual_value=str(nfe.totais.valor_total_nota),
                expected_value=str(calculated_total),
                legal_reference='Manual NF-e, Item 7.2',
                financial_impact=abs(calculated_total - nfe.totais.valor_total_nota),
                can_auto_correct=True,
                corrected_value=str(calculated_total)
            ))

        # 4. Validar somatório PIS
        total_pis = sum(item.impostos.pis_valor for item in nfe.items)
        if abs(total_pis - nfe.totais.valor_pis) > Decimal('0.02'):
            errors.append(ValidationError(
                code='TOTAL_003',
                field='valor_pis',
                message=f'Total PIS divergente. Soma itens: {total_pis}, Informado: {nfe.totais.valor_pis}',
                severity=Severity.ERROR,
                actual_value=str(nfe.totais.valor_pis),
                expected_value=str(total_pis),
                legal_reference='Manual NF-e',
                financial_impact=abs(total_pis - nfe.totais.valor_pis),
                can_auto_correct=True
            ))

        # 5. Validar somatório COFINS
        total_cofins = sum(item.impostos.cofins_valor for item in nfe.items)
        if abs(total_cofins - nfe.totais.valor_cofins) > Decimal('0.02'):
            errors.append(ValidationError(
                code='TOTAL_004',
                field='valor_cofins',
                message=f'Total COFINS divergente. Soma itens: {total_cofins}, Informado: {nfe.totais.valor_cofins}',
                severity=Severity.ERROR,
                actual_value=str(nfe.totais.valor_cofins),
                expected_value=str(total_cofins),
                legal_reference='Manual NF-e',
                financial_impact=abs(total_cofins - nfe.totais.valor_cofins),
                can_auto_correct=True
            ))

        return errors
