# -*- coding: utf-8 -*-
"""
CSV Parser para NF-e - MVP Sucroalcooleiro

Especificação:
- Colunas obrigatórias
- Normalização de NCM (8 dígitos) e CFOP (4 dígitos)
- Conversão de valores decimais
- Validação de formato
"""

import pandas as pd
from typing import List, Dict, Optional
from decimal import Decimal
from datetime import datetime
import re

from ...domain.entities.nfe_entity import (
    NFeEntity, NFeItem, Empresa, ImpostoItem, TotaisNFe,
    TipoOperacao, ValidationStatus, ValidationError, Severity
)


class CSVParserException(Exception):
    """Exceção customizada para erros de parsing"""
    pass


class NFeCSVParser:
    """
    Parser de CSV para NF-e do setor sucroalcooleiro

    Formato esperado do CSV:
    - chave_acesso, numero_nfe, serie, data_emissao
    - cnpj_emitente, razao_social_emitente, uf_emitente
    - cnpj_destinatario, razao_social_destinatario, uf_destinatario
    - numero_item, codigo_produto, descricao, ncm, cfop, unidade
    - quantidade, valor_unitario, valor_total
    - icms_cst, icms_aliquota, icms_valor
    - pis_cst, pis_aliquota, pis_valor
    - cofins_cst, cofins_aliquota, cofins_valor
    """

    # Colunas obrigatórias
    REQUIRED_COLUMNS = [
        # Identificação da NF-e
        'chave_acesso',
        'numero_nfe',
        'serie',
        'data_emissao',

        # Emitente
        'cnpj_emitente',
        'razao_social_emitente',
        'uf_emitente',

        # Destinatário
        'cnpj_destinatario',
        'razao_social_destinatario',
        'uf_destinatario',

        # Item
        'numero_item',
        'codigo_produto',
        'descricao',
        'ncm',
        'cfop',
        'unidade',
        'quantidade',
        'valor_unitario',
        'valor_total',

        # Impostos
        'pis_cst',
        'pis_aliquota',
        'pis_valor',
        'cofins_cst',
        'cofins_aliquota',
        'cofins_valor',
    ]

    # Colunas opcionais
    OPTIONAL_COLUMNS = [
        'icms_cst',
        'icms_base',
        'icms_aliquota',
        'icms_valor',
        'ipi_cst',
        'ipi_aliquota',
        'ipi_valor',
        'valor_desconto',
        'valor_frete',
        'natureza_operacao',
        'tipo_acucar',  # Específico açúcar: cristal, refinado, etc
        'icumsa',  # Índice de cor do açúcar
    ]

    def __init__(self):
        self.parse_errors: List[str] = []

    def parse_csv(self, csv_path: str) -> List[NFeEntity]:
        """
        Parsear arquivo CSV e retornar lista de NF-es

        Args:
            csv_path: Caminho para arquivo CSV

        Returns:
            Lista de NFeEntity parseadas

        Raises:
            CSVParserException: Se houver erro crítico no parsing
        """
        self.parse_errors = []

        try:
            # Ler CSV completo forçando tipos importantes como string
            dtype_spec = {
                'chave_acesso': str,
                'item_pis_cst': str,
                'item_cofins_cst': str,
                'pis_cst': str,
                'cofins_cst': str,
                'item_ncm': str,
                'ncm': str,
                'item_cfop': str,
                'cfop': str
            }
            df = pd.read_csv(csv_path, dtype=dtype_spec, encoding='utf-8', keep_default_na=False, na_values=[''])
        except UnicodeDecodeError:
            # Tentar encoding alternativo
            try:
                dtype_spec = {
                    'chave_acesso': str,
                    'item_pis_cst': str,
                    'item_cofins_cst': str,
                    'pis_cst': str,
                    'cofins_cst': str,
                    'item_ncm': str,
                    'ncm': str,
                    'item_cfop': str,
                    'cfop': str
                }
                df = pd.read_csv(csv_path, dtype=dtype_spec, encoding='latin-1', keep_default_na=False, na_values=[''])
            except Exception as e:
                raise CSVParserException(f"Erro ao ler CSV: {e}")
        except Exception as e:
            raise CSVParserException(f"Erro ao ler CSV: {e}")

        # Normalizar dados PRIMEIRO (inclui mapeamento de colunas)
        df = self._normalize_dataframe(df)

        # DEPOIS validar colunas obrigatórias
        self._validate_columns(df)

        # Agrupar por NF-e (chave_acesso)
        nfes = []
        for chave, group in df.groupby('chave_acesso'):
            try:
                nfe = self._parse_nfe_group(group)
                nfes.append(nfe)
            except Exception as e:
                error_msg = f"Erro ao parsear NF-e {chave}: {e}"
                self.parse_errors.append(error_msg)
                print(f"⚠️ {error_msg}")

        if not nfes and self.parse_errors:
            raise CSVParserException(
                f"Nenhuma NF-e foi parseada com sucesso. Erros: {'; '.join(self.parse_errors)}"
            )

        return nfes

    def _validate_columns(self, df: pd.DataFrame):
        """
        Validar colunas - permite parsing parcial

        Apenas valida se há colunas MÍNIMAS para identificar uma NF-e.
        Validações fiscais serão limitadas conforme colunas disponíveis.
        """
        # Colunas MÍNIMAS absolutas (identificação básica)
        minimum_required = [
            'chave_acesso', 'numero_nfe',
            'cnpj_emitente', 'cnpj_destinatario'
        ]

        missing_minimum = [col for col in minimum_required if col not in df.columns]

        if missing_minimum:
            raise CSVParserException(
                f"Colunas MÍNIMAS ausentes (impossível identificar NF-e): {', '.join(missing_minimum)}"
            )

        # Verificar se há ALGUMA validação fiscal possível
        fiscal_columns = ['ncm', 'cfop', 'pis_cst', 'cofins_cst', 'valor_total']
        has_any_fiscal = any(col in df.columns for col in fiscal_columns)

        if not has_any_fiscal:
            # Não tem dados fiscais - alertar mas não bloquear
            import logging
            logging.warning("⚠️ Nenhuma coluna fiscal encontrada - validações limitadas")

    def _normalize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalizar dados do DataFrame"""
        df = df.copy()

        # Mapear nomes de colunas alternativos
        column_mapping = {
            'numero_nf': 'numero_nfe',
            'emitente_cnpj': 'cnpj_emitente',
            'emitente_razao_social': 'razao_social_emitente',
            'emitente_uf': 'uf_emitente',
            'destinatario_cnpj': 'cnpj_destinatario',
            'destinatario_razao_social': 'razao_social_destinatario',
            'destinatario_uf': 'uf_destinatario',
            'item_numero': 'numero_item',
            'item_codigo': 'codigo_produto',
            'item_descricao': 'descricao',
            'item_ncm': 'ncm',
            'item_cfop': 'cfop',
            'item_unidade': 'unidade',
            'item_quantidade': 'quantidade',
            'item_valor_unitario': 'valor_unitario',
            'item_valor_total': 'valor_total',
            'item_icms_base': 'icms_base',
            'item_icms_aliquota': 'icms_aliquota',
            'item_icms_valor': 'icms_valor',
            'item_ipi_base': 'ipi_base',
            'item_ipi_aliquota': 'ipi_aliquota',
            'item_ipi_valor': 'ipi_valor',
            'item_pis_base': 'pis_base',
            'item_pis_aliquota': 'pis_aliquota',
            'item_pis_valor': 'pis_valor',
            'item_pis_cst': 'pis_cst',
            'item_cofins_base': 'cofins_base',
            'item_cofins_aliquota': 'cofins_aliquota',
            'item_cofins_valor': 'cofins_valor',
            'item_cofins_cst': 'cofins_cst',
        }
        df.rename(columns=column_mapping, inplace=True)

        # Remover colunas duplicadas (manter a primeira)
        df = df.loc[:, ~df.columns.duplicated()]

        # Garantir que chave_acesso seja string pura
        if 'chave_acesso' in df.columns:
            df['chave_acesso'] = df['chave_acesso'].astype(str).str.replace('.0', '', regex=False)

        # Remover espaços em branco
        for col in df.columns:
            try:
                if pd.api.types.is_string_dtype(df[col]) or df[col].dtype == 'object':
                    df[col] = df[col].astype(str).str.strip()
            except:
                pass

        # Normalizar NCM (8 dígitos)
        if 'ncm' in df.columns:
            df['ncm'] = df['ncm'].astype(str).apply(self._normalize_ncm)

        # Normalizar CFOP (4 dígitos)
        if 'cfop' in df.columns:
            df['cfop'] = df['cfop'].astype(str).apply(self._normalize_cfop)

        # Normalizar CNPJ (14 dígitos, apenas números)
        if 'cnpj_emitente' in df.columns:
            df['cnpj_emitente'] = df['cnpj_emitente'].astype(str).apply(self._normalize_cnpj)
        if 'cnpj_destinatario' in df.columns:
            df['cnpj_destinatario'] = df['cnpj_destinatario'].astype(str).apply(self._normalize_cnpj)

        # Normalizar CST PIS/COFINS (2 dígitos)
        if 'pis_cst' in df.columns:
            df['pis_cst'] = df['pis_cst'].astype(str).apply(self._normalize_cst)
        if 'cofins_cst' in df.columns:
            df['cofins_cst'] = df['cofins_cst'].astype(str).apply(self._normalize_cst)

        # Normalizar valores decimais
        decimal_columns = [
            'quantidade', 'valor_unitario', 'valor_total',
            'pis_aliquota', 'pis_valor', 'cofins_aliquota', 'cofins_valor',
            'icms_aliquota', 'icms_valor', 'ipi_aliquota', 'ipi_valor',
            'valor_desconto', 'valor_frete'
        ]

        for col in decimal_columns:
            if col in df.columns:
                df[col] = df[col].astype(str).apply(self._normalize_decimal)

        return df

    def _normalize_ncm(self, ncm: str) -> str:
        """Normalizar NCM para 8 dígitos"""
        if pd.isna(ncm) or not ncm:
            return ''

        # Remover pontos e hífens
        ncm_clean = re.sub(r'[.\-]', '', str(ncm))

        # Garantir 8 dígitos (preencher com zeros à direita se necessário)
        if len(ncm_clean) < 8:
            ncm_clean = ncm_clean.ljust(8, '0')
        elif len(ncm_clean) > 8:
            ncm_clean = ncm_clean[:8]

        return ncm_clean

    def _normalize_cfop(self, cfop: str) -> str:
        """Normalizar CFOP para 4 dígitos"""
        if pd.isna(cfop) or not cfop:
            return ''

        # Remover pontos
        cfop_clean = re.sub(r'[.]', '', str(cfop))

        # Garantir 4 dígitos
        if len(cfop_clean) < 4:
            cfop_clean = cfop_clean.zfill(4)
        elif len(cfop_clean) > 4:
            cfop_clean = cfop_clean[:4]

        return cfop_clean

    def _normalize_cnpj(self, cnpj: str) -> str:
        """Normalizar CNPJ para 14 dígitos"""
        if pd.isna(cnpj) or not cnpj:
            return ''

        # Remover formatação (pontos, hífens, barras)
        cnpj_clean = re.sub(r'[.\-/]', '', str(cnpj))

        # Garantir 14 dígitos
        if len(cnpj_clean) < 14:
            cnpj_clean = cnpj_clean.zfill(14)

        return cnpj_clean

    def _normalize_cst(self, cst: str) -> str:
        """Normalizar CST para 2 dígitos"""
        if pd.isna(cst) or not cst or cst == '':
            return ''

        # Remover espaços
        cst_clean = str(cst).strip()

        # Garantir 2 dígitos (preencher com zero à esquerda)
        if len(cst_clean) == 1 and cst_clean.isdigit():
            cst_clean = cst_clean.zfill(2)
        elif len(cst_clean) > 2:
            cst_clean = cst_clean[:2]

        return cst_clean

    def _normalize_decimal(self, value: str) -> str:
        """Normalizar valor decimal"""
        if pd.isna(value) or not value:
            return '0.00'

        # Remover espaços e trocar vírgula por ponto
        value_clean = str(value).strip().replace(',', '.')

        try:
            # Converter para Decimal e retornar string formatada
            decimal_value = Decimal(value_clean)
            return str(decimal_value)
        except:
            return '0.00'

    def _parse_nfe_group(self, group: pd.DataFrame) -> NFeEntity:
        """Parsear grupo de linhas que representam uma NF-e"""
        # Pegar primeira linha para dados da nota
        first_row = group.iloc[0]

        # Parsear emitente
        emitente = Empresa(
            cnpj=first_row['cnpj_emitente'],
            razao_social=first_row['razao_social_emitente'],
            uf=first_row['uf_emitente'],
            nome_fantasia=first_row.get('nome_fantasia_emitente', None),
            ie=first_row.get('ie_emitente', None)
        )

        # Parsear destinatário
        destinatario = Empresa(
            cnpj=first_row['cnpj_destinatario'],
            razao_social=first_row['razao_social_destinatario'],
            uf=first_row['uf_destinatario'],
            nome_fantasia=first_row.get('nome_fantasia_destinatario', None),
            ie=first_row.get('ie_destinatario', None)
        )

        # Parsear itens
        items = []
        for _, row in group.iterrows():
            item = self._parse_item(row)
            items.append(item)

        # Calcular totais
        totais = self._calculate_totals(items)

        # Determinar CFOP predominante (usar do primeiro item)
        cfop_nota = items[0].cfop if items else ''

        # Parsear data de emissão
        data_emissao = self._parse_date(first_row['data_emissao'])

        # Determinar natureza da operação
        natureza = first_row.get('natureza_operacao', '')
        if pd.isna(natureza) or not natureza or natureza == 'nan':
            natureza = 'Venda de mercadoria'

        # Criar entidade NF-e
        nfe = NFeEntity(
            chave_acesso=str(first_row['chave_acesso']),
            numero=str(first_row['numero_nfe']),
            serie=str(first_row['serie']),
            data_emissao=data_emissao,
            emitente=emitente,
            destinatario=destinatario,
            items=items,
            totais=totais,
            cfop_nota=cfop_nota,
            natureza_operacao=natureza,
            uf_origem=emitente.uf,
            uf_destino=destinatario.uf,
            validation_status=ValidationStatus.PENDING,
            csv_source={
                'file': 'uploaded_csv',
                'rows': len(group)
            }
        )

        return nfe

    def _parse_item(self, row: pd.Series) -> NFeItem:
        """Parsear item da NF-e - permite dados parciais"""

        # Helper para conversão segura de valores
        def safe_str(val, default=''):
            """Converter para string, tratando NaN"""
            if pd.isna(val):
                return default
            return str(val).strip()

        def safe_decimal(val, default='0'):
            """Converter para Decimal, tratando NaN"""
            if pd.isna(val):
                return Decimal(default)
            try:
                return Decimal(str(val).replace(',', '.'))
            except:
                return Decimal(default)

        def safe_int(val, default=1):
            """Converter para int, tratando NaN"""
            if pd.isna(val):
                return default
            try:
                return int(float(val))
            except:
                return default

        # Parsear impostos (valores padrão se não disponíveis)
        impostos = ImpostoItem(
            # ICMS
            icms_cst=safe_str(row.get('icms_cst', '')),
            icms_base=safe_decimal(row.get('icms_base', '0')),
            icms_aliquota=safe_decimal(row.get('icms_aliquota', '0')),
            icms_valor=safe_decimal(row.get('icms_valor', '0')),

            # IPI
            ipi_cst=safe_str(row.get('ipi_cst', '')),
            ipi_base=safe_decimal(row.get('ipi_base', '0')),
            ipi_aliquota=safe_decimal(row.get('ipi_aliquota', '0')),
            ipi_valor=safe_decimal(row.get('ipi_valor', '0')),

            # PIS (permite ausência)
            pis_cst=safe_str(row.get('pis_cst', '')),
            pis_base=safe_decimal(row.get('pis_base', row.get('valor_total', '0'))),
            pis_aliquota=safe_decimal(row.get('pis_aliquota', '0')),
            pis_valor=safe_decimal(row.get('pis_valor', '0')),

            # COFINS (permite ausência)
            cofins_cst=safe_str(row.get('cofins_cst', '')),
            cofins_base=safe_decimal(row.get('cofins_base', row.get('valor_total', '0'))),
            cofins_aliquota=safe_decimal(row.get('cofins_aliquota', '0')),
            cofins_valor=safe_decimal(row.get('cofins_valor', '0')),
        )

        # Criar item (valores padrão se ausentes)
        item = NFeItem(
            numero_item=safe_int(row.get('numero_item', 1)),
            codigo_produto=safe_str(row.get('codigo_produto', '')),
            descricao=safe_str(row.get('descricao', '')),
            ncm=safe_str(row.get('ncm', '')),
            cfop=safe_str(row.get('cfop', '')),
            unidade=safe_str(row.get('unidade', '')),
            quantidade=safe_decimal(row.get('quantidade', '0')),
            valor_unitario=safe_decimal(row.get('valor_unitario', '0')),
            valor_total=safe_decimal(row.get('valor_total', '0')),
            valor_desconto=safe_decimal(row.get('valor_desconto', '0')),
            valor_frete=safe_decimal(row.get('valor_frete', '0')),
            impostos=impostos,
            tipo_acucar=safe_str(row.get('tipo_acucar', None)) if row.get('tipo_acucar') else None,
            icumsa=safe_str(row.get('icumsa', None)) if row.get('icumsa') else None,
        )

        return item

    def _calculate_totals(self, items: List[NFeItem]) -> TotaisNFe:
        """Calcular totais da NF-e baseado nos itens"""
        totais = TotaisNFe()

        # Somar valores
        totais.valor_produtos = sum(item.valor_total for item in items)
        totais.valor_desconto = sum(item.valor_desconto for item in items)
        totais.valor_frete = sum(item.valor_frete for item in items)

        # Somar impostos
        totais.valor_icms = sum(item.impostos.icms_valor for item in items)
        totais.valor_ipi = sum(item.impostos.ipi_valor for item in items)
        totais.valor_pis = sum(item.impostos.pis_valor for item in items)
        totais.valor_cofins = sum(item.impostos.cofins_valor for item in items)

        # Calcular base de cálculo ICMS (simplificado)
        totais.base_calculo_icms = totais.valor_produtos

        # Calcular valor total
        totais.valor_total_nota = (
            totais.valor_produtos +
            totais.valor_frete +
            totais.valor_seguro +
            totais.valor_outras_despesas -
            totais.valor_desconto
        )

        return totais

    def _parse_date(self, date_str: str) -> datetime:
        """Parsear data em diferentes formatos"""
        if pd.isna(date_str) or not date_str:
            return datetime.now()

        # Formatos comuns
        date_formats = [
            '%Y-%m-%d',
            '%d/%m/%Y',
            '%d-%m-%Y',
            '%Y/%m/%d',
            '%Y%m%d',
        ]

        for fmt in date_formats:
            try:
                return datetime.strptime(str(date_str), fmt)
            except ValueError:
                continue

        # Se nenhum formato funcionou, retornar data atual
        self.parse_errors.append(f"Data inválida: {date_str}, usando data atual")
        return datetime.now()

    def get_parse_errors(self) -> List[str]:
        """Retornar lista de erros de parsing"""
        return self.parse_errors

    def validate_csv_structure(self, csv_path: str) -> Dict[str, any]:
        """
        Validar estrutura do CSV antes do parsing completo

        Returns:
            Dict com status da validação
        """
        try:
            df = pd.read_csv(csv_path, dtype=str, nrows=5)
        except Exception as e:
            return {
                'valid': False,
                'error': f'Erro ao ler CSV: {e}',
                'missing_columns': [],
                'extra_columns': []
            }

        # Verificar colunas
        missing_cols = [col for col in self.REQUIRED_COLUMNS if col not in df.columns]
        extra_cols = [col for col in df.columns if col not in self.REQUIRED_COLUMNS + self.OPTIONAL_COLUMNS]

        return {
            'valid': len(missing_cols) == 0,
            'missing_columns': missing_cols,
            'extra_columns': extra_cols,
            'total_columns': len(df.columns),
            'sample_rows': len(df),
            'columns_found': list(df.columns)
        }


def create_csv_template(output_path: str):
    """
    Criar template de CSV para facilitar preenchimento

    Args:
        output_path: Caminho para salvar template
    """
    template_data = {
        # Identificação
        'chave_acesso': ['44230512345678901234567890123456789012345678'],
        'numero_nfe': ['000001'],
        'serie': ['1'],
        'data_emissao': ['2023-05-15'],

        # Emitente
        'cnpj_emitente': ['12345678000190'],
        'razao_social_emitente': ['USINA AÇÚCAR LTDA'],
        'uf_emitente': ['SP'],

        # Destinatário
        'cnpj_destinatario': ['98765432000180'],
        'razao_social_destinatario': ['DISTRIBUIDORA ABC LTDA'],
        'uf_destinatario': ['PE'],

        # Item
        'numero_item': ['1'],
        'codigo_produto': ['ACUCAR-CRISTAL-50KG'],
        'descricao': ['AÇÚCAR CRISTAL 50KG'],
        'ncm': ['17019900'],
        'cfop': ['6101'],
        'unidade': ['SC'],
        'quantidade': ['1000'],
        'valor_unitario': ['85.50'],
        'valor_total': ['85500.00'],

        # Impostos
        'icms_cst': ['00'],
        'icms_aliquota': ['18.00'],
        'icms_valor': ['15390.00'],
        'pis_cst': ['01'],
        'pis_aliquota': ['1.65'],
        'pis_valor': ['1410.75'],
        'cofins_cst': ['01'],
        'cofins_aliquota': ['7.60'],
        'cofins_valor': ['6498.00'],

        # Opcionais
        'tipo_acucar': ['cristal'],
        'icumsa': ['150'],
    }

    df = pd.DataFrame(template_data)
    df.to_csv(output_path, index=False, encoding='utf-8')
    print(f"✅ Template CSV criado: {output_path}")
