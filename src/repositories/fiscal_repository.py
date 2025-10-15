# -*- coding: utf-8 -*-
"""
Fiscal Repository - Acesso ao Database de Regras Fiscais

Métodos para consulta das regras de validação:
- NCM Rules
- PIS/COFINS Rules
- CFOP Rules
- State Overrides (SP + PE)
- Legal References
"""

import sqlite3
from typing import Optional, Dict, List, Any
from pathlib import Path
from datetime import date


class FiscalRepository:
    """
    Repositório de acesso às regras fiscais no SQLite

    Provê interface para queries no rules.db
    Suporta consulta em camadas: CSV Local → SQLite → LLM (opcional)
    """

    def __init__(self, db_path: str = None, use_local_csv: bool = True, use_ai_fallback: bool = False):
        """
        Inicializar repositório

        Args:
            db_path: Caminho para rules.db (default: src/database/rules.db)
            use_local_csv: Habilitar consulta ao CSV local como primeira camada
            use_ai_fallback: Habilitar consulta LLM como última camada (fallback)
        """
        if db_path is None:
            # Path padrão relativo ao projeto
            project_root = Path(__file__).parent.parent.parent
            db_path = project_root / "src" / "database" / "rules.db"

        self.db_path = str(db_path)
        self.conn = None
        self.use_local_csv = use_local_csv
        self.use_ai_fallback = use_ai_fallback

        # Inicializar repositório CSV local
        self.local_repo = None
        if use_local_csv:
            try:
                from repositories.local_csv_repository import LocalCSVRepository
                self.local_repo = LocalCSVRepository()
            except Exception as e:
                import logging
                logging.warning(f"LocalCSVRepository não disponível: {e}")
                self.local_repo = None

        self._connect()

    def _connect(self):
        """Conectar ao database"""
        try:
            # check_same_thread=False permite uso em múltiplas threads (Streamlit)
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row  # Retornar dicts
        except sqlite3.Error as e:
            raise ConnectionError(f"Erro ao conectar ao database: {e}")

    def close(self):
        """Fechar conexão"""
        if self.conn:
            self.conn.close()

    def __enter__(self):
        """Context manager enter"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

    # =====================================================
    # NCM Rules
    # =====================================================

    def get_ncm_rule(self, ncm: str) -> Optional[Dict[str, Any]]:
        """
        Obter regra de NCM com consulta em camadas

        Ordem de precedência:
        1. CSV Local (base_validacao.csv) - prioridade máxima
        2. SQLite (rules.db) - base padrão do sistema
        3. LLM (opcional) - fallback com IA

        Args:
            ncm: Código NCM (8 dígitos)

        Returns:
            Dict com dados do NCM ou None se não encontrado
        """
        # Camada 1: Consultar CSV local primeiro
        if self.local_repo and self.local_repo.is_available():
            rule = self.local_repo.get_ncm_rule(ncm)
            if rule:
                return rule

        # Camada 2: Consultar SQLite
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT
                ncm,
                description,
                category,
                ipi_rate,
                is_ipi_exempt,
                pis_cofins_regime,
                keywords,
                product_type,
                sector,
                notes
            FROM ncm_rules
            WHERE ncm = ?
              AND (valid_until IS NULL OR valid_until >= DATE('now'))
        """, (ncm,))

        row = cursor.fetchone()
        if row:
            return dict(row)

        # Camada 3: LLM fallback (se habilitado)
        # TODO: Implementar consulta ao agente LLM como última camada
        # if self.use_ai_fallback:
        #     return self._query_llm_for_ncm(ncm)

        return None

    def get_all_sugar_ncms(self) -> List[Dict[str, Any]]:
        """
        Obter todos os NCMs de açúcar válidos

        Returns:
            Lista de dicts com NCMs de açúcar
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT
                ncm,
                description,
                product_type,
                keywords
            FROM v_sugar_ncms
            ORDER BY ncm
        """)

        return [dict(row) for row in cursor.fetchall()]

    def validate_ncm_exists(self, ncm: str) -> bool:
        """
        Verificar se NCM existe e está válido

        Args:
            ncm: Código NCM

        Returns:
            True se NCM existe e está válido
        """
        rule = self.get_ncm_rule(ncm)
        return rule is not None

    def get_ncm_keywords(self, ncm: str) -> List[str]:
        """
        Obter palavras-chave de um NCM

        Args:
            ncm: Código NCM

        Returns:
            Lista de palavras-chave
        """
        rule = self.get_ncm_rule(ncm)
        if rule and rule.get('keywords'):
            import json
            return json.loads(rule['keywords'])
        return []

    # =====================================================
    # PIS/COFINS Rules
    # =====================================================

    def get_pis_cofins_rule(self, cst: str, ncm: str = None) -> Optional[Dict[str, Any]]:
        """
        Obter regra PIS/COFINS por CST (com suporte a camadas)

        Args:
            cst: CST PIS/COFINS (2 dígitos)
            ncm: Código NCM (opcional, para consulta no CSV local)

        Returns:
            Dict com regra ou None
        """
        # Camada 1: Consultar CSV local se NCM fornecido
        if ncm and self.local_repo and self.local_repo.is_available():
            rule = self.local_repo.get_pis_cofins_rule(ncm, tipo_operacao='saida')
            if rule and rule.get('pis_cst') == cst:
                return rule

        # Camada 2: Consultar SQLite
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT
                cst,
                description,
                situation_type,
                pis_rate_standard,
                cofins_rate_standard,
                pis_rate_cumulative,
                cofins_rate_cumulative,
                requires_base_calculation,
                allows_credit,
                legal_reference,
                legal_article,
                notes
            FROM pis_cofins_rules
            WHERE cst = ?
        """, (cst,))

        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

    def get_valid_csts(self) -> List[str]:
        """
        Obter lista de CSTs válidos

        Returns:
            Lista de CSTs válidos
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT cst
            FROM pis_cofins_rules
            ORDER BY cst
        """)

        return [row['cst'] for row in cursor.fetchall()]

    def get_pis_cofins_rates(self, cst: str, regime: str = 'STANDARD') -> Dict[str, float]:
        """
        Obter alíquotas PIS/COFINS

        Args:
            cst: CST PIS/COFINS
            regime: 'STANDARD' (não-cumulativo) ou 'CUMULATIVE'

        Returns:
            Dict com {'pis': aliquota, 'cofins': aliquota}
        """
        rule = self.get_pis_cofins_rule(cst)
        if not rule:
            return {'pis': 0.0, 'cofins': 0.0}

        if regime == 'CUMULATIVE':
            return {
                'pis': float(rule.get('pis_rate_cumulative', 0) or 0),
                'cofins': float(rule.get('cofins_rate_cumulative', 0) or 0)
            }
        else:
            return {
                'pis': float(rule.get('pis_rate_standard', 0) or 0),
                'cofins': float(rule.get('cofins_rate_standard', 0) or 0)
            }

    def is_cst_valid(self, cst: str) -> bool:
        """
        Verificar se CST é válido

        Args:
            cst: CST a validar

        Returns:
            True se válido
        """
        return cst in self.get_valid_csts()

    # =====================================================
    # CFOP Rules
    # =====================================================

    def get_cfop_rule(self, cfop: str) -> Optional[Dict[str, Any]]:
        """
        Obter regra de CFOP

        Args:
            cfop: Código CFOP (4 dígitos)

        Returns:
            Dict com regra ou None
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT
                cfop,
                description,
                operation_type,
                operation_scope,
                nature,
                requires_icms,
                requires_ipi,
                exempt_pis_cofins,
                common_for_sector,
                legal_reference,
                notes
            FROM cfop_rules
            WHERE cfop = ?
        """, (cfop,))

        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

    def get_cfops_by_scope(self, scope: str) -> List[Dict[str, Any]]:
        """
        Obter CFOPs por escopo

        Args:
            scope: 'INTERNO', 'INTERESTADUAL', 'EXTERIOR'

        Returns:
            Lista de CFOPs
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT cfop, description, operation_type, nature
            FROM cfop_rules
            WHERE operation_scope = ?
            ORDER BY cfop
        """, (scope,))

        return [dict(row) for row in cursor.fetchall()]

    def get_sugar_cfops(self) -> List[Dict[str, Any]]:
        """
        Obter CFOPs comuns para açúcar

        Returns:
            Lista de CFOPs
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT
                cfop,
                description,
                operation_scope,
                nature
            FROM v_sugar_cfops
            ORDER BY cfop
        """)

        return [dict(row) for row in cursor.fetchall()]

    def validate_cfop_scope(self, cfop: str, is_interstate: bool) -> bool:
        """
        Validar se CFOP está correto para operação (interna/interestadual)

        Args:
            cfop: Código CFOP
            is_interstate: True se operação é interestadual

        Returns:
            True se CFOP está correto
        """
        rule = self.get_cfop_rule(cfop)
        if not rule:
            return False

        scope = rule['operation_scope']

        if is_interstate:
            return scope in ['INTERESTADUAL', 'EXTERIOR']
        else:
            return scope == 'INTERNO'

    # =====================================================
    # State Overrides (SP + PE)
    # =====================================================

    def get_state_rules(self, uf: str, ncm: str = None) -> List[Dict[str, Any]]:
        """
        Obter regras estaduais (overlay)

        Args:
            uf: UF (SP, PE)
            ncm: NCM específico (opcional)

        Returns:
            Lista de regras estaduais
        """
        cursor = self.conn.cursor()

        if ncm:
            cursor.execute("""
                SELECT
                    state,
                    override_type,
                    ncm,
                    cfop,
                    rule_name,
                    rule_description,
                    icms_rate,
                    icms_reduction_rate,
                    is_st,
                    st_mva,
                    legal_reference,
                    legal_article,
                    decree_number,
                    severity,
                    notes
                FROM state_overrides
                WHERE state = ?
                  AND (ncm = ? OR ncm IS NULL)
                  AND (valid_until IS NULL OR valid_until >= DATE('now'))
                ORDER BY override_type
            """, (uf, ncm))
        else:
            cursor.execute("""
                SELECT
                    state,
                    override_type,
                    ncm,
                    cfop,
                    rule_name,
                    rule_description,
                    icms_rate,
                    icms_reduction_rate,
                    is_st,
                    st_mva,
                    legal_reference,
                    legal_article,
                    decree_number,
                    severity,
                    notes
                FROM state_overrides
                WHERE state = ?
                  AND (valid_until IS NULL OR valid_until >= DATE('now'))
                ORDER BY override_type
            """, (uf,))

        return [dict(row) for row in cursor.fetchall()]

    def get_state_icms_rate(self, uf: str, ncm: str = None) -> Optional[float]:
        """
        Obter alíquota ICMS estadual

        Args:
            uf: UF
            ncm: NCM (opcional)

        Returns:
            Alíquota ICMS ou None
        """
        rules = self.get_state_rules(uf, ncm)

        for rule in rules:
            if rule['override_type'] == 'ICMS' and rule.get('icms_rate'):
                return float(rule['icms_rate'])

        return None

    def has_state_rules(self, uf: str) -> bool:
        """
        Verificar se UF tem regras específicas

        Args:
            uf: UF

        Returns:
            True se tem regras
        """
        rules = self.get_state_rules(uf)
        return len(rules) > 0

    # =====================================================
    # Legal References
    # =====================================================

    def get_legal_reference(self, code: str) -> Optional[Dict[str, Any]]:
        """
        Obter referência legal completa

        Args:
            code: Código da referência (LEI_10637, IN_2121, etc)

        Returns:
            Dict com referência ou None
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT
                code,
                ref_type,
                number,
                year,
                title,
                summary,
                issuing_body,
                scope,
                url,
                relevant_articles,
                published_date,
                effective_date
            FROM legal_refs
            WHERE code = ?
        """, (code,))

        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

    def get_legal_references_by_tax(self, tax: str) -> List[Dict[str, Any]]:
        """
        Obter referências legais que afetam determinado tributo

        Args:
            tax: Nome do tributo (PIS, COFINS, ICMS, IPI)

        Returns:
            Lista de referências
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT
                code,
                title,
                ref_type,
                number,
                year,
                url
            FROM legal_refs
            WHERE affects_taxes LIKE ?
            ORDER BY year DESC, number
        """, (f'%{tax}%',))

        return [dict(row) for row in cursor.fetchall()]

    def format_legal_citation(self, code: str) -> str:
        """
        Formatar citação legal completa

        Args:
            code: Código da referência

        Returns:
            String formatada (ex: "Lei 10.637/2002 - Lei do PIS não-cumulativo")
        """
        ref = self.get_legal_reference(code)
        if not ref:
            return code

        ref_type = ref['ref_type'].replace('_', ' ').title()
        number = ref['number']
        year = ref['year']
        title = ref['title']

        return f"{ref_type} {number}/{year} - {title}"

    # =====================================================
    # Métodos de Diagnóstico e Estatísticas
    # =====================================================

    def get_repository_layers_status(self) -> Dict[str, Any]:
        """
        Obter status das camadas de consulta

        Returns:
            Dict com informações sobre cada camada
        """
        status = {
            'camadas_ativas': [],
            'camadas_disponiveis': 3,
            'ordem_precedencia': ['CSV Local', 'SQLite', 'LLM (fallback)']
        }

        # Status CSV Local
        if self.local_repo and self.local_repo.is_available():
            status['camadas_ativas'].append('CSV Local')
            status['csv_local'] = self.local_repo.get_statistics()
        else:
            status['csv_local'] = {'disponivel': False}

        # Status SQLite
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM ncm_rules")
            ncm_count = cursor.fetchone()['count']
            status['camadas_ativas'].append('SQLite')
            status['sqlite'] = {
                'disponivel': True,
                'database': self.db_path,
                'total_ncm_rules': ncm_count
            }
        except Exception as e:
            status['sqlite'] = {'disponivel': False, 'erro': str(e)}

        # Status LLM
        status['llm'] = {
            'habilitado': self.use_ai_fallback,
            'disponivel': False  # TODO: Implementar verificação de API key
        }
        if self.use_ai_fallback:
            status['camadas_ativas'].append('LLM')

        status['total_camadas_ativas'] = len(status['camadas_ativas'])

        return status

    # =====================================================
    # Queries Auxiliares
    # =====================================================

    def get_database_version(self) -> str:
        """
        Obter versão do schema

        Returns:
            Versão do schema
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT value
            FROM db_metadata
            WHERE key = 'schema_version'
        """)

        row = cursor.fetchone()
        return row['value'] if row else 'unknown'

    def get_last_population_date(self) -> Optional[str]:
        """
        Obter data da última população

        Returns:
            Data ISO ou None
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT value
            FROM db_metadata
            WHERE key = 'last_population'
        """)

        row = cursor.fetchone()
        return row['value'] if row else None

    def get_statistics(self) -> Dict[str, int]:
        """
        Obter estatísticas do database

        Returns:
            Dict com contagens
        """
        cursor = self.conn.cursor()

        stats = {}
        tables = ['ncm_rules', 'pis_cofins_rules', 'cfop_rules', 'state_overrides', 'legal_refs']

        for table in tables:
            cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
            stats[table] = cursor.fetchone()['count']

        return stats

    # =====================================================
    # Validação Integrada
    # =====================================================

    def validate_tax_configuration(
        self,
        ncm: str,
        pis_cst: str,
        cofins_cst: str,
        cfop: str
    ) -> Dict[str, Any]:
        """
        Validação integrada de configuração tributária

        Args:
            ncm: NCM
            pis_cst: CST PIS
            cofins_cst: CST COFINS
            cfop: CFOP

        Returns:
            Dict com resultado da validação
        """
        result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'ncm_info': None,
            'pis_info': None,
            'cofins_info': None,
            'cfop_info': None
        }

        # Validar NCM
        ncm_rule = self.get_ncm_rule(ncm)
        if not ncm_rule:
            result['valid'] = False
            result['errors'].append(f"NCM {ncm} não encontrado no database")
        else:
            result['ncm_info'] = ncm_rule

        # Validar PIS CST
        pis_rule = self.get_pis_cofins_rule(pis_cst)
        if not pis_rule:
            result['valid'] = False
            result['errors'].append(f"CST PIS {pis_cst} inválido")
        else:
            result['pis_info'] = pis_rule

        # Validar COFINS CST
        cofins_rule = self.get_pis_cofins_rule(cofins_cst)
        if not cofins_rule:
            result['valid'] = False
            result['errors'].append(f"CST COFINS {cofins_cst} inválido")
        else:
            result['cofins_info'] = cofins_rule

        # Validar CFOP
        cfop_rule = self.get_cfop_rule(cfop)
        if not cfop_rule:
            result['warnings'].append(f"CFOP {cfop} não reconhecido (pode ser válido mas fora do escopo MVP)")
        else:
            result['cfop_info'] = cfop_rule

        return result


# =====================================================
# Factory Functions
# =====================================================

def create_fiscal_repository(db_path: str = None) -> FiscalRepository:
    """
    Factory para criar repositório

    Args:
        db_path: Caminho customizado (opcional)

    Returns:
        FiscalRepository instanciado
    """
    return FiscalRepository(db_path)


def get_default_repository() -> FiscalRepository:
    """
    Obter repositório com path padrão

    Returns:
        FiscalRepository com database padrão
    """
    return FiscalRepository()
