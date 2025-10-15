# -*- coding: utf-8 -*-
"""
Local CSV Repository - Repositório de Base de Validação Local

Lê regras fiscais de um arquivo CSV local editável pelo usuário.
Funciona como primeira camada de consulta antes do SQLite e LLM.
"""

import csv
from typing import Optional, Dict, List
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class LocalCSVRepository:
    """
    Repositório para leitura de regras fiscais de CSV local

    O arquivo base_validacao.csv contém regras customizadas da empresa,
    tendo prioridade sobre as regras do banco de dados SQLite.
    """

    def __init__(self, csv_path: str = None):
        """
        Inicializar repositório

        Args:
            csv_path: Caminho para base_validacao.csv (default: raiz do projeto)
        """
        if csv_path is None:
            # Path padrão relativo ao projeto
            project_root = Path(__file__).parent.parent.parent
            csv_path = project_root / "base_validacao.csv"

        self.csv_path = Path(csv_path)
        self.rules_cache = None
        self._load_rules()

    def _load_rules(self):
        """Carregar regras do CSV para memória (cache)"""
        if not self.csv_path.exists():
            logger.warning(f"Arquivo {self.csv_path} não encontrado. LocalCSVRepository desabilitado.")
            self.rules_cache = {}
            return

        self.rules_cache = {}

        try:
            with open(self.csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                for row in reader:
                    # Ignorar linhas de comentário ou vazias
                    if not row.get('ncm') or row['ncm'].startswith('#'):
                        continue

                    ncm = row['ncm'].strip()

                    # Armazenar regra completa por NCM
                    self.rules_cache[ncm] = {
                        'ncm': ncm,
                        'descricao': row.get('descricao', '').strip(),
                        'pis_cst_saida': row.get('pis_cst_saida', '').strip(),
                        'pis_aliquota_saida': self._parse_float(row.get('pis_aliquota_saida')),
                        'cofins_cst_saida': row.get('cofins_cst_saida', '').strip(),
                        'cofins_aliquota_saida': self._parse_float(row.get('cofins_aliquota_saida')),
                        'pis_cst_entrada': row.get('pis_cst_entrada', '').strip(),
                        'pis_aliquota_entrada': self._parse_float(row.get('pis_aliquota_entrada')),
                        'cofins_cst_entrada': row.get('cofins_cst_entrada', '').strip(),
                        'cofins_aliquota_entrada': self._parse_float(row.get('cofins_aliquota_entrada')),
                        'cfop_saida_permitidos': row.get('cfop_saida_permitidos', '').strip(),
                        'cfop_entrada_permitidos': row.get('cfop_entrada_permitidos', '').strip(),
                        'icms_sp_reducao_bc': row.get('icms_sp_reducao_bc', '').strip(),
                        'icms_pe_credito_presumido': row.get('icms_pe_credito_presumido', '').strip(),
                        'base_legal': row.get('base_legal', '').strip(),
                        'observacoes': row.get('observacoes', '').strip()
                    }

            logger.info(f"✅ LocalCSVRepository carregado: {len(self.rules_cache)} regras de {self.csv_path}")

        except Exception as e:
            logger.error(f"Erro ao carregar {self.csv_path}: {e}")
            self.rules_cache = {}

    def _parse_float(self, value: str) -> Optional[float]:
        """Converter string para float, retornando None se inválido"""
        if not value or value.strip() == '':
            return None
        try:
            return float(value.strip())
        except ValueError:
            return None

    def reload(self):
        """Recarregar regras do CSV (útil se o arquivo foi editado)"""
        self._load_rules()

    def is_available(self) -> bool:
        """Verificar se repositório está disponível"""
        return self.rules_cache is not None and len(self.rules_cache) > 0

    def get_ncm_rule(self, ncm: str) -> Optional[Dict]:
        """
        Buscar regra de NCM no CSV local

        Args:
            ncm: Código NCM (8 dígitos)

        Returns:
            Dict com regra completa ou None se não encontrado
        """
        if not self.is_available():
            return None

        ncm = ncm.strip()
        rule = self.rules_cache.get(ncm)

        if rule:
            logger.debug(f"✅ NCM {ncm} encontrado no LocalCSVRepository")

        return rule

    def get_pis_cofins_rule(self, ncm: str, tipo_operacao: str = 'saida') -> Optional[Dict]:
        """
        Buscar regra de PIS/COFINS no CSV local

        Args:
            ncm: Código NCM
            tipo_operacao: 'saida' ou 'entrada'

        Returns:
            Dict com regras de PIS/COFINS ou None
        """
        rule = self.get_ncm_rule(ncm)

        if not rule:
            return None

        if tipo_operacao == 'saida':
            return {
                'ncm': ncm,
                'pis_cst': rule['pis_cst_saida'],
                'pis_aliquota': rule['pis_aliquota_saida'],
                'cofins_cst': rule['cofins_cst_saida'],
                'cofins_aliquota': rule['cofins_aliquota_saida'],
                'base_legal': rule['base_legal']
            }
        else:  # entrada
            return {
                'ncm': ncm,
                'pis_cst': rule['pis_cst_entrada'],
                'pis_aliquota': rule['pis_aliquota_entrada'],
                'cofins_cst': rule['cofins_cst_entrada'],
                'cofins_aliquota': rule['cofins_aliquota_entrada'],
                'base_legal': rule['base_legal']
            }

    def get_cfop_rule(self, cfop: str) -> Optional[Dict]:
        """
        Verificar se CFOP é válido consultando regras NCM

        Args:
            cfop: Código CFOP (4 dígitos)

        Returns:
            Dict com informações do CFOP ou None
        """
        if not self.is_available():
            return None

        cfop = cfop.strip()

        # Determinar tipo de operação pelo primeiro dígito
        if cfop.startswith('5') or cfop.startswith('6'):
            tipo = 'saida'
        elif cfop.startswith('1') or cfop.startswith('2'):
            tipo = 'entrada'
        else:
            return None

        # Buscar em todas as regras para ver se o CFOP está listado
        for ncm, rule in self.rules_cache.items():
            if tipo == 'saida':
                cfops_permitidos = rule.get('cfop_saida_permitidos', '')
            else:
                cfops_permitidos = rule.get('cfop_entrada_permitidos', '')

            if cfop in cfops_permitidos.split('|'):
                return {
                    'code': cfop,
                    'description': f"CFOP {cfop} ({tipo})",
                    'operation_type': tipo,
                    'valid': True
                }

        return None

    def validate_ncm_cfop(self, ncm: str, cfop: str) -> bool:
        """
        Validar se combinação NCM × CFOP é válida

        Args:
            ncm: Código NCM
            cfop: Código CFOP

        Returns:
            True se combinação é válida, False caso contrário
        """
        rule = self.get_ncm_rule(ncm)

        if not rule:
            return False

        # Determinar tipo de operação
        if cfop.startswith('5') or cfop.startswith('6'):
            cfops_permitidos = rule.get('cfop_saida_permitidos', '')
        elif cfop.startswith('1') or cfop.startswith('2'):
            cfops_permitidos = rule.get('cfop_entrada_permitidos', '')
        else:
            return False

        return cfop in cfops_permitidos.split('|')

    def get_state_rule(self, uf: str, ncm: str) -> Optional[Dict]:
        """
        Buscar regras estaduais (ICMS) no CSV

        Args:
            uf: Sigla do estado (SP, PE, etc.)
            ncm: Código NCM

        Returns:
            Dict com regras estaduais ou None
        """
        rule = self.get_ncm_rule(ncm)

        if not rule:
            return None

        # Montar resposta conforme estado
        state_rule = {
            'uf': uf,
            'ncm': ncm
        }

        if uf == 'SP':
            rbc = rule.get('icms_sp_reducao_bc', '')
            if rbc and rbc.upper() == 'SIM':
                state_rule['tipo'] = 'reducao_bc'
                state_rule['descricao'] = 'Redução de Base de Cálculo ICMS'
                state_rule['base_legal'] = 'RICMS/SP Anexo II Art.3 V'
                state_rule['observacao'] = 'Açúcar cristal/refinado - RBC do ICMS'

        elif uf == 'PE':
            credito = rule.get('icms_pe_credito_presumido', '')
            if credito and credito.isdigit():
                state_rule['tipo'] = 'credito_presumido'
                state_rule['percentual'] = float(credito)
                state_rule['descricao'] = f'Crédito presumido {credito}% sobre saídas'
                state_rule['base_legal'] = 'Lei Estadual PE'
                state_rule['observacao'] = 'Regime substitutivo - não acumula com créditos normais'
            elif 'ISENTO' in credito.upper():
                state_rule['tipo'] = 'isencao'
                state_rule['descricao'] = 'Isenção ICMS'
                state_rule['base_legal'] = 'Lei Estadual PE'
                state_rule['observacao'] = rule.get('observacoes', '')

        return state_rule if len(state_rule) > 2 else None

    def get_all_ncms(self) -> List[str]:
        """
        Retornar lista de todos os NCMs cadastrados

        Returns:
            Lista de códigos NCM
        """
        if not self.is_available():
            return []

        return list(self.rules_cache.keys())

    def get_statistics(self) -> Dict:
        """
        Retornar estatísticas do repositório

        Returns:
            Dict com estatísticas
        """
        if not self.is_available():
            return {
                'disponivel': False,
                'total_regras': 0
            }

        # Contar regras por tipo
        acucar_count = sum(1 for ncm in self.rules_cache.keys() if ncm.startswith('1701'))
        insumos_count = sum(1 for ncm in self.rules_cache.keys() if not ncm.startswith('1701'))

        return {
            'disponivel': True,
            'arquivo': str(self.csv_path),
            'total_regras': len(self.rules_cache),
            'acucar_ncms': acucar_count,
            'insumos_ncms': insumos_count,
            'estados_suportados': ['SP', 'PE']
        }
