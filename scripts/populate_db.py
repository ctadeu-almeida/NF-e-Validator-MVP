#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de População do Database - MVP Sucroalcooleiro

Popula rules.db com:
- NCMs de açúcar (1701.xx.xx)
- CSTs PIS/COFINS válidos
- CFOPs comuns
- Referências legais
- Regras estaduais SP + PE (overlay mínimo)

Versão: 1.0.0
"""

import sqlite3
import json
from pathlib import Path
from datetime import date


class DatabasePopulator:
    """Populador do database de regras"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self.version = "1.0.0"

    def connect(self):
        """Conectar ao database"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        print(f"[OK] Conectado a: {self.db_path}")

    def create_schema(self, schema_path: str):
        """Criar schema do database"""
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()

        # Executar script SQL
        self.conn.executescript(schema_sql)
        self.conn.commit()
        print("[OK] Schema criado com sucesso")

    def populate_ncm_rules(self):
        """Popular NCMs de acucar"""
        print("\n[*] Populando NCM Rules...")

        ncm_data = [
            {
                'ncm': '17011100',
                'description': 'Açúcar de cana, em bruto',
                'category': 'ACUCAR_BRUTO',
                'ipi_rate': 0.00,
                'is_ipi_exempt': 1,
                'pis_cofins_regime': 'STANDARD',
                'keywords': json.dumps(['açúcar', 'cana', 'bruto', 'raw', 'sugar']),
                'valid_from': '2023-01-01',
                'valid_until': None,
                'version': self.version,
                'sector': 'sucroalcooleiro',
                'product_type': 'bruto',
                'notes': 'Açúcar de cana bruto - isento de IPI'
            },
            {
                'ncm': '17011200',
                'description': 'Açúcar de beterraba, em bruto',
                'category': 'ACUCAR_BRUTO',
                'ipi_rate': 0.00,
                'is_ipi_exempt': 1,
                'pis_cofins_regime': 'STANDARD',
                'keywords': json.dumps(['açúcar', 'beterraba', 'bruto', 'sugar', 'beet']),
                'valid_from': '2023-01-01',
                'valid_until': None,
                'version': self.version,
                'sector': 'sucroalcooleiro',
                'product_type': 'bruto',
                'notes': 'Açúcar de beterraba bruto - isento de IPI'
            },
            {
                'ncm': '17019100',
                'description': 'Açúcar refinado, adicionado de aromatizante ou de corante',
                'category': 'ACUCAR_REFINADO',
                'ipi_rate': 0.00,
                'is_ipi_exempt': 1,
                'pis_cofins_regime': 'STANDARD',
                'keywords': json.dumps(['açúcar', 'refinado', 'aromatizante', 'corante', 'refined']),
                'valid_from': '2023-01-01',
                'valid_until': None,
                'version': self.version,
                'sector': 'sucroalcooleiro',
                'product_type': 'refinado',
                'notes': 'Açúcar refinado com aditivos - isento de IPI'
            },
            {
                'ncm': '17019900',
                'description': 'Outros açúcares de cana ou de beterraba e sacarose quimicamente pura, no estado sólido',
                'category': 'ACUCAR_OUTROS',
                'ipi_rate': 0.00,
                'is_ipi_exempt': 1,
                'pis_cofins_regime': 'STANDARD',
                'keywords': json.dumps(['açúcar', 'cristal', 'sacarose', 'sugar', 'crystal']),
                'valid_from': '2023-01-01',
                'valid_until': None,
                'version': self.version,
                'sector': 'sucroalcooleiro',
                'product_type': 'cristal',
                'notes': 'Açúcar cristal e outros - isento de IPI. NCM mais comum para açúcar cristal.'
            },
            {
                'ncm': '17021100',
                'description': 'Lactose e xarope de lactose',
                'category': 'OUTROS_ACUCARES',
                'ipi_rate': 0.00,
                'is_ipi_exempt': 1,
                'pis_cofins_regime': 'STANDARD',
                'keywords': json.dumps(['lactose', 'xarope']),
                'valid_from': '2023-01-01',
                'valid_until': None,
                'version': self.version,
                'sector': 'sucroalcooleiro',
                'product_type': 'lactose',
                'notes': 'Lactose - capítulo 17'
            },
        ]

        cursor = self.conn.cursor()
        for ncm in ncm_data:
            cursor.execute("""
                INSERT OR REPLACE INTO ncm_rules (
                    ncm, description, category, ipi_rate, is_ipi_exempt,
                    pis_cofins_regime, keywords, valid_from, valid_until,
                    version, sector, product_type, notes
                ) VALUES (
                    :ncm, :description, :category, :ipi_rate, :is_ipi_exempt,
                    :pis_cofins_regime, :keywords, :valid_from, :valid_until,
                    :version, :sector, :product_type, :notes
                )
            """, ncm)

        self.conn.commit()
        print(f"[OK] {len(ncm_data)} NCMs inseridos")

    def populate_pis_cofins_rules(self):
        """Popular CSTs PIS/COFINS"""
        print("\n[*] Populando PIS/COFINS Rules...")

        cst_data = [
            {
                'cst': '01',
                'description': 'Operação Tributável com Alíquota Básica',
                'situation_type': 'TRIBUTADA',
                'pis_rate_standard': 1.65,
                'cofins_rate_standard': 7.60,
                'pis_rate_cumulative': 0.65,
                'cofins_rate_cumulative': 3.00,
                'requires_base_calculation': 1,
                'allows_credit': 1,
                'legal_reference': 'Lei 10.637/2002 e Lei 10.833/2003',
                'legal_article': 'Art. 2º - Alíquotas de 1,65% (PIS) e 7,6% (COFINS)',
                'valid_for_operations': json.dumps(['VENDA', 'COMPRA']),
                'version': self.version,
                'notes': 'CST mais comum para operações tributadas no regime não-cumulativo'
            },
            {
                'cst': '04',
                'description': 'Operação Tributável Monofásica - Revenda a Alíquota Zero',
                'situation_type': 'TRIBUTADA_MONOFASICA',
                'pis_rate_standard': 0.00,
                'cofins_rate_standard': 0.00,
                'pis_rate_cumulative': 0.00,
                'cofins_rate_cumulative': 0.00,
                'requires_base_calculation': 0,
                'allows_credit': 0,
                'legal_reference': 'Lei 10.637/2002 e Lei 10.833/2003',
                'legal_article': 'Art. 3º - Tributação monofásica',
                'valid_for_operations': json.dumps(['VENDA']),
                'version': self.version,
                'notes': 'Para produtos com tributação concentrada (combustíveis, bebidas, etc)'
            },
            {
                'cst': '06',
                'description': 'Operação Tributável a Alíquota Zero',
                'situation_type': 'ALIQUOTA_ZERO',
                'pis_rate_standard': 0.00,
                'cofins_rate_standard': 0.00,
                'pis_rate_cumulative': 0.00,
                'cofins_rate_cumulative': 0.00,
                'requires_base_calculation': 1,
                'allows_credit': 1,
                'legal_reference': 'Lei 10.637/2002 e Lei 10.833/2003',
                'legal_article': 'Art. 5º - Alíquota zero para exportações',
                'valid_for_operations': json.dumps(['VENDA', 'EXPORTACAO']),
                'version': self.version,
                'notes': 'Usado principalmente para exportações'
            },
            {
                'cst': '07',
                'description': 'Operação Isenta da Contribuição',
                'situation_type': 'ISENTA',
                'pis_rate_standard': 0.00,
                'cofins_rate_standard': 0.00,
                'pis_rate_cumulative': 0.00,
                'cofins_rate_cumulative': 0.00,
                'requires_base_calculation': 0,
                'allows_credit': 0,
                'legal_reference': 'Lei 10.637/2002 e Lei 10.833/2003',
                'legal_article': 'Art. 5º e 6º - Isenções específicas',
                'valid_for_operations': json.dumps(['VENDA', 'COMPRA']),
                'version': self.version,
                'notes': 'Operações com isenção legal'
            },
            {
                'cst': '08',
                'description': 'Operação sem Incidência da Contribuição',
                'situation_type': 'NAO_INCIDENCIA',
                'pis_rate_standard': 0.00,
                'cofins_rate_standard': 0.00,
                'pis_rate_cumulative': 0.00,
                'cofins_rate_cumulative': 0.00,
                'requires_base_calculation': 0,
                'allows_credit': 0,
                'legal_reference': 'Lei 10.637/2002 e Lei 10.833/2003',
                'legal_article': 'Art. 4º - Operações sem incidência',
                'valid_for_operations': json.dumps(['VENDA', 'COMPRA', 'EXPORTACAO']),
                'version': self.version,
                'notes': 'Operações fora do campo de incidência (ex: exportação)'
            },
            {
                'cst': '49',
                'description': 'Outras Operações de Saída',
                'situation_type': 'OUTRAS',
                'pis_rate_standard': None,
                'cofins_rate_standard': None,
                'pis_rate_cumulative': None,
                'cofins_rate_cumulative': None,
                'requires_base_calculation': 0,
                'allows_credit': 0,
                'legal_reference': 'Lei 10.637/2002 e Lei 10.833/2003',
                'legal_article': None,
                'valid_for_operations': json.dumps(['VENDA']),
                'version': self.version,
                'notes': 'Outras situações não especificadas'
            },
            {
                'cst': '50',
                'description': 'Operação com Direito a Crédito - Vinculada Exclusivamente a Receita Tributada',
                'situation_type': 'TRIBUTADA',
                'pis_rate_standard': 1.65,
                'cofins_rate_standard': 7.60,
                'pis_rate_cumulative': 0.00,
                'cofins_rate_cumulative': 0.00,
                'requires_base_calculation': 1,
                'allows_credit': 1,
                'legal_reference': 'Lei 10.637/2002 e Lei 10.833/2003',
                'legal_article': 'Art. 3º - Créditos do regime não-cumulativo',
                'valid_for_operations': json.dumps(['COMPRA']),
                'version': self.version,
                'notes': 'CST de entrada - direito a crédito integral'
            },
        ]

        cursor = self.conn.cursor()
        for cst in cst_data:
            cursor.execute("""
                INSERT OR REPLACE INTO pis_cofins_rules (
                    cst, description, situation_type,
                    pis_rate_standard, cofins_rate_standard,
                    pis_rate_cumulative, cofins_rate_cumulative,
                    requires_base_calculation, allows_credit,
                    legal_reference, legal_article, valid_for_operations,
                    version, notes
                ) VALUES (
                    :cst, :description, :situation_type,
                    :pis_rate_standard, :cofins_rate_standard,
                    :pis_rate_cumulative, :cofins_rate_cumulative,
                    :requires_base_calculation, :allows_credit,
                    :legal_reference, :legal_article, :valid_for_operations,
                    :version, :notes
                )
            """, cst)

        self.conn.commit()
        print(f"[OK] {len(cst_data)} CSTs PIS/COFINS inseridos")

    def populate_cfop_rules(self):
        """Popular CFOPs comuns"""
        print("\n[*] Populando CFOP Rules...")

        cfop_data = [
            # Saídas internas (5xxx)
            {
                'cfop': '5101',
                'description': 'Venda de produção do estabelecimento',
                'operation_type': 'SAIDA',
                'operation_scope': 'INTERNO',
                'nature': 'VENDA',
                'requires_icms': 1,
                'requires_ipi': 0,
                'exempt_pis_cofins': 0,
                'common_for_sector': 'sucroalcooleiro',
                'legal_reference': 'Tabela CFOP - Ajuste SINIEF 07/05',
                'version': self.version,
                'notes': 'CFOP mais comum para venda interna de açúcar produzido'
            },
            {
                'cfop': '5102',
                'description': 'Venda de mercadoria adquirida ou recebida de terceiros',
                'operation_type': 'SAIDA',
                'operation_scope': 'INTERNO',
                'nature': 'VENDA',
                'requires_icms': 1,
                'requires_ipi': 0,
                'exempt_pis_cofins': 0,
                'common_for_sector': 'geral',
                'legal_reference': 'Tabela CFOP - Ajuste SINIEF 07/05',
                'version': self.version,
                'notes': 'Venda interna de mercadoria adquirida (revenda)'
            },

            # Saídas interestaduais (6xxx)
            {
                'cfop': '6101',
                'description': 'Venda de produção do estabelecimento',
                'operation_type': 'SAIDA',
                'operation_scope': 'INTERESTADUAL',
                'nature': 'VENDA',
                'requires_icms': 1,
                'requires_ipi': 0,
                'exempt_pis_cofins': 0,
                'common_for_sector': 'sucroalcooleiro',
                'legal_reference': 'Tabela CFOP - Ajuste SINIEF 07/05',
                'version': self.version,
                'notes': 'CFOP mais comum para venda interestadual de açúcar produzido'
            },
            {
                'cfop': '6102',
                'description': 'Venda de mercadoria adquirida ou recebida de terceiros',
                'operation_type': 'SAIDA',
                'operation_scope': 'INTERESTADUAL',
                'nature': 'VENDA',
                'requires_icms': 1,
                'requires_ipi': 0,
                'exempt_pis_cofins': 0,
                'common_for_sector': 'geral',
                'legal_reference': 'Tabela CFOP - Ajuste SINIEF 07/05',
                'version': self.version,
                'notes': 'Venda interestadual de mercadoria adquirida (revenda)'
            },

            # Exportações (7xxx)
            {
                'cfop': '7101',
                'description': 'Venda de produção do estabelecimento',
                'operation_type': 'SAIDA',
                'operation_scope': 'EXTERIOR',
                'nature': 'EXPORTACAO',
                'requires_icms': 0,
                'requires_ipi': 0,
                'exempt_pis_cofins': 1,
                'common_for_sector': 'sucroalcooleiro',
                'legal_reference': 'Tabela CFOP - Ajuste SINIEF 07/05',
                'version': self.version,
                'notes': 'Exportação - isento de ICMS, IPI, PIS e COFINS'
            },

            # Entradas internas (1xxx)
            {
                'cfop': '1101',
                'description': 'Compra para industrialização ou produção rural',
                'operation_type': 'ENTRADA',
                'operation_scope': 'INTERNO',
                'nature': 'COMPRA',
                'requires_icms': 1,
                'requires_ipi': 0,
                'exempt_pis_cofins': 0,
                'common_for_sector': 'geral',
                'legal_reference': 'Tabela CFOP - Ajuste SINIEF 07/05',
                'version': self.version,
                'notes': 'Compra interna para industrialização'
            },

            # Entradas interestaduais (2xxx)
            {
                'cfop': '2101',
                'description': 'Compra para industrialização ou produção rural',
                'operation_type': 'ENTRADA',
                'operation_scope': 'INTERESTADUAL',
                'nature': 'COMPRA',
                'requires_icms': 1,
                'requires_ipi': 0,
                'exempt_pis_cofins': 0,
                'common_for_sector': 'geral',
                'legal_reference': 'Tabela CFOP - Ajuste SINIEF 07/05',
                'version': self.version,
                'notes': 'Compra interestadual para industrialização'
            },
        ]

        cursor = self.conn.cursor()
        for cfop in cfop_data:
            cursor.execute("""
                INSERT OR REPLACE INTO cfop_rules (
                    cfop, description, operation_type, operation_scope,
                    nature, requires_icms, requires_ipi, exempt_pis_cofins,
                    common_for_sector, legal_reference, version, notes
                ) VALUES (
                    :cfop, :description, :operation_type, :operation_scope,
                    :nature, :requires_icms, :requires_ipi, :exempt_pis_cofins,
                    :common_for_sector, :legal_reference, :version, :notes
                )
            """, cfop)

        self.conn.commit()
        print(f"[OK] {len(cfop_data)} CFOPs inseridos")

    def populate_state_overrides(self):
        """Popular regras estaduais SP + PE (overlay mínimo MVP)"""
        print("\n[*] Populando State Overrides (SP + PE)...")

        state_data = [
            # São Paulo
            {
                'state': 'SP',
                'override_type': 'ICMS',
                'ncm': '17019900',
                'cfop': None,
                'sector': 'sucroalcooleiro',
                'rule_name': 'ICMS Padrão Açúcar SP',
                'rule_description': 'Alíquota padrão de ICMS para açúcar em operações internas em SP',
                'icms_rate': 18.00,
                'icms_reduction_rate': None,
                'is_st': 0,
                'st_mva': None,
                'legal_reference': 'RICMS/SP Decreto 45.490/2000',
                'legal_article': 'Art. 52 - Alíquota interna de 18%',
                'decree_number': 'Decreto 45.490/2000',
                'valid_from': '2023-01-01',
                'valid_until': None,
                'version': self.version,
                'severity': 'WARNING',
                'notes': 'MVP: validação mínima - apenas warning se divergir'
            },
            {
                'state': 'SP',
                'override_type': 'REDUCAO_BC',
                'ncm': None,
                'cfop': '5101',
                'sector': 'sucroalcooleiro',
                'rule_name': 'Redução BC ICMS - Produtos Primários',
                'rule_description': 'Alguns produtos primários podem ter redução de base de cálculo em SP',
                'icms_rate': 18.00,
                'icms_reduction_rate': 0.00,  # MVP: sem redução por padrão
                'is_st': 0,
                'st_mva': None,
                'legal_reference': 'RICMS/SP Decreto 45.490/2000',
                'legal_article': 'Art. 53 - Verificar convênios específicos',
                'decree_number': 'Decreto 45.490/2000',
                'valid_from': '2023-01-01',
                'valid_until': None,
                'version': self.version,
                'severity': 'INFO',
                'notes': 'MVP: informativo - verificar legislação específica se aplicável'
            },

            # Pernambuco
            {
                'state': 'PE',
                'override_type': 'ICMS',
                'ncm': '17019900',
                'cfop': None,
                'sector': 'sucroalcooleiro',
                'rule_name': 'ICMS Padrão Açúcar PE',
                'rule_description': 'Alíquota padrão de ICMS para açúcar em operações internas em PE',
                'icms_rate': 18.00,
                'icms_reduction_rate': None,
                'is_st': 0,
                'st_mva': None,
                'legal_reference': 'RICMS/PE Decreto 14.876/1991',
                'legal_article': 'Art. 18 - Alíquota interna de 18%',
                'decree_number': 'Decreto 14.876/1991',
                'valid_from': '2023-01-01',
                'valid_until': None,
                'version': self.version,
                'severity': 'WARNING',
                'notes': 'MVP: validação mínima - apenas warning se divergir'
            },
        ]

        cursor = self.conn.cursor()
        for state_rule in state_data:
            cursor.execute("""
                INSERT OR REPLACE INTO state_overrides (
                    state, override_type, ncm, cfop, sector,
                    rule_name, rule_description, icms_rate, icms_reduction_rate,
                    is_st, st_mva, legal_reference, legal_article, decree_number,
                    valid_from, valid_until, version, severity, notes
                ) VALUES (
                    :state, :override_type, :ncm, :cfop, :sector,
                    :rule_name, :rule_description, :icms_rate, :icms_reduction_rate,
                    :is_st, :st_mva, :legal_reference, :legal_article, :decree_number,
                    :valid_from, :valid_until, :version, :severity, :notes
                )
            """, state_rule)

        self.conn.commit()
        print(f"[OK] {len(state_data)} regras estaduais (SP + PE) inseridas")

    def populate_legal_refs(self):
        """Popular referências legais"""
        print("\n[*] Populando Legal References...")

        legal_data = [
            {
                'code': 'LEI_10637',
                'ref_type': 'LEI',
                'number': '10.637',
                'year': 2002,
                'title': 'Lei do PIS não-cumulativo',
                'summary': 'Dispõe sobre a não-cumulatividade na cobrança da contribuição para o PIS/PASEP',
                'issuing_body': 'RECEITA_FEDERAL',
                'scope': 'FEDERAL',
                'applicable_states': None,
                'full_text': None,
                'url': 'http://www.planalto.gov.br/ccivil_03/leis/2002/l10637.htm',
                'relevant_articles': json.dumps({
                    'Art. 2º': 'Alíquota de 1,65%',
                    'Art. 3º': 'Direito ao crédito',
                    'Art. 5º': 'Isenções e alíquota zero'
                }),
                'affects_taxes': json.dumps(['PIS']),
                'published_date': '2002-12-30',
                'effective_date': '2002-12-01',
                'revoked_date': None,
                'version': self.version,
                'notes': 'Lei fundamental do PIS não-cumulativo'
            },
            {
                'code': 'LEI_10833',
                'ref_type': 'LEI',
                'number': '10.833',
                'year': 2003,
                'title': 'Lei da COFINS não-cumulativa',
                'summary': 'Institui a Contribuição para o Financiamento da Seguridade Social não-cumulativa',
                'issuing_body': 'RECEITA_FEDERAL',
                'scope': 'FEDERAL',
                'applicable_states': None,
                'full_text': None,
                'url': 'http://www.planalto.gov.br/ccivil_03/leis/2003/l10.833.htm',
                'relevant_articles': json.dumps({
                    'Art. 2º': 'Alíquota de 7,6%',
                    'Art. 3º': 'Direito ao crédito',
                    'Art. 6º': 'Isenções e alíquota zero'
                }),
                'affects_taxes': json.dumps(['COFINS']),
                'published_date': '2003-12-29',
                'effective_date': '2004-02-01',
                'revoked_date': None,
                'version': self.version,
                'notes': 'Lei fundamental da COFINS não-cumulativa'
            },
            {
                'code': 'IN_2121',
                'ref_type': 'INSTRUCAO_NORMATIVA',
                'number': '2.121',
                'year': 2022,
                'title': 'Instrução Normativa RFB nº 2.121/2022',
                'summary': 'Dispõe sobre a Nomenclatura Comum do Mercosul (NCM)',
                'issuing_body': 'RECEITA_FEDERAL',
                'scope': 'FEDERAL',
                'applicable_states': None,
                'full_text': None,
                'url': 'https://www.gov.br/receitafederal/pt-br/assuntos/aduana-e-comercio-exterior/manuais/importacao/topicos-1/classificacao-fiscal/nomenclatura-comum-do-mercosul-ncm',
                'relevant_articles': json.dumps({
                    'Anexo I': 'Tabela NCM completa',
                    'Capítulo 17': 'Açúcares e produtos de confeitaria'
                }),
                'affects_taxes': json.dumps(['ICMS', 'IPI', 'II']),
                'published_date': '2022-12-23',
                'effective_date': '2023-01-01',
                'revoked_date': None,
                'version': self.version,
                'notes': 'Tabela NCM vigente - atualizada anualmente'
            },
            {
                'code': 'TIPI_17',
                'ref_type': 'TABELA',
                'number': 'Capítulo 17',
                'year': 2023,
                'title': 'TIPI - Tabela de Incidência do Imposto sobre Produtos Industrializados - Capítulo 17',
                'summary': 'Açúcares e produtos de confeitaria - NCMs e alíquotas de IPI',
                'issuing_body': 'RECEITA_FEDERAL',
                'scope': 'FEDERAL',
                'applicable_states': None,
                'full_text': None,
                'url': 'https://www.gov.br/receitafederal/pt-br/assuntos/aduana-e-comercio-exterior/manuais/importacao/topicos-1/classificacao-fiscal/tipi',
                'relevant_articles': json.dumps({
                    '1701': 'Açúcares de cana ou de beterraba - IPI: 0% (isento)',
                    '1702': 'Outros açúcares - IPI variável'
                }),
                'affects_taxes': json.dumps(['IPI']),
                'published_date': '2023-01-01',
                'effective_date': '2023-01-01',
                'revoked_date': None,
                'version': self.version,
                'notes': 'Açúcar do capítulo 17 geralmente isento de IPI'
            },
            {
                'code': 'SINIEF_0705',
                'ref_type': 'AJUSTE',
                'number': '07/05',
                'year': 2005,
                'title': 'Ajuste SINIEF 07/05 - Tabela CFOP',
                'summary': 'Código Fiscal de Operações e Prestações - Tabela completa',
                'issuing_body': 'CONFAZ',
                'scope': 'FEDERAL',
                'applicable_states': json.dumps(['ALL']),
                'full_text': None,
                'url': 'https://www.confaz.fazenda.gov.br/legislacao/ajustes/2005/ajuste-sinief-07-05',
                'relevant_articles': json.dumps({
                    'Anexo I': 'Tabela CFOP completa'
                }),
                'affects_taxes': json.dumps(['ICMS']),
                'published_date': '2005-07-30',
                'effective_date': '2005-10-01',
                'revoked_date': None,
                'version': self.version,
                'notes': 'Tabela CFOP oficial - base para validação'
            },
        ]

        cursor = self.conn.cursor()
        for legal in legal_data:
            cursor.execute("""
                INSERT OR REPLACE INTO legal_refs (
                    code, ref_type, number, year, title, summary,
                    issuing_body, scope, applicable_states, full_text, url,
                    relevant_articles, affects_taxes, published_date,
                    effective_date, revoked_date, version, notes
                ) VALUES (
                    :code, :ref_type, :number, :year, :title, :summary,
                    :issuing_body, :scope, :applicable_states, :full_text, :url,
                    :relevant_articles, :affects_taxes, :published_date,
                    :effective_date, :revoked_date, :version, :notes
                )
            """, legal)

        self.conn.commit()
        print(f"[OK] {len(legal_data)} referências legais inseridas")

    def update_metadata(self):
        """Atualizar metadata do database"""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE db_metadata
            SET value = ?, updated_at = CURRENT_TIMESTAMP
            WHERE key = 'last_population'
        """, (date.today().isoformat(),))
        self.conn.commit()
        print("\n[OK] Metadata atualizada")

    def verify_population(self):
        """Verificar população do database"""
        print("\n[INFO] Verificando população...")

        cursor = self.conn.cursor()

        # Contar registros
        counts = {}
        tables = ['ncm_rules', 'pis_cofins_rules', 'cfop_rules', 'state_overrides', 'legal_refs']

        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            counts[table] = cursor.fetchone()[0]

        print("\n[STATS] Estatísticas:")
        for table, count in counts.items():
            print(f"  • {table}: {count} registros")

        # Testar views
        print("\n[CHECK] Testando views...")
        cursor.execute("SELECT COUNT(*) FROM v_sugar_ncms")
        sugar_ncms = cursor.fetchone()[0]
        print(f"  • v_sugar_ncms: {sugar_ncms} NCMs de açúcar")

        cursor.execute("SELECT COUNT(*) FROM v_valid_csts")
        valid_csts = cursor.fetchone()[0]
        print(f"  • v_valid_csts: {valid_csts} CSTs válidos")

        cursor.execute("SELECT COUNT(*) FROM v_sugar_cfops")
        sugar_cfops = cursor.fetchone()[0]
        print(f"  • v_sugar_cfops: {sugar_cfops} CFOPs comuns")

        cursor.execute("SELECT COUNT(*) FROM v_state_rules_active")
        state_rules = cursor.fetchone()[0]
        print(f"  • v_state_rules_active: {state_rules} regras SP+PE ativas")

        return counts

    def close(self):
        """Fechar conexão"""
        if self.conn:
            self.conn.close()
            print("\n[OK] Conexão fechada")


def main():
    """Main function"""
    print("=" * 60)
    print("NF-e Validator - Database Population")
    print("MVP Sucroalcooleiro - Açúcar (SP + PE)")
    print("=" * 60)

    # Caminhos
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    db_path = project_root / "src" / "database" / "rules.db"
    schema_path = project_root / "src" / "database" / "schema.sql"

    # Criar diretório se não existir
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Verificar se schema existe
    if not schema_path.exists():
        print(f"[ERROR] Schema não encontrado: {schema_path}")
        return

    # Criar populator
    populator = DatabasePopulator(str(db_path))

    try:
        # Conectar
        populator.connect()

        # Criar schema
        print("\n[BUILD] Criando schema...")
        populator.create_schema(str(schema_path))

        # Popular tabelas
        populator.populate_ncm_rules()
        populator.populate_pis_cofins_rules()
        populator.populate_cfop_rules()
        populator.populate_state_overrides()
        populator.populate_legal_refs()

        # Atualizar metadata
        populator.update_metadata()

        # Verificar
        counts = populator.verify_population()

        # Resumo final
        print("\n" + "=" * 60)
        print("[OK] DATABASE POPULADO COM SUCESSO!")
        print("=" * 60)
        print(f"\n[LOCATION] Database: {db_path}")
        print(f"[INFO] Total de registros: {sum(counts.values())}")

    except Exception as e:
        print(f"\n[ERROR] Erro durante população: {e}")
        import traceback
        traceback.print_exc()

    finally:
        populator.close()


if __name__ == "__main__":
    main()
