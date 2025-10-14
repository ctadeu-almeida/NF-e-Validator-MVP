# -*- coding: utf-8 -*-
"""
EDA Agent - Exploratory Data Analysis Agent

This module contains the main EDA agent that can analyze CSV files and answer questions
about data using various analysis techniques and visualizations.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, Any, List, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import Tool, AgentExecutor, create_react_agent
from langchain.memory import ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import tool
from langchain.schema.output_parser import StrOutputParser
import io
import sys
from contextlib import redirect_stdout, redirect_stderr
# offline_analyzer removido - não mais necessário

class EDAAgent:
    """
    Main EDA Agent class that provides comprehensive data analysis capabilities
    """

    def __init__(self, model_type: str = "gemini", api_key: str = None):
        """
        Initialize the EDA Agent with Gemini AI model

        IMPORTANTE: Apenas Gemini é suportado. Agentes são obrigatórios.

        Args:
            model_type (str): "gemini" - único modelo suportado
            api_key (str): API key do Google (obrigatória)
        """
        if model_type != "gemini":
            raise ValueError("Apenas 'gemini' é suportado.")

        self.model_type = model_type
        self.api_key = api_key
        self.data = None
        self.filename = None
        self.offline_analyzer = None  # Mantido apenas para compatibilidade de tools
        self.llm = None
        self.api_available = False
        self.chart_callback = None

        # Sistema de memória expandido para conclusões e contexto
        self.analysis_history = []  # Histórico de análises realizadas
        self.conclusions_memory = []  # Conclusões extraídas
        self.session_context = {  # Contexto da sessão atual
            'dataset_summary': None,
            'key_findings': [],
            'analysis_count': 0
        }

        # Initialize based on model type - APENAS AGENTES
        if model_type == "gemini" and api_key:
            self._init_gemini(api_key)
        else:
            raise ValueError(f"Configuração inválida para {model_type}. API key do Gemini é obrigatória.")

        # SEMPRE inicializar agentes quando API estiver disponível
        if self.api_available:
            print(f"✅ {model_type.title()} inicializado - configurando agentes...")
            # Memória aprimorada para manter contexto de análises
            from langchain.memory import ConversationSummaryBufferMemory

            self.memory = ConversationSummaryBufferMemory(
                llm=self.llm,
                memory_key="chat_history",
                return_messages=True,
                input_key="input",
                max_token_limit=2000,  # Manter histórico substancial
                summary_message_cls=None  # Usar mensagens padrão
            )
            self.tools = self._create_tools()
            self.agent_executor = self._create_agent()
            print(f"🤖 Agentes configurados para {model_type.title()}")
        else:
            raise RuntimeError(f"Falha ao inicializar {model_type.title()}. Agentes são obrigatórios.")

    def _init_gemini(self, api_key: str):
        """Initialize Google Gemini"""
        try:
            # Tentar modelos Gemini 2.5 disponíveis em ordem de prioridade
            models_to_try = [
                'gemini-2.5-flash',
                'gemini-2.5-pro',
                'gemini-2.0-flash-exp'
            ]

            for model_name in models_to_try:
                try:
                    print(f"🔄 Tentando inicializar {model_name}...")
                    self.llm = ChatGoogleGenerativeAI(
                        temperature=0.1,
                        model=model_name,
                        google_api_key=api_key,
                        max_output_tokens=4096,  # Valor mais conservador
                        convert_system_message_to_human=True,
                        max_retries=2,  # Reduzido para evitar loops
                        request_timeout=120,  # Timeout aumentado para 2 min
                        streaming=False  # Desabilitar streaming que pode causar problemas
                    )

                    # Testar inicialização com uma pergunta simples
                    test_response = self.llm.invoke([{"role": "user", "content": "Teste: responda apenas 'OK'"}])
                    if test_response and test_response.content:
                        self.api_available = True
                        print(f"✅ Google Gemini inicializado com sucesso: {model_name}")
                        return
                    else:
                        print(f"⚠️ {model_name} retornou resposta vazia")

                except Exception as model_error:
                    print(f"❌ Falha com {model_name}: {model_error}")
                    continue

            # Se chegou aqui, nenhum modelo funcionou
            raise Exception("Nenhum modelo Gemini disponível funcionou")

        except Exception as e:
            print(f"❌ Falha ao inicializar Google Gemini: {e}")
            self.api_available = False


    def load_data(self, file_path: str) -> bool:
        """
        Load CSV data for analysis

        Args:
            file_path (str): Path to CSV file

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Try different encodings and separators for better compatibility
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            separators = [',', ';', '\t']

            self.data = None
            load_error = None

            for encoding in encodings:
                for sep in separators:
                    # Try multiple reading strategies
                    reading_strategies = [
                        # Strategy 1: Handle malformed CSV with nested quotes
                        {
                            'encoding': encoding,
                            'sep': sep,
                            'low_memory': False,
                            'quoting': 1,  # QUOTE_ALL
                            'doublequote': True,
                            'skipinitialspace': True
                        },
                        # Strategy 2: Standard reading
                        {
                            'encoding': encoding,
                            'sep': sep,
                            'low_memory': False,
                            'quotechar': '"',
                            'skipinitialspace': True
                        },
                        # Strategy 3: No quote handling
                        {
                            'encoding': encoding,
                            'sep': sep,
                            'low_memory': False,
                            'quoting': 3  # QUOTE_NONE
                        },
                        # Strategy 4: Alternative quote character
                        {
                            'encoding': encoding,
                            'sep': sep,
                            'low_memory': False,
                            'quotechar': "'",
                            'skipinitialspace': True
                        }
                    ]

                    for strategy_idx, params in enumerate(reading_strategies):
                        try:
                            self.data = pd.read_csv(file_path, **params)
                            if self.data.shape[1] > 1:  # Valid if has more than 1 column
                                strategy_name = f"estratégia {strategy_idx + 1}"
                                print(f"✅ Arquivo carregado com encoding '{encoding}', separador '{sep}' ({strategy_name})")
                                break
                        except Exception as e:
                            load_error = e
                            continue

                    if self.data is not None and self.data.shape[1] > 1:
                        break
                if self.data is not None and self.data.shape[1] > 1:
                    break

            # If still only 1 column, try to fix malformed CSV
            if self.data is not None and self.data.shape[1] == 1:
                self.data = self._fix_malformed_csv(file_path)

            if self.data is None or self.data.shape[1] <= 1:
                raise Exception(f"Não foi possível carregar o arquivo. Último erro: {load_error}")

            self.filename = file_path.split('\\')[-1] if '\\' in file_path else file_path.split('/')[-1]

            # Clean problematic quotes first
            self.data = self._clean_quotes_from_data(self.data)

            # Apply general preprocessing to any CSV file
            self.data = self._preprocess_csv_data(self.data)

            # Initialize offline analyzer
            # offline_analyzer removido

            return True
        except Exception as e:
            print(f"❌ Erro ao carregar dados: {e}")
            print("💡 Dicas:")
            print("   - Verifique se o arquivo não está aberto em outro programa")
            print("   - Confirme se você tem permissão para acessar o arquivo")
            print("   - Verifique se o caminho está correto")
            return False

    def _fix_malformed_csv(self, file_path: str) -> pd.DataFrame:
        """
        Fix malformed CSV files with nested quotes

        Args:
            file_path (str): Path to the malformed CSV file

        Returns:
            pd.DataFrame: Fixed data
        """
        print("🔧 Corrigindo formato CSV mal formado...")

        try:
            # Read the raw file and fix the format
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            fixed_lines = []
            for line in lines:
                # Fix the malformed header and data
                if line.startswith('"Time,'):
                    # Fix header line: "Time,""V1"",""V2""... to Time,V1,V2...
                    fixed_line = line.strip().strip('"')  # Remove outer quotes
                    fixed_line = fixed_line.replace('""', '"')  # Fix double quotes
                    fixed_line = fixed_line.replace('","', ',').replace('",', ',').replace(',"', ',')
                    fixed_line = fixed_line.replace('"', '')  # Remove all remaining quotes
                    fixed_lines.append(fixed_line + '\n')
                else:
                    # Fix data lines
                    line = line.strip()
                    if '""' in line:
                        # Handle lines with pattern: value,""value"",""value""...
                        parts = []
                        in_quotes = False
                        current_part = ""
                        i = 0
                        while i < len(line):
                            if line[i:i+2] == '""':
                                if current_part:
                                    parts.append(current_part)
                                    current_part = ""
                                i += 2
                                continue
                            elif line[i] == '"':
                                i += 1
                                continue
                            elif line[i] == ',':
                                if current_part:
                                    parts.append(current_part)
                                    current_part = ""
                                i += 1
                                continue
                            current_part += line[i]
                            i += 1

                        if current_part:
                            parts.append(current_part)

                        fixed_lines.append(','.join(parts) + '\n')
                    else:
                        fixed_lines.append(line + '\n')

            # Create a temporary file-like object from fixed content
            from io import StringIO
            fixed_content = ''.join(fixed_lines)
            fixed_file = StringIO(fixed_content)

            # Read the fixed CSV
            fixed_data = pd.read_csv(fixed_file)
            print(f"   ✓ CSV corrigido: {fixed_data.shape[1]} colunas")

            return fixed_data

        except Exception as e:
            print(f"   ❌ Erro ao corrigir CSV: {e}")
            return None

    def _clean_quotes_from_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Clean problematic quotes from CSV data that can interfere with processing

        Args:
            data (pd.DataFrame): Raw data with potential quote issues

        Returns:
            pd.DataFrame: Data with quotes cleaned
        """
        print("🧹 Limpando aspas...")

        cleaned_data = data.copy()

        # Clean column names
        cleaned_data.columns = [col.strip().strip('"').strip("'") for col in cleaned_data.columns]

        # 2. Clean data values in object columns
        object_cols = cleaned_data.select_dtypes(include=['object']).columns
        cleaned_values_count = 0

        for col in object_cols:
            # Check if column has problematic quotes
            sample_values = cleaned_data[col].astype(str).head(10)
            has_quotes = any('"' in str(val) for val in sample_values)

            if has_quotes:
                try:
                    # Clean quotes from the entire column
                    original_series = cleaned_data[col].astype(str)

                    # Remove leading/trailing quotes and clean internal quotes
                    cleaned_series = original_series.str.strip()
                    cleaned_series = cleaned_series.str.strip('"').str.strip("'")

                    # Handle double quotes that might be escaped
                    cleaned_series = cleaned_series.str.replace('""', '"')
                    cleaned_series = cleaned_series.str.replace("''", "'")

                    # Convert back to original type if it was numeric
                    try:
                        # Test if the cleaned version can be numeric
                        numeric_test = pd.to_numeric(cleaned_series, errors='coerce')
                        if numeric_test.notna().sum() / len(numeric_test) > 0.8:
                            cleaned_data[col] = numeric_test
                            cleaned_values_count += 1
                        else:
                            cleaned_data[col] = cleaned_series
                            cleaned_values_count += 1
                    except:
                        cleaned_data[col] = cleaned_series
                        cleaned_values_count += 1

                except:
                    pass

        if cleaned_values_count > 0:
            print(f"   ✓ {cleaned_values_count} colunas processadas")

        # Additional cleaning
        for col in cleaned_data.columns:
            if cleaned_data[col].dtype == 'object':
                try:
                    cleaned_data[col] = cleaned_data[col].astype(str).str.replace('\ufeff', '').str.strip()
                    cleaned_data[col] = cleaned_data[col].replace(['nan', 'NaN', 'NULL', 'null', ''], pd.NA)
                except:
                    pass

        print("✅ Aspas limpas!")
        print()

        return cleaned_data

    def _preprocess_teste_csv(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Preprocess the teste.csv file with specific treatments for fraud detection data

        Args:
            data (pd.DataFrame): Raw data from teste.csv

        Returns:
            pd.DataFrame: Preprocessed data
        """
        print("📋 Aplicando tratamentos específicos para dados de fraude...")

        # Create a copy to avoid modifying original
        processed_data = data.copy()

        # 1. Ensure proper column names and types
        expected_columns = ['Time'] + [f'V{i}' for i in range(1, 29)] + ['Amount', 'Class']

        # 2. Convert Class to categorical with proper labels
        if 'Class' in processed_data.columns:
            processed_data['Class'] = processed_data['Class'].astype(int)
            processed_data['Class_Label'] = processed_data['Class'].map({0: 'Normal', 1: 'Fraudulenta'})
            print(f"   ✓ Classes identificadas: {processed_data['Class'].value_counts().to_dict()}")

        # 3. Ensure Time is properly formatted
        if 'Time' in processed_data.columns:
            processed_data['Time'] = pd.to_numeric(processed_data['Time'], errors='coerce')
            print(f"   ✓ Tempo: {processed_data['Time'].min():.2f}s a {processed_data['Time'].max():.2f}s")

        # 4. Ensure Amount is properly formatted
        if 'Amount' in processed_data.columns:
            processed_data['Amount'] = pd.to_numeric(processed_data['Amount'], errors='coerce')
            print(f"   ✓ Valores: ${processed_data['Amount'].min():.2f} a ${processed_data['Amount'].max():.2f}")

        # 5. Ensure V1-V28 columns are numeric (PCA components)
        pca_columns = [col for col in processed_data.columns if col.startswith('V') and col[1:].isdigit()]
        for col in pca_columns:
            processed_data[col] = pd.to_numeric(processed_data[col], errors='coerce')

        print(f"   ✓ {len(pca_columns)} componentes PCA processadas")

        # 6. Create additional derived features for fraud analysis
        if 'Amount' in processed_data.columns and 'Time' in processed_data.columns:
            # Hour of day (assuming Time is seconds from start)
            processed_data['Hour'] = ((processed_data['Time'] / 3600) % 24).astype(int)

            # Amount categories
            processed_data['Amount_Category'] = pd.cut(
                processed_data['Amount'],
                bins=[0, 10, 50, 100, 500, float('inf')],
                labels=['Muito_Baixo', 'Baixo', 'Medio', 'Alto', 'Muito_Alto']
            )

            print("   ✓ Features derivadas criadas: Hour, Amount_Category")

        # 7. Check data quality
        missing_values = processed_data.isnull().sum().sum()
        if missing_values > 0:
            print(f"   ⚠️ {missing_values} valores faltantes encontrados")
        else:
            print("   ✓ Nenhum valor faltante")

        # 8. Fraud analysis summary
        if 'Class' in processed_data.columns:
            fraud_rate = (processed_data['Class'] == 1).mean() * 100
            print(f"   📊 Taxa de fraude: {fraud_rate:.2f}%")

        print("✅ Tratamento específico do arquivo teste.csv concluído!")
        print()

        return processed_data

    def _preprocess_csv_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        General preprocessing for any CSV file

        Args:
            data (pd.DataFrame): Raw CSV data

        Returns:
            pd.DataFrame: Preprocessed data
        """
        print("📋 Processando dados...")

        processed_data = data.copy()

        # Clean column names
        processed_data.columns = processed_data.columns.str.strip().str.replace('"', '')

        # 2. Detect and convert numeric columns
        numeric_converted = 0
        for col in processed_data.columns:
            if processed_data[col].dtype == 'object':
                # Try to convert to numeric
                try:
                    # Remove common non-numeric characters and quotes
                    cleaned_series = processed_data[col].astype(str)
                    cleaned_series = cleaned_series.str.replace('"', '')  # Remove quotes
                    cleaned_series = cleaned_series.str.replace(',', '.')  # Handle decimal separator
                    cleaned_series = cleaned_series.str.replace(r'[^\d.-]', '', regex=True)

                    # Handle empty strings
                    cleaned_series = cleaned_series.replace('', '0')

                    numeric_series = pd.to_numeric(cleaned_series, errors='coerce')

                    # If most values are successfully converted, use numeric
                    successful_conversion_rate = numeric_series.notna().sum() / len(numeric_series)
                    if successful_conversion_rate > 0.8:
                        processed_data[col] = numeric_series
                        numeric_converted += 1
                except:
                    pass

        # Force conversion for expected numeric columns
        expected_numeric_cols = ['Time', 'Amount'] + [f'V{i}' for i in range(1, 29)]
        forced_conversions = 0
        for col in expected_numeric_cols:
            if col in processed_data.columns and processed_data[col].dtype == 'object':
                try:
                    cleaned_series = processed_data[col].astype(str).str.replace('"', '').str.replace(',', '.')
                    cleaned_series = cleaned_series.str.replace(r'[^\d.-]', '', regex=True).replace('', '0')
                    processed_data[col] = pd.to_numeric(cleaned_series, errors='coerce')
                    forced_conversions += 1
                except:
                    pass

        total_converted = numeric_converted + forced_conversions
        if total_converted > 0:
            print(f"   ✓ {total_converted} colunas convertidas para numéricas")

        # Handle missing values and cleanup
        missing_total = processed_data.isnull().sum().sum()
        if missing_total > 0:
            print(f"   ⚠️ {missing_total} valores faltantes")

        # Remove empty rows/columns
        processed_data = processed_data.dropna(how='all').loc[:, ~processed_data.isnull().all()]

        # Final summary
        numeric_cols = processed_data.select_dtypes(include=[np.number]).columns
        categorical_cols = processed_data.select_dtypes(include=['object', 'category']).columns

        print(f"   📊 {len(numeric_cols)} numéricas, {len(categorical_cols)} categóricas, {len(processed_data)} registros")

        # Handle Class column for classification (don't add new column, just detect)
        if 'Class' in processed_data.columns and processed_data['Class'].dtype in ['int64', 'float64']:
            unique_classes = processed_data['Class'].unique()
            if len(unique_classes) <= 10:
                print(f"   🎯 Alvo de classificação detectado: {unique_classes}")

        print("✅ Dados processados!")
        print()

        return processed_data

    def _create_tools(self) -> List[Tool]:
        """Create analysis tools for the agent"""

        @tool
        def describe_data() -> str:
            """Get basic information about the loaded dataset including shape, columns, data types"""
            if self.data is None:
                return "No data loaded. Please load a CSV file first."

            info = []
            info.append(f"Dataset: {self.filename}")
            info.append(f"Shape: {self.data.shape[0]} rows, {self.data.shape[1]} columns")
            info.append(f"Columns: {list(self.data.columns)}")
            info.append(f"Data types:\n{self.data.dtypes.to_string()}")
            info.append(f"Missing values:\n{self.data.isnull().sum().to_string()}")

            return "\n\n".join(info)

        @tool
        def get_statistical_summary() -> str:
            """Get statistical summary of numerical columns"""
            if self.data is None:
                return "No data loaded. Please load a CSV file first."

            numeric_cols = self.data.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) == 0:
                return "No numerical columns found in the dataset."

            summary = self.data[numeric_cols].describe()
            return f"Statistical Summary:\n{summary.to_string()}"

        @tool
        def check_correlations() -> str:
            """Calculate and return correlation matrix for numerical columns"""
            if self.data is None:
                return "No data loaded. Please load a CSV file first."

            numeric_cols = self.data.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) < 2:
                return "Need at least 2 numerical columns to calculate correlations."

            corr_matrix = self.data[numeric_cols].corr()
            return f"Correlation Matrix:\n{corr_matrix.to_string()}"

        @tool
        def detect_outliers(column: str = None) -> str:
            """Detect outliers using IQR method for a specific column or all numerical columns"""
            if self.data is None:
                return "No data loaded. Please load a CSV file first."

            numeric_cols = self.data.select_dtypes(include=[np.number]).columns

            if column and column not in numeric_cols:
                return f"Column '{column}' not found or not numerical."

            cols_to_check = [column] if column else numeric_cols
            outlier_info = []

            for col in cols_to_check:
                Q1 = self.data[col].quantile(0.25)
                Q3 = self.data[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR

                outliers = self.data[(self.data[col] < lower_bound) | (self.data[col] > upper_bound)]
                outlier_count = len(outliers)

                outlier_info.append(f"Column '{col}': {outlier_count} outliers detected")
                if outlier_count > 0:
                    outlier_info.append(f"  Range: {lower_bound:.2f} to {upper_bound:.2f}")
                    outlier_info.append(f"  Outlier values sample: {outliers[col].head().tolist()}")

            return "\n".join(outlier_info)

        @tool
        def analyze_categorical_data() -> str:
            """Analyze categorical columns including value counts and unique values"""
            if self.data is None:
                return "No data loaded. Please load a CSV file first."

            categorical_cols = self.data.select_dtypes(include=['object', 'category']).columns

            if len(categorical_cols) == 0:
                return "No categorical columns found in the dataset."

            cat_info = []
            for col in categorical_cols:
                unique_count = self.data[col].nunique()
                cat_info.append(f"Column '{col}':")
                cat_info.append(f"  Unique values: {unique_count}")
                cat_info.append(f"  Value counts:\n{self.data[col].value_counts().head().to_string()}")
                cat_info.append("")

            return "\n".join(cat_info)

        @tool
        def generate_and_execute_python_code(question: str) -> str:
            """Generate and execute Python code to answer the user's question about the data."""
            if self.data is None:
                return "No data loaded. Please load a CSV file first."

            # Create a safe execution environment
            # Criar pasta charts se não existir
            import os
            import datetime
            charts_dir = 'charts'
            if not os.path.exists(charts_dir):
                os.makedirs(charts_dir)

            # Gerar timestamp único para arquivos
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

            # Verificar se self.data existe
            if self.data is None:
                return "Erro: Nenhum dataset foi carregado. Use load_data() primeiro."

            local_vars = {
                'data': self.data,
                'pd': pd,
                'np': np,
                'plt': plt,
                'sns': sns,
                'os': os,
                'timestamp': timestamp
            }

            # Debug: verificar se variáveis estão sendo passadas
            print(f"🔍 Debug: data shape = {self.data.shape}, variáveis passadas = {list(local_vars.keys())}")

            # Ask the LLM to generate Python code for the specific question
            code_generation_prompt = f"""
            Você tem um dataset pandas chamado 'data' carregado. O usuário fez a seguinte pergunta:
            "{question}"

            Gere código Python que responda especificamente a esta pergunta. O código deve:
            1. Analisar os dados relevantes e fazer cálculos necessários
            2. Imprimir resultados claros e informativos usando print()
            3. Gerar gráficos relevantes quando apropriado usando matplotlib/seaborn
            4. Salvar gráficos como PNG na pasta charts/ se criados
            5. Tirar conclusões baseadas nos dados analisados

            VARIÁVEIS DISPONÍVEIS:
            - data: DataFrame principal com os dados ({self.data.shape[0]} linhas, {self.data.shape[1]} colunas)
            - pd: pandas
            - np: numpy
            - plt: matplotlib.pyplot
            - sns: seaborn
            - os: os module
            - timestamp: string única para nomes de arquivo

            Dataset info:
            - Shape: {self.data.shape}
            - Columns: {list(self.data.columns)}
            - Data types: {dict(self.data.dtypes)}

            EXEMPLO DE CÓDIGO VÁLIDO:
            ```python
            # Verificar se data está carregado
            print(f"Dataset shape: {{data.shape}}")
            print(f"Columns: {{list(data.columns)}}")

            # Gerar análise
            numeric_cols = data.select_dtypes(include=[np.number]).columns
            for col in numeric_cols[:3]:  # Primeiras 3 colunas
                plt.figure(figsize=(10, 6))
                data[col].hist(bins=30)
                plt.title(f'Distribuição de {{col}}')
                plt.tight_layout()
                plt.savefig(f'charts/{{timestamp}}_hist_{{col}}.png', dpi=300, bbox_inches='tight')
                plt.close()
                print(f"Gráfico salvo: charts/{{timestamp}}_hist_{{col}}.png")
            ```

            IMPORTANTE:
            - Use SEMPRE 'data' como nome do DataFrame
            - SEMPRE feche figuras com plt.close()
            - Use timestamp para nomes únicos de arquivo

            Retorne APENAS o código Python, sem explicações adicionais.
            """

            try:
                # Generate code using the LLM
                code_response = self.llm.invoke([{"role": "user", "content": code_generation_prompt}])
                generated_code = code_response.content.strip()

                # Clean the code (remove markdown formatting if present)
                if generated_code.startswith("```python"):
                    generated_code = generated_code[9:]
                if generated_code.startswith("```"):
                    generated_code = generated_code[3:]
                if generated_code.endswith("```"):
                    generated_code = generated_code[:-3]

                # Capture output
                output_buffer = io.StringIO()
                error_buffer = io.StringIO()

                # Execute the generated code
                with redirect_stdout(output_buffer), redirect_stderr(error_buffer):
                    exec(generated_code, {"__builtins__": __builtins__}, local_vars)

                output = output_buffer.getvalue()
                errors = error_buffer.getvalue()

                result = [f"Código gerado:\n{generated_code}\n"]
                result.append("="*50)

                if output:
                    result.append(f"Resultado:\n{output}")
                if errors:
                    result.append(f"Avisos/Erros:\n{errors}")

                # Sempre incluir uma conclusão interpretativa
                conclusion_prompt = f"""
                Baseado na pergunta: "{question}"
                E no resultado da execução do código:
                {output[:1000] if output else "Sem output textual"}

                Forneça uma conclusão interpretativa clara em 2-3 frases sobre o que estes resultados revelam sobre os dados.
                Seja específico e direto.
                """

                try:
                    conclusion_response = self.llm.invoke([{"role": "user", "content": conclusion_prompt}])
                    conclusion = conclusion_response.content.strip()
                    if conclusion:
                        result.append(f"\n🔍 Conclusão:\n{conclusion}")

                        # Armazenar conclusão na memória da sessão
                        self._store_analysis_conclusion(question, conclusion, output)
                except:
                    fallback_conclusion = f"Análise executada com sucesso para: {question}"
                    result.append(f"\n🔍 {fallback_conclusion}")
                    self._store_analysis_conclusion(question, fallback_conclusion, output)

                return "\n".join(result) if result else "Code executed successfully with no output."

            except Exception as e:
                return f"Error generating or executing code: {str(e)}"

        @tool
        def get_temporal_analysis() -> str:
            """Analyze temporal patterns if Time column exists"""
            if self.data is None:
                return "No data loaded. Please load a CSV file first."

            if 'Time' not in self.data.columns:
                return "No 'Time' column found in the dataset."

            time_info = []
            time_info.append(f"Time column analysis:")
            time_info.append(f"  Min time: {self.data['Time'].min()}")
            time_info.append(f"  Max time: {self.data['Time'].max()}")
            time_info.append(f"  Time range: {self.data['Time'].max() - self.data['Time'].min()} seconds")

            # Check for patterns
            time_diff = self.data['Time'].diff().dropna()
            time_info.append(f"  Average time between transactions: {time_diff.mean():.2f} seconds")

            return "\n".join(time_info)

        @tool
        def get_previous_conclusions() -> str:
            """Get conclusions from previous analyses in this session"""
            if not self.conclusions_memory:
                return "No previous analyses have been performed in this session."

            conclusions_summary = []
            conclusions_summary.append("CONCLUSÕES DE ANÁLISES ANTERIORES:")
            conclusions_summary.append("=" * 50)

            for i, conclusion in enumerate(self.conclusions_memory[-5:], 1):  # Últimas 5
                conclusions_summary.append(f"\n{i}. Análise: {conclusion['analysis_type']}")
                conclusions_summary.append(f"   Pergunta: {conclusion['question']}")
                conclusions_summary.append(f"   Conclusão: {conclusion['conclusion']}")
                if conclusion.get('key_findings'):
                    conclusions_summary.append(f"   Descobertas: {conclusion['key_findings']}")

            return "\n".join(conclusions_summary)

        @tool
        def get_session_context() -> str:
            """Get current session context including dataset summary and key findings"""
            context_info = []
            context_info.append("CONTEXTO DA SESSÃO ATUAL:")
            context_info.append("=" * 50)

            if self.session_context['dataset_summary']:
                context_info.append(f"Dataset: {self.session_context['dataset_summary']}")

            context_info.append(f"Análises realizadas: {self.session_context['analysis_count']}")

            if self.session_context['key_findings']:
                context_info.append("\nPrincipais descobertas:")
                for finding in self.session_context['key_findings']:
                    context_info.append(f"  • {finding}")

            if self.analysis_history:
                context_info.append(f"\nTipos de análises já realizadas:")
                analysis_types = [a['type'] for a in self.analysis_history]
                unique_types = list(set(analysis_types))
                context_info.append(f"  {', '.join(unique_types)}")

            return "\n".join(context_info)

        return [
            describe_data,
            get_statistical_summary,
            check_correlations,
            detect_outliers,
            analyze_categorical_data,
            generate_and_execute_python_code,
            get_temporal_analysis,
            get_previous_conclusions,
            get_session_context
        ]

    def _create_agent(self) -> AgentExecutor:
        """Create the main EDA agent"""
        from langchain.prompts import PromptTemplate

        prompt = PromptTemplate.from_template("""Você é um analista de dados expert especializado em Análise Exploratória de Dados (EDA).
Seu objetivo é responder perguntas sobre datasets CSV mantendo MEMÓRIA e CONTEXTO das análises anteriores.

MEMÓRIA E CONTEXTO:
- SEMPRE consulte get_previous_conclusions antes de análises para manter continuidade
- Use get_session_context para entender o que já foi descoberto
- Referencie análises anteriores quando relevante
- Construa sobre descobertas prévias ao invés de repetir análises

INSTRUÇÕES IMPORTANTES:
1. CONSULTE MEMÓRIA: Use get_previous_conclusions e get_session_context para contexto
2. ANÁLISES COMPLEXAS: Use generate_and_execute_python_code para cálculos
3. ESTRUTURA BÁSICA: Use describe_data para informações gerais
4. SEJA CONTEXTUAL: Referencie análises anteriores e construa sobre elas
5. MENCIONE GRÁFICOS: Se gerar visualizações, informe que foram salvos em charts/

HISTÓRICO DA CONVERSA:
{chat_history}

FERRAMENTAS DISPONÍVEIS:
{tools}

FORMATO DE RESPOSTA:
Question: a pergunta que você deve responder
Thought: pense sobre o contexto e análises anteriores primeiro
Action: escolha uma ferramenta de [{tool_names}]
Action Input: entrada para a ferramenta
Observation: resultado da ferramenta
... (Thought/Action/Action Input/Observation pode repetir)
Thought: agora sei a resposta final considerando o contexto
Final Answer: resposta final que conecta com análises anteriores quando relevante

ESTRATÉGIA COM MEMÓRIA:
1. SEMPRE comece consultando get_previous_conclusions se não for a primeira pergunta
2. Use get_session_context para entender descobertas já feitas
3. Para análises específicas: use generate_and_execute_python_code
4. Conecte novas descobertas com conclusões anteriores

Comece!

Question: {input}
Thought:{agent_scratchpad}""")

        agent = create_react_agent(self.llm, self.tools, prompt)
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True,  # Ativar para debug
            handle_parsing_errors=True,
            return_intermediate_steps=True,  # Manter passos intermediários
            max_iterations=25,  # Aumentado de 15 para 25
            early_stopping_method="generate",  # Mudado de "force" para "generate"
            max_execution_time=300,  # Aumentado de 120 para 300 segundos (5 min)
        )

    def ask_question(self, question: str) -> str:
        """
        Ask a question about the loaded data

        Args:
            question (str): Question about the data

        Returns:
            str: Agent's response
        """
        if self.data is None:
            return "Please load a CSV file first using the load_data method."

        # APENAS AGENTES - sem fallback offline
        if not self.api_available or not self.agent_executor:
            return f"❌ Erro: Agente {self.model_type} não está disponível. Verifique a configuração."

        try:
            print(f"🤖 Executando pergunta via agente {self.model_type.title()}...")

            # Proteger contra StopIteration com try-catch específico
            try:
                response = self.agent_executor.invoke({"input": question})
            except StopIteration as stop_iter:
                # Converter StopIteration em RuntimeError conforme Python 3.7+
                print(f"⚠️ StopIteration capturado e convertido: {stop_iter}")
                raise RuntimeError(f"Agent generator completed unexpectedly: {stop_iter}")

            # Melhorar extração da resposta
            if isinstance(response, dict):
                # Verificar output principal
                if "output" in response and response["output"]:
                    final_answer = response["output"]
                # Verificar se há passos intermediários com resultados
                elif "intermediate_steps" in response and response["intermediate_steps"]:
                    # Extrair último resultado útil dos passos intermediários
                    last_step = response["intermediate_steps"][-1]
                    if len(last_step) > 1:
                        final_answer = f"Resultado da análise:\n{last_step[1]}"
                    else:
                        final_answer = "Análise executada, mas resposta incompleta."
                else:
                    final_answer = "Análise concluída, mas sem resposta estruturada."

                # Adicionar informações dos passos intermediários se útil
                if "intermediate_steps" in response and len(response["intermediate_steps"]) > 1:
                    final_answer += f"\n\n📊 Passos executados: {len(response['intermediate_steps'])}"

                return final_answer
            else:
                return str(response) if response else "Análise executada sem resposta."

        except RuntimeError as e:
            error_msg = str(e)
            print(f"❌ RuntimeError no agente {self.model_type}: {error_msg[:100]}")

            # Tratamento específico para StopIteration convertido
            if "generator" in error_msg.lower() or "stopiteration" in error_msg.lower():
                return f"❌ Erro de gerador no {self.model_type.title()}. Pode estar relacionado à versão do SDK.\n\n💡 Tente reformular a pergunta ou reinicialize o modelo."
            else:
                return f"❌ Erro no agente {self.model_type.title()}: {error_msg[:200]}\n\n💡 Tente uma pergunta mais simples ou reinicialize o modelo."

        except Exception as e:
            error_str = str(e)
            print(f"❌ Erro geral no agente {self.model_type}: {error_str[:100]}")

            # Tratamento específico para "No generation chunks were returned"
            if "no generation chunks were returned" in error_str.lower():
                # Tentar usar ferramentas básicas como fallback
                try:
                    print("🔄 Tentando fallback com ferramentas básicas...")
                    if "distribuição" in question.lower() or "histograma" in question.lower():
                        stats_result = self._create_tools()[1]()  # get_statistical_summary
                        return f"📊 Análise básica (fallback):\n{stats_result}\n\n⚠️ Nota: Erro no Gemini ('No generation chunks'), usando análise simplificada."
                    else:
                        basic_info = self._create_tools()[0]()  # describe_data
                        return f"📋 Informações básicas (fallback):\n{basic_info}\n\n⚠️ Nota: Erro no Gemini ('No generation chunks'), reformule a pergunta."
                except:
                    pass

                return f"❌ Erro no agente Gemini: No generation chunks were returned\n\n💡 Este erro pode ocorrer por:\n• Conteúdo bloqueado por filtros de segurança\n• Pergunta muito complexa ou mal formatada\n• Problemas temporários da API\n\n🔄 Sugestões:\n• Reformule a pergunta de forma mais simples\n• Tente uma pergunta diferente\n• Verifique sua chave da API\n• Reinicialize o modelo"

            # Tratamento específico de erros de API
            elif any(keyword in error_str.lower() for keyword in ['quota', 'exceeded', '429', 'rate limit']):
                return f"⚠️ Cota da API {self.model_type.title()} excedida.\n\n💡 Aguarde um momento e tente novamente."
            elif "stopiteration" in error_str.lower():
                return f"❌ Erro de iterador no {self.model_type.title()}. Versão do SDK pode ser incompatível.\n\n💡 Tente reformular a pergunta ou verifique a versão do google-generativeai."
            else:
                return f"❌ Erro no agente {self.model_type.title()}: {error_str[:200]}\n\n💡 Verifique sua configuração ou tente novamente."

    # MODO OFFLINE REMOVIDO - Apenas métodos de análise auxiliares mantidos

    def _analyze_data_types(self) -> str:
        """
        Analisa os tipos de dados de forma detalhada

        Returns:
            str: Análise detalhada dos tipos de dados
        """
        if self.data is None:
            return "Nenhum dado carregado."

        result = []
        result.append("ANÁLISE DE TIPOS DE DADOS")
        result.append("=" * 50)
        result.append(f"Dataset: {self.filename}")
        result.append(f"Shape: {self.data.shape[0]} linhas, {self.data.shape[1]} colunas")
        result.append("")

        # Análise por tipo
        numeric_cols = self.data.select_dtypes(include=[np.number]).columns
        categorical_cols = self.data.select_dtypes(include=['object', 'category']).columns
        datetime_cols = self.data.select_dtypes(include=['datetime64']).columns

        result.append("RESUMO POR TIPO:")
        result.append(f"- Colunas numéricas: {len(numeric_cols)}")
        result.append(f"- Colunas categóricas: {len(categorical_cols)}")
        result.append(f"- Colunas de data/hora: {len(datetime_cols)}")
        result.append("")

        # Detalhes das colunas numéricas
        if len(numeric_cols) > 0:
            result.append("COLUNAS NUMÉRICAS:")
            for col in numeric_cols:
                dtype = str(self.data[col].dtype)
                non_null = self.data[col].count()
                result.append(f"  - {col}: {dtype} ({non_null} valores válidos)")

        # Detalhes das colunas categóricas
        if len(categorical_cols) > 0:
            result.append("")
            result.append("COLUNAS CATEGÓRICAS:")
            for col in categorical_cols:
                unique_vals = self.data[col].nunique()
                non_null = self.data[col].count()
                result.append(f"  - {col}: object ({non_null} valores válidos, {unique_vals} únicos)")

        # Detalhes das colunas de data
        if len(datetime_cols) > 0:
            result.append("")
            result.append("COLUNAS DE DATA/HORA:")
            for col in datetime_cols:
                non_null = self.data[col].count()
                result.append(f"  - {col}: datetime64 ({non_null} valores válidos)")

        # Informações adicionais
        result.append("")
        result.append("INFORMAÇÕES ADICIONAIS:")
        result.append(f"- Total de valores ausentes: {self.data.isnull().sum().sum()}")
        result.append(f"- Uso de memória: {self.data.memory_usage(deep=True).sum() / 1024**2:.2f} MB")

        return "\n".join(result)

    def _generate_simple_plots(self, chart_callback=None):
        """Gera gráficos básicos para análise exploratória"""
        import os
        import matplotlib.pyplot as plt
        import seaborn as sns

        # Criar pasta charts se não existir
        charts_dir = 'charts'
        if not os.path.exists(charts_dir):
            os.makedirs(charts_dir)

        # Configurar estilo
        plt.style.use('default')
        sns.set_palette("husl")

        generated_charts = []

        # 1. Histogramas para variáveis numéricas
        numeric_cols = self.data.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            n_cols = min(len(numeric_cols), 4)
            n_rows = (len(numeric_cols) + n_cols - 1) // n_cols

            plt.figure(figsize=(15, 4 * n_rows))
            for i, col in enumerate(numeric_cols):
                plt.subplot(n_rows, n_cols, i + 1)
                self.data[col].hist(bins=30, alpha=0.7)
                plt.title(f'Distribuição de {col}')
                plt.xlabel(col)
                plt.ylabel('Frequência')

            plt.tight_layout()
            chart_name = 'distribuicoes_numericas'
            plt.savefig(f'{charts_dir}/{chart_name}.png', dpi=300, bbox_inches='tight')
            plt.close()
            generated_charts.append(chart_name)

        # 2. Matriz de correlação (se tiver mais de 1 variável numérica)
        if len(numeric_cols) > 1:
            plt.figure(figsize=(10, 8))
            corr_matrix = self.data[numeric_cols].corr()
            sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0,
                       square=True, linewidths=0.5)
            plt.title('Matriz de Correlação')
            plt.tight_layout()
            chart_name = 'matriz_correlacao'
            plt.savefig(f'{charts_dir}/{chart_name}.png', dpi=300, bbox_inches='tight')
            plt.close()
            generated_charts.append(chart_name)

        # 3. Gráficos de barras para variáveis categóricas
        categorical_cols = self.data.select_dtypes(include=['object']).columns
        if len(categorical_cols) > 0:
            n_cols = min(len(categorical_cols), 3)
            n_rows = (len(categorical_cols) + n_cols - 1) // n_cols

            plt.figure(figsize=(15, 4 * n_rows))
            for i, col in enumerate(categorical_cols):
                plt.subplot(n_rows, n_cols, i + 1)
                value_counts = self.data[col].value_counts().head(10)  # Top 10 valores
                value_counts.plot(kind='bar', alpha=0.7)
                plt.title(f'Distribuição de {col}')
                plt.xlabel(col)
                plt.ylabel('Contagem')
                plt.xticks(rotation=45)

            plt.tight_layout()
            chart_name = 'distribuicoes_categoricas'
            plt.savefig(f'{charts_dir}/{chart_name}.png', dpi=300, bbox_inches='tight')
            plt.close()
            generated_charts.append(chart_name)

        # Chamar callback para registrar gráficos gerados
        if chart_callback and generated_charts:
            chart_callback(generated_charts)
        elif self.chart_callback and generated_charts:
            self.chart_callback(generated_charts)

    def _generate_analysis_code(self, question: str) -> str:
        """
        Gera código Python específico para responder à pergunta do usuário

        Args:
            question (str): Pergunta do usuário

        Returns:
            str: Código Python para análise
        """
        question_lower = question.lower()

        # Obter informações básicas do dataset
        shape = self.data.shape
        columns = list(self.data.columns)
        numeric_cols = list(self.data.select_dtypes(include=[np.number]).columns)
        categorical_cols = list(self.data.select_dtypes(include=['object']).columns)

        # Mapear tipos de perguntas para código Python específico
        if any(word in question_lower for word in ['tipos', 'type', 'dtype', 'dados']):
            return f"""# Análise de tipos de dados
print("=== ANÁLISE DE TIPOS DE DADOS ===")
print(f"Shape do dataset: {{data.shape}}")
print(f"Colunas: {{list(data.columns)}}")
print("\\n--- TIPOS POR CATEGORIA ---")
numeric_cols = data.select_dtypes(include=['number']).columns.tolist()
categorical_cols = data.select_dtypes(include=['object']).columns.tolist()
datetime_cols = data.select_dtypes(include=['datetime']).columns.tolist()

print(f"Numéricas ({len(numeric_cols)}): {numeric_cols[:5]}{'...' if len(numeric_cols) > 5 else ''}")
print(f"Categóricas ({len(categorical_cols)}): {categorical_cols[:5]}{'...' if len(categorical_cols) > 5 else ''}")
print(f"Data/Hora ({len(datetime_cols)}): {datetime_cols}")

print("\\n--- DETALHES DOS TIPOS ---")
for col in data.columns:
    print(f"{{col}}: {{data[col].dtype}} ({{data[col].count()}} valores válidos)")
"""

        elif any(word in question_lower for word in ['correlação', 'correlações', 'relacionamento']):
            return f"""# Análise de correlações
import seaborn as sns
import matplotlib.pyplot as plt

print("=== ANÁLISE DE CORRELAÇÕES ===")
numeric_cols = data.select_dtypes(include=['number']).columns.tolist()

if len(numeric_cols) >= 2:
    # Calcular matriz de correlação
    corr_matrix = data[numeric_cols].corr()
    print("Matriz de Correlação:")
    print(corr_matrix.round(3))

    # Encontrar correlações mais fortes (> 0.7 ou < -0.7)
    strong_corr = []
    for i in range(len(corr_matrix.columns)):
        for j in range(i+1, len(corr_matrix.columns)):
            val = corr_matrix.iloc[i, j]
            if abs(val) > 0.7:
                strong_corr.append((corr_matrix.columns[i], corr_matrix.columns[j], val))

    print("\\n--- CORRELAÇÕES FORTES (|r| > 0.7) ---")
    for col1, col2, corr_val in strong_corr:
        print(f"{{col1}} ↔ {{col2}}: {{corr_val:.3f}}")

    # Gerar gráfico de correlação
    plt.figure(figsize=(10, 8))
    sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0, square=True, fmt='.2f')
    plt.title('Matriz de Correlação')
    plt.tight_layout()
    chart_name = 'matriz_correlacao'
    plt.savefig(f'charts/{chart_name}.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"\\nGráfico salvo: charts/{chart_name}.png")
else:
    print("Necessário pelo menos 2 colunas numéricas para calcular correlação")
"""

        elif any(word in question_lower for word in ['outlier', 'outliers', 'atípico', 'extremo']):
            return f"""# Detecção de outliers
import matplotlib.pyplot as plt

print("=== DETECÇÃO DE OUTLIERS ===")
numeric_cols = data.select_dtypes(include=['number']).columns.tolist()

outlier_summary = []
for col in numeric_cols:
    Q1 = data[col].quantile(0.25)
    Q3 = data[col].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR

    outliers = data[(data[col] < lower_bound) | (data[col] > upper_bound)]
    outlier_count = len(outliers)
    outlier_pct = (outlier_count / len(data)) * 100

    print(f"\\n--- {{col}} ---")
    print(f"Outliers detectados: {{outlier_count}} ({{outlier_pct:.1f}}%)")
    print(f"Limites: {{lower_bound:.2f}} a {{upper_bound:.2f}}")

    if outlier_count > 0:
        print(f"Valores outliers (amostra): {{outliers[col].head().tolist()}}")
        outlier_summary.append((col, outlier_count, outlier_pct))

# Gerar boxplot para visualizar outliers
if numeric_cols:
    fig, axes = plt.subplots(1, min(4, len(numeric_cols)), figsize=(15, 5))
    if len(numeric_cols) == 1:
        axes = [axes]

    for i, col in enumerate(numeric_cols[:4]):
        data[col].plot(kind='box', ax=axes[i])
        axes[i].set_title(f'Boxplot - {{col}}')

    plt.tight_layout()
    plt.savefig('charts/outliers_boxplot.png', dpi=300, bbox_inches='tight')
    print("\\nGráfico salvo: charts/outliers_boxplot.png")

print(f"\\n--- RESUMO GERAL ---")
print(f"Total de colunas analisadas: {{len(numeric_cols)}}")
print(f"Colunas com outliers: {{len(outlier_summary)}}")
"""

        elif any(word in question_lower for word in ['distribuição', 'estatística', 'estatísticas', 'resumo']):
            return f"""# Estatísticas descritivas
import matplotlib.pyplot as plt

print("=== ESTATÍSTICAS DESCRITIVAS ===")
numeric_cols = data.select_dtypes(include=['number']).columns.tolist()

if numeric_cols:
    print("--- RESUMO ESTATÍSTICO ---")
    desc_stats = data[numeric_cols].describe()
    print(desc_stats)

    print("\\n--- ANÁLISE POR COLUNA ---")
    for col in numeric_cols:
        print(f"\\n{{col}}:")
        print(f"  Média: {{data[col].mean():.2f}}")
        print(f"  Mediana: {{data[col].median():.2f}}")
        print(f"  Desvio Padrão: {{data[col].std():.2f}}")
        print(f"  Amplitude: {{data[col].max() - data[col].min():.2f}}")
        print(f"  Coef. Variação: {{(data[col].std()/data[col].mean())*100:.1f}}%")

    # Gerar histogramas
    n_cols = min(len(numeric_cols), 4)
    n_rows = (len(numeric_cols) + n_cols - 1) // n_cols

    fig, axes = plt.subplots(n_rows, n_cols, figsize=(15, 4*n_rows))
    if n_rows == 1:
        axes = [axes] if n_cols == 1 else axes
    else:
        axes = axes.flatten()

    for i, col in enumerate(numeric_cols):
        data[col].hist(bins=30, alpha=0.7, ax=axes[i])
        axes[i].set_title(f'Distribuição - {{col}}')
        axes[i].set_xlabel(col)
        axes[i].set_ylabel('Frequência')

    # Remover subplots vazios
    for i in range(len(numeric_cols), len(axes)):
        fig.delaxes(axes[i])

    plt.tight_layout()
    plt.savefig('charts/distribuicoes.png', dpi=300, bbox_inches='tight')
    print("\\nGráfico salvo: charts/distribuicoes.png")
else:
    print("Nenhuma coluna numérica encontrada para estatísticas")
"""

        elif any(word in question_lower for word in ['intervalo', 'mínimo', 'máximo', 'min', 'max', 'amplitude']):
            return f"""# Análise de intervalos (min/max)
print("=== ANÁLISE DE INTERVALOS ===")
numeric_cols = data.select_dtypes(include=['number']).columns.tolist()

if numeric_cols:
    print("--- INTERVALOS POR VARIÁVEL ---")
    for col in numeric_cols:
        min_val = data[col].min()
        max_val = data[col].max()
        amplitude = max_val - min_val

        print(f"\\n{{col}}:")
        print(f"  Mínimo: {{min_val}}")
        print(f"  Máximo: {{max_val}}")
        print(f"  Amplitude: {{amplitude}}")
        print(f"  Percentil 5%: {{data[col].quantile(0.05)}}")
        print(f"  Percentil 95%: {{data[col].quantile(0.95)}}")

    # Tabela resumo
    import pandas as pd
    summary_df = pd.DataFrame({{
        'Mínimo': [data[col].min() for col in numeric_cols],
        'Máximo': [data[col].max() for col in numeric_cols],
        'Amplitude': [data[col].max() - data[col].min() for col in numeric_cols]
    }}, index=numeric_cols)

    print("\\n--- TABELA RESUMO ---")
    print(summary_df.round(2))
else:
    print("Nenhuma coluna numérica encontrada")
"""

        else:
            # Análise geral para perguntas não específicas
            return f"""# Análise exploratória geral
print("=== ANÁLISE EXPLORATÓRIA GERAL ===")
print(f"Dataset: {{data.shape[0]}} linhas, {{data.shape[1]}} colunas")

# Informações básicas
print("\\n--- ESTRUTURA DOS DADOS ---")
print("Tipos de dados:")
print(data.dtypes.value_counts())

print("\\n--- VALORES AUSENTES ---")
missing = data.isnull().sum()
if missing.sum() > 0:
    print("Colunas com valores ausentes:")
    print(missing[missing > 0])
else:
    print("Nenhum valor ausente encontrado")

# Análise por tipo de coluna
numeric_cols = data.select_dtypes(include=['number']).columns.tolist()
categorical_cols = data.select_dtypes(include=['object']).columns.tolist()

if numeric_cols:
    print("\\n--- RESUMO NUMÉRICO ---")
    print(data[numeric_cols].describe().round(2))

if categorical_cols:
    print("\\n--- ANÁLISE CATEGÓRICA ---")
    for col in categorical_cols[:3]:  # Apenas primeiras 3
        print(f"\\n{{col}} - {{data[col].nunique()}} valores únicos:")
        print(data[col].value_counts().head())

print(f"\\n--- CONCLUSÃO ---")
print(f"Dataset pronto para análise com {{len(numeric_cols)}} vars numéricas e {{len(categorical_cols)}} categóricas")
"""

    def _execute_analysis_code(self, python_code: str) -> dict:
        """
        Executa o código Python gerado e retorna resultados formatados

        Args:
            python_code (str): Código Python para executar

        Returns:
            dict: Resultado com output e conclusões
        """
        try:
            # Criar ambiente de execução seguro
            local_vars = {{
                'data': self.data,
                'pd': pd,
                'np': np,
                'plt': plt,
                'sns': sns
            }}

            # Capturar output
            output_buffer = io.StringIO()

            # Lista para capturar gráficos gerados
            generated_charts = []

            # Função mock para plt.savefig que captura nomes
            original_savefig = plt.savefig
            def capture_savefig(filename, **kwargs):
                original_savefig(filename, **kwargs)
                if isinstance(filename, str) and filename.startswith('charts/'):
                    chart_name = filename.replace('charts/', '').replace('.png', '')
                    generated_charts.append(chart_name)

            # Substituir apenas no matplotlib, não no local_vars
            plt.savefig = capture_savefig

            # Executar código
            with redirect_stdout(output_buffer):
                exec(python_code, {"__builtins__": __builtins__}, local_vars)

            # Restaurar função original
            plt.savefig = original_savefig

            output = output_buffer.getvalue()

            # Registrar gráficos gerados no callback
            if self.chart_callback and generated_charts:
                self.chart_callback(generated_charts)

            # Gerar conclusões baseadas no output
            conclusions = self._generate_conclusions_from_output(output, python_code)

            return {
                'output': output if output else "Código executado com sucesso (sem output textual)",
                'conclusions': conclusions
            }

        except Exception as e:
            return {
                'output': f"Erro na execução: {str(e)}",
                'conclusions': "Não foi possível gerar conclusões devido ao erro na execução."
            }

    def _generate_conclusions_from_output(self, output: str, code: str) -> str:
        """
        Gera conclusões inteligentes baseadas no output do código executado

        Args:
            output (str): Output da execução do código
            code (str): Código Python executado

        Returns:
            str: Conclusões sobre os resultados
        """
        conclusions = []

        # Análise baseada no tipo de código executado
        if 'tipos de dados' in code.lower() or 'dtype' in code.lower():
            numeric_count = len(self.data.select_dtypes(include=['number']).columns)
            categorical_count = len(self.data.select_dtypes(include=['object']).columns)

            conclusions.append(f"• O dataset possui {{numeric_count}} variáveis numéricas e {{categorical_count}} categóricas")

            if numeric_count > categorical_count:
                conclusions.append("• Predominância de dados numéricos - ideal para análises estatísticas")
            elif categorical_count > numeric_count:
                conclusions.append("• Predominância de dados categóricos - adequado para análises de classificação")

        elif 'correlação' in code.lower():
            conclusions.append("• Correlações revelam relacionamentos lineares entre variáveis")
            conclusions.append("• Valores próximos de ±1 indicam correlação forte")
            conclusions.append("• Correlações fortes podem indicar redundância ou dependência entre variáveis")

        elif 'outlier' in code.lower():
            conclusions.append("• Outliers podem representar anomalias, erros ou casos especiais")
            conclusions.append("• Em detecção de fraude, outliers são especialmente importantes")
            conclusions.append("• Considere investigar registros com valores extremos")

        elif 'distribuição' in code.lower() or 'estatística' in code.lower():
            conclusions.append("• Estatísticas descritivas revelam padrões centrais dos dados")
            conclusions.append("• Desvio padrão alto indica maior variabilidade")
            conclusions.append("• Compare média vs mediana para identificar assimetria")

        elif 'intervalo' in code.lower() or 'amplitude' in code.lower():
            conclusions.append("• Amplitude mostra a dispersão dos dados")
            conclusions.append("• Intervalos muito amplos podem indicar presença de outliers")
            conclusions.append("• Percentis 5% e 95% mostram distribuição mais robusta")

        else:
            # Conclusões gerais
            conclusions.append(f"• Dataset analisado: {self.data.shape[0]} registros, {self.data.shape[1]} variáveis")
            conclusions.append("• Análise executada com sucesso usando código Python personalizado")
            conclusions.append("• Resultados baseados em cálculos diretos dos dados")

        return "\n".join(conclusions)

    def _analyze_data_types(self) -> str:
        """
        Analisa os tipos de dados de forma detalhada

        Returns:
            str: Análise detalhada dos tipos de dados
        """
        if self.data is None:
            return "Nenhum dado carregado."

        result = []
        result.append("ANÁLISE DE TIPOS DE DADOS")
        result.append("=" * 50)
        result.append(f"Dataset: {self.filename}")
        result.append(f"Shape: {self.data.shape[0]} linhas, {self.data.shape[1]} colunas")
        result.append("")

        # Análise por tipo
        numeric_cols = self.data.select_dtypes(include=[np.number]).columns
        categorical_cols = self.data.select_dtypes(include=['object', 'category']).columns
        datetime_cols = self.data.select_dtypes(include=['datetime64']).columns

        result.append("RESUMO POR TIPO:")
        result.append(f"- Colunas numericas: {len(numeric_cols)}")
        result.append(f"- Colunas categoricas: {len(categorical_cols)}")
        result.append(f"- Colunas de data/hora: {len(datetime_cols)}")
        result.append("")

        # Detalhes das colunas numéricas
        if len(numeric_cols) > 0:
            result.append("COLUNAS NUMERICAS:")
            for col in numeric_cols:
                dtype = str(self.data[col].dtype)
                non_null = self.data[col].count()
                result.append(f"  - {col}: {dtype} ({non_null} valores validos)")

        # Detalhes das colunas categóricas
        if len(categorical_cols) > 0:
            result.append("")
            result.append("COLUNAS CATEGORICAS:")
            for col in categorical_cols:
                unique_vals = self.data[col].nunique()
                non_null = self.data[col].count()
                result.append(f"  - {col}: object ({non_null} valores validos, {unique_vals} unicos)")

        # Detalhes das colunas de data
        if len(datetime_cols) > 0:
            result.append("")
            result.append("COLUNAS DE DATA/HORA:")
            for col in datetime_cols:
                non_null = self.data[col].count()
                result.append(f"  - {col}: datetime64 ({non_null} valores validos)")

        # Informações adicionais
        result.append("")
        result.append("INFORMACOES ADICIONAIS:")
        result.append(f"- Total de valores ausentes: {self.data.isnull().sum().sum()}")
        result.append(f"- Uso de memoria: {self.data.memory_usage(deep=True).sum() / 1024**2:.2f} MB")

        return "\n".join(result)

    def get_data_summary(self) -> Dict[str, Any]:
        """
        Get a comprehensive summary of the loaded data

        Returns:
            Dict containing various data summary metrics
        """
        if self.data is None:
            return {"error": "No data loaded"}

        summary = {
            "filename": self.filename,
            "shape": self.data.shape,
            "columns": list(self.data.columns),
            "data_types": self.data.dtypes.to_dict(),
            "missing_values": self.data.isnull().sum().to_dict(),
            "numerical_columns": list(self.data.select_dtypes(include=[np.number]).columns),
            "categorical_columns": list(self.data.select_dtypes(include=['object', 'category']).columns)
        }

        # Add statistical summary for numerical columns
        numeric_cols = self.data.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            summary["statistical_summary"] = self.data[numeric_cols].describe().to_dict()

        return summary

    def set_chart_callback(self, callback):
        """Define função callback para registrar gráficos gerados"""
        self.chart_callback = callback

    def _store_analysis_conclusion(self, question: str, conclusion: str, output: str):
        """Armazena conclusão da análise na memória da sessão"""
        import datetime

        # Determinar tipo de análise baseado na pergunta
        question_lower = question.lower()
        if any(word in question_lower for word in ['correlação', 'correlações', 'relacionamento']):
            analysis_type = "Análise de Correlação"
        elif any(word in question_lower for word in ['outlier', 'outliers', 'atípico']):
            analysis_type = "Detecção de Outliers"
        elif any(word in question_lower for word in ['distribuição', 'estatística', 'estatísticas']):
            analysis_type = "Estatísticas Descritivas"
        elif any(word in question_lower for word in ['tipos', 'type', 'estrutura']):
            analysis_type = "Estrutura dos Dados"
        else:
            analysis_type = "Análise Geral"

        # Extrair descobertas principais do output
        key_findings = []
        if output:
            lines = output.split('\n')
            for line in lines:
                if any(keyword in line.lower() for keyword in ['correlação', 'outliers', 'média', 'máximo', 'mínimo']):
                    key_findings.append(line.strip())

        # Armazenar na memória de conclusões
        conclusion_entry = {
            'timestamp': datetime.datetime.now(),
            'question': question,
            'analysis_type': analysis_type,
            'conclusion': conclusion,
            'key_findings': key_findings[:3],  # Top 3 descobertas
            'output_summary': output[:200] if output else ""  # Resumo do output
        }

        self.conclusions_memory.append(conclusion_entry)

        # Manter apenas últimas 10 conclusões para eficiência
        if len(self.conclusions_memory) > 10:
            self.conclusions_memory = self.conclusions_memory[-10:]

        # Atualizar contexto da sessão
        self.session_context['analysis_count'] += 1

        # Adicionar descoberta principal ao contexto se relevante
        if conclusion and len(conclusion) > 20:
            finding_summary = conclusion[:100] + "..." if len(conclusion) > 100 else conclusion
            if finding_summary not in self.session_context['key_findings']:
                self.session_context['key_findings'].append(finding_summary)

            # Manter apenas 5 descobertas principais
            if len(self.session_context['key_findings']) > 5:
                self.session_context['key_findings'] = self.session_context['key_findings'][-5:]

        # Armazenar histórico de análise
        self.analysis_history.append({
            'timestamp': datetime.datetime.now(),
            'type': analysis_type,
            'question': question,
            'success': True
        })

        # Atualizar resumo do dataset na primeira análise
        if not self.session_context['dataset_summary'] and self.data is not None:
            self.session_context['dataset_summary'] = f"{self.filename}: {self.data.shape[0]} linhas, {self.data.shape[1]} colunas"

    def process_question(self, question: str) -> str:
        """
        Processa uma pergunta do usuário (alias para ask_question para compatibilidade)

        Args:
            question (str): Pergunta sobre os dados

        Returns:
            str: Resposta do agente
        """
        return self.ask_question(question)

    def load_dataframe(self, dataframe: pd.DataFrame, filename: str = "dataframe_data") -> bool:
        """
        Carrega dados diretamente de um DataFrame pandas

        Args:
            dataframe (pd.DataFrame): DataFrame com os dados
            filename (str): Nome fictício para o arquivo

        Returns:
            bool: True se carregado com sucesso, False caso contrário
        """
        try:
            self.data = dataframe.copy()
            self.filename = filename

            # Initialize offline analyzer
            # offline_analyzer removido

            print(f"DataFrame carregado: {self.data.shape[0]} linhas, {self.data.shape[1]} colunas")
            return True

        except Exception as e:
            print(f"Erro ao carregar DataFrame: {e}")
            return False

    def clear_memory(self):
        """Limpa toda a memória e contexto da sessão"""
        try:
            # Limpar memória do LangChain
            if hasattr(self, 'memory') and self.memory:
                self.memory.clear()

            # Limpar memória de conclusões
            self.analysis_history.clear()
            self.conclusions_memory.clear()

            # Resetar contexto da sessão
            self.session_context = {
                'dataset_summary': None,
                'key_findings': [],
                'analysis_count': 0
            }

            print("🧹 Memória e contexto da sessão limpos")

        except Exception as e:
            print(f"⚠️ Erro ao limpar memória: {e}")

    def get_memory_summary(self) -> dict:
        """Retorna resumo da memória atual"""
        return {
            'conclusions_count': len(self.conclusions_memory),
            'analysis_count': self.session_context['analysis_count'],
            'key_findings_count': len(self.session_context['key_findings']),
            'dataset_summary': self.session_context['dataset_summary'],
            'has_conversation_memory': hasattr(self, 'memory') and self.memory is not None
        }