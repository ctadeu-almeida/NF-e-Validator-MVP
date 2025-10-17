# -*- coding: utf-8 -*-
"""
Gerador de Relatórios de Auditoria - MVP Sucroalcooleiro

Formatos:
- JSON estruturado (para integração)
- Markdown (para leitura humana)

Incluir:
- Economia potencial
- Citações legais com versão
- Severidade dos erros
- Recomendações de ação
"""

import json
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
from decimal import Decimal

from ...domain.entities.nfe_entity import (
    NFeEntity, AuditReport, ValidationError, Severity
)


class NumpyEncoder(json.JSONEncoder):
    """Encoder JSON que converte tipos numpy/pandas para tipos Python nativos"""
    def default(self, obj):
        if isinstance(obj, (np.integer, np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32)):
            return float(obj)
        elif isinstance(obj, (np.ndarray,)):
            return obj.tolist()
        elif isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


class ReportGenerator:
    """Gerador de relatórios de auditoria fiscal"""

    def __init__(self, version: str = "1.0.0-mvp"):
        self.version = version

    def generate_json_report(self, nfe: NFeEntity) -> Dict:
        """
        Gerar relatório JSON estruturado

        Args:
            nfe: NF-e validada

        Returns:
            Dict com relatório completo
        """
        # Criar relatório de auditoria
        audit_report = AuditReport(nfe=nfe)
        audit_report.generate_summary()

        # Estruturar JSON
        report = {
            'metadata': {
                'report_version': self.version,
                'generated_at': datetime.now().isoformat(),
                'validator': 'NF-e Validator MVP - Setor Sucroalcooleiro'
            },
            'nfe_info': {
                'chave_acesso': str(nfe.chave_acesso),
                'numero': str(nfe.numero),
                'serie': str(nfe.serie),
                'data_emissao': nfe.data_emissao.isoformat(),
                'emitente': {
                    'cnpj': str(nfe.emitente.cnpj),
                    'razao_social': str(nfe.emitente.razao_social),
                    'uf': str(nfe.emitente.uf)
                },
                'destinatario': {
                    'cnpj': str(nfe.destinatario.cnpj),
                    'razao_social': str(nfe.destinatario.razao_social),
                    'uf': str(nfe.destinatario.uf)
                },
                'totais': {
                    'valor_produtos': float(nfe.totais.valor_produtos) if nfe.totais.valor_produtos else 0.0,
                    'valor_total_nota': float(nfe.totais.valor_total_nota) if nfe.totais.valor_total_nota else 0.0,
                    'valor_pis': float(nfe.totais.valor_pis) if nfe.totais.valor_pis else 0.0,
                    'valor_cofins': float(nfe.totais.valor_cofins) if nfe.totais.valor_cofins else 0.0,
                },
                'operacao': {
                    'cfop': str(nfe.cfop_nota) if nfe.cfop_nota else '',
                    'natureza': str(nfe.natureza_operacao) if nfe.natureza_operacao else '',
                    'tipo': 'INTERESTADUAL' if nfe.is_interstate() else 'INTERNA',
                    'uf_origem': str(nfe.uf_origem) if nfe.uf_origem else '',
                    'uf_destino': str(nfe.uf_destino) if nfe.uf_destino else ''
                }
            },
            'validation_summary': {
                'status': str(nfe.validation_status.value),
                'total_errors': int(audit_report.total_errors),
                'by_severity': {
                    'critical': int(audit_report.critical_count),
                    'error': int(audit_report.error_count),
                    'warning': int(audit_report.warning_count),
                    'info': int(audit_report.info_count)
                },
                'financial_impact': {
                    'total': float(audit_report.total_financial_impact) if audit_report.total_financial_impact else 0.0,
                    'currency': 'BRL',
                    'description': 'Economia potencial se erros forem corrigidos'
                }
            },
            'errors': self._format_errors_json(nfe.validation_errors),
            'errors_by_type': self._group_errors_by_type(nfe.validation_errors),
            'items_analysis': self._analyze_items_json(nfe),
            'recommendations': audit_report.recommendations,
            'legal_references': self._extract_legal_references(nfe.validation_errors)
        }

        return report

    def generate_markdown_report(self, nfe: NFeEntity) -> str:
        """
        Gerar relatório Markdown para leitura humana

        Args:
            nfe: NF-e validada

        Returns:
            String Markdown formatada
        """
        # Criar relatório de auditoria
        audit_report = AuditReport(nfe=nfe)
        audit_report.generate_summary()

        md = []

        # Cabeçalho
        md.append("# 📋 RELATÓRIO DE AUDITORIA FISCAL")
        md.append(f"**NF-e Validator MVP** - Setor Sucroalcooleiro  ")
        md.append(f"*Versão: {self.version}*  ")
        md.append(f"*Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}*\n")
        md.append("---\n")

        # Informações da NF-e
        md.append("## 📄 Informações da NF-e\n")
        md.append(f"**Chave de Acesso:** `{nfe.chave_acesso}`  ")
        md.append(f"**Número:** {nfe.numero} | **Série:** {nfe.serie}  ")
        md.append(f"**Data de Emissão:** {nfe.data_emissao.strftime('%d/%m/%Y')}\n")

        md.append("### Emitente")
        md.append(f"- **CNPJ:** {self._format_cnpj(nfe.emitente.cnpj)}")
        md.append(f"- **Razão Social:** {nfe.emitente.razao_social}")
        md.append(f"- **UF:** {nfe.emitente.uf}\n")

        md.append("### Destinatário")
        md.append(f"- **CNPJ:** {self._format_cnpj(nfe.destinatario.cnpj)}")
        md.append(f"- **Razão Social:** {nfe.destinatario.razao_social}")
        md.append(f"- **UF:** {nfe.destinatario.uf}\n")

        md.append("### Operação")
        operacao_tipo = "🌍 INTERESTADUAL" if nfe.is_interstate() else "🏠 INTERNA"
        md.append(f"- **Tipo:** {operacao_tipo} ({nfe.uf_origem} → {nfe.uf_destino})")
        md.append(f"- **CFOP:** {nfe.cfop_nota}")
        md.append(f"- **Natureza:** {nfe.natureza_operacao}\n")

        md.append("---\n")

        # Resumo da Validação
        md.append("## 📊 RESUMO DA VALIDAÇÃO\n")

        # Status geral
        status_icon = "✅" if audit_report.total_errors == 0 else "❌"
        md.append(f"### Status: {status_icon} {nfe.validation_status.value}\n")

        md.append(f"**Total de Problemas Encontrados:** {audit_report.total_errors}\n")

        if audit_report.total_errors > 0:
            md.append("| Severidade | Quantidade |")
            md.append("|------------|------------|")
            md.append(f"| 🔴 **CRÍTICO** | {audit_report.critical_count} |")
            md.append(f"| 🟠 **ERRO** | {audit_report.error_count} |")
            md.append(f"| 🟡 **AVISO** | {audit_report.warning_count} |")
            md.append(f"| 🔵 **INFO** | {audit_report.info_count} |")
            md.append("")

        # Impacto Financeiro
        if audit_report.total_financial_impact > 0:
            md.append("### 💰 IMPACTO FINANCEIRO\n")
            md.append(f"**Economia Potencial:** R$ {audit_report.total_financial_impact:,.2f}\n")
            md.append("*Valor total que pode ser economizado corrigindo os erros identificados.*\n")

        md.append("---\n")

        # Detalhamento dos Erros
        if nfe.validation_errors:
            md.append("## 🔍 DETALHAMENTO DOS ERROS\n")

            # Agrupar por severidade
            errors_by_severity = {
                Severity.CRITICAL: [],
                Severity.ERROR: [],
                Severity.WARNING: [],
                Severity.INFO: []
            }

            for error in nfe.validation_errors:
                errors_by_severity[error.severity].append(error)

            # Exibir por severidade
            severity_labels = {
                Severity.CRITICAL: ("🔴 ERROS CRÍTICOS", "Requer ação IMEDIATA"),
                Severity.ERROR: ("🟠 ERROS", "Requer correção"),
                Severity.WARNING: ("🟡 AVISOS", "Verificação recomendada"),
                Severity.INFO: ("🔵 INFORMAÇÕES", "Pontos de atenção")
            }

            for severity, (label, description) in severity_labels.items():
                errors = errors_by_severity[severity]
                if errors:
                    md.append(f"### {label}")
                    md.append(f"*{description}*\n")

                    for i, error in enumerate(errors, 1):
                        md.append(f"#### {i}. {error.message}\n")

                        md.append(f"**Código:** `{error.code}`  ")
                        md.append(f"**Campo:** `{error.field}`  ")

                        if error.item_numero:
                            md.append(f"**Item:** #{error.item_numero}  ")

                        if error.actual_value:
                            md.append(f"**Valor Atual:** `{error.actual_value}`  ")
                        if error.expected_value:
                            md.append(f"**Valor Esperado:** `{error.expected_value}`  ")

                        if error.financial_impact:
                            md.append(f"**💵 Impacto:** R$ {error.financial_impact:,.2f}  ")

                        # Base Legal
                        md.append(f"\n📚 **Base Legal:** {error.legal_reference}")
                        if error.legal_article:
                            md.append(f" - {error.legal_article}")

                        # Sugestão de correção
                        if error.suggestion:
                            md.append(f"\n💡 **Sugestão:** {error.suggestion}")

                        if error.can_auto_correct and error.corrected_value:
                            md.append(f"\n✨ **Correção Automática Disponível:** `{error.corrected_value}`")

                        md.append("\n")

            md.append("---\n")

        # Análise por Item
        md.append("## 📦 ANÁLISE POR ITEM\n")

        for item in nfe.items:
            md.append(f"### Item {item.numero_item}: {item.descricao}\n")

            md.append(f"- **Código:** {item.codigo_produto}")
            md.append(f"- **NCM:** {self._format_ncm(item.ncm)}")
            md.append(f"- **CFOP:** {item.cfop}")
            md.append(f"- **Quantidade:** {item.quantidade} {item.unidade}")
            md.append(f"- **Valor Unitário:** R$ {item.valor_unitario:,.2f}")
            md.append(f"- **Valor Total:** R$ {item.valor_total:,.2f}\n")

            # Tributação
            md.append("**Tributação:**")
            md.append(f"- PIS: CST {item.impostos.pis_cst} | {item.impostos.pis_aliquota}% | R$ {item.impostos.pis_valor:,.2f}")
            md.append(f"- COFINS: CST {item.impostos.cofins_cst} | {item.impostos.cofins_aliquota}% | R$ {item.impostos.cofins_valor:,.2f}")

            # Erros do item
            item_errors = [e for e in nfe.validation_errors if e.item_numero == item.numero_item]
            if item_errors:
                md.append(f"\n**⚠️ {len(item_errors)} problema(s) encontrado(s) neste item**")

            md.append("")

        md.append("---\n")

        # Recomendações
        if audit_report.recommendations:
            md.append("## 💡 RECOMENDAÇÕES\n")

            for i, rec in enumerate(audit_report.recommendations, 1):
                md.append(f"{i}. {rec}")

            md.append("")

        # Totais da Nota
        md.append("---\n")
        md.append("## 💰 TOTAIS DA NF-e\n")

        md.append("| Descrição | Valor |")
        md.append("|-----------|------:|")
        md.append(f"| Valor dos Produtos | R$ {nfe.totais.valor_produtos:,.2f} |")
        md.append(f"| PIS | R$ {nfe.totais.valor_pis:,.2f} |")
        md.append(f"| COFINS | R$ {nfe.totais.valor_cofins:,.2f} |")
        md.append(f"| ICMS | R$ {nfe.totais.valor_icms:,.2f} |")
        md.append(f"| **Valor Total da Nota** | **R$ {nfe.totais.valor_total_nota:,.2f}** |")

        md.append("")

        # Rodapé
        md.append("---\n")
        md.append("## 📌 Notas\n")
        md.append("- Este relatório foi gerado automaticamente pelo **NF-e Validator MVP**")
        md.append("- Validações baseadas na legislação federal vigente")
        md.append("- Estados validados neste MVP: **SP** e **PE**")
        md.append("- Setor: **Sucroalcooleiro** (Açúcar)")
        md.append(f"- Versão do validador: `{self.version}`")
        md.append("\n---")
        md.append("\n*Desenvolvido com ❤️ para o setor sucroalcooleiro brasileiro*")

        return "\n".join(md)

    def _format_errors_json(self, errors: List[ValidationError]) -> List[Dict]:
        """Formatar erros para JSON"""
        return [
            {
                'code': str(e.code) if e.code else '',
                'field': str(e.field) if e.field else '',
                'message': str(e.message) if e.message else '',
                'severity': str(e.severity.value) if e.severity else '',
                'item_numero': int(e.item_numero) if e.item_numero else None,
                'actual_value': str(e.actual_value) if e.actual_value else None,
                'expected_value': str(e.expected_value) if e.expected_value else None,
                'suggestion': str(e.suggestion) if e.suggestion else None,
                'legal_reference': str(e.legal_reference) if e.legal_reference else None,
                'legal_article': str(e.legal_article) if e.legal_article else None,
                'financial_impact': float(e.financial_impact) if e.financial_impact else 0.0,
                'can_auto_correct': bool(e.can_auto_correct),
                'corrected_value': str(e.corrected_value) if e.corrected_value else None
            }
            for e in errors
        ]

    def _group_errors_by_type(self, errors: List[ValidationError]) -> Dict[str, int]:
        """Agrupar erros por tipo"""
        types = {}
        for error in errors:
            error_type = error.code.split('_')[0]
            types[error_type] = types.get(error_type, 0) + 1
        return types

    def _analyze_items_json(self, nfe: NFeEntity) -> List[Dict]:
        """Analisar itens para JSON"""
        return [
            {
                'numero_item': int(item.numero_item) if item.numero_item else 0,
                'descricao': str(item.descricao) if item.descricao else '',
                'ncm': str(item.ncm) if item.ncm else '',
                'cfop': str(item.cfop) if item.cfop else '',
                'valor_total': float(item.valor_total) if item.valor_total else 0.0,
                'errors_count': len([e for e in nfe.validation_errors if e.item_numero == item.numero_item]),
                'is_sugar': bool(nfe.is_sugar_product(item))
            }
            for item in nfe.items
        ]

    def _extract_legal_references(self, errors: List[ValidationError]) -> List[Dict]:
        """Extrair referências legais únicas"""
        refs = {}
        for error in errors:
            if error.legal_reference and error.legal_reference not in refs:
                refs[error.legal_reference] = {
                    'reference': error.legal_reference,
                    'article': error.legal_article,
                    'occurrences': 1
                }
            elif error.legal_reference:
                refs[error.legal_reference]['occurrences'] += 1

        return list(refs.values())

    def _format_cnpj(self, cnpj: str) -> str:
        """Formatar CNPJ: 12.345.678/0001-90"""
        if len(cnpj) == 14:
            return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"
        return cnpj

    def _format_ncm(self, ncm: str) -> str:
        """Formatar NCM: 1701.99.00"""
        if len(ncm) == 8:
            return f"{ncm[:4]}.{ncm[4:6]}.{ncm[6:]}"
        return ncm

    def save_json_report(self, nfe: NFeEntity, output_path: str):
        """Salvar relatório JSON em arquivo"""
        report = self.generate_json_report(nfe)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"✅ Relatório JSON salvo: {output_path}")

    def save_markdown_report(self, nfe: NFeEntity, output_path: str):
        """Salvar relatório Markdown em arquivo"""
        report = self.generate_markdown_report(nfe)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"✅ Relatório Markdown salvo: {output_path}")
