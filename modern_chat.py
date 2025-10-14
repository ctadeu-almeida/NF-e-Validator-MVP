import streamlit as st
import sqlite3
import json
import base64
from datetime import datetime
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
from io import BytesIO
import uuid

# =====================================================
# DATABASE MANAGER - Histórico Persistente
# =====================================================

class ChatHistoryDB:
    def __init__(self, db_path="chat_history.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                session_id TEXT,
                timestamp TEXT,
                role TEXT,
                content TEXT,
                content_type TEXT,
                metadata TEXT
            )
        """)
        conn.commit()
        conn.close()

    def save_message(self, session_id, role, content, content_type="text", metadata=None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        msg_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO conversations VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            msg_id,
            session_id,
            datetime.now().isoformat(),
            role,
            content,
            content_type,
            json.dumps(metadata or {})
        ))
        conn.commit()
        conn.close()
        return msg_id

    def get_session_history(self, session_id, limit=100):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM conversations
            WHERE session_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (session_id, limit))
        messages = cursor.fetchall()
        conn.close()
        return list(reversed(messages))

    def export_conversation(self, session_id):
        messages = self.get_session_history(session_id, limit=10000)
        return json.dumps([{
            "id": m[0],
            "timestamp": m[2],
            "role": m[3],
            "content": m[4],
            "type": m[5]
        } for m in messages], indent=2)

# =====================================================
# MESSAGE COMPONENTS - Diferentes tipos de mensagens
# =====================================================

class MessageRenderer:
    @staticmethod
    def render_text(content, role):
        """Renderiza mensagem de texto"""
        alignment = "flex-end" if role == "user" else "flex-start"
        bg_color = "#075E54"

        st.markdown(f"""
            <div style="display: flex; justify-content: {alignment}; margin: 10px 0;">
                <div style="background-color: {bg_color};
                            padding: 10px 15px;
                            border-radius: 10px;
                            max-width: 70%;
                            box-shadow: 0 1px 2px rgba(0,0,0,0.1);">
                    <p style="margin: 0; color: #FFFFFF !important;">{content}</p>
                </div>
            </div>
        """, unsafe_allow_html=True)

    @staticmethod
    def render_image(image_data, role):
        """Renderiza imagem base64"""
        alignment = "flex-end" if role == "user" else "flex-start"
        st.markdown(f"""
            <div style="display: flex; justify-content: {alignment}; margin: 10px 0;">
                <div style="max-width: 70%;">
                    <img src="data:image/png;base64,{image_data}"
                         style="width: 100%; border-radius: 10px;
                                box-shadow: 0 1px 2px rgba(0,0,0,0.1);">
                </div>
            </div>
        """, unsafe_allow_html=True)

    @staticmethod
    def render_plotly(fig_json, role):
        """Renderiza gráfico Plotly"""
        fig = go.Figure(json.loads(fig_json))
        st.plotly_chart(fig, use_container_width=True)

    @staticmethod
    def render_dataframe(df_json, role):
        """Renderiza DataFrame"""
        df = pd.read_json(df_json)
        st.dataframe(df, use_container_width=True)

    @staticmethod
    def render_file(file_info, role):
        """Renderiza link de arquivo"""
        alignment = "flex-end" if role == "user" else "flex-start"
        st.markdown(f"""
            <div style="display: flex; justify-content: {alignment}; margin: 10px 0;">
                <div style="background-color: #075E54;
                            padding: 10px 15px;
                            border-radius: 10px;
                            max-width: 70%;">
                    <p style="margin: 0; color: #FFFFFF !important;">📎 {file_info['name']}</p>
                    <small style="color: #FFFFFF !important;">{file_info['size']} KB</small>
                </div>
            </div>
        """, unsafe_allow_html=True)

# =====================================================
# CHAT INTERFACE - Interface principal
# =====================================================

class WhatsAppStyleChat:
    def __init__(self, session_id=None):
        self.db = ChatHistoryDB()
        self.session_id = session_id or str(uuid.uuid4())
        self.renderer = MessageRenderer()

        # Inicializar session state
        if 'messages' not in st.session_state:
            st.session_state.messages = []
            self._load_history()

    def _load_history(self):
        """Carrega histórico do banco"""
        history = self.db.get_session_history(self.session_id)
        for msg in history:
            st.session_state.messages.append({
                'id': msg[0],
                'role': msg[3],
                'content': msg[4],
                'type': msg[5],
                'metadata': json.loads(msg[6])
            })

    def render_header(self):
        """Renderiza header estilo WhatsApp"""
        st.markdown("""
            <div style="background: #075E54;
                        color: white;
                        padding: 15px;
                        border-radius: 10px 10px 0 0;
                        display: flex;
                        align-items: center;">
                <div style="width: 40px;
                            height: 40px;
                            background: #25D366;
                            border-radius: 50%;
                            margin-right: 15px;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            font-size: 20px;">
                    🤖
                </div>
                <div>
                    <h3 style="margin: 0; color: #FFFFFF !important;">EDA Assistant</h3>
                    <small style="color: #FFFFFF !important;">Online - Análise de Dados com IA</small>
                </div>
            </div>
        """, unsafe_allow_html=True)

    def render_messages(self):
        """Renderiza todas as mensagens"""
        chat_container = st.container()

        with chat_container:
            for msg in st.session_state.messages:
                if msg['type'] == 'text':
                    self.renderer.render_text(msg['content'], msg['role'])
                elif msg['type'] == 'image':
                    self.renderer.render_image(msg['content'], msg['role'])
                elif msg['type'] == 'plotly':
                    self.renderer.render_plotly(msg['content'], msg['role'])
                elif msg['type'] == 'dataframe':
                    self.renderer.render_dataframe(msg['content'], msg['role'])
                elif msg['type'] == 'file':
                    self.renderer.render_file(
                        json.loads(msg['content']),
                        msg['role']
                    )

    def add_message(self, role, content, content_type="text", metadata=None):
        """Adiciona nova mensagem"""
        msg = {
            'id': str(uuid.uuid4()),
            'role': role,
            'content': content,
            'type': content_type,
            'metadata': metadata or {}
        }
        st.session_state.messages.append(msg)

        # Salvar no banco
        self.db.save_message(
            self.session_id,
            role,
            content,
            content_type,
            metadata
        )

    def add_plotly_chart(self, fig, role="assistant"):
        """Adiciona gráfico Plotly"""
        fig_json = fig.to_json()
        self.add_message(role, fig_json, "plotly")

    def add_dataframe(self, df, role="assistant"):
        """Adiciona DataFrame"""
        df_json = df.to_json()
        self.add_message(role, df_json, "dataframe")

    def add_image_from_bytes(self, image_bytes, role="assistant"):
        """Adiciona imagem de bytes"""
        b64 = base64.b64encode(image_bytes).decode()
        self.add_message(role, b64, "image")

    def render_input_area(self):
        """Renderiza área de input com opções"""
        col1, col2 = st.columns([8, 1])

        with col1:
            user_input = st.chat_input("Digite sua mensagem...")

        with col2:
            if st.button("🗑️", help="Limpar conversa"):
                st.session_state.messages = []
                st.rerun()

        return user_input, None

    def export_conversation(self):
        """Exporta conversa como JSON"""
        return self.db.export_conversation(self.session_id)

# =====================================================
# INTEGRAÇÃO COM EDA
# =====================================================

def process_eda_query(query, eda_agent=None, df=None):
    """Processa query EDA usando o agente existente"""
    if not eda_agent:
        return {"type": "text", "content": "❌ Agente EDA não inicializado"}

    try:
        # Usar o agente EDA existente
        response = eda_agent.ask_question(query)

        # Verificar se há gráficos gerados
        charts_dir = Path('charts')
        if charts_dir.exists():
            chart_files = list(charts_dir.glob('*.png'))
            # Pegar gráficos mais recentes (últimos 120 segundos - tempo aumentado)
            import time
            current_time = time.time()
            recent_charts = [
                f for f in chart_files
                if current_time - f.stat().st_mtime < 120  # 2 minutos
            ]

            # Debug: mostrar informações dos gráficos
            print(f"🔍 Charts encontrados: {len(chart_files)}")
            print(f"📊 Charts recentes: {len(recent_charts)}")
            for chart in recent_charts:
                age = current_time - chart.stat().st_mtime
                print(f"  - {chart.name} (idade: {age:.1f}s)")

            if recent_charts:
                print(f"✅ Enviando {len(recent_charts)} gráfico(s) para o chat")
                return {
                    "type": "multi",
                    "content": [
                        {"type": "text", "content": response},
                        {"type": "charts", "content": recent_charts}
                    ]
                }
            else:
                print("⚠️ Nenhum gráfico recente encontrado")

        return {"type": "text", "content": response}

    except Exception as e:
        return {"type": "text", "content": f"❌ Erro: {str(e)}"}

# =====================================================
# APLICAÇÃO PRINCIPAL - Integrada com app.py
# =====================================================

def render_modern_chat():
    """Função para ser chamada do app.py principal"""

    # CSS WhatsApp
    st.markdown("""
        <style>
        .stApp {
            background-color: #075E54 !important;
        }
        .main-chat-container {
            background-color: #075E54;
            border-radius: 10px;
            padding: 0;
            margin: 10px 0;
        }
        .main-chat-container * {
            color: #FFFFFF !important;
        }
        .main-chat-container h1, .main-chat-container h2, .main-chat-container h3,
        .main-chat-container h4, .main-chat-container h5, .main-chat-container h6 {
            color: #FFFFFF !important;
        }
        .main-chat-container p, .main-chat-container div, .main-chat-container span {
            color: #FFFFFF !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # Verificar se tem agente e dados carregados
    if not st.session_state.get('eda_agent'):
        st.warning("⚠️ Inicialize um modelo IA primeiro")
        return

    if st.session_state.get('current_data') is None:
        st.warning("⚠️ Carregue um dataset CSV primeiro")
        return

    # Inicializar chat
    chat = WhatsAppStyleChat()

    # Container principal
    with st.container():
        st.markdown('<div class="main-chat-container">', unsafe_allow_html=True)

        # Header
        chat.render_header()

        # Mensagens
        chat.render_messages()

        st.markdown('</div>', unsafe_allow_html=True)

    # Input
    user_input, file_upload = chat.render_input_area()

    # Processar input
    if user_input:
        # Adicionar mensagem do usuário
        chat.add_message("user", user_input)

        # Processar com EDA agent
        with st.spinner("🤖 Analisando..."):
            result = process_eda_query(
                user_input,
                st.session_state.eda_agent,
                st.session_state.current_data
            )

        # Adicionar resposta
        if result['type'] == 'text':
            chat.add_message("assistant", result['content'])
        elif result['type'] == 'multi':
            for item in result['content']:
                if item['type'] == 'text':
                    chat.add_message("assistant", item['content'])
                elif item['type'] == 'charts':
                    # Converter gráficos para base64
                    for chart_path in item['content']:
                        with open(chart_path, 'rb') as f:
                            chart_bytes = f.read()
                        chat.add_image_from_bytes(chart_bytes)

        st.rerun()

    # Upload removido - dados carregados via sidebar principal

# Para teste standalone
if __name__ == "__main__":
    st.set_page_config(
        page_title="Modern EDA Chat",
        page_icon="💬",
        layout="wide"
    )
    render_modern_chat()