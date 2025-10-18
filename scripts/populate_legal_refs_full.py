#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Popular Referências Legais Completas
Versão compatível com schema legal_refs

Popula tabela legal_refs com 19+ referências fiscais brasileiras
"""

import sqlite3
import json
from pathlib import Path


def populate_legal_refs_full():
    """Popular referências legais completas"""

    # Conectar ao database
    project_root = Path(__file__).parent.parent
    db_path = project_root / "src" / "database" / "rules.db"

    print(f"[*] Conectando a: {db_path}")
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Limpar referências existentes (manter apenas as 5 básicas ou substituir todas)
    print("[*] Limpando referências antigas...")
    cursor.execute('DELETE FROM legal_refs')

    # Referências legais completas
    references = [
        # =====================================================
        # LEGISLAÇÃO FEDERAL - PIS/COFINS
        # =====================================================
        {
            'code': 'LEI_10925_2004',
            'ref_type': 'LEI',
            'number': '10.925',
            'year': 2004,
            'title': 'Lei 10.925/2004 - Alíquota Zero Açúcar',
            'summary': 'Reduz as alíquotas de PIS/PASEP e COFINS para insumos agropecuários. Art. 1º X: Alíquota Zero para açúcar. Art. 8º: Suspensão para insumos destinados à atividade agropecuária.',
            'issuing_body': 'RECEITA_FEDERAL',
            'scope': 'FEDERAL',
            'applicable_states': None,
            'full_text': None,
            'url': 'http://www.planalto.gov.br/ccivil_03/_ato2004-2006/2004/lei/l10.925.htm',
            'relevant_articles': json.dumps({
                'Art. 1º X': 'Alíquota Zero para açúcar NCM 1701',
                'Art. 8º': 'Suspensão PIS/COFINS para insumos agrícolas'
            }),
            'affects_taxes': json.dumps(['PIS', 'COFINS']),
            'published_date': '2004-07-23',
            'effective_date': '2004-07-23',
            'revoked_date': None,
            'version': '1.0.0',
            'notes': 'Principal legislação para setor sucroalcooleiro. Aplicável a açúcar de cana (NCM 1701), etanol (NCM 2207) e insumos agrícolas.'
        },
        {
            'code': 'LEI_10637_2002',
            'ref_type': 'LEI',
            'number': '10.637',
            'year': 2002,
            'title': 'Lei 10.637/2002 - PIS Não-Cumulativo',
            'summary': 'Dispõe sobre a não-cumulatividade da contribuição para o PIS/PASEP. Regime padrão: 1,65% com direito a crédito sobre insumos.',
            'issuing_body': 'RECEITA_FEDERAL',
            'scope': 'FEDERAL',
            'applicable_states': None,
            'full_text': None,
            'url': 'http://www.planalto.gov.br/ccivil_03/leis/2002/l10637.htm',
            'relevant_articles': json.dumps({
                'Art. 2º': 'Alíquota de 1,65%',
                'Art. 3º': 'Direito ao crédito sobre insumos',
                'Art. 5º': 'Isenções e alíquota zero'
            }),
            'affects_taxes': json.dumps(['PIS']),
            'published_date': '2002-12-30',
            'effective_date': '2002-12-01',
            'revoked_date': None,
            'version': '1.0.0',
            'notes': 'Regime não-cumulativo permite crédito de PIS sobre aquisições de insumos, matérias-primas, embalagens e energia elétrica.'
        },
        {
            'code': 'LEI_10833_2003',
            'ref_type': 'LEI',
            'number': '10.833',
            'year': 2003,
            'title': 'Lei 10.833/2003 - COFINS Não-Cumulativa',
            'summary': 'Dispõe sobre a não-cumulatividade da COFINS. Regime padrão: 7,6% com direito a crédito sobre insumos.',
            'issuing_body': 'RECEITA_FEDERAL',
            'scope': 'FEDERAL',
            'applicable_states': None,
            'full_text': None,
            'url': 'http://www.planalto.gov.br/ccivil_03/leis/2003/l10.833.htm',
            'relevant_articles': json.dumps({
                'Art. 2º': 'Alíquota de 7,6%',
                'Art. 3º': 'Direito ao crédito sobre insumos',
                'Art. 6º': 'Isenções e alíquota zero'
            }),
            'affects_taxes': json.dumps(['COFINS']),
            'published_date': '2003-12-29',
            'effective_date': '2004-02-01',
            'revoked_date': None,
            'version': '1.0.0',
            'notes': 'Paralelo à Lei 10.637/2002, estabelece regime não-cumulativo para COFINS.'
        },
        {
            'code': 'LEI_11033_2004_ART17',
            'ref_type': 'LEI',
            'number': '11.033',
            'year': 2004,
            'title': 'Lei 11.033/2004 - Art. 17 - Manutenção de Créditos',
            'summary': 'Permite manutenção de créditos de PIS/COFINS mesmo quando a saída é com alíquota zero ou isenta. Aplicável ao setor sucroalcooleiro.',
            'issuing_body': 'RECEITA_FEDERAL',
            'scope': 'FEDERAL',
            'applicable_states': None,
            'full_text': None,
            'url': 'http://www.planalto.gov.br/ccivil_03/_ato2004-2006/2004/lei/l11033.htm',
            'relevant_articles': json.dumps({
                'Art. 17': 'Manutenção de créditos mesmo com saída a alíquota zero'
            }),
            'affects_taxes': json.dumps(['PIS', 'COFINS']),
            'published_date': '2004-12-21',
            'effective_date': '2004-12-21',
            'revoked_date': None,
            'version': '1.0.0',
            'notes': 'Fundamental para o setor: permite crédito de PIS/COFINS sobre insumos mesmo quando a venda de açúcar tem alíquota zero (Lei 10.925/2004).'
        },
        {
            'code': 'LEI_9715_1998',
            'ref_type': 'LEI',
            'number': '9.715',
            'year': 1998,
            'title': 'Lei 9.715/1998 - PIS Cumulativo',
            'summary': 'Regime cumulativo de PIS/PASEP. Alíquota: 0,65%. Sem direito a crédito.',
            'issuing_body': 'RECEITA_FEDERAL',
            'scope': 'FEDERAL',
            'applicable_states': None,
            'full_text': None,
            'url': 'http://www.planalto.gov.br/ccivil_03/leis/l9715.htm',
            'relevant_articles': json.dumps({
                'Art. 8º': 'Alíquota de 0,65% (cumulativo)'
            }),
            'affects_taxes': json.dumps(['PIS']),
            'published_date': '1998-11-25',
            'effective_date': '1998-12-01',
            'revoked_date': None,
            'version': '1.0.0',
            'notes': 'Aplicável a empresas optantes pelo Simples Nacional ou lucro presumido (dependendo do caso).'
        },
        {
            'code': 'LEI_9718_1998',
            'ref_type': 'LEI',
            'number': '9.718',
            'year': 1998,
            'title': 'Lei 9.718/1998 - COFINS Cumulativa',
            'summary': 'Regime cumulativo de COFINS. Alíquota: 3%. Sem direito a crédito.',
            'issuing_body': 'RECEITA_FEDERAL',
            'scope': 'FEDERAL',
            'applicable_states': None,
            'full_text': None,
            'url': 'http://www.planalto.gov.br/ccivil_03/leis/l9718.htm',
            'relevant_articles': json.dumps({
                'Art. 3º': 'Alíquota de 3% (cumulativo)'
            }),
            'affects_taxes': json.dumps(['COFINS']),
            'published_date': '1998-11-27',
            'effective_date': '1998-12-01',
            'revoked_date': None,
            'version': '1.0.0',
            'notes': 'Aplicável a empresas no regime cumulativo.'
        },

        # =====================================================
        # LEGISLAÇÃO FEDERAL - IPI
        # =====================================================
        {
            'code': 'TIPI_CAPITULO_17',
            'ref_type': 'TABELA',
            'number': 'Capítulo 17',
            'year': 2023,
            'title': 'TIPI - Capítulo 17 (Açúcares)',
            'summary': 'Tabela de Incidência do IPI - Capítulo 17: Açúcares e produtos de confeitaria. NCM 1701: Açúcares de cana ou beterraba.',
            'issuing_body': 'RECEITA_FEDERAL',
            'scope': 'FEDERAL',
            'applicable_states': None,
            'full_text': None,
            'url': 'http://normas.receita.fazenda.gov.br/sijut2consulta/link.action?idAto=96423',
            'relevant_articles': json.dumps({
                '1701': 'Açúcares de cana ou beterraba - IPI: 0% (isento)',
                '1702': 'Outros açúcares - IPI variável'
            }),
            'affects_taxes': json.dumps(['IPI']),
            'published_date': '2022-12-30',
            'effective_date': '2023-01-01',
            'revoked_date': None,
            'version': '1.0.0',
            'notes': 'Açúcar geralmente tem IPI de 0% (isento). Verificar TIPI atualizada para alíquotas específicas.'
        },

        # =====================================================
        # LEGISLAÇÃO ESTADUAL - SÃO PAULO
        # =====================================================
        {
            'code': 'RICMS_SP_ANEXO_II',
            'ref_type': 'DECRETO',
            'number': '45.490',
            'year': 2000,
            'title': 'RICMS/SP - Anexo II - Redução BC',
            'summary': 'Redução de Base de Cálculo do ICMS em SP. Art. 3º, V: Açúcar (cesta básica) - Redução de BC.',
            'issuing_body': 'SEFAZ_SP',
            'scope': 'ESTADUAL',
            'applicable_states': json.dumps(['SP']),
            'full_text': None,
            'url': 'https://legislacao.fazenda.sp.gov.br/Paginas/RICMS_2000.aspx',
            'relevant_articles': json.dumps({
                'Art. 3º V': 'Redução BC ICMS para açúcar (cesta básica)'
            }),
            'affects_taxes': json.dumps(['ICMS']),
            'published_date': '2000-11-30',
            'effective_date': '2001-01-01',
            'revoked_date': None,
            'version': '1.0.0',
            'notes': 'Açúcar de cana e beterraba têm redução de base de cálculo do ICMS em SP por serem considerados produtos da cesta básica.'
        },
        {
            'code': 'RICMS_SP_ST_ACUCAR',
            'ref_type': 'DECRETO',
            'number': '45.490',
            'year': 2000,
            'title': 'RICMS/SP - Substituição Tributária (Açúcar)',
            'summary': 'Regras de Substituição Tributária para açúcar em SP. Verificar aplicabilidade conforme operação.',
            'issuing_body': 'SEFAZ_SP',
            'scope': 'ESTADUAL',
            'applicable_states': json.dumps(['SP']),
            'full_text': None,
            'url': 'https://legislacao.fazenda.sp.gov.br/Paginas/RICMS_2000.aspx',
            'relevant_articles': json.dumps({
                'Art. 313-Z19': 'ST aplicável ao açúcar em algumas operações'
            }),
            'affects_taxes': json.dumps(['ICMS']),
            'published_date': '2000-11-30',
            'effective_date': '2001-01-01',
            'revoked_date': None,
            'version': '1.0.0',
            'notes': 'ST pode ser aplicável em algumas operações com açúcar em SP. MVA varia conforme o produto.'
        },

        # =====================================================
        # LEGISLAÇÃO ESTADUAL - PERNAMBUCO
        # =====================================================
        {
            'code': 'RICMS_PE_CREDITO_PRESUMIDO',
            'ref_type': 'DECRETO',
            'number': '14.876',
            'year': 1991,
            'title': 'RICMS/PE - Crédito Presumido 9%',
            'summary': 'Crédito presumido de 9% do valor da operação para açúcar de cana em PE (regime substitutivo ao sistema comum).',
            'issuing_body': 'SEFAZ_PE',
            'scope': 'ESTADUAL',
            'applicable_states': json.dumps(['PE']),
            'full_text': None,
            'url': 'https://www.sefaz.pe.gov.br/Legislacao/Tributaria/RICMS',
            'relevant_articles': json.dumps({
                'Art. XX': 'Crédito presumido de 9% para açúcar'
            }),
            'affects_taxes': json.dumps(['ICMS']),
            'published_date': '1991-XX-XX',
            'effective_date': '1991-XX-XX',
            'revoked_date': None,
            'version': '1.0.0',
            'notes': 'Benefício fiscal específico de PE para setor sucroalcooleiro. Aplicável a NCM 1701 (açúcar de cana).'
        },
        {
            'code': 'RICMS_PE_ISENCAO_CANA',
            'ref_type': 'DECRETO',
            'number': '14.876',
            'year': 1991,
            'title': 'RICMS/PE - Isenção Cana-de-açúcar',
            'summary': 'Isenção de ICMS nas operações com cana-de-açúcar in natura em PE.',
            'issuing_body': 'SEFAZ_PE',
            'scope': 'ESTADUAL',
            'applicable_states': json.dumps(['PE']),
            'full_text': None,
            'url': 'https://www.sefaz.pe.gov.br/Legislacao/Tributaria/RICMS',
            'relevant_articles': json.dumps({
                'Art. YY': 'Isenção ICMS para cana-de-açúcar in natura'
            }),
            'affects_taxes': json.dumps(['ICMS']),
            'published_date': '1991-XX-XX',
            'effective_date': '1991-XX-XX',
            'revoked_date': None,
            'version': '1.0.0',
            'notes': 'Cana-de-açúcar destinada à industrialização tem isenção de ICMS em PE.'
        },

        # =====================================================
        # JURISPRUDÊNCIA - STJ
        # =====================================================
        {
            'code': 'STJ_RESP_1221170',
            'ref_type': 'JURISPRUDENCIA',
            'number': '1.221.170',
            'year': 2011,
            'title': 'REsp 1.221.170/PR - STJ - Manutenção Créditos',
            'summary': 'Tese: Empresas sujeitas a alíquota zero de PIS/COFINS (como açúcar) podem manter créditos sobre insumos adquiridos. Não há "estorno" de créditos.',
            'issuing_body': 'STJ',
            'scope': 'JURISPRUDENCIA',
            'applicable_states': None,
            'full_text': None,
            'url': 'https://processo.stj.jus.br/processo/revista/documento/mediado/?componente=ITA&sequencial=1074236',
            'relevant_articles': json.dumps({
                'Tese': 'Manutenção de créditos PIS/COFINS mesmo com saída a alíquota zero'
            }),
            'affects_taxes': json.dumps(['PIS', 'COFINS']),
            'published_date': '2011-09-14',
            'effective_date': '2011-09-14',
            'revoked_date': None,
            'version': '1.0.0',
            'notes': 'Leading case do STJ sobre manutenção de créditos no setor sucroalcooleiro. Fundamenta-se na Lei 11.033/2004 Art. 17.'
        },
        {
            'code': 'STJ_RESP_INSUMOS_AGRICOLAS',
            'ref_type': 'JURISPRUDENCIA',
            'number': 'Vários',
            'year': 2015,
            'title': 'STJ - Insumos Fase Agrícola',
            'summary': 'Jurisprudência consolidada do STJ reconhecendo que fertilizantes, defensivos e combustíveis usados na fase agrícola são insumos que geram crédito de PIS/COFINS.',
            'issuing_body': 'STJ',
            'scope': 'JURISPRUDENCIA',
            'applicable_states': None,
            'full_text': None,
            'url': 'https://www.stj.jus.br/sites/portalp/Jurisprudencia',
            'relevant_articles': json.dumps({
                'Tese': 'Insumos agrícolas geram direito a crédito PIS/COFINS'
            }),
            'affects_taxes': json.dumps(['PIS', 'COFINS']),
            'published_date': '2015-XX-XX',
            'effective_date': '2015-XX-XX',
            'revoked_date': None,
            'version': '1.0.0',
            'notes': 'Base legal: Lei 10.925/2004 Art. 8º (suspensão) + Lei 10.637/2002 e 10.833/2003 (crédito sobre insumos).'
        },

        # =====================================================
        # JURISPRUDÊNCIA - STF
        # =====================================================
        {
            'code': 'STF_TEMA_69',
            'ref_type': 'JURISPRUDENCIA',
            'number': 'RE 574.706',
            'year': 2017,
            'title': 'Tema 69 - STF - Exclusão ICMS da BC PIS/COFINS',
            'summary': 'Tese de Repercussão Geral: O ICMS não compõe a base de cálculo de PIS e COFINS. RE 574.706/PR.',
            'issuing_body': 'STF',
            'scope': 'JURISPRUDENCIA',
            'applicable_states': None,
            'full_text': None,
            'url': 'https://portal.stf.jus.br/jurisprudenciaRepercussao/tema.asp?num=69',
            'relevant_articles': json.dumps({
                'Tese': 'ICMS não integra a base de cálculo de PIS/COFINS'
            }),
            'affects_taxes': json.dumps(['PIS', 'COFINS', 'ICMS']),
            'published_date': '2017-03-15',
            'effective_date': '2017-03-15',
            'revoked_date': None,
            'version': '1.0.0',
            'notes': 'Modulação: Efeitos a partir de 15/03/2017. Empresas devem excluir ICMS da BC de PIS/COFINS nos cálculos.'
        },

        # =====================================================
        # RECEITA FEDERAL - NORMAS
        # =====================================================
        {
            'code': 'IN_RFB_2121_2022',
            'ref_type': 'INSTRUCAO_NORMATIVA',
            'number': '2.121',
            'year': 2022,
            'title': 'IN RFB 2.121/2022 - NCM',
            'summary': 'Instrução Normativa que consolida normas sobre NCM e classificação fiscal de mercadorias.',
            'issuing_body': 'RECEITA_FEDERAL',
            'scope': 'FEDERAL',
            'applicable_states': None,
            'full_text': None,
            'url': 'http://normas.receita.fazenda.gov.br/sijut2consulta/link.action?idAto=128522',
            'relevant_articles': json.dumps({
                'Anexo I': 'Tabela NCM completa',
                'Capítulo 17': 'Açúcares e produtos de confeitaria'
            }),
            'affects_taxes': json.dumps(['ICMS', 'IPI', 'II']),
            'published_date': '2022-12-15',
            'effective_date': '2023-01-01',
            'revoked_date': None,
            'version': '1.0.0',
            'notes': 'Referência oficial para classificação NCM. Deve ser consultada em conjunto com a TIPI.'
        },
        {
            'code': 'TABELA_CST_PIS_COFINS',
            'ref_type': 'TABELA',
            'number': 'Anexo NF-e',
            'year': 2023,
            'title': 'Tabela de CST - PIS/COFINS',
            'summary': 'Código de Situação Tributária para PIS e COFINS. Padronização nacional conforme legislação federal.',
            'issuing_body': 'RECEITA_FEDERAL',
            'scope': 'FEDERAL',
            'applicable_states': None,
            'full_text': None,
            'url': 'http://www.nfe.fazenda.gov.br/portal/principal.aspx',
            'relevant_articles': json.dumps({
                'CST 01': 'Operação tributável (alíquota básica)',
                'CST 06': 'Alíquota zero',
                'CST 50': 'Operação com direito a crédito'
            }),
            'affects_taxes': json.dumps(['PIS', 'COFINS']),
            'published_date': '2023-01-01',
            'effective_date': '2023-01-01',
            'revoked_date': None,
            'version': '1.0.0',
            'notes': 'CSTs principais: 01 (tributável), 06 (alíquota zero), 50 (crédito), 73 (suspensão), 99 (outros).'
        },

        # =====================================================
        # SIMPLES NACIONAL
        # =====================================================
        {
            'code': 'LC_123_2006',
            'ref_type': 'LEI_COMPLEMENTAR',
            'number': '123',
            'year': 2006,
            'title': 'Lei Complementar 123/2006 - Simples Nacional',
            'summary': 'Institui o Simples Nacional. Empresas optantes recolhem PIS/COFINS unificado, sem destaque separado (CST 99).',
            'issuing_body': 'CONGRESSO_NACIONAL',
            'scope': 'FEDERAL',
            'applicable_states': None,
            'full_text': None,
            'url': 'http://www.planalto.gov.br/ccivil_03/leis/lcp/lcp123.htm',
            'relevant_articles': json.dumps({
                'Art. 13': 'Abrangência do Simples Nacional',
                'Art. 18': 'Anexos e alíquotas'
            }),
            'affects_taxes': json.dumps(['PIS', 'COFINS', 'ICMS', 'IPI']),
            'published_date': '2006-12-14',
            'effective_date': '2007-07-01',
            'revoked_date': None,
            'version': '1.0.0',
            'notes': 'Empresas no Simples Nacional: CST PIS/COFINS = 99. Alíquota integra faixa do anexo aplicável.'
        },

        # =====================================================
        # CFOP
        # =====================================================
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
                'Anexo I': 'Tabela CFOP completa - operações internas, interestaduais e exterior'
            }),
            'affects_taxes': json.dumps(['ICMS']),
            'published_date': '2005-07-30',
            'effective_date': '2005-10-01',
            'revoked_date': None,
            'version': '1.0.0',
            'notes': 'Tabela CFOP oficial - base para validação de natureza da operação.'
        },
    ]

    # Inserir registros
    print(f"\n[*] Inserindo {len(references)} referências legais...")

    for ref in references:
        cursor.execute('''
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
        ''', ref)

    conn.commit()

    # Verificar
    cursor.execute('SELECT COUNT(*) as total FROM legal_refs')
    total = cursor.fetchone()[0]
    print(f"\n[OK] {total} referências inseridas com sucesso!")

    # Estatísticas por scope
    cursor.execute('''
        SELECT scope, COUNT(*) as total
        FROM legal_refs
        GROUP BY scope
        ORDER BY total DESC
    ''')

    print("\n[STATS] Por escopo:")
    for row in cursor.fetchall():
        print(f"  • {row[0]}: {row[1]} referência(s)")

    # Estatísticas por tipo
    cursor.execute('''
        SELECT ref_type, COUNT(*) as total
        FROM legal_refs
        GROUP BY ref_type
        ORDER BY total DESC
    ''')

    print("\n[STATS] Por tipo:")
    for row in cursor.fetchall():
        print(f"  • {row[0]}: {row[1]} referência(s)")

    conn.close()
    print("\n[OK] Concluído!")


if __name__ == '__main__':
    print("=" * 70)
    print("POPULAR REFERÊNCIAS LEGAIS COMPLETAS")
    print("=" * 70)
    populate_legal_refs_full()
