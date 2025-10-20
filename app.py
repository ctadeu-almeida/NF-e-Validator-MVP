import streamlit as st
import pandas as pd
import sys
import os
from pathlib import Path
import tempfile
import traceback
import zipfile
import io

# Adicionar o diretório src ao path para imports
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

# Imports do sistema EDA existente
try:
    from agents.eda_agent import EDAAgent
    from config.settings import get_settings, setup_directories
    from data_processing.excel_generator import ExcelGenerator
    from visualization.chart_generator import ChartGenerator
    from data_processing.csv_pipeline import process_csv_file
except ImportError as e:
    st.error(f"❌ Erro ao importar módulos: {e}")
    st.error("Verifique se todos os arquivos estão no local correto.")
    st.stop()

# Importar sistema de chat moderno
try:
    from modern_chat import render_modern_chat
    MODERN_CHAT_AVAILABLE = True
except ImportError:
    MODERN_CHAT_AVAILABLE = False

# Importar NF-e Validator (novo módulo)
try:
    from nfe_validator.infrastructure.parsers.csv_parser import NFeCSVParser
    from nfe_validator.domain.services.federal_validators import (
        NCMValidator, PISCOFINSValidator, CFOPValidator, TotalsValidator
    )
    from nfe_validator.domain.services.state_validators import SPValidator, PEValidator
    from nfe_validator.infrastructure.validators.report_generator import ReportGenerator
    from repositories.fiscal_repository import FiscalRepository
    NFE_VALIDATOR_AVAILABLE = True
except ImportError:
    NFE_VALIDATOR_AVAILABLE = False

# Configuração da página Streamlit
st.set_page_config(
    page_title="Sistema EDA - Análise Exploratória de Dados",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 30px;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .chat-container {
        background: transparent;
        border-radius: 15px;
        padding: 20px;
        margin: 20px 0;
        max-height: 500px;
        overflow-y: auto;
        border: none;
    }
    .user-message {
        background-color: #DCF8C6;
        color: #000000;
        padding: 12px 18px;
        border-radius: 18px 18px 4px 18px;
        margin: 12px 0;
        margin-left: 25%;
        position: relative;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        line-height: 1.4;
    }
    .assistant-message {
        background-color: #FFFFFF;
        color: #000000;
        padding: 12px 18px;
        border-radius: 18px 18px 18px 4px;
        margin: 12px 0;
        margin-right: 25%;
        position: relative;
        border-left: 3px solid #25D366;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        line-height: 1.4;
        white-space: pre-wrap;
    }
    .message-timestamp {
        font-size: 0.75em;
        color: #666666;
        margin-top: 6px;
        text-align: right;
        font-style: italic;
    }
    .chat-container::-webkit-scrollbar {
        width: 6px;
    }
    .chat-container::-webkit-scrollbar-track {
        background: #161b22;
        border-radius: 3px;
    }
    .chat-container::-webkit-scrollbar-thumb {
        background: #30363d;
        border-radius: 3px;
    }
    .chat-container::-webkit-scrollbar-thumb:hover {
        background: #484f58;
    }
    .metric-card {
        background: white;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Inicializar estado da sessão"""
    if 'eda_agent' not in st.session_state:
        st.session_state.eda_agent = None
    if 'api_validated' not in st.session_state:
        st.session_state.api_validated = False
    if 'current_data' not in st.session_state:
        st.session_state.current_data = None
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = {}
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
    if 'charts_generated' not in st.session_state:
        st.session_state.charts_generated = []
    if 'session_charts' not in st.session_state:
        st.session_state.session_charts = []
    if 'selected_model' not in st.session_state:
        st.session_state.selected_model = "gemini"
    if 'model_initialized' not in st.session_state:
        st.session_state.model_initialized = False

def initialize_model(model_type: str, api_key: str = None) -> tuple:
    """Inicializar modelo selecionado"""
    try:
        # Configurar diretórios
        setup_directories()

        # Criar agente com modelo selecionado - SEMPRE COM AGENTES
        agent = EDAAgent(model_type=model_type, api_key=api_key)

        if agent.api_available:
            return True, agent, f"✅ {model_type.title()} inicializado com agentes!"
        else:
            return False, None, f"❌ Falha ao inicializar {model_type.title()}. Verifique configuração."

    except Exception as e:
        return False, None, f"❌ Erro: {str(e)}"

def analyze_csv_structure(file_content):
    """Analisar estrutura do CSV para detectar o melhor separador e formato"""
    # Ler as primeiras linhas para análise
    lines = file_content.decode('utf-8', errors='ignore').split('\n')[:10]

    # Contadores para diferentes separadores
    separators_analysis = {}

    for sep in [',', ';', '\t', '|']:
        separator_info = {
            'separator': sep,
            'avg_columns': 0,
            'consistency': 0,
            'sample_columns': []
        }

        column_counts = []
        for line in lines[:5]:  # Analisar primeiras 5 linhas
            if line.strip():
                columns = len(line.split(sep))
                column_counts.append(columns)
                separator_info['sample_columns'].append(columns)

        if column_counts:
            separator_info['avg_columns'] = sum(column_counts) / len(column_counts)
            # Calcular consistência (quantas linhas têm o mesmo número de colunas)
            most_common_count = max(set(column_counts), key=column_counts.count)
            separator_info['consistency'] = column_counts.count(most_common_count) / len(column_counts)

        separators_analysis[sep] = separator_info

    return separators_analysis

def preprocess_csv_data(uploaded_file):
    """Pré-processar dados CSV com análise inteligente de estrutura"""
    try:
        # Ler conteúdo do arquivo
        file_content = uploaded_file.getvalue()

        # Analisar estrutura do CSV
        with st.spinner("🔍 Analisando estrutura do arquivo CSV..."):
            structure_analysis = analyze_csv_structure(file_content)

            # Mostrar análise detalhada
            with st.expander("📋 Análise Detalhada da Estrutura do CSV", expanded=False):
                st.write("**Resultados da análise de separadores:**")

                for sep, info in structure_analysis.items():
                    sep_name = {',' : 'Vírgula', ';': 'Ponto-e-vírgula', '\t': 'Tab', '|': 'Pipe'}[sep]
                    st.write(f"**{sep_name} ('{sep}'):**")
                    st.write(f"  • Média de colunas: {info['avg_columns']:.1f}")
                    st.write(f"  • Consistência: {info['consistency']*100:.1f}%")
                    st.write(f"  • Amostras: {info['sample_columns']}")

        # Escolher melhor separador baseado na análise
        best_separator = None
        best_score = 0

        for sep, info in structure_analysis.items():
            # Score baseado no número de colunas e consistência
            # Priorizar separadores que geram mais colunas e são consistentes
            score = info['avg_columns'] * info['consistency']

            # Bonus para separadores que geram número esperado de colunas (31 para fraude)
            if 30 <= info['avg_columns'] <= 35:
                score *= 2

            if score > best_score:
                best_score = score
                best_separator = sep

        # Criar arquivo temporário
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv', mode='wb') as tmp_file:
            tmp_file.write(file_content)
            temp_path = tmp_file.name

        # Carregar dados com o melhor separador detectado
        if best_separator:
            try:
                data = pd.read_csv(temp_path, sep=best_separator)
                sep_name = {',' : 'vírgula', ';': 'ponto-e-vírgula', '\t': 'tab', '|': 'pipe'}[best_separator]
                st.success(f"✅ Melhor separador detectado: **{sep_name}** - {len(data.columns)} colunas")

                # Mostrar informações da detecção
                col_det1, col_det2, col_det3 = st.columns(3)
                with col_det1:
                    st.metric("🔢 Colunas Detectadas", len(data.columns))
                with col_det2:
                    consistency = structure_analysis[best_separator]['consistency']
                    st.metric("✅ Consistência", f"{consistency*100:.1f}%")
                with col_det3:
                    st.metric("📊 Linhas Válidas", len(data))

            except Exception as e:
                st.error(f"❌ Erro ao processar com separador detectado: {e}")
                # Fallback para vírgula
                data = pd.read_csv(temp_path, sep=',')
                st.warning("⚠️ Usando vírgula como separador padrão")
        else:
            # Fallback
            data = pd.read_csv(temp_path, sep=',')
            st.warning("⚠️ Não foi possível detectar separador ideal. Usando vírgula.")

        return data, temp_path, best_separator

    except Exception as e:
        st.error(f"❌ Erro no pré-processamento: {str(e)}")
        return None, None, None

def extract_csv_files_from_zip(zip_file):
    """Extrair e listar arquivos CSV de um ZIP"""
    try:
        with zipfile.ZipFile(io.BytesIO(zip_file.getvalue()), 'r') as zip_ref:
            # Listar todos os arquivos no ZIP
            all_files = zip_ref.namelist()

            # Filtrar arquivos CSV com lógica robusta
            csv_files = []
            for file_path in all_files:
                # Verificações específicas
                is_csv = file_path.lower().endswith('.csv')
                is_not_directory = not file_path.endswith('/')
                is_not_hidden = not any(part.startswith('.') for part in file_path.split('/'))
                is_not_macos = not file_path.startswith('__MACOSX/')
                has_content = True

                try:
                    # Verificar se o arquivo tem conteúdo
                    file_info = zip_ref.getinfo(file_path)
                    has_content = file_info.file_size > 0
                except:
                    has_content = False

                if is_csv and is_not_directory and is_not_hidden and is_not_macos and has_content:
                    csv_files.append(file_path)

            if not csv_files:
                return None, "❌ Nenhum arquivo CSV válido encontrado no ZIP"

            # Extrair informações dos arquivos CSV
            csv_info = []
            for csv_file in csv_files:
                try:
                    file_info = zip_ref.getinfo(csv_file)
                    file_content = zip_ref.read(csv_file)

                    csv_info.append({
                        'name': csv_file.split('/')[-1],  # Apenas o nome do arquivo, sem caminho
                        'full_path': csv_file,  # Caminho completo para referência
                        'size': round(file_info.file_size / 1024, 2),  # KB
                        'content': file_content
                    })

                except Exception as e:
                    continue

            return csv_info, f"✅ {len(csv_info)} arquivo(s) CSV processado(s) com sucesso"

    except Exception as e:
        return None, f"❌ Erro ao processar ZIP: {str(e)}"

def load_csv_from_zip_content(csv_content, filename, agent):
    """Carregar CSV específico do conteúdo extraído do ZIP"""
    try:
        # Criar arquivo temporário com o conteúdo CSV
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.csv', delete=False) as tmp_file:
            tmp_file.write(csv_content)
            tmp_file_path = tmp_file.name

        try:
            # Usar pandas para ler diretamente
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            separators = [',', ';', '\t']

            data = None
            for encoding in encodings:
                for sep in separators:
                    try:
                        data = pd.read_csv(tmp_file_path, encoding=encoding, sep=sep, low_memory=False)
                        if data.shape[1] > 1:  # Valid if has more than 1 column
                            break
                    except:
                        continue
                if data is not None and data.shape[1] > 1:
                    break

            return data
        finally:
            # Limpar arquivo temporário
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)

    except Exception as e:
        st.error(f"❌ Erro ao carregar {filename}: {str(e)}")
        return None

def merge_multiple_csvs(csv_files_info):
    """Unir múltiplos CSVs em um único dataset"""
    try:
        all_dataframes = []
        file_info = []

        st.info("🔄 Processando e unindo todos os arquivos CSV...")

        for csv_info in csv_files_info:
            st.write(f"📄 Processando: {csv_info['name']}")

            # Carregar CSV individual
            df = load_csv_from_zip_content(csv_info['content'], csv_info['name'], None)

            if df is not None:
                # Adicionar coluna identificadora do arquivo de origem
                df['_source_file'] = csv_info['name']
                all_dataframes.append(df)
                file_info.append(f"{csv_info['name']} ({len(df)} linhas)")
                st.success(f"✅ {csv_info['name']}: {len(df)} linhas, {len(df.columns)} colunas")
            else:
                st.warning(f"⚠️ Falha ao processar {csv_info['name']}")

        if not all_dataframes:
            return None, "❌ Nenhum arquivo CSV pôde ser processado"

        # Verificar se todos têm estruturas compatíveis
        st.write("🔍 Verificando compatibilidade de estruturas...")

        first_cols = set(all_dataframes[0].columns) - {'_source_file'}
        compatible = True

        for i, df in enumerate(all_dataframes[1:], 1):
            df_cols = set(df.columns) - {'_source_file'}
            if df_cols != first_cols:
                st.warning(f"⚠️ {csv_files_info[i]['name']} tem estrutura diferente")
                compatible = False

        if compatible:
            # União simples (mesmas colunas)
            st.write("✅ Estruturas compatíveis - fazendo união simples")
            merged_df = pd.concat(all_dataframes, ignore_index=True)
            method = "União (concat)"
        else:
            # União com todas as colunas (outer join)
            st.write("🔄 Estruturas diferentes - fazendo união completa (outer join)")
            merged_df = pd.concat(all_dataframes, ignore_index=True, sort=False)
            method = "União completa (outer join)"

        # Informações finais
        total_rows = len(merged_df)
        total_cols = len(merged_df.columns)
        sources = merged_df['_source_file'].value_counts()

        info_message = f"""
✅ **Dataset unificado criado com sucesso!**

📊 **Estatísticas:**
- **Total de linhas:** {total_rows:,}
- **Total de colunas:** {total_cols}
- **Método:** {method}
- **Arquivos processados:** {len(all_dataframes)}

📁 **Origem dos dados:**
{chr(10).join([f"- {file}: {count:,} linhas" for file, count in sources.items()])}

💡 **Nota:** Coluna '_source_file' adicionada para identificar origem dos dados
        """

        return merged_df, info_message

    except Exception as e:
        return None, f"❌ Erro ao unir arquivos CSV: {str(e)}"

def load_and_analyze_data(uploaded_file, agent):
    """Carregar e preparar dados para análise usando pipeline automático"""
    try:
        # Criar arquivo temporário para o pipeline
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv', mode='wb') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            temp_path = tmp_file.name

        # Usar o pipeline automático de tratamento
        with st.spinner("🔄 Processando arquivo com pipeline automático..."):
            df_tratado, resumo = process_csv_file(temp_path)

        # Exibir resultados do pipeline
        st.success("✅ Pipeline automático executado com sucesso!")

        # Mostrar resumo do processamento
        col_resume1, col_resume2, col_resume3, col_resume4 = st.columns(4)
        with col_resume1:
            st.metric("📊 Linhas Processadas", f"{resumo['total_rows']:,}")
        with col_resume2:
            st.metric("📋 Colunas Detectadas", resumo['total_columns'])
        with col_resume3:
            st.metric("🔢 Colunas Numéricas", resumo['numeric_columns_count'])
        with col_resume4:
            st.metric("💾 Uso de Memória", f"{resumo['memory_usage_mb']} MB")

        # Exibir detalhes do pipeline em expansível
        with st.expander("🔍 Detalhes do Processamento Automático", expanded=False):
            col_detail1, col_detail2 = st.columns(2)

            with col_detail1:
                st.write("**📊 Estatísticas Gerais:**")
                st.write(f"• Total de linhas: {resumo['total_rows']:,}")
                st.write(f"• Total de colunas: {resumo['total_columns']}")
                st.write(f"• Valores ausentes tratados: {resumo['total_missing_values']:,}")
                st.write(f"• Uso de memória: {resumo['memory_usage_mb']} MB")

            with col_detail2:
                st.write("**🔧 Tipos de Dados Detectados:**")
                st.write(f"• Numéricas: {resumo['numeric_columns_count']}")
                st.write(f"• Categóricas: {resumo['categorical_columns_count']}")
                st.write(f"• Data/Hora: {resumo['datetime_columns_count']}")

            # Mostrar colunas por tipo
            if resumo['columns_by_type']['numeric']:
                st.write("**🔢 Colunas Numéricas:**")
                numeric_display = resumo['columns_by_type']['numeric'][:10]
                st.write(f"{', '.join(numeric_display)}")
                if len(resumo['columns_by_type']['numeric']) > 10:
                    st.write(f"... e mais {len(resumo['columns_by_type']['numeric']) - 10} colunas")

            if resumo['columns_by_type']['categorical']:
                st.write("**📝 Colunas Categóricas:**")
                st.write(f"{', '.join(resumo['columns_by_type']['categorical'])}")

            # Mostrar amostra dos dados tratados
            st.write("**👀 Amostra dos Dados Tratados:**")
            st.dataframe(df_tratado.head(5), width="stretch")

        # Verificar se é dataset de detecção de fraude
        expected_columns = ['Time'] + [f'V{i}' for i in range(1, 29)] + ['Amount', 'Class']
        if set(expected_columns).issubset(set(df_tratado.columns)):
            st.info("🎯 Dataset de detecção de fraude detectado!")

            # Estatísticas específicas de fraude
            fraud_count = (df_tratado['Class'] == 1).sum() if 'Class' in df_tratado.columns else 0
            normal_count = (df_tratado['Class'] == 0).sum() if 'Class' in df_tratado.columns else 0

            col_fraud1, col_fraud2, col_fraud3 = st.columns(3)
            with col_fraud1:
                st.metric("🔍 Transações Fraudulentas", f"{fraud_count:,}")
            with col_fraud2:
                st.metric("✅ Transações Normais", f"{normal_count:,}")
            with col_fraud3:
                fraud_rate = (fraud_count / len(df_tratado) * 100) if len(df_tratado) > 0 else 0
                st.metric("📊 Taxa de Fraude", f"{fraud_rate:.3f}%")

            st.success("✨ Pipeline otimizado para análise de detecção de fraude aplicado!")

        # Carregar DataFrame tratado diretamente no agente
        with st.spinner("🤖 Carregando dados tratados no sistema EDA..."):
            success = agent.load_dataframe(df_tratado, uploaded_file.name)
            if not success:
                st.error("❌ Erro ao carregar dados no agente")
                return None

        # Limpar arquivo temporário
        os.unlink(temp_path)

        st.success("🎉 Dados processados e carregados com sucesso no sistema EDA!")
        return df_tratado

    except Exception as e:
        st.error(f"❌ Erro ao carregar dados: {str(e)}")
        st.code(traceback.format_exc())
        if 'temp_path' in locals() and temp_path:
            try:
                os.unlink(temp_path)
            except:
                pass
        return None

def _generate_consolidated_markdown_report(nfes_com_problemas, total_critical, total_errors, total_warnings, total_impact):
    """Gera relatório consolidado em Markdown de todas as NF-es com problemas"""
    from datetime import datetime
    from nfe_validator.domain.entities.nfe_entity import Severity

    md = []
    md.append("# 📊 RELATÓRIO CONSOLIDADO - NF-E VALIDATOR")
    md.append("")
    md.append(f"**Data de Geração:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    md.append(f"**Total de NF-es Analisadas:** {len(nfes_com_problemas)}")
    md.append("")
    md.append("---")
    md.append("")

    # Resumo Executivo
    md.append("## 📈 RESUMO EXECUTIVO")
    md.append("")
    md.append(f"- 🔴 **Erros Críticos:** {total_critical}")
    md.append(f"- 🟠 **Erros:** {total_errors}")
    md.append(f"- 🟡 **Avisos:** {total_warnings}")
    md.append(f"- 💰 **Impacto Financeiro Total:** R$ {total_impact:,.2f}")
    md.append("")
    md.append("---")
    md.append("")

    # Organizar por severidade
    nfes_criticas = [nfe for nfe in nfes_com_problemas if any(e.severity == Severity.CRITICAL for e in nfe.validation_errors)]
    nfes_erro = [nfe for nfe in nfes_com_problemas if any(e.severity == Severity.ERROR for e in nfe.validation_errors) and nfe not in nfes_criticas]
    nfes_aviso = [nfe for nfe in nfes_com_problemas if nfe not in nfes_criticas and nfe not in nfes_erro]

    # Seção de Críticos
    if nfes_criticas:
        md.append(f"## 🔴 ERROS CRÍTICOS ({len(nfes_criticas)} NF-e(s))")
        md.append("")
        md.append("**⚠️ AÇÃO IMEDIATA NECESSÁRIA**")
        md.append("")

        for nfe in nfes_criticas:
            md.append(f"### NF-e {nfe.numero}")
            md.append("")
            md.append(f"- **Emitente:** {nfe.emitente.razao_social}")
            md.append(f"- **CNPJ:** {nfe.emitente.cnpj}")
            md.append(f"- **Chave de Acesso:** `{nfe.chave_acesso}`")
            md.append(f"- **Impacto Financeiro:** R$ {nfe.get_total_financial_impact():,.2f}")
            md.append("")

            critical_errors = [e for e in nfe.validation_errors if e.severity == Severity.CRITICAL]
            md.append(f"**Problemas Detectados:** {len(critical_errors)}")
            md.append("")

            for i, error in enumerate(critical_errors, 1):
                md.append(f"#### {i}. {error.message}")
                md.append(f"- **Campo:** {error.field}")
                md.append(f"- **Valor Atual:** {error.actual_value or 'N/A'}")
                md.append(f"- **Valor Esperado:** {error.expected_value or 'N/A'}")
                md.append(f"- **Base Legal:** {error.legal_reference or 'N/A'}")
                if error.financial_impact:
                    md.append(f"- **Impacto Financeiro:** R$ {error.financial_impact:,.2f}")
                md.append("")

            md.append("---")
            md.append("")

    # Seção de Erros
    if nfes_erro:
        md.append(f"## 🟠 ERROS ({len(nfes_erro)} NF-e(s))")
        md.append("")
        md.append("**⚠️ CORREÇÃO NECESSÁRIA**")
        md.append("")

        for nfe in nfes_erro:
            md.append(f"### NF-e {nfe.numero}")
            md.append("")
            md.append(f"- **Emitente:** {nfe.emitente.razao_social}")
            md.append(f"- **CNPJ:** {nfe.emitente.cnpj}")
            md.append(f"- **Chave de Acesso:** `{nfe.chave_acesso}`")
            md.append(f"- **Impacto Financeiro:** R$ {nfe.get_total_financial_impact():,.2f}")
            md.append("")

            error_list = [e for e in nfe.validation_errors if e.severity == Severity.ERROR]
            md.append(f"**Problemas Detectados:** {len(error_list)}")
            md.append("")

            for i, error in enumerate(error_list, 1):
                md.append(f"#### {i}. {error.message}")
                md.append(f"- **Campo:** {error.field}")
                md.append(f"- **Valor Atual:** {error.actual_value or 'N/A'}")
                md.append(f"- **Valor Esperado:** {error.expected_value or 'N/A'}")
                if error.financial_impact:
                    md.append(f"- **Impacto Financeiro:** R$ {error.financial_impact:,.2f}")
                md.append("")

            md.append("---")
            md.append("")

    # Seção de Avisos
    if nfes_aviso:
        md.append(f"## 🟡 AVISOS ({len(nfes_aviso)} NF-e(s))")
        md.append("")
        md.append("**ℹ️ REVISÃO RECOMENDADA**")
        md.append("")

        for nfe in nfes_aviso:
            md.append(f"### NF-e {nfe.numero}")
            md.append("")
            md.append(f"- **Emitente:** {nfe.emitente.razao_social}")
            md.append(f"- **CNPJ:** {nfe.emitente.cnpj}")
            md.append(f"- **Chave de Acesso:** `{nfe.chave_acesso}`")
            md.append("")

            warning_list = [e for e in nfe.validation_errors if e.severity == Severity.WARNING]
            md.append(f"**Observações:** {len(warning_list)}")
            md.append("")

            for i, warning in enumerate(warning_list, 1):
                md.append(f"#### {i}. {warning.message}")
                md.append(f"- **Campo:** {warning.field}")
                md.append(f"- **Valor Atual:** {warning.actual_value or 'N/A'}")
                md.append("")

            md.append("---")
            md.append("")

    # Rodapé
    md.append("---")
    md.append("")
    md.append("**Relatório gerado por:** NF-e Validator MVP - Setor Sucroalcooleiro")
    md.append("")
    md.append("🤖 *Powered by Claude Code*")

    return "\n".join(md)


def validate_nfe_with_pipeline(nfe, repo, use_ai_agent=False, api_key=None):
    """
    Execute full NF-e validation pipeline

    IMPORTANTE: LLM NÃO é executado automaticamente aqui.
    Validação rápida usa apenas CSV Local + SQLite.

    Args:
        nfe: NFeEntity to validate
        repo: FiscalRepository
        use_ai_agent: Enable AI agent for NCM classification (IGNORADO na validação inicial)
        api_key: Google API key for agent

    Returns:
        nfe with validation errors populated
    """
    from nfe_validator.domain.entities.nfe_entity import Severity

    # Federal Validators (usam CSV Local → SQLite, SEM LLM)
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

    # AI Agent NÃO é executado aqui automaticamente
    # Será chamado apenas sob demanda em função separada

    return nfe


def validate_nfe_item_with_ai(nfe, item_numero, repo, api_key):
    """
    Validar item específico da NF-e usando Agente IA (sob demanda)

    Args:
        nfe: NFeEntity
        item_numero: Número do item a validar
        repo: FiscalRepository
        api_key: Google API key

    Returns:
        Dict com sugestão do agente IA
    """
    try:
        from agents.ncm_agent import create_ncm_agent

        # Find item
        item = next((i for i in nfe.items if i.numero_item == item_numero), None)
        if not item:
            return {'error': 'Item não encontrado'}

        # Create agent
        agent = create_ncm_agent(repo, api_key)

        # Classify NCM
        result = agent.classify_ncm(item.descricao, item.ncm)

        return result

    except Exception as e:
        return {
            'error': str(e),
            'suggested_ncm': None,
            'confidence': 0,
            'reasoning': f"Erro ao consultar IA: {str(e)}"
        }


def render_nfe_validator_tab():
    """Render NF-e Validator tab content - usa dados do EDA"""
    st.subheader("🧾 Validação de Notas Fiscais Eletrônicas")
    st.markdown("**Validação Fiscal Automatizada - Análise de Dados Carregados no EDA**")
    st.markdown("---")

    # Get repository from session state
    repo = st.session_state.get('fiscal_repository')

    if repo is None:
        st.error("❌ Base fiscal não carregada! Configure na barra lateral.")
        return

    # Check if data is loaded from EDA
    if st.session_state.get('current_data') is None:
        st.warning("⚠️ Nenhum dado carregado no EDA")
        st.info("""
        **Para usar a validação de NF-e:**

        1. Carregue um arquivo CSV na aba "📊 Análise de Dados (EDA)"
        2. Aguarde o processamento dos dados
        3. Retorne para esta aba para validar as NF-es

        O sistema irá analisar os dados já carregados e identificar inconsistências fiscais.
        """)
        return

    # Data is loaded - show info and validate
    data = st.session_state.current_data
    filename = st.session_state.get('current_filename', 'Dataset')

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("### 📊 Dados Carregados")
        st.success(f"**Arquivo:** {filename}")
        st.metric("📄 Linhas", f"{len(data):,}")
        st.metric("📋 Colunas", len(data.columns))

        # Validate button
        if st.button("🔍 Validar NF-es dos Dados", type="primary"):
            with st.spinner("Analisando estrutura dos dados..."):
                try:
                    # Importar mapeador de colunas
                    from nfe_validator.infrastructure.parsers.column_mapper import ColumnMapper

                    # Mapear colunas automaticamente
                    mapping, missing = ColumnMapper.map_columns(data)

                    # Mostrar relatório de mapeamento
                    with st.expander("📋 Mapeamento de Colunas", expanded=True):
                        report = ColumnMapper.get_mapping_report(mapping, missing)
                        st.markdown(report)

                        # Verificar se há ALGUMA validação fiscal possível
                        capabilities = ColumnMapper.get_validation_capabilities(mapping)
                        has_any_fiscal = any([
                            capabilities.get('ncm', False),
                            capabilities.get('cfop', False),
                            capabilities.get('pis_cofins', False),
                            capabilities.get('valores', False)
                        ])

                        if not has_any_fiscal:
                            # NENHUMA validação fiscal possível - ALERTA GRANDE
                            st.markdown("""
                            <div style="
                                background-color: #ff4444;
                                color: white;
                                padding: 30px;
                                border-radius: 10px;
                                text-align: center;
                                margin: 20px 0;
                                border: 3px solid #cc0000;
                            ">
                                <h1 style="font-size: 36px; margin: 0; font-weight: bold;">
                                    ⚠️ ESSE DOCUMENTO NÃO POSSUI DADOS FISCAIS ⚠️
                                </h1>
                                <p style="font-size: 18px; margin-top: 15px;">
                                    O arquivo carregado NÃO contém informações de ITENS e IMPOSTOS necessárias para validação fiscal.
                                </p>
                            </div>
                            """, unsafe_allow_html=True)

                            st.error("""
                            **Arquivo atual:** Apenas dados cadastrais (emitente, destinatário, totais).

                            **Para validação fiscal, você precisa de um arquivo contendo:**
                            - 📦 **Itens da NF-e** (produtos, descrições, quantidades)
                            - 🏷️ **NCM** (classificação fiscal)
                            - 📋 **CFOP** (código de operação)
                            - 💰 **PIS/COFINS** (CST, alíquotas, valores)
                            - 📊 **Valores** (unitário, total)

                            💡 **Dica:** Carregue o arquivo de **ITENS** da NF-e (não apenas o cabeçalho).
                            """)
                            return  # PARA aqui - não continua

                        # Mostrar capacidades de validação
                        st.markdown("### 🔍 Validações Possíveis:")

                        cap_col1, cap_col2 = st.columns(2)
                        with cap_col1:
                            st.write("✅" if capabilities['identificacao'] else "❌", "Identificação (chave, número)")
                            st.write("✅" if capabilities['partes'] else "❌", "Emitente/Destinatário")
                            st.write("✅" if capabilities['ncm'] else "❌", "Validação NCM")
                            st.write("✅" if capabilities['cfop'] else "❌", "Validação CFOP")

                        with cap_col2:
                            st.write("✅" if capabilities['pis_cofins'] else "❌", "Validação PIS/COFINS")
                            st.write("✅" if capabilities['valores'] else "❌", "Valores e Totais")
                            st.write("✅" if capabilities['itens_completos'] else "❌", "Itens Completos")

                    # Verificar se há dados mínimos para validação
                    has_minimum_data = ColumnMapper.is_nfe_complete(mapping)

                    if not has_minimum_data:
                        st.warning("⚠️ Dados parciais detectados - Validação limitada")
                        st.info("""
                        **Colunas mínimas ausentes:**
                        - Chave de acesso ou número da NF-e
                        - Data de emissão
                        - CNPJ do emitente
                        - CNPJ do destinatário

                        **Arquivo atual:** Apenas cabeçalho de NF-e detectado.

                        💡 **Dica:** Para validação fiscal completa, carregue também o arquivo de **itens**
                        contendo NCM, CFOP, valores e impostos (PIS/COFINS).

                        ⚙️ **A validação continuará** com as colunas disponíveis, mas alguns erros podem não ser detectados.
                        """)
                        # NÃO retornar - continuar com validação parcial

                    # Aplicar mapeamento aos dados
                    with st.spinner("Aplicando mapeamento de colunas..."):
                        data_mapped = ColumnMapper.apply_mapping(data, mapping)

                        # Adicionar colunas faltantes com valores padrão
                        for col in missing:
                            if col not in data_mapped.columns:
                                # Valores padrão conforme o tipo de coluna
                                if 'valor' in col or 'aliquota' in col:
                                    data_mapped[col] = 0.0
                                elif 'cst' in col:
                                    data_mapped[col] = ''
                                elif 'numero_item' in col:
                                    data_mapped[col] = 1
                                else:
                                    data_mapped[col] = ''

                        # Save mapped dataframe to temp CSV
                        temp_dir = tempfile.gettempdir()
                        temp_path = Path(temp_dir) / f"nfe_validation_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"
                        data_mapped.to_csv(temp_path, index=False, encoding='utf-8')

                    # Parse CSV (full file, no limits)
                    with st.spinner("Processando NF-es..."):
                        parser = NFeCSVParser()
                        nfes = parser.parse_csv(str(temp_path))

                        if not nfes:
                            st.error("❌ Não foi possível processar as NF-es")
                            return

                        st.info(f"📋 {len(nfes)} NF-e(s) encontrada(s) nos dados")

                    # Validate all NF-es (RÁPIDO - apenas CSV + SQLite, SEM LLM)
                    validated_nfes = []
                    validation_errors_count = 0

                    # Progress bar for validation
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    for i, nfe in enumerate(nfes):
                        status_text.text(f"⚡ Validando NF-e {i+1}/{len(nfes)} (análise rápida - local)...")

                        try:
                            validated_nfe = validate_nfe_with_pipeline(nfe, repo, use_ai_agent=False, api_key=None)
                            validated_nfes.append(validated_nfe)
                        except Exception as e:
                            # Registrar erro mas continuar validação
                            validation_errors_count += 1
                            st.warning(f"⚠️ Erro ao validar NF-e {nfe.numero}: {str(e)}")

                            # Adicionar erro ao objeto NF-e
                            from nfe_validator.domain.entities.nfe_entity import ValidationError, Severity
                            nfe.validation_errors.append(ValidationError(
                                code='SYSTEM_ERROR',
                                field='nfe',
                                message=f'Erro inesperado na validação: {str(e)}',
                                severity=Severity.CRITICAL,
                                actual_value=str(e),
                                legal_reference='Sistema de Validação'
                            ))
                            validated_nfes.append(nfe)

                        progress_bar.progress((i + 1) / len(nfes))

                    progress_bar.empty()
                    status_text.empty()

                    # Mostrar resumo de erros de sistema
                    if validation_errors_count > 0:
                        st.warning(f"⚠️ {validation_errors_count} NF-e(s) apresentaram erro de sistema durante validação")

                    # Store in session state
                    st.session_state.nfe_results = validated_nfes
                    st.session_state.nfe_validated = True
                    st.session_state.nfe_mapping = mapping
                    st.session_state.nfe_capabilities = capabilities
                    st.session_state.nfe_has_minimum_data = has_minimum_data
                    st.session_state.nfe_missing_columns = missing

                    # Clean up temp file
                    if temp_path.exists():
                        temp_path.unlink()

                    if has_minimum_data:
                        st.success(f"✅ {len(validated_nfes)} NF-e(s) validada(s) com dados completos!")
                    else:
                        st.warning(f"⚠️ {len(validated_nfes)} NF-e(s) validada(s) com dados parciais!")
                        st.info(f"📋 {len(missing)} coluna(s) ausente(s) - Validações limitadas aplicadas")

                    st.rerun()

                except Exception as e:
                    st.error(f"❌ Erro ao processar: {str(e)}")
                    import traceback
                    with st.expander("🔍 Detalhes do erro"):
                        st.code(traceback.format_exc())

    with col2:
        st.markdown("### 📋 Como Funciona")
        st.info("""
        **Validação Automática de NF-es:**

        1. ✅ **Dados já carregados** no EDA são reutilizados
        2. 🔍 **Análise automática** de estrutura fiscal
        3. ⚠️ **Detecção de inconsistências**:
           - NCM × Descrição do produto
           - Alíquotas PIS/COFINS incorretas
           - CFOP incompatível com operação
           - Erros de cálculo e totais
           - Regras estaduais (SP/PE)

        4. 📊 **Relatórios detalhados** com impacto financeiro
        5. 🤖 **Agente IA** (opcional) para classificação NCM

        **Colunas necessárias no CSV:**
        - Identificação: chave_acesso, numero_nfe, serie, data_emissao
        - Partes: cnpj/razao_social emitente e destinatário, UF
        - Itens: ncm, cfop, quantidade, valores
        - Impostos: pis_cst/aliquota/valor, cofins_cst/aliquota/valor
        """)

    # Results section
    if st.session_state.get('nfe_validated') and st.session_state.get('nfe_results'):
        st.markdown("---")
        st.header("📈 Resultados da Validação")

        # Check if there are ANY fiscal validations possible
        capabilities = st.session_state.get('nfe_capabilities', {})
        has_any_fiscal = any([
            capabilities.get('ncm', False),
            capabilities.get('cfop', False),
            capabilities.get('pis_cofins', False),
            capabilities.get('valores', False)
        ])

        if not has_any_fiscal:
            # Nenhuma validação fiscal possível
            st.error("⚠️ **ESSE DOCUMENTO NÃO POSSUI DADOS FISCAIS**")
            st.warning("""
            O arquivo carregado não contém colunas necessárias para validação fiscal.

            **Colunas ausentes críticas:**
            - NCM (Nomenclatura Comum do Mercosul)
            - CFOP (Código Fiscal de Operações)
            - PIS/COFINS (CST, alíquotas, valores)
            - Valores de itens

            **Arquivo atual:** Apenas dados cadastrais (emitente, destinatário).

            Para validação fiscal, carregue um arquivo contendo **dados de itens e impostos**.
            """)
            return  # Não mostrar resultados

        # Show data completeness warning if needed
        if not st.session_state.get('nfe_has_minimum_data', True):
            missing_cols = st.session_state.get('nfe_missing_columns', [])
            with st.expander("⚠️ Colunas Ausentes na Validação", expanded=True):
                st.warning(f"**{len(missing_cols)} coluna(s) não encontrada(s) no arquivo:**")

                # Group by category
                categories = {
                    'Identificação': ['chave_acesso', 'numero_nfe', 'serie', 'data_emissao'],
                    'Itens': ['numero_item', 'codigo_produto', 'descricao', 'quantidade', 'valor_unitario', 'valor_total'],
                    'NCM/CFOP': ['ncm', 'cfop'],
                    'PIS': ['pis_cst', 'pis_aliquota', 'pis_valor'],
                    'COFINS': ['cofins_cst', 'cofins_aliquota', 'cofins_valor'],
                    'ICMS': ['icms_cst', 'icms_aliquota', 'icms_valor']
                }

                for category, cols in categories.items():
                    missing_in_cat = [c for c in missing_cols if c in cols]
                    if missing_in_cat:
                        st.error(f"**{category}:** {', '.join(missing_in_cat)}")

                st.info("""
                **Impacto:** Algumas validações não puderam ser executadas.
                Verifique o relatório de validação para ver quais análises foram realizadas.
                """)

        nfes = st.session_state.nfe_results

        # Select NF-e to view
        if len(nfes) > 1:
            selected_idx = st.selectbox(
                "Selecione a NF-e para visualizar:",
                range(len(nfes)),
                format_func=lambda i: f"NF-e {nfes[i].numero} - {nfes[i].chave_acesso[:10]}..."
            )
            nfe = nfes[selected_idx]
        else:
            nfe = nfes[0]

        # Summary metrics
        from nfe_validator.domain.entities.nfe_entity import Severity

        # Calcular métricas de cobertura
        total_items = len(nfe.items)

        # Itens validados por tipo (conta erros específicos ou sucesso)
        ncm_validated = sum(1 for item in nfe.items if item.ncm)
        pis_validated = 0
        cofins_validated = 0
        cfop_validated = sum(1 for item in nfe.items if item.cfop)

        # Contar validações PIS/COFINS (se não tem erro 999, foi validado)
        for item in nfe.items:
            item_errors = [e for e in nfe.validation_errors if e.item_numero == item.numero_item]
            has_pis_999 = any(e.code == 'PIS_999' for e in item_errors)
            has_cofins_999 = any(e.code == 'COFINS_999' for e in item_errors)

            if not has_pis_999 and item.impostos.pis_cst:
                pis_validated += 1
            if not has_cofins_999 and item.impostos.cofins_cst:
                cofins_validated += 1

        col1, col2, col3, col4 = st.columns(4)

        critical = sum(1 for e in nfe.validation_errors if e.severity == Severity.CRITICAL)
        error = sum(1 for e in nfe.validation_errors if e.severity == Severity.ERROR)
        warning = sum(1 for e in nfe.validation_errors if e.severity == Severity.WARNING)

        with col1:
            st.metric("🔴 Crítico", critical)
        with col2:
            st.metric("🟠 Erro", error)
        with col3:
            st.metric("🟡 Aviso", warning)
        with col4:
            impact = nfe.get_total_financial_impact()
            st.metric("💰 Impacto", f"R$ {impact:,.2f}")

        # Métricas de cobertura de validação
        st.markdown("#### 📊 Cobertura de Validação")
        col_cov1, col_cov2, col_cov3, col_cov4 = st.columns(4)

        with col_cov1:
            ncm_pct = (ncm_validated / total_items * 100) if total_items > 0 else 0
            st.metric("NCM Validado", f"{ncm_validated}/{total_items}", f"{ncm_pct:.0f}%")
        with col_cov2:
            cfop_pct = (cfop_validated / total_items * 100) if total_items > 0 else 0
            st.metric("CFOP Validado", f"{cfop_validated}/{total_items}", f"{cfop_pct:.0f}%")
        with col_cov3:
            pis_pct = (pis_validated / total_items * 100) if total_items > 0 else 0
            st.metric("PIS Validado", f"{pis_validated}/{total_items}", f"{pis_pct:.0f}%")
        with col_cov4:
            cofins_pct = (cofins_validated / total_items * 100) if total_items > 0 else 0
            st.metric("COFINS Validado", f"{cofins_validated}/{total_items}", f"{cofins_pct:.0f}%")

        # Alerta se cobertura baixa
        if pis_validated < total_items or cofins_validated < total_items:
            missing_rules = total_items - min(pis_validated, cofins_validated)
            st.info(f"""
            ℹ️ **{missing_rules} item(ns)** sem regra PIS/COFINS cadastrada na base de dados.
            Para validação completa, adicione as regras em `base_validacao.csv` ou verifique se os CSTs estão corretos.
            """)

        st.markdown("---")

        # Validation status
        if critical > 0 or error > 0:
            st.error("❌ NF-e INVÁLIDA - Requer correção")
        elif warning > 0:
            st.warning("⚠️ NF-e VÁLIDA COM AVISOS")
        else:
            st.success("✅ NF-e VÁLIDA")

        # Tabs for different views
        tab_report, tab_consolidated, tab_json, tab_ai, tab_legal, tab_download = st.tabs([
            "📋 Relatório Individual",
            "📊 Relatório Consolidado",
            "📄 JSON",
            "🤖 Sugestões IA",
            "📚 Fontes Legais",
            "💾 Downloads"
        ])

        with tab_report:
            # Generate Markdown report
            generator = ReportGenerator()
            md_report = generator.generate_markdown_report(nfe)
            st.markdown(md_report, unsafe_allow_html=True)

        with tab_consolidated:
            st.subheader("📊 Relatório Consolidado - Todas as NF-es com Problemas")

            # Filtrar apenas NF-es com problemas
            nfes_com_problemas = [nfe for nfe in nfes if len(nfe.validation_errors) > 0]

            if not nfes_com_problemas:
                st.success("✅ **Excelente!** Todas as NF-es estão conformes. Nenhum problema detectado.")
            else:
                st.warning(f"⚠️ **{len(nfes_com_problemas)} de {len(nfes)} NF-e(s) apresentaram problemas**")

                # Métricas consolidadas
                total_critical = sum(sum(1 for e in nfe.validation_errors if e.severity == Severity.CRITICAL) for nfe in nfes_com_problemas)
                total_errors = sum(sum(1 for e in nfe.validation_errors if e.severity == Severity.ERROR) for nfe in nfes_com_problemas)
                total_warnings = sum(sum(1 for e in nfe.validation_errors if e.severity == Severity.WARNING) for nfe in nfes_com_problemas)
                total_impact = sum(nfe.get_total_financial_impact() for nfe in nfes_com_problemas)

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("🔴 Total Críticos", total_critical)
                with col2:
                    st.metric("🟠 Total Erros", total_errors)
                with col3:
                    st.metric("🟡 Total Avisos", total_warnings)
                with col4:
                    st.metric("💰 Impacto Total", f"R$ {total_impact:,.2f}")

                st.markdown("---")

                # Organizar por severidade
                nfes_criticas = [nfe for nfe in nfes_com_problemas if any(e.severity == Severity.CRITICAL for e in nfe.validation_errors)]
                nfes_erro = [nfe for nfe in nfes_com_problemas if any(e.severity == Severity.ERROR for e in nfe.validation_errors) and nfe not in nfes_criticas]
                nfes_aviso = [nfe for nfe in nfes_com_problemas if nfe not in nfes_criticas and nfe not in nfes_erro]

                # Seção de Críticos
                if nfes_criticas:
                    with st.expander(f"🔴 **CRÍTICOS** ({len(nfes_criticas)} NF-e(s)) - Ação Imediata Necessária", expanded=True):
                        for nfe in nfes_criticas:
                            st.markdown(f"### NF-e {nfe.numero} - {nfe.emitente.razao_social}")
                            st.markdown(f"**Chave:** `{nfe.chave_acesso}`")

                            critical_errors = [e for e in nfe.validation_errors if e.severity == Severity.CRITICAL]
                            st.error(f"**{len(critical_errors)} erro(s) crítico(s) detectado(s)**")

                            for error in critical_errors:
                                st.markdown(f"""
                                - **Campo:** {error.field}
                                - **Problema:** {error.message}
                                - **Valor atual:** {error.actual_value or 'N/A'}
                                - **Esperado:** {error.expected_value or 'N/A'}
                                - **Base legal:** {error.legal_reference or 'N/A'}
                                """)

                                if error.financial_impact:
                                    st.warning(f"💰 Impacto financeiro: R$ {error.financial_impact:,.2f}")

                            st.markdown("---")

                # Seção de Erros
                if nfes_erro:
                    with st.expander(f"🟠 **ERROS** ({len(nfes_erro)} NF-e(s)) - Correção Necessária", expanded=False):
                        for nfe in nfes_erro:
                            st.markdown(f"### NF-e {nfe.numero} - {nfe.emitente.razao_social}")
                            st.markdown(f"**Chave:** `{nfe.chave_acesso}`")

                            error_list = [e for e in nfe.validation_errors if e.severity == Severity.ERROR]
                            st.warning(f"**{len(error_list)} erro(s) detectado(s)**")

                            for error in error_list:
                                st.markdown(f"""
                                - **Campo:** {error.field}
                                - **Problema:** {error.message}
                                - **Valor atual:** {error.actual_value or 'N/A'}
                                - **Esperado:** {error.expected_value or 'N/A'}
                                """)

                                if error.financial_impact:
                                    st.info(f"💰 Impacto financeiro: R$ {error.financial_impact:,.2f}")

                            st.markdown("---")

                # Seção de Avisos
                if nfes_aviso:
                    with st.expander(f"🟡 **AVISOS** ({len(nfes_aviso)} NF-e(s)) - Revisão Recomendada", expanded=False):
                        for nfe in nfes_aviso:
                            st.markdown(f"### NF-e {nfe.numero} - {nfe.emitente.razao_social}")
                            st.markdown(f"**Chave:** `{nfe.chave_acesso}`")

                            warning_list = [e for e in nfe.validation_errors if e.severity == Severity.WARNING]
                            st.info(f"**{len(warning_list)} aviso(s) detectado(s)**")

                            for warning in warning_list:
                                st.markdown(f"""
                                - **Campo:** {warning.field}
                                - **Observação:** {warning.message}
                                - **Valor atual:** {warning.actual_value or 'N/A'}
                                """)

                            st.markdown("---")

                # Botão de exportação do relatório consolidado
                st.markdown("### 💾 Exportar Relatório Consolidado")

                # Gerar relatório consolidado em Markdown
                consolidated_md = _generate_consolidated_markdown_report(nfes_com_problemas, total_critical, total_errors, total_warnings, total_impact)

                col_exp1, col_exp2 = st.columns(2)
                with col_exp1:
                    st.download_button(
                        label="📥 Baixar Relatório Consolidado (Markdown)",
                        data=consolidated_md,
                        file_name=f"relatorio_consolidado_{len(nfes_com_problemas)}_nfes.md",
                        mime="text/markdown"
                    )

        with tab_json:
            # Generate JSON report
            json_report = generator.generate_json_report(nfe)
            st.json(json_report)

        with tab_ai:
            st.subheader("🤖 Validação com Inteligência Artificial")

            st.info("""
            **Validação sob demanda com LLM:**

            A validação inicial foi realizada usando apenas regras locais (CSV + SQLite).
            Use o Agente IA para validar itens específicos quando houver dúvidas sobre NCM.
            """)

            # Check if API key is available
            api_key = st.session_state.get('ncm_api_key', None)

            if not api_key:
                st.warning("⚠️ Configure a chave da API Gemini na barra lateral para usar o Agente IA")
            else:
                st.success("✅ Agente IA disponível")

                # Show items with NCM errors for AI validation
                ncm_errors = [e for e in nfe.validation_errors if 'NCM' in e.code]

                if ncm_errors:
                    st.warning(f"🔍 {len(ncm_errors)} erro(s) de NCM detectado(s) na validação local")

                    # Select item to validate with AI
                    items_with_errors = list(set([e.item_numero for e in ncm_errors if e.item_numero]))

                    if items_with_errors:
                        # Criar mapeamento de item_numero para item completo
                        # Normalizar tipos para int
                        items_with_errors = [int(x) if not isinstance(x, int) else x for x in items_with_errors]
                        item_map = {int(item.numero_item): item for item in nfe.items if int(item.numero_item) in items_with_errors}

                        def format_item_option(x):
                            """Format item option for selectbox"""
                            try:
                                item = item_map[int(x)]
                                desc = item.descricao[:50] if item.descricao else "Sem descrição"
                                ncm = item.ncm if item.ncm else "N/A"
                                return f"Item #{x} - {desc}... (NCM: {ncm})"
                            except:
                                return f"Item #{x}"

                        selected_items = st.multiselect(
                            "Selecione os itens para validar com IA (você pode selecionar múltiplos itens):",
                            items_with_errors,
                            default=[],
                            format_func=format_item_option,
                            help="Clique no campo e selecione quantos itens desejar. Os itens selecionados aparecerão como tags."
                        )

                        col_btn1, col_btn2 = st.columns([3, 1])
                        with col_btn1:
                            validate_btn = st.button("🤖 Validar com Agente IA", type="primary", disabled=len(selected_items) == 0)
                        with col_btn2:
                            if st.button("Selecionar Todos"):
                                selected_items = items_with_errors
                                st.rerun()

                        if validate_btn:
                            if 'ai_ncm_suggestions' not in st.session_state:
                                st.session_state.ai_ncm_suggestions = {}

                            # Validação em lote
                            progress_bar = st.progress(0)
                            status_text = st.empty()

                            for i, item_num in enumerate(selected_items):
                                status_text.text(f"🤖 Consultando Gemini 2.5 para Item #{item_num} ({i+1}/{len(selected_items)})...")
                                result = validate_nfe_item_with_ai(nfe, item_num, repo, api_key)
                                st.session_state.ai_ncm_suggestions[item_num] = result
                                progress_bar.progress((i + 1) / len(selected_items))

                            progress_bar.empty()
                            status_text.empty()
                            st.rerun()
                else:
                    st.success("✅ Nenhum erro de NCM detectado na validação local")

                    # Option to validate all items anyway
                    if st.checkbox("Validar todos os itens com IA (pode demorar)"):
                        if st.button("🚀 Validar TODOS com IA", type="secondary"):
                            st.session_state.ai_ncm_suggestions = {}

                            progress = st.progress(0)
                            status = st.empty()

                            for i, item in enumerate(nfe.items):
                                status.text(f"Validando item {i+1}/{len(nfe.items)} com IA...")
                                result = validate_nfe_item_with_ai(nfe, item.numero_item, repo, api_key)
                                st.session_state.ai_ncm_suggestions[item.numero_item] = result
                                progress.progress((i + 1) / len(nfe.items))

                            progress.empty()
                            status.empty()
                            st.rerun()

            # Show AI suggestions if available
            if st.session_state.get('ai_ncm_suggestions'):
                st.markdown("---")
                st.subheader("📊 Sugestões do Agente IA")

                for item_num, suggestion in st.session_state.ai_ncm_suggestions.items():
                    with st.expander(f"Item #{item_num}", expanded=True):
                        if suggestion.get('error'):
                            st.error(f"❌ Erro: {suggestion['error']}")
                        else:
                            col1, col2, col3 = st.columns(3)

                            with col1:
                                st.metric("NCM Sugerido", suggestion.get('suggested_ncm', 'N/A'))
                            with col2:
                                st.metric("Confiança", f"{suggestion.get('confidence', 0)}%")
                            with col3:
                                is_correct = suggestion.get('is_correct')
                                status = "✅ Correto" if is_correct else "❌ Incorreto" if is_correct is False else "❓ Incerto"
                                st.metric("Status", status)

                            st.markdown("**Raciocínio do Agente:**")
                            st.code(suggestion.get('reasoning', 'N/A'), language='text')

        with tab_legal:
            st.subheader("📚 Fontes de Consulta Legal")

            st.info("""
            **Base de Conhecimento Legislativo:**

            Esta seção apresenta as principais fontes legais utilizadas nas validações fiscais.
            Use como referência para contestações, consultas e treinamento.
            """)

            # Filtros
            col_filter1, col_filter2 = st.columns(2)

            with col_filter1:
                category_filter = st.selectbox(
                    "Filtrar por Categoria:",
                    ["Todas", "FEDERAL", "ESTADUAL", "JURISPRUDENCIA"],
                    key="legal_category_filter"
                )

            with col_filter2:
                search_query = st.text_input(
                    "🔍 Buscar por palavra-chave:",
                    placeholder="Ex: açúcar, PIS, ICMS, crédito...",
                    key="legal_search"
                )

            # Buscar referências
            if search_query:
                references = repo.search_legal_references(search_query)
                st.info(f"📊 {len(references)} referência(s) encontrada(s) para: **{search_query}**")
            elif category_filter != "Todas":
                references = repo.get_all_legal_references(category=category_filter)
            else:
                references = repo.get_all_legal_references()

            # Agrupar por scope
            categories = {}
            for ref in references:
                cat = ref['scope']
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(ref)

            # Exibir por categoria
            for cat_name, refs in sorted(categories.items()):
                with st.expander(f"📂 {cat_name} ({len(refs)} referência(s))", expanded=(category_filter == cat_name)):
                    for ref in refs:
                        st.markdown(f"### {ref['title']}")

                        col_meta1, col_meta2 = st.columns(2)
                        with col_meta1:
                            st.markdown(f"**Código:** `{ref['code']}`")
                            st.markdown(f"**Tipo:** {ref['ref_type']}")
                        with col_meta2:
                            st.markdown(f"**Âmbito:** {ref['scope']}")
                            if ref.get('published_date'):
                                st.markdown(f"**Data:** {ref['published_date']}")

                        st.markdown(f"**Descrição:**")
                        st.markdown(ref.get('summary', 'N/A'))

                        if ref.get('notes'):
                            st.info(f"💡 **Notas:** {ref['notes']}")

                        if ref.get('url'):
                            st.markdown(f"🔗 [Acessar legislação completa]({ref['url']})")

                        st.markdown("---")

            # Estatísticas
            st.markdown("### 📊 Estatísticas da Base Legal")
            col_stat1, col_stat2, col_stat3 = st.columns(3)

            with col_stat1:
                federal_count = len([r for r in references if r['scope'] == 'FEDERAL'])
                st.metric("Federal", federal_count)

            with col_stat2:
                estadual_count = len([r for r in references if r['scope'] == 'ESTADUAL'])
                st.metric("Estadual", estadual_count)

            with col_stat3:
                municipal_count = len([r for r in references if r['scope'] == 'MUNICIPAL'])
                st.metric("Municipal", municipal_count)

        with tab_download:
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
                import json
                json_bytes = json.dumps(json_report, ensure_ascii=False, indent=2).encode('utf-8')
                st.download_button(
                    label="📋 Download JSON",
                    data=json_bytes,
                    file_name=f"nfe_{nfe.numero}_report.json",
                    mime="application/json"
                )


def main():
    """Função principal da aplicação Streamlit"""
    initialize_session_state()

    # Cabeçalho principal
    st.markdown("""
    <div class="main-header">
        <h1>🤖 Sistema EDA + NF-e Validator</h1>
        <p>Análise inteligente de dados CSV e Validação Fiscal automatizada</p>
    </div>
    """, unsafe_allow_html=True)

    # Criar tabs para EDA e NF-e Validator
    if NFE_VALIDATOR_AVAILABLE and st.session_state.get('fiscal_repository') is not None:
        tab_eda, tab_nfe = st.tabs(["📊 Análise de Dados (EDA)", "🧾 Validação de NF-e"])
    else:
        # Se NF-e não disponível, mostrar só EDA
        tab_eda = st.container()
        tab_nfe = None

    # Sidebar para configurações
    with st.sidebar:
        st.header("⚙️ Configurações")

        # Seção de API Keys
        st.subheader("🔑 Chaves de API")

        with st.expander("🤖 Configurar APIs de IA", expanded=True):
            # Google Gemini API Key
            gemini_api_key = st.text_input(
                "Google Gemini API Key:",
                type="password",
                help="Obtenha sua chave em: https://makersuite.google.com/app/apikey",
                key="gemini_api_key_input"
            )

            # OpenAI API Key
            openai_api_key = st.text_input(
                "OpenAI API Key:",
                type="password",
                help="Obtenha sua chave em: https://platform.openai.com/api-keys",
                key="openai_api_key_input"
            )

            # Grok API Key
            grok_api_key = st.text_input(
                "Grok API Key:",
                type="password",
                help="Obtenha sua chave em: https://x.ai",
                key="grok_api_key_input"
            )

        # Salvar API keys no session_state
        if gemini_api_key:
            st.session_state.gemini_api_key = gemini_api_key
        if openai_api_key:
            st.session_state.openai_api_key = openai_api_key
        if grok_api_key:
            st.session_state.grok_api_key = grok_api_key

        # Modelo padrão (por enquanto apenas Gemini é suportado)
        model_option = "gemini"
        api_key = gemini_api_key  # Usar Gemini como padrão

        # Botão de inicialização
        if st.button("🚀 Inicializar Modelo", type="primary"):
            if model_option == "gemini" and not api_key:
                st.error("❌ Chave da API é obrigatória para Gemini")
            else:
                with st.spinner(f"Inicializando {model_option.title()}..."):
                    success, agent, message = initialize_model(model_option, api_key)

                    if success:
                        st.session_state.eda_agent = agent
                        st.session_state.selected_model = model_option
                        st.session_state.model_initialized = True
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)

        # Status do modelo
        if st.session_state.model_initialized and st.session_state.eda_agent:
            st.markdown(f"""
            <div class="success-box">
                ✅ <strong>{st.session_state.selected_model.title()} Ativo!</strong>
            </div>
            """, unsafe_allow_html=True)

        # NF-e Validator Settings (independente do EDA)
        if NFE_VALIDATOR_AVAILABLE:
            st.markdown("---")
            st.subheader("🧾 NF-e Validator")

            # Check if fiscal repository is loaded
            if 'fiscal_repository' not in st.session_state:
                st.session_state.fiscal_repository = None
                st.session_state.nfe_validated = False
                st.session_state.nfe_results = None

            # Load repository button
            if st.session_state.fiscal_repository is None:
                st.info("💡 **Todas as camadas de validação estão ativadas:**\n- 📄 CSV Local\n- 💾 SQLite\n- 🤖 Agente LLM (fallback)")

                if st.button("📚 Carregar Base Fiscal", type="secondary"):
                    with st.spinner("Carregando base de dados fiscal..."):
                        try:
                            # Todas as camadas ativadas por padrão
                            st.session_state.fiscal_repository = FiscalRepository(
                                use_local_csv=True,
                                use_ai_fallback=True
                            )
                            st.success("✅ Base fiscal carregada com todas as camadas!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Erro ao carregar base: {e}")
            else:
                st.success("✅ Base fiscal carregada")

                # Show repository layers status
                try:
                    layers_status = st.session_state.fiscal_repository.get_repository_layers_status()

                    with st.expander("📊 Status das Camadas", expanded=False):
                        st.metric("Camadas Ativas", f"{layers_status['total_camadas_ativas']}/{layers_status['camadas_disponiveis']}")

                        for layer in layers_status['camadas_ativas']:
                            st.success(f"✅ {layer}")

                        # Detalhes CSV Local
                        if layers_status['csv_local']['disponivel']:
                            csv_stats = layers_status['csv_local']
                            st.info(f"📄 CSV Local: {csv_stats['total_regras']} regras ({csv_stats['acucar_ncms']} açúcar + {csv_stats['insumos_ncms']} insumos)")

                        # Detalhes SQLite
                        if layers_status['sqlite']['disponivel']:
                            st.info(f"💾 SQLite: {layers_status['sqlite']['total_ncm_rules']} NCMs cadastrados")
                except Exception as e:
                    st.warning(f"⚠️ Não foi possível obter estatísticas: {e}")

                # Show repository stats (legacy)
                try:
                    stats = st.session_state.fiscal_repository.get_statistics()
                    st.metric("Regras Carregadas", sum(stats.values()))
                except:
                    pass

                # API Key for AI validation (optional, on-demand only)
                st.markdown("**🤖 Agente IA (Opcional - Sob Demanda)**")

                # Try to reuse Gemini API key if available
                if st.session_state.model_initialized and st.session_state.eda_agent:
                    ncm_api_key = st.session_state.eda_agent.api_key
                    st.info("✅ Usando chave da API do Gemini EDA")
                    st.session_state.ncm_api_key = ncm_api_key
                else:
                    ncm_api_key = st.text_input(
                        "Google API Key (Gemini):",
                        type="password",
                        help="Necessário apenas para validação com IA (sob demanda). A validação local funciona sem API key.",
                        key="ncm_api_key"
                    )
                    st.session_state.ncm_api_key = ncm_api_key

                st.caption("💡 A validação inicial NÃO usa IA - apenas regras locais (rápido)")

        # Sempre usar chat moderno
        if MODERN_CHAT_AVAILABLE:
            st.session_state.use_modern_chat = True

        # Mostrar informações do dataset atual se carregado
        if st.session_state.get('current_data') is not None:
            data = st.session_state.current_data
            filename = st.session_state.get('current_filename', 'Dataset')

            st.subheader("📊 Dataset Carregado")

            # Verificar se é um dataset unificado (tem coluna _source_file)
            if '_source_file' in data.columns:
                sources = data['_source_file'].value_counts()
                st.success(f"🔗 **{filename}**")
                st.write(f"📏 **Dimensões:** {data.shape[0]:,} linhas × {data.shape[1]} colunas")

                with st.expander("📁 Arquivos de origem", expanded=False):
                    for source, count in sources.items():
                        st.write(f"• **{source}:** {count:,} linhas")
            else:
                st.success(f"📄 **{filename}**")
                st.write(f"📏 **Dimensões:** {data.shape[0]:,} linhas × {data.shape[1]} colunas")

        st.divider()

        # Upload de arquivo
        if st.session_state.model_initialized:
            st.subheader("📂 Upload de Dados")
            uploaded_file = st.file_uploader(
                "Escolha um arquivo CSV ou ZIP:",
                type=['csv', 'zip'],
                help="Selecione um arquivo CSV individual ou ZIP com múltiplos CSVs"
            )

            if uploaded_file and st.session_state.eda_agent:
                file_extension = uploaded_file.name.lower().split('.')[-1]

                if file_extension == 'csv':
                    # Processamento normal de CSV
                    if st.button("📊 Carregar Dados CSV"):
                        with st.spinner("Carregando e analisando dados..."):
                            data = load_and_analyze_data(uploaded_file, st.session_state.eda_agent)
                            if data is not None:
                                st.session_state.current_data = data
                                st.success("✅ Dados CSV carregados com sucesso!")
                                st.rerun()

                elif file_extension == 'zip':
                    # Processamento de ZIP - UNIR todos os arquivos em um dataset
                    if st.button("📊 Carregar e UNIR TODOS os CSVs do ZIP"):
                        with st.spinner("Extraindo arquivos CSV do ZIP..."):
                            csv_files, message = extract_csv_files_from_zip(uploaded_file)

                        st.info(message)

                        if csv_files:
                            # Unir TODOS os arquivos CSV em um único dataset
                            with st.spinner("Unindo todos os arquivos CSV..."):
                                merged_data, merge_info = merge_multiple_csvs(csv_files)

                            if merged_data is not None:
                                # Carregar dataset unificado no agente
                                st.session_state.eda_agent.data = merged_data
                                st.session_state.eda_agent.filename = f"ZIP_Unified_{len(csv_files)}_files"
                                st.session_state.current_data = merged_data
                                st.session_state.current_filename = f"Dataset Unificado ({len(csv_files)} arquivos)"

                                # Limpar múltiplos datasets se existir
                                if 'multiple_datasets' in st.session_state:
                                    del st.session_state.multiple_datasets

                                # Mostrar informações detalhadas
                                st.success("🎉 Dataset unificado criado com sucesso!")
                                st.markdown(merge_info)
                                st.rerun()
                            else:
                                st.error(f"❌ Falha ao unir arquivos: {merge_info}")

    # Tab NF-e Validator (if available)
    if tab_nfe is not None:
        with tab_nfe:
            render_nfe_validator_tab()

    # Tab EDA - wrap existing EDA content
    with tab_eda:
        # Área principal de conteúdo EDA
        if not st.session_state.model_initialized:
            st.info("👆 Selecione e inicialize um modelo de IA com agentes na barra lateral para começar.")

            # Informações sobre os modelos disponíveis com agentes
            st.subheader("🤖 Modelos de IA Disponíveis")

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("""
                ### 🧠 Google Gemini + Agentes
                **🌐 IA Avançada com Orquestração**
                - 🤖 **Agentes especializados** para análise
                - 🧠 **LLM Gemini** para consultas inteligentes
                - 📊 **Geração automática** de código Python
                - 🔍 **Análise contextual** dos dados
                - 📝 **Respostas detalhadas** e insights profundos
                - ⚠️ Requer API key do Google
                """)

            with col2:
                st.markdown("""
                ### 🔧 Recursos Avançados
                **⚡ Funcionalidades Premium**
                - 🧠 **Memória contextual** entre perguntas
                - 🔄 **Pipeline automático** de dados
                - 📊 **Visualizações dinâmicas**
                - 🎯 **Análises especializadas**
                - 📝 **Relatórios detalhados**
                - ✨ **Clean Architecture** enterprise
                """)

            st.markdown("---")
            st.info("💡 **Modelo ativo**: **Gemini** com agentes para orquestração inteligente de análises complexas!")

        elif st.session_state.current_data is None:
            st.info("👆 Faça upload de um arquivo CSV na barra lateral para começar a análise.")

        else:
            # Interface principal com dados carregados
            st.subheader("📊 Dados Processados e Carregados")

            # Badge indicando uso do pipeline
            st.markdown("""
            <div style="background: linear-gradient(90deg, #28a745, #20c997); color: white; padding: 10px; border-radius: 5px; text-align: center; margin-bottom: 20px;">
                ✨ <strong>Dados processados com Pipeline Automático</strong> - Normalizados e otimizados para análise
            </div>
            """, unsafe_allow_html=True)

            # Informações básicas dos dados tratados
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("📄 Linhas", f"{len(st.session_state.current_data):,}")
            with col2:
                st.metric("📋 Colunas", len(st.session_state.current_data.columns))
            with col3:
                st.metric("🔢 Numéricas", len(st.session_state.current_data.select_dtypes(include=['number']).columns))
            with col4:
                st.metric("📝 Categóricas", len(st.session_state.current_data.select_dtypes(include=['object']).columns))

            # Preview dos dados com informações detalhadas
            with st.expander("👀 Visualizar Dados", expanded=False):
                data = st.session_state.current_data

                # Mostrar informações sobre o dataset
                st.write("**Informações do Dataset:**")

                # Verificar se é dataset de fraude
                if 'Class' in data.columns and 'Time' in data.columns and 'Amount' in data.columns:
                    col_desc1, col_desc2 = st.columns(2)

                    with col_desc1:
                        st.write("**📋 Estrutura do Dataset de Fraude:**")
                        st.write("• **Time**: Segundos desde primeira transação")
                        st.write("• **V1-V28**: Componentes PCA (dados anonimizados)")
                        st.write("• **Amount**: Valor da transação")
                        st.write("• **Class**: 0=Normal, 1=Fraudulenta")

                    with col_desc2:
                        st.write("**📊 Estatísticas Rápidas:**")
                        st.write(f"• Total de transações: {len(data):,}")
                        st.write(f"• Período: {data['Time'].min():.0f}s a {data['Time'].max():.0f}s")
                        st.write(f"• Valor médio: R$ {data['Amount'].mean():.2f}")
                        st.write(f"• Valor máximo: R$ {data['Amount'].max():.2f}")

                # Mostrar primeiras linhas
                st.write("**🔍 Primeiras 10 linhas:**")
                st.dataframe(data.head(10), width="stretch")

                # Mostrar informações dos tipos de dados
                st.write("**🔤 Tipos de Dados:**")
                col_types1, col_types2 = st.columns(2)

                with col_types1:
                    numeric_cols = data.select_dtypes(include=['number']).columns.tolist()
                    st.write(f"**Numéricas ({len(numeric_cols)}):** {', '.join(numeric_cols[:10])}")
                    if len(numeric_cols) > 10:
                        st.write(f"... e mais {len(numeric_cols) - 10} colunas")

                with col_types2:
                    categorical_cols = data.select_dtypes(include=['object']).columns.tolist()
                    if categorical_cols:
                        st.write(f"**Categóricas ({len(categorical_cols)}):** {', '.join(categorical_cols)}")
                    else:
                        st.write("**Categóricas:** Nenhuma detectada")

            # Interface de conversação
            model_name = "🧠 Gemini + Agentes"  # Apenas Gemini é suportado

            # Usar apenas chat moderno
            if MODERN_CHAT_AVAILABLE:
                render_modern_chat()
                return

            # Fallback para chat clássico se moderno não estiver disponível
            st.subheader(f"💬 Chat com {model_name}")
            st.warning("Chat moderno não disponível, usando versão clássica")

            # Cabeçalho do chat com botões de controle
            col_chat1, col_chat2, col_chat3 = st.columns([3, 1, 1])
            with col_chat1:
                st.markdown("### 💬 Histórico da Conversa")
            with col_chat2:
                if st.button("🗑️ Limpar Chat", help="Limpar histórico de conversa", key="clear_chat_btn"):
                    st.session_state.conversation_history = []
                    st.session_state.show_response = False
                    st.rerun()
            with col_chat3:
                if st.button("🗂️ Limpar Gráficos", help="Remover gráficos gerados", key="clear_charts_btn"):
                    try:
                        settings = get_settings()
                        charts_dir = Path(settings.charts_dir)
                        if charts_dir.exists():
                            import shutil
                            shutil.rmtree(charts_dir)
                            charts_dir.mkdir(exist_ok=True)
                        # Limpar também a lista de gráficos da sessão
                        st.session_state.session_charts = []
                        st.success("✅ Gráficos removidos!")
                        st.rerun()
                    except:
                        st.error("❌ Erro ao remover gráficos")

            # Exibir histórico de conversas no estilo chat
            st.markdown('<div class="chat-container">', unsafe_allow_html=True)

            if st.session_state.conversation_history:
                # Exibir conversas em ordem cronológica com keys únicas
                for i, conv in enumerate(st.session_state.conversation_history):
                    try:
                        # Validar estrutura da conversa
                        if not all(key in conv for key in ['question', 'answer', 'timestamp']):
                            continue

                        # Container único para cada conversa
                        with st.container():
                            # Mensagem do usuário
                            question_text = str(conv['question'])[:500]  # Limitar tamanho
                            st.markdown(f"""
                            <div class="user-message">
                                {question_text}
                                <div class="message-timestamp">Você • {conv['timestamp'].strftime('%H:%M:%S')}</div>
                            </div>
                            """, unsafe_allow_html=True)

                            # Resposta do assistente com melhor formatação
                            answer_text = str(conv['answer'])
                            if len(answer_text) > 5000:  # Limitar resposta para evitar problemas
                                answer_text = answer_text[:5000] + "... [resposta truncada]"

                            # Limpar caracteres problemáticos
                            formatted_answer = answer_text.replace('\n', '<br>').replace('  ', '&nbsp;&nbsp;')
                            formatted_answer = formatted_answer.replace('"', '&quot;').replace("'", '&#39;')

                            # Destacar títulos em negrito
                            formatted_answer = formatted_answer.replace('📊 ANALISE', '<strong>📊 ANÁLISE</strong>')
                            formatted_answer = formatted_answer.replace('📈 ANALISE', '<strong>📈 ANÁLISE</strong>')
                            formatted_answer = formatted_answer.replace('🔍 DETECCAO', '<strong>🔍 DETECÇÃO</strong>')
                            formatted_answer = formatted_answer.replace('💡 CONCLUSOES', '<strong>💡 CONCLUSÕES</strong>')
                            formatted_answer = formatted_answer.replace('📊 ANÁLISE DE TIPOS DE DADOS', '<strong>📊 ANÁLISE DE TIPOS DE DADOS</strong>')
                            formatted_answer = formatted_answer.replace('📈 ANÁLISE DE CORRELAÇÕES', '<strong>📈 ANÁLISE DE CORRELAÇÕES</strong>')
                            formatted_answer = formatted_answer.replace('🔍 DETECÇÃO DE OUTLIERS', '<strong>🔍 DETECÇÃO DE OUTLIERS</strong>')

                            st.markdown(f"""
                            <div class="assistant-message">
                                {formatted_answer}
                                <div class="message-timestamp">{model_name} • {conv['timestamp'].strftime('%H:%M:%S')}</div>
                            </div>
                            """, unsafe_allow_html=True)

                    except Exception as e:
                        st.error(f"❌ Erro ao exibir conversa {i}: {str(e)}")
                        continue

            st.markdown('</div>', unsafe_allow_html=True)

            # Campo de pergunta com estilo melhorado
            st.markdown("""
            <style>
            .stTextInput > div > div > input {
                background-color: #21262d;
                color: #f0f6fc;
                border: 1px solid #30363d;
                border-radius: 10px;
                padding: 12px;
            }
            .stTextInput > div > div > input:focus {
                border-color: #007bff;
                box-shadow: 0 0 0 1px #007bff;
            }
            </style>
            """, unsafe_allow_html=True)

            # Inicializar estados para controle de reatividade
            if 'input_counter' not in st.session_state:
                st.session_state.input_counter = 0
            if 'last_question' not in st.session_state:
                st.session_state.last_question = ""
            if 'processing' not in st.session_state:
                st.session_state.processing = False
            if 'show_response' not in st.session_state:
                st.session_state.show_response = False

            # Seção de input com container estável
            with st.container():
                # Usar form para melhor controle de reatividade
                with st.form(key=f"question_form_{st.session_state.input_counter}", clear_on_submit=True):
                    user_question = st.text_input(
                        "",
                        placeholder="Digite sua pergunta sobre os dados...",
                        key=f"input_field_{st.session_state.input_counter}"
                    )

                    col1, col2 = st.columns([1, 4])
                    with col1:
                        send_button = st.form_submit_button("📤 Enviar", type="primary")

                    with col2:
                        if st.session_state.processing:
                            st.info("🔄 Processando pergunta...")

            # Processar pergunta quando enviada
            if send_button and user_question and not st.session_state.processing:
                st.session_state.processing = True
                st.session_state.last_question = user_question
                st.rerun()

            # Processar a pergunta em estado separado para evitar conflitos
            if st.session_state.processing and st.session_state.last_question:
                with st.spinner("🤖 Analisando seus dados..."):
                    try:
                        # Configurar callback para registrar gráficos gerados
                        def chart_callback(chart_names):
                            for chart_name in chart_names:
                                if chart_name not in st.session_state.session_charts:
                                    st.session_state.session_charts.append(chart_name)

                        st.session_state.eda_agent.set_chart_callback(chart_callback)

                        # Processar pergunta através do agente
                        response = st.session_state.eda_agent.process_question(st.session_state.last_question)

                        # Validar resposta antes de salvar
                        if not response:
                            response = "❌ Nenhuma resposta gerada pelo agente"

                        # Limpar resposta para evitar problemas de formatação
                        cleaned_response = str(response).replace("```python", "```\npython").replace("```", "\n```\n")

                        # Salvar na conversa
                        st.session_state.conversation_history.append({
                            'question': st.session_state.last_question,
                            'answer': cleaned_response,
                            'timestamp': pd.Timestamp.now()
                        })

                        # Reset do estado de processamento
                        st.session_state.processing = False
                        st.session_state.last_question = ""
                        st.session_state.input_counter += 1
                        st.session_state.show_response = True

                        # Reexecutar para atualizar interface
                        st.rerun()

                    except Exception as e:
                        st.error(f"❌ Erro na análise: {str(e)}")
                        st.write("**Detalhes do erro:**")
                        st.code(str(e))
                        st.session_state.processing = False

            # Mostrar última resposta de forma estável
            if st.session_state.show_response and st.session_state.conversation_history:
                try:
                    latest_conv = st.session_state.conversation_history[-1]
                    st.success("✅ Nova resposta adicionada ao chat!")

                    # Garantir que temos uma resposta válida
                    if 'answer' in latest_conv and latest_conv['answer']:
                        with st.expander("📋 Última Resposta", expanded=True):
                            answer_text = str(latest_conv['answer'])

                            st.markdown(f"**🙋 Pergunta:** {latest_conv['question']}")
                            st.markdown(f"**⏰ Horário:** {latest_conv['timestamp'].strftime('%d/%m/%Y %H:%M:%S')}")

                            # Processar resposta para separar código e resultado
                            if "Código gerado:" in answer_text and "="*50 in answer_text:
                                # Separar partes da resposta
                                parts = answer_text.split("="*50)

                                # Código gerado
                                if len(parts) > 0 and "Código gerado:" in parts[0]:
                                    code_section = parts[0].replace("Código gerado:", "").strip()
                                    if code_section:
                                        st.markdown("**🐍 Código Python Gerado:**")
                                        st.code(code_section, language="python")

                                # Resultado da execução
                                if len(parts) > 1:
                                    result_text = parts[1].strip()
                                    if result_text:
                                        st.markdown("**📊 Resultado da Análise:**")

                                        # Processar diferentes seções do resultado
                                        sections = result_text.split('\n')
                                        current_section = ""

                                        for line in sections:
                                            if line.startswith("Resultado:"):
                                                if current_section:
                                                    st.text(current_section)
                                                    current_section = ""
                                                st.markdown("**📈 Resultado:**")
                                            elif line.startswith("Avisos/Erros:"):
                                                if current_section:
                                                    st.text(current_section)
                                                    current_section = ""
                                                if line.strip() != "Avisos/Erros:":
                                                    st.markdown("**⚠️ Avisos/Erros:**")
                                            elif line.startswith("🔍 Conclusão:"):
                                                if current_section:
                                                    st.text(current_section)
                                                    current_section = ""
                                                st.markdown("**🔍 Conclusão da Análise:**")
                                            else:
                                                current_section += line + "\n"

                                        # Mostrar última seção se houver
                                        if current_section.strip():
                                            st.text(current_section.strip())
                            else:
                                # Resposta normal sem código
                                st.markdown("**🤖 Resposta:**")
                                if len(answer_text) > 10000:
                                    answer_text = answer_text[:10000] + "... [resposta truncada]"
                                st.markdown(answer_text)

                            # Verificar e exibir gráficos gerados
                            import os
                            charts_dir = 'charts'
                            if os.path.exists(charts_dir):
                                chart_files = [f for f in os.listdir(charts_dir) if f.endswith('.png')]
                                if chart_files:
                                    st.markdown("**📈 Gráficos Gerados:**")

                                    # Ordenar por data de modificação (mais recente primeiro)
                                    chart_files.sort(key=lambda x: os.path.getmtime(os.path.join(charts_dir, x)), reverse=True)

                                    # Mostrar até 5 gráficos mais recentes
                                    for chart_file in chart_files[:5]:
                                        chart_path = os.path.join(charts_dir, chart_file)
                                        try:
                                            st.image(chart_path, caption=chart_file.replace('.png', '').replace('_', ' ').title())
                                        except:
                                            pass

                    else:
                        st.error("❌ Resposta vazia ou inválida")

                    st.session_state.show_response = False

                except Exception as e:
                    st.error(f"❌ Erro ao exibir resposta: {str(e)}")
                    st.session_state.show_response = False

            # Verificar se há gráficos gerados APENAS desta sessão atual
            if st.session_state.session_charts:
                try:
                    settings = get_settings()
                    charts_dir = Path(settings.charts_dir)

                    if charts_dir.exists():
                        # Mostrar apenas gráficos que foram explicitamente gerados nesta sessão
                        existing_charts = []
                        for chart_name in st.session_state.session_charts:
                            chart_path = charts_dir / f"{chart_name}.png"
                            if chart_path.exists():
                                existing_charts.append(chart_path)

                        if existing_charts:
                            st.markdown("---")
                            st.subheader("📈 Gráficos Gerados Nesta Sessão")

                            for idx, chart_file in enumerate(existing_charts):
                                # Melhor apresentação dos gráficos com keys únicas
                                chart_time = pd.Timestamp.fromtimestamp(chart_file.stat().st_mtime)

                                with st.container(key=f"chart_container_{idx}_{chart_file.stem}"):
                                    col_img, col_info = st.columns([3, 1])

                                    with col_img:
                                        st.image(
                                            str(chart_file),
                                            caption=chart_file.stem.replace('_', ' ').title(),
                                            use_column_width=True,
                                            key=f"chart_img_{idx}_{chart_file.stem}"
                                        )

                                    with col_info:
                                        st.write(f"**📊 {chart_file.stem.replace('_', ' ').title()}**")
                                        st.write(f"🕒 {chart_time.strftime('%H:%M:%S')}")
                                        st.write(f"📏 {chart_file.stat().st_size // 1024}KB")
                except:
                    pass  # Ignorar se não conseguir acessar gráficos


def render_classic_chat(model_name: str):
    """Renderiza interface de chat clássica (código atual)"""
    # Indicador do modelo ativo
    st.markdown(f"""
    <div style="background: linear-gradient(90deg, #28a745, #20c997); color: white; padding: 8px; border-radius: 5px; text-align: center; margin-bottom: 15px; font-size: 14px;">
        <strong>Modelo Ativo:</strong> {model_name}
    </div>
    """, unsafe_allow_html=True)

    # Sugestões de perguntas específicas para dataset de fraude
    if 'Class' in st.session_state.current_data.columns:
        with st.expander("💡 Sugestões de Análises para Detecção de Fraude", expanded=False):
            col_sug1, col_sug2 = st.columns(2)

            with col_sug1:
                st.write("• Distribuição de classes (fraude vs normal)")
                st.write("• Análise temporal das transações")
                st.write("• Correlação entre variáveis V1-V28")

            with col_sug2:
                st.write("• Outliers em valores de transação")
                st.write("• Padrões de hora do dia")
                st.write("• Série temporal das transações")

    # Continuar com a interface clássica existente...
    # (O resto do código de chat atual continua aqui)

if __name__ == "__main__":
    main()