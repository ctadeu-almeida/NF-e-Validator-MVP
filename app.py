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

def main():
    """Função principal da aplicação Streamlit"""
    initialize_session_state()

    # Cabeçalho principal
    st.markdown("""
    <div class="main-header">
        <h1>🤖 Sistema EDA - Análise Exploratória de Dados com IA</h1>
        <p>Análise inteligente de dados CSV com agentes especializados</p>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar para configurações
    with st.sidebar:
        st.header("⚙️ Configurações")

        # Seção de seleção de modelo IA
        st.subheader("🤖 Modelo de IA")

        model_option = "gemini"  # Apenas Gemini é suportado
        st.info("🧠 **Modelo ativo:** Google Gemini com Agentes")

        # Campo de API Key (apenas para Gemini)
        api_key = None
        if model_option == "gemini":
            st.write("**🔑 Configuração do Gemini:**")
            api_key = st.text_input(
                "Chave da API Google Gemini:",
                type="password",
                help="Obtenha sua chave em: https://makersuite.google.com/app/apikey"
            )



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

    # Área principal de conteúdo
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

    elif not st.session_state.current_data is not None:
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