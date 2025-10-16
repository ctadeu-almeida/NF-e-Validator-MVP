# -*- coding: utf-8 -*-
"""
Popula tabela legal_references com legislação fiscal brasileira
"""

import sqlite3
from datetime import datetime

def populate_legal_references():
    """Popular tabela de referências legais"""

    conn = sqlite3.connect('rules.db')
    cursor = conn.cursor()

    # Limpar tabela existente
    cursor.execute('DELETE FROM legal_references')

    references = [
        # =====================================================
        # LEGISLAÇÃO FEDERAL - PIS/COFINS
        # =====================================================
        {
            'category': 'FEDERAL',
            'subcategory': 'PIS/COFINS',
            'reference_code': 'LEI_10925_2004',
            'title': 'Lei 10.925/2004',
            'description': 'Reduz as alíquotas de PIS/PASEP e COFINS para insumos agropecuários. Art. 1º X: Alíquota Zero para açúcar. Art. 8º: Suspensão para insumos destinados à atividade agropecuária.',
            'url': 'http://www.planalto.gov.br/ccivil_03/_ato2004-2006/2004/lei/l10.925.htm',
            'scope': 'NACIONAL',
            'enacted_date': '2004-07-23',
            'notes': 'Principal legislação para setor sucroalcooleiro. Aplicável a açúcar de cana (NCM 1701), etanol (NCM 2207) e insumos agrícolas.'
        },
        {
            'category': 'FEDERAL',
            'subcategory': 'PIS/COFINS',
            'reference_code': 'LEI_10637_2002',
            'title': 'Lei 10.637/2002',
            'description': 'Dispõe sobre a não-cumulatividade da contribuição para o PIS/PASEP. Regime padrão: 1,65% com direito a crédito sobre insumos.',
            'url': 'http://www.planalto.gov.br/ccivil_03/leis/2002/l10637.htm',
            'scope': 'NACIONAL',
            'enacted_date': '2002-12-30',
            'notes': 'Regime não-cumulativo permite crédito de PIS sobre aquisições de insumos, matérias-primas, embalagens e energia elétrica.'
        },
        {
            'category': 'FEDERAL',
            'subcategory': 'PIS/COFINS',
            'reference_code': 'LEI_10833_2003',
            'title': 'Lei 10.833/2003',
            'description': 'Dispõe sobre a não-cumulatividade da COFINS. Regime padrão: 7,6% com direito a crédito sobre insumos.',
            'url': 'http://www.planalto.gov.br/ccivil_03/leis/2003/l10.833.htm',
            'scope': 'NACIONAL',
            'enacted_date': '2003-12-29',
            'notes': 'Paralelo à Lei 10.637/2002, estabelece regime não-cumulativo para COFINS.'
        },
        {
            'category': 'FEDERAL',
            'subcategory': 'PIS/COFINS',
            'reference_code': 'LEI_11033_2004_ART17',
            'title': 'Lei 11.033/2004 - Art. 17',
            'description': 'Permite manutenção de créditos de PIS/COFINS mesmo quando a saída é com alíquota zero ou isenta. Aplicável ao setor sucroalcooleiro.',
            'url': 'http://www.planalto.gov.br/ccivil_03/_ato2004-2006/2004/lei/l11033.htm',
            'scope': 'NACIONAL',
            'enacted_date': '2004-12-21',
            'notes': 'Fundamental para o setor: permite crédito de PIS/COFINS sobre insumos mesmo quando a venda de açúcar tem alíquota zero (Lei 10.925/2004).'
        },
        {
            'category': 'FEDERAL',
            'subcategory': 'PIS/COFINS',
            'reference_code': 'LEI_9715_1998',
            'title': 'Lei 9.715/1998',
            'description': 'Regime cumulativo de PIS/PASEP. Alíquota: 0,65%. Sem direito a crédito.',
            'url': 'http://www.planalto.gov.br/ccivil_03/leis/l9715.htm',
            'scope': 'NACIONAL',
            'enacted_date': '1998-11-25',
            'notes': 'Aplicável a empresas optantes pelo Simples Nacional ou lucro presumido (dependendo do caso).'
        },
        {
            'category': 'FEDERAL',
            'subcategory': 'PIS/COFINS',
            'reference_code': 'LEI_9718_1998',
            'title': 'Lei 9.718/1998',
            'description': 'Regime cumulativo de COFINS. Alíquota: 3%. Sem direito a crédito.',
            'url': 'http://www.planalto.gov.br/ccivil_03/leis/l9718.htm',
            'scope': 'NACIONAL',
            'enacted_date': '1998-11-27',
            'notes': 'Aplicável a empresas no regime cumulativo.'
        },

        # =====================================================
        # LEGISLAÇÃO FEDERAL - IPI
        # =====================================================
        {
            'category': 'FEDERAL',
            'subcategory': 'IPI',
            'reference_code': 'TIPI_CAPITULO_17',
            'title': 'TIPI - Capítulo 17 (Açúcares)',
            'description': 'Tabela de Incidência do IPI - Capítulo 17: Açúcares e produtos de confeitaria. NCM 1701: Açúcares de cana ou beterraba.',
            'url': 'http://normas.receita.fazenda.gov.br/sijut2consulta/link.action?idAto=96423',
            'scope': 'NACIONAL',
            'enacted_date': '2022-12-30',
            'notes': 'Açúcar geralmente tem IPI de 0% (isento). Verificar TIPI atualizada para alíquotas específicas.'
        },

        # =====================================================
        # LEGISLAÇÃO ESTADUAL - SÃO PAULO
        # =====================================================
        {
            'category': 'ESTADUAL',
            'subcategory': 'ICMS - SP',
            'reference_code': 'RICMS_SP_ANEXO_II',
            'title': 'RICMS/SP - Anexo II',
            'description': 'Redução de Base de Cálculo do ICMS em SP. Art. 3º, V: Açúcar (cesta básica) - Redução de BC.',
            'url': 'https://legislacao.fazenda.sp.gov.br/Paginas/RICMS_2000.aspx',
            'scope': 'SÃO PAULO',
            'enacted_date': '2000-11-30',
            'notes': 'Açúcar de cana e beterraba têm redução de base de cálculo do ICMS em SP por serem considerados produtos da cesta básica.'
        },
        {
            'category': 'ESTADUAL',
            'subcategory': 'ICMS - SP',
            'reference_code': 'RICMS_SP_ST_ACUCAR',
            'title': 'RICMS/SP - Substituição Tributária (Açúcar)',
            'description': 'Regras de Substituição Tributária para açúcar em SP. Verificar aplicabilidade conforme operação.',
            'url': 'https://legislacao.fazenda.sp.gov.br/Paginas/RICMS_2000.aspx',
            'scope': 'SÃO PAULO',
            'enacted_date': '2000-11-30',
            'notes': 'ST pode ser aplicável em algumas operações com açúcar em SP. MVA varia conforme o produto.'
        },

        # =====================================================
        # LEGISLAÇÃO ESTADUAL - PERNAMBUCO
        # =====================================================
        {
            'category': 'ESTADUAL',
            'subcategory': 'ICMS - PE',
            'reference_code': 'RICMS_PE_CREDITO_PRESUMIDO',
            'title': 'RICMS/PE - Crédito Presumido 9%',
            'description': 'Crédito presumido de 9% do valor da operação para açúcar de cana em PE (regime substitutivo ao sistema comum).',
            'url': 'https://www.sefaz.pe.gov.br/Legislacao/Tributaria/RICMS',
            'scope': 'PERNAMBUCO',
            'enacted_date': 'Várias',
            'notes': 'Benefício fiscal específico de PE para setor sucroalcooleiro. Aplicável a NCM 1701 (açúcar de cana).'
        },
        {
            'category': 'ESTADUAL',
            'subcategory': 'ICMS - PE',
            'reference_code': 'RICMS_PE_ISENCAO_CANA',
            'title': 'RICMS/PE - Isenção Cana-de-açúcar',
            'description': 'Isenção de ICMS nas operações com cana-de-açúcar in natura em PE.',
            'url': 'https://www.sefaz.pe.gov.br/Legislacao/Tributaria/RICMS',
            'scope': 'PERNAMBUCO',
            'enacted_date': 'Várias',
            'notes': 'Cana-de-açúcar destinada à industrialização tem isenção de ICMS em PE.'
        },

        # =====================================================
        # JURISPRUDÊNCIA - STJ
        # =====================================================
        {
            'category': 'JURISPRUDENCIA',
            'subcategory': 'STJ',
            'reference_code': 'STJ_RESP_1221170',
            'title': 'REsp 1.221.170/PR - STJ',
            'description': 'Tese: Empresas sujeitas a alíquota zero de PIS/COFINS (como açúcar) podem manter créditos sobre insumos adquiridos. Não há "estorno" de créditos.',
            'url': 'https://processo.stj.jus.br/processo/revista/documento/mediado/?componente=ITA&sequencial=1074236',
            'scope': 'NACIONAL',
            'enacted_date': '2011-09-14',
            'notes': 'Leading case do STJ sobre manutenção de créditos no setor sucroalcooleiro. Fundamenta-se na Lei 11.033/2004 Art. 17.'
        },
        {
            'category': 'JURISPRUDENCIA',
            'subcategory': 'STJ',
            'reference_code': 'STJ_RESP_INSUMOS_AGRICOLAS',
            'title': 'STJ - Insumos Fase Agrícola',
            'description': 'Jurisprudência consolidada do STJ reconhecendo que fertilizantes, defensivos e combustíveis usados na fase agrícola são insumos que geram crédito de PIS/COFINS.',
            'url': 'https://www.stj.jus.br/sites/portalp/Jurisprudencia',
            'scope': 'NACIONAL',
            'enacted_date': 'Várias',
            'notes': 'Base legal: Lei 10.925/2004 Art. 8º (suspensão) + Lei 10.637/2002 e 10.833/2003 (crédito sobre insumos).'
        },

        # =====================================================
        # JURISPRUDÊNCIA - STF
        # =====================================================
        {
            'category': 'JURISPRUDENCIA',
            'subcategory': 'STF',
            'reference_code': 'STF_TEMA_69',
            'title': 'Tema 69 - STF (Exclusão ICMS)',
            'description': 'Tese de Repercussão Geral: O ICMS não compõe a base de cálculo de PIS e COFINS. RE 574.706/PR.',
            'url': 'https://portal.stf.jus.br/jurisprudenciaRepercussao/tema.asp?num=69',
            'scope': 'NACIONAL',
            'enacted_date': '2017-03-15',
            'notes': 'Modulação: Efeitos a partir de 15/03/2017. Empresas devem excluir ICMS da BC de PIS/COFINS nos cálculos.'
        },

        # =====================================================
        # RECEITA FEDERAL - NORMAS
        # =====================================================
        {
            'category': 'FEDERAL',
            'subcategory': 'RECEITA_FEDERAL',
            'reference_code': 'IN_RFB_2121_2022',
            'title': 'IN RFB 2.121/2022',
            'description': 'Instrução Normativa que consolida normas sobre NCM e classificação fiscal de mercadorias.',
            'url': 'http://normas.receita.fazenda.gov.br/sijut2consulta/link.action?idAto=128522',
            'scope': 'NACIONAL',
            'enacted_date': '2022-12-15',
            'notes': 'Referência oficial para classificação NCM. Deve ser consultada em conjunto com a TIPI.'
        },
        {
            'category': 'FEDERAL',
            'subcategory': 'RECEITA_FEDERAL',
            'reference_code': 'TABELA_CST_PIS_COFINS',
            'title': 'Tabela de CST - PIS/COFINS',
            'description': 'Código de Situação Tributária para PIS e COFINS. Padronização nacional conforme legislação federal.',
            'url': 'http://www.nfe.fazenda.gov.br/portal/principal.aspx',
            'scope': 'NACIONAL',
            'enacted_date': 'Várias',
            'notes': 'CSTs principais: 01 (tributável), 06 (alíquota zero), 50 (crédito), 73 (suspensão), 99 (outros).'
        },

        # =====================================================
        # SIMPLES NACIONAL
        # =====================================================
        {
            'category': 'FEDERAL',
            'subcategory': 'SIMPLES_NACIONAL',
            'reference_code': 'LC_123_2006',
            'title': 'Lei Complementar 123/2006',
            'description': 'Institui o Simples Nacional. Empresas optantes recolhem PIS/COFINS unificado, sem destaque separado (CST 99).',
            'url': 'http://www.planalto.gov.br/ccivil_03/leis/lcp/lcp123.htm',
            'scope': 'NACIONAL',
            'enacted_date': '2006-12-14',
            'notes': 'Empresas no Simples Nacional: CST PIS/COFINS = 99. Alíquota integra faixa do anexo aplicável.'
        },
    ]

    # Inserir registros
    for ref in references:
        cursor.execute('''
            INSERT INTO legal_references
            (category, subcategory, reference_code, title, description, url, scope, enacted_date, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            ref['category'],
            ref['subcategory'],
            ref['reference_code'],
            ref['title'],
            ref['description'],
            ref['url'],
            ref['scope'],
            ref['enacted_date'],
            ref['notes']
        ))

    conn.commit()

    # Verificar
    cursor.execute('SELECT COUNT(*) FROM legal_references')
    count = cursor.fetchone()[0]
    print(f'Total de referencias inseridas: {count}')

    # Listar por categoria
    cursor.execute('''
        SELECT category, COUNT(*) as total
        FROM legal_references
        GROUP BY category
    ''')

    print('\nResumo por categoria:')
    for row in cursor.fetchall():
        print(f'  {row[0]}: {row[1]} referencias')

    conn.close()
    print('\nConcluido!')

if __name__ == '__main__':
    populate_legal_references()
