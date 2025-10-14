# -*- coding: utf-8 -*-
"""
Gerador de Relatório PDF - Agentes Autônomos
Sistema CSVEDA - Análise Exploratória de Dados com IA
"""

from reportlab.lib.pagesizes import A4, letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.colors import Color, HexColor
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.pdfgen import canvas
from datetime import datetime
import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches


def create_architecture_diagram():
    """Cria diagrama da arquitetura do sistema"""
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 8)
    ax.axis('off')

    # Cores
    color_ui = '#4A90E2'
    color_app = '#7ED321'
    color_domain = '#F5A623'
    color_infra = '#BD10E0'

    # Camada de Interface (UI)
    ui_rect = patches.Rectangle((1, 6.5), 8, 1, linewidth=2, edgecolor=color_ui, facecolor=color_ui, alpha=0.3)
    ax.add_patch(ui_rect)
    ax.text(5, 7, 'Interface Layer\n(Streamlit + Chat WhatsApp-style)', ha='center', va='center', fontsize=10, weight='bold')

    # Camada de Aplicação
    app_rect = patches.Rectangle((1, 5), 8, 1.2, linewidth=2, edgecolor=color_app, facecolor=color_app, alpha=0.3)
    ax.add_patch(app_rect)
    ax.text(5, 5.6, 'Application Layer\n(Use Cases + Interfaces)', ha='center', va='center', fontsize=10, weight='bold')

    # Camada de Domínio
    domain_rect = patches.Rectangle((1, 3.5), 8, 1.2, linewidth=2, edgecolor=color_domain, facecolor=color_domain, alpha=0.3)
    ax.add_patch(domain_rect)
    ax.text(5, 4.1, 'Domain Layer\n(Entities + Services + Business Logic)', ha='center', va='center', fontsize=10, weight='bold')

    # Camada de Infraestrutura
    infra_rect = patches.Rectangle((1, 1), 8, 2.2, linewidth=2, edgecolor=color_infra, facecolor=color_infra, alpha=0.3)
    ax.add_patch(infra_rect)
    ax.text(5, 2.1, 'Infrastructure Layer\n(Adapters + External Services + DI Container)', ha='center', va='center', fontsize=10, weight='bold')

    # Componentes específicos
    components = [
        (2, 1.5, 'LangChain\nAgents'),
        (4, 1.5, 'Google Gemini\nAPI'),
        (6, 1.5, 'Pandas\nProcessor'),
        (8, 1.5, 'Memory\nSystem')
    ]

    for x, y, text in components:
        comp_rect = patches.Rectangle((x-0.4, y-0.3), 0.8, 0.6, linewidth=1, edgecolor='black', facecolor='white', alpha=0.8)
        ax.add_patch(comp_rect)
        ax.text(x, y, text, ha='center', va='center', fontsize=8)

    # Setas de dependência
    arrow_props = dict(arrowstyle='->', connectionstyle='arc3', color='gray', lw=1.5)
    ax.annotate('', xy=(5, 6.4), xytext=(5, 6.2), arrowprops=arrow_props)
    ax.annotate('', xy=(5, 4.9), xytext=(5, 4.7), arrowprops=arrow_props)
    ax.annotate('', xy=(5, 3.4), xytext=(5, 3.2), arrowprops=arrow_props)

    ax.set_title('CSVEDA - Clean Architecture com Agentes Autônomos', fontsize=14, weight='bold', pad=20)

    plt.tight_layout()
    plt.savefig('architecture_diagram.png', dpi=300, bbox_inches='tight')
    plt.close()
    return 'architecture_diagram.png'


def create_agent_flow_diagram():
    """Cria diagrama do fluxo dos agentes"""
    fig, ax = plt.subplots(1, 1, figsize=(12, 10))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')

    # Definir posições dos componentes
    components = [
        (5, 9, 'Usuário\n(Pergunta)', '#FF6B6B'),
        (5, 7.5, 'Chat Interface\n(Streamlit)', '#4ECDC4'),
        (5, 6, 'EDA Agent\n(LangChain ReAct)', '#45B7D1'),
        (2, 4.5, 'Memória\n(Conclusões)', '#96CEB4'),
        (5, 4.5, 'Ferramentas\n(Python Tools)', '#FFEAA7'),
        (8, 4.5, 'LLM\n(Google Gemini)', '#DDA0DD'),
        (3, 3, 'Análise\nEstatística', '#FFB347'),
        (5, 3, 'Geração de\nCódigo Python', '#98D8C8'),
        (7, 3, 'Visualizações\n(Gráficos)', '#F7DC6F'),
        (5, 1.5, 'Resposta Final\n+ Conclusões', '#AED6F1')
    ]

    # Desenhar componentes
    for x, y, text, color in components:
        circle = patches.Circle((x, y), 0.6, linewidth=2, edgecolor='black', facecolor=color, alpha=0.7)
        ax.add_patch(circle)
        ax.text(x, y, text, ha='center', va='center', fontsize=9, weight='bold')

    # Desenhar fluxos
    flows = [
        ((5, 8.4), (5, 8.1)),  # Usuário -> Interface
        ((5, 6.9), (5, 6.6)),  # Interface -> Agent
        ((5, 5.4), (2, 5.1)),  # Agent -> Memória
        ((5, 5.4), (5, 5.1)),  # Agent -> Ferramentas
        ((5, 5.4), (8, 5.1)),  # Agent -> LLM
        ((5, 3.9), (3, 3.6)),  # Ferramentas -> Análise
        ((5, 3.9), (5, 3.6)),  # Ferramentas -> Código
        ((5, 3.9), (7, 3.6)),  # Ferramentas -> Visualizações
        ((3, 2.4), (5, 2.1)),  # Análise -> Resposta
        ((5, 2.4), (5, 2.1)),  # Código -> Resposta
        ((7, 2.4), (5, 2.1))   # Visualizações -> Resposta
    ]

    arrow_props = dict(arrowstyle='->', connectionstyle='arc3', color='#2C3E50', lw=2)
    for start, end in flows:
        ax.annotate('', xy=end, xytext=start, arrowprops=arrow_props)

    # Adicionar labels especiais
    ax.text(0.5, 4.5, 'Contexto\nHistórico', ha='center', va='center', fontsize=8,
            bbox=dict(boxstyle="round,pad=0.3", facecolor='lightblue', alpha=0.5))
    ax.text(9.5, 4.5, 'Processamento\nLinguístico', ha='center', va='center', fontsize=8,
            bbox=dict(boxstyle="round,pad=0.3", facecolor='lightgreen', alpha=0.5))

    ax.set_title('Fluxo de Processamento dos Agentes Autônomos', fontsize=14, weight='bold', pad=20)

    plt.tight_layout()
    plt.savefig('agent_flow_diagram.png', dpi=300, bbox_inches='tight')
    plt.close()
    return 'agent_flow_diagram.png'


def generate_report():
    """Gera o relatório PDF completo"""

    # Criar diagramas
    arch_diagram = create_architecture_diagram()
    flow_diagram = create_agent_flow_diagram()

    # Configuração do documento
    doc = SimpleDocTemplate(
        "Agentes Autônomos – Relatório da Atividade Extra.pdf",
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18
    )

    # Estilos
    styles = getSampleStyleSheet()

    # Estilos customizados
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=HexColor('#2C3E50')
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        spaceBefore=20,
        textColor=HexColor('#34495E')
    )

    subheading_style = ParagraphStyle(
        'CustomSubHeading',
        parent=styles['Heading3'],
        fontSize=12,
        spaceAfter=8,
        spaceBefore=12,
        textColor=HexColor('#5D6D7E')
    )

    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=12,
        alignment=TA_JUSTIFY,
        leftIndent=0,
        rightIndent=0
    )

    # Construir o conteúdo
    story = []

    # Título principal
    story.append(Paragraph("Agentes Autônomos", title_style))
    story.append(Paragraph("Relatório da Atividade Extra", title_style))
    story.append(Spacer(1, 20))

    # Informações do projeto
    info_data = [
        ['Sistema:', 'CSVEDA - Análise Exploratória de Dados com IA'],
        ['Desenvolvedor:', 'Claude Code'],
        ['Data:', datetime.now().strftime('%d/%m/%Y')],
        ['Versão:', '1.0.0']
    ]

    info_table = Table(info_data, colWidths=[2*inch, 4*inch])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), HexColor('#ECF0F1')),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.black),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 12),
        ('GRID', (0,0), (-1,-1), 1, colors.black)
    ]))

    story.append(info_table)
    story.append(Spacer(1, 30))

    # 1. Framework Escolhida
    story.append(Paragraph("1. Framework Escolhida", heading_style))

    framework_text = """
    A solução foi desenvolvida utilizando uma arquitetura moderna baseada em múltiplas tecnologias integradas:
    """
    story.append(Paragraph(framework_text, normal_style))

    # Tabela de frameworks
    framework_data = [
        ['Componente', 'Framework/Tecnologia', 'Versão', 'Finalidade'],
        ['Interface de Usuário', 'Streamlit', '1.28+', 'Interface web responsiva com chat WhatsApp-style'],
        ['Agentes Autônomos', 'LangChain', '0.1+', 'Framework para construção de agentes com LLM'],
        ['Modelo de Linguagem', 'Google Gemini', '2.5', 'Processamento de linguagem natural e geração de código'],
        ['Alternativa LLM', 'Mistral via Ollama', 'Latest', 'Modelo local para redundância'],
        ['Processamento de Dados', 'Pandas + NumPy', '2.1+', 'Manipulação e análise de datasets CSV'],
        ['Visualizações', 'Matplotlib + Seaborn', '5.17+', 'Geração automática de gráficos'],
        ['Arquitetura', 'Clean Architecture', 'Custom', 'Separação de responsabilidades e testabilidade'],
        ['Injeção de Dependências', 'DI Container Custom', '1.0', 'Inversão de controle e modularidade'],
        ['Logging', 'Loguru', '0.7+', 'Logging estruturado em JSON'],
        ['Configuração', 'Pydantic + Python-decouple', '2.5+', 'Gestão de configurações externa'],
        ['Testes', 'Pytest', '7.4+', 'Testes unitários e de integração'],
        ['CI/CD', 'GitHub Actions', 'Latest', 'Pipeline de integração e deploy contínuo']
    ]

    framework_table = Table(framework_data, colWidths=[1.5*inch, 1.8*inch, 0.8*inch, 2.2*inch])
    framework_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), HexColor('#3498DB')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, HexColor('#F8F9FA')])
    ]))

    story.append(framework_table)
    story.append(Spacer(1, 20))

    # Justificativa da escolha
    justificativa_text = """
    <b>Justificativa das Escolhas:</b><br/>
    • <b>LangChain</b>: Framework líder para desenvolvimento de agentes autônomos com LLM, oferecendo padrões ReAct, ferramentas integradas e gestão de memória.<br/>
    • <b>Google Gemini</b>: Modelo de linguagem de última geração com capacidades avançadas de geração de código e análise de dados.<br/>
    • <b>Streamlit</b>: Framework Python que permite desenvolvimento rápido de interfaces web interativas, ideal para prototipagem de aplicações de dados.<br/>
    • <b>Clean Architecture</b>: Padrão arquitetural que promove separação de responsabilidades, testabilidade e manutenibilidade.<br/>
    • <b>Pandas</b>: Biblioteca padrão da indústria para manipulação de dados estruturados em Python.
    """
    story.append(Paragraph(justificativa_text, normal_style))
    story.append(PageBreak())

    # 2. Como a Solução foi Estruturada
    story.append(Paragraph("2. Como a Solução foi Estruturada", heading_style))

    estrutura_text = """
    A solução segue os princípios da Clean Architecture, implementando separação clara de responsabilidades
    através de camadas bem definidas. O sistema foi projetado para ser modular, testável e extensível.
    """
    story.append(Paragraph(estrutura_text, normal_style))

    # Diagrama de arquitetura
    story.append(Paragraph("2.1. Arquitetura do Sistema", subheading_style))
    if os.path.exists(arch_diagram):
        story.append(Image(arch_diagram, width=6*inch, height=4*inch))
    story.append(Spacer(1, 15))

    # Descrição das camadas
    camadas_text = """
    <b>Estrutura em Camadas:</b><br/><br/>
    <b>1. Interface Layer (Apresentação):</b><br/>
    • Interface web desenvolvida em Streamlit com design WhatsApp-style<br/>
    • Chat interativo com histórico persistente<br/>
    • Exibição automática de gráficos e resultados<br/>
    • Responsável apenas pela apresentação e interação com usuário<br/><br/>

    <b>2. Application Layer (Aplicação):</b><br/>
    • Casos de uso que orquestram o fluxo de dados<br/>
    • Interfaces que definem contratos com a infraestrutura<br/>
    • LoadDatasetUseCase, AnalyzeDatasetUseCase, ExportAnalysisUseCase<br/>
    • Coordena interações entre domínio e infraestrutura<br/><br/>

    <b>3. Domain Layer (Domínio):</b><br/>
    • Entidades de negócio: DatasetInfo, AnalysisResult, Visualization<br/>
    • Serviços de domínio: DataAnalysisService, QueryAnalysisService<br/>
    • Lógica de negócio pura, independente de frameworks<br/>
    • Regras de análise estatística e validação de dados<br/><br/>

    <b>4. Infrastructure Layer (Infraestrutura):</b><br/>
    • Adaptadores para frameworks externos<br/>
    • Implementações concretas das interfaces<br/>
    • DI Container para injeção de dependências<br/>
    • Integração com APIs externas (Gemini, Ollama)
    """
    story.append(Paragraph(camadas_text, normal_style))
    story.append(PageBreak())

    # Fluxo dos agentes
    story.append(Paragraph("2.2. Fluxo de Processamento dos Agentes", subheading_style))
    if os.path.exists(flow_diagram):
        story.append(Image(flow_diagram, width=6*inch, height=5*inch))
    story.append(Spacer(1, 15))

    agentes_text = """
    <b>Sistema de Agentes Autônomos:</b><br/><br/>

    <b>EDA Agent (Agente Principal):</b><br/>
    • Implementa padrão ReAct (Reasoning + Acting) do LangChain<br/>
    • Possui 9 ferramentas especializadas para análise de dados<br/>
    • Sistema de memória avançado com ConversationSummaryBufferMemory<br/>
    • Capaz de gerar e executar código Python dinamicamente<br/><br/>

    <b>Ferramentas Disponíveis:</b><br/>
    • describe_data: Informações estruturais do dataset<br/>
    • get_statistical_summary: Estatísticas descritivas<br/>
    • check_correlations: Análise de correlações<br/>
    • detect_outliers: Detecção de outliers (IQR, Z-score)<br/>
    • analyze_categorical_data: Análise de variáveis categóricas<br/>
    • generate_and_execute_python_code: Geração dinâmica de código<br/>
    • get_temporal_analysis: Análise de padrões temporais<br/>
    • get_previous_conclusions: Acesso ao histórico de análises<br/>
    • get_session_context: Contexto da sessão atual<br/><br/>

    <b>Sistema de Memória:</b><br/>
    • Mantém contexto entre perguntas consecutivas<br/>
    • Armazena conclusões e descobertas principais<br/>
    • Categoriza automaticamente tipos de análise realizadas<br/>
    • Permite síntese inteligente de múltiplas análises
    """
    story.append(Paragraph(agentes_text, normal_style))
    story.append(PageBreak())

    # Estrutura de diretórios
    story.append(Paragraph("2.3. Estrutura de Diretórios", subheading_style))

    estrutura_dir = """
    <b>Organização do Código:</b><br/><br/>
    <font name="Courier">
    CSVEDA/<br/>
    ├── src/<br/>
    │   ├── domain/                    # Camada de Domínio<br/>
    │   │   ├── entities.py           # Entidades de negócio<br/>
    │   │   └── services.py           # Serviços de domínio<br/>
    │   ├── application/              # Camada de Aplicação<br/>
    │   │   ├── use_cases/           # Casos de uso<br/>
    │   │   └── interfaces/          # Contratos para infraestrutura<br/>
    │   ├── infrastructure/          # Camada de Infraestrutura<br/>
    │   │   ├── adapters/           # Implementações de interfaces<br/>
    │   │   └── di/                 # Sistema de injeção de dependências<br/>
    │   ├── interfaces/             # Interfaces globais (LLM, Agents)<br/>
    │   ├── agents/                 # Implementação dos agentes<br/>
    │   ├── utils/                  # Utilitários (Logger)<br/>
    │   └── config/                 # Configurações<br/>
    ├── tests/                      # Testes automatizados<br/>
    ├── .github/workflows/          # CI/CD<br/>
    ├── charts/                     # Gráficos gerados<br/>
    ├── app.py                      # Aplicação principal<br/>
    ├── requirements.txt            # Dependências<br/>
    ├── pytest.ini                 # Configuração de testes<br/>
    ├── pyproject.toml             # Configuração do projeto<br/>
    └── .env.example               # Template de configuração
    </font>
    """
    story.append(Paragraph(estrutura_dir, normal_style))
    story.append(Spacer(1, 20))

    # Características técnicas
    story.append(Paragraph("2.4. Características Técnicas Implementadas", subheading_style))

    caracteristicas_data = [
        ['Funcionalidade', 'Implementação', 'Benefício'],
        ['Logging Estruturado', 'Loguru com formato JSON', 'Auditoria e debug avançado'],
        ['Configuração Externa', 'Pydantic + .env', 'Deployment flexível'],
        ['Testes Automatizados', 'Pytest com fixtures', 'Qualidade e confiabilidade'],
        ['CI/CD Pipeline', 'GitHub Actions', 'Integração e deploy contínuo'],
        ['Sistema de Memória', 'ConversationSummaryBufferMemory', 'Contexto entre perguntas'],
        ['Geração de Código', 'LLM dinâmico + execução segura', 'Análises personalizadas'],
        ['Tratamento de Erros', 'Fallbacks inteligentes', 'Robustez e disponibilidade'],
        ['Arquitetura Limpa', 'Separação de camadas', 'Manutenibilidade'],
        ['DI Container', 'Injeção de dependências', 'Testabilidade e modularidade']
    ]

    caracteristicas_table = Table(caracteristicas_data, colWidths=[2*inch, 2.3*inch, 2*inch])
    caracteristicas_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), HexColor('#E74C3C')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, HexColor('#FDEDEC')])
    ]))

    story.append(caracteristicas_table)
    story.append(PageBreak())

    # Inovações implementadas
    story.append(Paragraph("2.5. Inovações e Diferenciais", subheading_style))

    inovacoes_text = """
    <b>Principais Inovações Implementadas:</b><br/><br/>

    <b>1. Sistema de Memória Contextual:</b><br/>
    • Agente mantém contexto completo entre perguntas<br/>
    • Armazenamento automático de conclusões e descobertas<br/>
    • Síntese inteligente de múltiplas análises<br/>
    • Categorização automática de tipos de análise<br/><br/>

    <b>2. Geração Dinâmica de Código:</b><br/>
    • LLM gera código Python personalizado para cada pergunta<br/>
    • Execução segura em ambiente controlado<br/>
    • Geração automática de visualizações<br/>
    • Validação e tratamento de erros<br/><br/>

    <b>3. Interface Conversacional Avançada:</b><br/>
    • Chat estilo WhatsApp com histórico persistente<br/>
    • Exibição automática de gráficos gerados<br/>
    • Processamento inteligente de respostas<br/>
    • Feedback visual do progresso<br/><br/>

    <b>4. Arquitetura Enterprise-Grade:</b><br/>
    • Clean Architecture com DDD<br/>
    • Injeção de dependências customizada<br/>
    • Sistema de logging estruturado<br/>
    • Pipeline CI/CD completo<br/>
    • Testes automatizados<br/><br/>

    <b>5. Robustez e Tolerância a Falhas:</b><br/>
    • Fallbacks inteligentes para erros de LLM<br/>
    • Sistema de retry com diferentes modelos<br/>
    • Validação de dados em múltiplas camadas<br/>
    • Tratamento específico de erros conhecidos
    """
    story.append(Paragraph(inovacoes_text, normal_style))
    story.append(Spacer(1, 20))

    # Conclusão
    story.append(Paragraph("3. Conclusão", heading_style))

    conclusao_text = """
    O sistema CSVEDA representa uma implementação avançada de agentes autônomos para análise exploratória
    de dados, combinando as melhores práticas de engenharia de software com tecnologias de IA de ponta.
    <br/><br/>
    A arquitetura limpa implementada garante que o sistema seja:<br/>
    • <b>Escalável</b>: Fácil adição de novos tipos de análise e ferramentas<br/>
    • <b>Manutenível</b>: Separação clara de responsabilidades<br/>
    • <b>Testável</b>: Cobertura completa de testes automatizados<br/>
    • <b>Robusto</b>: Tratamento abrangente de erros e fallbacks<br/>
    • <b>Inteligente</b>: Sistema de memória contextual único<br/>
    <br/>
    O diferencial principal está na capacidade do agente de manter contexto entre interações,
    construindo conhecimento incrementalmente e fornecendo análises cada vez mais sofisticadas
    conforme a conversa evolui.
    """
    story.append(Paragraph(conclusao_text, normal_style))

    # Gerar PDF
    doc.build(story)

    # Limpar arquivos temporários
    for file in [arch_diagram, flow_diagram]:
        if os.path.exists(file):
            os.remove(file)

    print("Relatorio PDF gerado com sucesso: 'Agentes Autonomos - Relatorio da Atividade Extra.pdf'")


if __name__ == "__main__":
    generate_report()