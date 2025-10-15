# -*- coding: utf-8 -*-
"""
Column Mapper - Mapeamento Inteligente de Colunas para NF-e

Mapeia colunas de diferentes formatos de CSV para o formato esperado pelo NFeCSVParser.
Suporta variações de nomes, maiúsculas/minúsculas, com/sem acentos.
"""

import re
from typing import Dict, List, Optional, Tuple
import pandas as pd


class ColumnMapper:
    """Mapeador inteligente de colunas para NF-e"""

    # Mapeamento de padrões de colunas
    COLUMN_PATTERNS = {
        # Identificação da NF-e
        'chave_acesso': [
            r'chave.*acesso', r'chave.*nf', r'chave', r'access.*key'
        ],
        'numero_nfe': [
            r'n[uú]mero.*nf', r'num.*nf', r'n[uú]mero$', r'numero$', r'nf.*number'
        ],
        'serie': [
            r's[eé]rie', r'serie', r'series'
        ],
        'data_emissao': [
            r'data.*emiss[aã]o', r'dt.*emiss', r'data.*nf', r'issue.*date', r'emissao'
        ],

        # Emitente
        'cnpj_emitente': [
            r'cnpj.*emit', r'cpf.*cnpj.*emit', r'emit.*cnpj'
        ],
        'razao_social_emitente': [
            r'raz[aã]o.*emit', r'nome.*emit', r'emit.*raz[aã]o', r'razao.*social.*emit'
        ],
        'uf_emitente': [
            r'uf.*emit', r'emit.*uf', r'estado.*emit'
        ],

        # Destinatário
        'cnpj_destinatario': [
            r'cnpj.*dest', r'cpf.*cnpj.*dest', r'dest.*cnpj'
        ],
        'razao_social_destinatario': [
            r'raz[aã]o.*dest', r'nome.*dest', r'dest.*raz[aã]o', r'razao.*social.*dest'
        ],
        'uf_destinatario': [
            r'uf.*dest', r'dest.*uf', r'estado.*dest'
        ],

        # Item
        'numero_item': [
            r'n[uú]mero.*item', r'num.*item', r'item.*num', r'seq.*item'
        ],
        'codigo_produto': [
            r'c[oó]d.*prod', r'prod.*code', r'c[oó]digo.*produto'
        ],
        'descricao': [
            r'descri[cç][aã]o', r'descricao.*prod', r'prod.*desc', r'description'
        ],
        'ncm': [
            r'^ncm$', r'ncm.*prod', r'c[oó]d.*ncm'
        ],
        'cfop': [
            r'^cfop$', r'c[oó]d.*cfop', r'nat.*oper'
        ],
        'unidade': [
            r'unid', r'un.*com', r'unit'
        ],
        'quantidade': [
            r'qtd', r'quant', r'qty'
        ],
        'valor_unitario': [
            r'v.*unit', r'valor.*unit', r'pre[cç]o.*unit', r'unit.*price'
        ],
        'valor_total': [
            r'v.*total.*item', r'valor.*total.*item', r'total.*item', r'valor.*nota.*fiscal'
        ],

        # PIS
        'pis_cst': [
            r'pis.*cst', r'cst.*pis', r'sit.*trib.*pis'
        ],
        'pis_aliquota': [
            r'pis.*al[ií]q', r'al[ií]q.*pis', r'%.*pis'
        ],
        'pis_valor': [
            r'pis.*val', r'val.*pis', r'v.*pis'
        ],

        # COFINS
        'cofins_cst': [
            r'cofins.*cst', r'cst.*cofins', r'sit.*trib.*cofins'
        ],
        'cofins_aliquota': [
            r'cofins.*al[ií]q', r'al[ií]q.*cofins', r'%.*cofins'
        ],
        'cofins_valor': [
            r'cofins.*val', r'val.*cofins', r'v.*cofins'
        ],

        # ICMS (opcional)
        'icms_cst': [
            r'icms.*cst', r'cst.*icms', r'sit.*trib.*icms'
        ],
        'icms_aliquota': [
            r'icms.*al[ií]q', r'al[ií]q.*icms', r'%.*icms'
        ],
        'icms_valor': [
            r'icms.*val', r'val.*icms', r'v.*icms'
        ],

        # Natureza da operação
        'natureza_operacao': [
            r'natureza.*opera', r'nat.*oper', r'tipo.*opera'
        ],
    }

    @staticmethod
    def normalize_column_name(col: str) -> str:
        """Normalizar nome de coluna para comparação"""
        # Remover acentos, converter para minúsculas, remover espaços extras
        col = str(col).lower().strip()
        # Remover acentos comuns
        col = col.replace('ã', 'a').replace('á', 'a').replace('à', 'a')
        col = col.replace('é', 'e').replace('ê', 'e')
        col = col.replace('í', 'i')
        col = col.replace('ó', 'o').replace('ô', 'o')
        col = col.replace('ú', 'u').replace('ü', 'u')
        col = col.replace('ç', 'c')
        # Substituir espaços e caracteres especiais por underscore
        col = re.sub(r'[^\w]+', '_', col)
        # Remover underscores múltiplos
        col = re.sub(r'_+', '_', col).strip('_')
        return col

    @classmethod
    def map_columns(cls, df: pd.DataFrame) -> Tuple[Dict[str, str], List[str]]:
        """
        Mapear colunas do DataFrame para formato esperado

        Args:
            df: DataFrame com dados originais

        Returns:
            Tupla com (mapeamento, colunas_faltantes)
            - mapeamento: dict {nome_esperado: nome_original}
            - colunas_faltantes: list de colunas não encontradas
        """
        mapping = {}
        missing = []

        # Normalizar nomes das colunas originais
        original_columns = df.columns.tolist()
        normalized_cols = {cls.normalize_column_name(col): col for col in original_columns}

        # Tentar mapear cada coluna esperada
        for target_col, patterns in cls.COLUMN_PATTERNS.items():
            found = False

            # Tentar cada padrão
            for pattern in patterns:
                for norm_col, orig_col in normalized_cols.items():
                    if re.search(pattern, norm_col, re.IGNORECASE):
                        mapping[target_col] = orig_col
                        found = True
                        break

                if found:
                    break

            if not found:
                missing.append(target_col)

        return mapping, missing

    @classmethod
    def apply_mapping(cls, df: pd.DataFrame, mapping: Dict[str, str]) -> pd.DataFrame:
        """
        Aplicar mapeamento ao DataFrame

        Args:
            df: DataFrame original
            mapping: Dicionário de mapeamento {novo_nome: nome_original}

        Returns:
            DataFrame com colunas renomeadas
        """
        # Criar cópia do DataFrame
        df_mapped = df.copy()

        # Renomear colunas conforme mapeamento
        reverse_mapping = {v: k for k, v in mapping.items()}
        df_mapped = df_mapped.rename(columns=reverse_mapping)

        return df_mapped

    @classmethod
    def get_mapping_report(cls, mapping: Dict[str, str], missing: List[str]) -> str:
        """
        Gerar relatório de mapeamento

        Args:
            mapping: Dicionário de mapeamento
            missing: Lista de colunas faltantes

        Returns:
            String com relatório formatado
        """
        report = "📋 **Relatório de Mapeamento de Colunas**\n\n"

        if mapping:
            report += f"✅ **{len(mapping)} colunas mapeadas:**\n\n"
            for target, original in sorted(mapping.items()):
                report += f"- `{original}` → `{target}`\n"

        if missing:
            report += f"\n⚠️ **{len(missing)} colunas não encontradas:**\n\n"
            for col in sorted(missing):
                report += f"- `{col}`\n"

            report += "\n💡 **Dica:** Algumas validações podem não funcionar sem essas colunas.\n"

        return report

    @classmethod
    def is_nfe_complete(cls, mapping: Dict[str, str]) -> bool:
        """
        Verificar se mapeamento contém colunas mínimas para validação NF-e

        Args:
            mapping: Dicionário de mapeamento

        Returns:
            True se tem colunas mínimas, False caso contrário
        """
        # Colunas mínimas obrigatórias
        required = {
            'chave_acesso', 'numero_nfe', 'data_emissao',
            'cnpj_emitente', 'cnpj_destinatario'
        }

        mapped_cols = set(mapping.keys())
        return required.issubset(mapped_cols)

    @classmethod
    def get_validation_capabilities(cls, mapping: Dict[str, str]) -> Dict[str, bool]:
        """
        Verificar quais validações são possíveis com as colunas disponíveis

        Args:
            mapping: Dicionário de mapeamento

        Returns:
            Dict com capacidades de validação
        """
        mapped_cols = set(mapping.keys())

        capabilities = {
            'identificacao': {'chave_acesso', 'numero_nfe'}.issubset(mapped_cols),
            'partes': {'cnpj_emitente', 'cnpj_destinatario'}.issubset(mapped_cols),
            'ncm': 'ncm' in mapped_cols,
            'cfop': 'cfop' in mapped_cols,
            'pis_cofins': {'pis_cst', 'pis_aliquota', 'cofins_cst', 'cofins_aliquota'}.issubset(mapped_cols),
            'valores': {'valor_total'}.issubset(mapped_cols),
            'itens_completos': {'numero_item', 'descricao', 'quantidade', 'valor_unitario'}.issubset(mapped_cols),
        }

        return capabilities
