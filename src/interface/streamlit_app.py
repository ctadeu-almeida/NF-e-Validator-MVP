# -*- coding: utf-8 -*-
"""
Streamlit Interface - NF-e Validator MVP

Interface web para validação de NF-e do setor sucroalcooleiro (açúcar).

Features:
- Upload de arquivos CSV
- Validação automática (Federal + SP/PE)
- Visualização de resultados (JSON + Markdown)
- Download de relatórios
- Agente IA para classificação NCM (opcional)
"""

import streamlit as st
import sys
from pathlib import Path
import json
from datetime import datetime
import os

# Add src to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'src'))

from nfe_validator.infrastructure.parsers.csv_parser import NFeCSVParser
from nfe_validator.domain.services.federal_validators import (
    NCMValidator,
    PISCOFINSValidator,
    CFOPValidator,
    TotalsValidator
)
from nfe_validator.domain.services.state_validators import (
    SPValidator,
    PEValidator
)
from nfe_validator.infrastructure.validators.report_generator import ReportGenerator
from repositories.fiscal_repository import FiscalRepository
from agents.ncm_agent import create_ncm_agent


# =====================================================
# Page Configuration
# =====================================================

st.set_page_config(
    page_title="NF-e Validator MVP - Sucroalcooleiro",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =====================================================
# Helper Functions
# =====================================================

@st.cache_resource
def load_repository():
    """Load fiscal repository (cached)"""
    try:
        return FiscalRepository()
    except Exception as e:
        st.error(f"Erro ao carregar database: {e}")
        return None


def validate_nfe(nfe, repo, use_ai_agent=False, api_key=None):
    """
    Run validation pipeline on NF-e

    Args:
        nfe: NFeEntity
        repo: FiscalRepository
        use_ai_agent: Use AI agent for NCM classification
        api_key: Google API key for agent

    Returns:
        nfe with validation errors
    """

    # Federal Validators
    item_validators = [
        NCMValidator(repo),
        PISCOFINSValidator(repo),
        CFOPValidator(repo)
    ]

    for validator in item_validators:
        for item in nfe.items:
            errors = validator.validate(item, nfe)
            nfe.validation_errors.extend(errors)

    # Totals Validator
    totals_validator = TotalsValidator(repo)
    totals_errors = totals_validator.validate(nfe)
    nfe.validation_errors.extend(totals_errors)

    # State Validators
    if nfe.emitente.uf == 'SP' or nfe.destinatario.uf == 'SP':
        sp_validator = SPValidator(repo)
        for item in nfe.items:
            errors = sp_validator.validate(item, nfe)
            nfe.validation_errors.extend(errors)

    if nfe.emitente.uf == 'PE' or nfe.destinatario.uf == 'PE':
        pe_validator = PEValidator(repo)
        for item in nfe.items:
            errors = pe_validator.validate(item, nfe)
            nfe.validation_errors.extend(errors)

    # AI Agent (optional)
    if use_ai_agent and api_key:
        try:
            with st.spinner("Inicializando Agente IA..."):
                agent = create_ncm_agent(repo, api_key)

            # Initialize suggestions dict
            if 'ai_suggestions' not in st.session_state:
                st.session_state.ai_suggestions = {}

            with st.spinner("Classificando NCMs com IA..."):
                for item in nfe.items:
                    try:
                        result = agent.classify_ncm(item.descricao, item.ncm)

                        if result.get('suggested_ncm'):
                            st.session_state.ai_suggestions[item.numero_item] = result

                    except Exception as item_error:
                        # Log error but continue with other items
                        st.session_state.ai_suggestions[item.numero_item] = {
                            'suggested_ncm': None,
                            'confidence': 0,
                            'reasoning': f"Erro ao processar: {str(item_error)}",
                            'is_correct': None,
                            'error': str(item_error)
                        }

        except Exception as e:
            st.warning(f"⚠️ Agente IA não disponível: {str(e)}")
            st.info("Continuando validação sem agente IA...")

    return nfe


# =====================================================
# Main Interface
# =====================================================

def main():
    """Main Streamlit application"""

    # Header
    st.title("📋 NF-e Validator MVP")
    st.markdown("**Validação Fiscal Automatizada - Setor Sucroalcooleiro (Açúcar)**")
    st.markdown("---")

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configurações")

        # Database info
        repo = load_repository()

        if repo is None:
            st.error("❌ Erro ao carregar database!")
            st.stop()

        try:
            db_version = repo.get_database_version()
            last_pop = repo.get_last_population_date()
            stats = repo.get_statistics()

            st.info(f"""
            **Database Status**
            - Versão: {db_version}
            - Última atualização: {last_pop}
            """)

            st.metric("Regras Carregadas", sum(stats.values()))
        except Exception as e:
            st.warning(f"⚠️ Erro ao obter info do database: {e}")

        st.markdown("---")

        # AI Agent settings
        st.subheader("🤖 Agente IA (Opcional)")
        use_ai = st.checkbox("Usar Agente para NCM", value=False)

        api_key = None
        if use_ai:
            api_key = st.text_input(
                "Google API Key",
                type="password",
                help="Necessário para classificação inteligente de NCM com Gemini 2.5",
                placeholder="AIza..."
            )

            if api_key:
                st.success("✅ API Key configurada")
            else:
                st.warning("⚠️ Insira sua API Key para usar o agente")

        st.markdown("---")

        # About
        st.subheader("ℹ️ Sobre")
        st.markdown("""
        **MVP Scope:**
        - ✅ Validações Federais (NCM, PIS/COFINS, CFOP)
        - ✅ Validações Estaduais (SP + PE)
        - ✅ Relatórios JSON + Markdown
        - ✅ Agente IA (Google Gemini 2.5 + LangChain ReAct)

        **Versão:** 1.0.0-mvp
        **LLM:** Google Gemini 2.5 Pro
        """)

    # Main content
    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("📤 Upload de NF-e")

        uploaded_file = st.file_uploader(
            "Selecione um arquivo CSV",
            type=['csv'],
            help="Arquivo CSV com dados da NF-e no formato esperado"
        )

        if uploaded_file:
            st.success(f"Arquivo carregado: {uploaded_file.name}")

            # Save to temp file
            import tempfile
            import os
            temp_dir = tempfile.gettempdir()
            temp_path = Path(temp_dir) / uploaded_file.name

            with open(temp_path, 'wb') as f:
                f.write(uploaded_file.getbuffer())

            # Parse button
            if st.button("🔍 Validar NF-e", type="primary"):
                with st.spinner("Processando..."):
                    try:
                        # Parse CSV completo
                        parser = NFeCSVParser()
                        nfes = parser.parse_csv(str(temp_path))

                        if not nfes:
                            st.error("Nenhuma NF-e encontrada no arquivo")
                            return

                        nfe = nfes[0]  # Get first NF-e

                        # Validate
                        nfe = validate_nfe(nfe, repo, use_ai, api_key)

                        # Store in session state
                        st.session_state.nfe = nfe
                        st.session_state.validated = True

                        st.success("✅ Validação concluída!")

                    except Exception as e:
                        st.error(f"Erro ao processar: {str(e)}")
                        import traceback
                        st.code(traceback.format_exc())

    with col2:
        st.subheader("📊 Instruções")

        if 'validated' not in st.session_state:
            st.info("""
            **Como usar:**

            1. Faça upload de um arquivo CSV com dados da NF-e
            2. (Opcional) Ative o Agente IA e insira sua API key do Google
            3. Clique em "Validar NF-e"
            4. Visualize os resultados e faça download dos relatórios

            **Formato CSV esperado:**

            O CSV deve conter as seguintes colunas:
            - `chave_acesso`, `numero_nfe`, `serie`, `data_emissao`
            - `cnpj_emitente`, `razao_social_emitente`, `uf_emitente`
            - `cnpj_destinatario`, `razao_social_destinatario`, `uf_destinatario`
            - `numero_item`, `codigo_produto`, `descricao`, `ncm`, `cfop`
            - `quantidade`, `unidade`, `valor_unitario`, `valor_total`
            - `pis_cst`, `pis_aliquota`, `pis_valor`
            - `cofins_cst`, `cofins_aliquota`, `cofins_valor`
            - `icms_aliquota`, `icms_valor`, `ipi_aliquota`, `ipi_valor`
            """)

    # Results section
    if 'validated' in st.session_state and st.session_state.validated:
        st.markdown("---")
        st.header("📈 Resultados da Validação")

        nfe = st.session_state.nfe

        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)

        from nfe_validator.domain.entities.nfe_entity import Severity

        critical = sum(1 for e in nfe.validation_errors if e.severity == Severity.CRITICAL)
        error = sum(1 for e in nfe.validation_errors if e.severity == Severity.ERROR)
        warning = sum(1 for e in nfe.validation_errors if e.severity == Severity.WARNING)
        info = sum(1 for e in nfe.validation_errors if e.severity == Severity.INFO)

        with col1:
            st.metric("🔴 Crítico", critical)

        with col2:
            st.metric("🟠 Erro", error)

        with col3:
            st.metric("🟡 Aviso", warning)

        with col4:
            impact = nfe.get_total_financial_impact()
            st.metric("💰 Impacto", f"R$ {impact:,.2f}")

        # Validation status
        if critical > 0 or error > 0:
            st.error("❌ NF-e INVÁLIDA - Requer correção")
        elif warning > 0:
            st.warning("⚠️ NF-e VÁLIDA COM AVISOS")
        else:
            st.success("✅ NF-e VÁLIDA")

        # Tabs for different views
        tab1, tab2, tab3, tab4 = st.tabs(["📋 Relatório", "📄 JSON", "🤖 Sugestões IA", "💾 Downloads"])

        with tab1:
            # Generate Markdown report
            generator = ReportGenerator()
            md_report = generator.generate_markdown_report(nfe)

            st.markdown(md_report, unsafe_allow_html=True)

        with tab2:
            # Generate JSON report
            json_report = generator.generate_json_report(nfe)

            st.json(json_report)

        with tab3:
            # AI Suggestions (if available)
            if 'ai_suggestions' in st.session_state and st.session_state.ai_suggestions:
                st.subheader("🤖 Sugestões do Agente IA")

                for item_num, suggestion in st.session_state.ai_suggestions.items():
                    with st.expander(f"Item #{item_num}"):
                        st.write(f"**NCM Sugerido:** {suggestion.get('suggested_ncm', 'N/A')}")
                        st.write(f"**Confiança:** {suggestion.get('confidence', 0)}%")
                        st.write(f"**NCM Correto:** {'❌ Não' if not suggestion.get('is_correct') else '✅ Sim'}")

                        st.markdown("**Raciocínio do Agente:**")
                        st.code(suggestion.get('reasoning', 'N/A'))
            else:
                st.info("Nenhuma sugestão de IA disponível. Ative o Agente IA nas configurações.")

        with tab4:
            # Download buttons
            st.subheader("💾 Baixar Relatórios")

            col1, col2 = st.columns(2)

            with col1:
                # Markdown download
                md_bytes = md_report.encode('utf-8')
                st.download_button(
                    label="📄 Download Markdown",
                    data=md_bytes,
                    file_name=f"nfe_{nfe.numero}_report.md",
                    mime="text/markdown"
                )

            with col2:
                # JSON download
                json_bytes = json.dumps(json_report, ensure_ascii=False, indent=2).encode('utf-8')
                st.download_button(
                    label="📋 Download JSON",
                    data=json_bytes,
                    file_name=f"nfe_{nfe.numero}_report.json",
                    mime="application/json"
                )


if __name__ == "__main__":
    main()
