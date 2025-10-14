-- =====================================================
-- NF-e Validator - Rules Database Schema
-- MVP Sucroalcooleiro - Açúcar (SP + PE)
-- Version: 1.0.0
-- =====================================================

-- =====================================================
-- 1. NCM Rules (Nomenclatura Comum do Mercosul)
-- =====================================================
CREATE TABLE IF NOT EXISTS ncm_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ncm VARCHAR(8) NOT NULL UNIQUE,
    description TEXT NOT NULL,
    category VARCHAR(50),

    -- Tributação federal
    ipi_rate DECIMAL(5,2) DEFAULT 0.00,
    is_ipi_exempt BOOLEAN DEFAULT 0,

    -- PIS/COFINS
    pis_cofins_regime VARCHAR(20) DEFAULT 'STANDARD', -- STANDARD, MONOFASICO, EXEMPT

    -- Validação
    keywords TEXT, -- JSON array de palavras-chave para validação de descrição

    -- Metadata
    valid_from DATE,
    valid_until DATE,
    version VARCHAR(20) DEFAULT '1.0',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Setor específico
    sector VARCHAR(50) DEFAULT 'sucroalcooleiro',
    product_type VARCHAR(50), -- cristal, refinado, bruto, etc

    -- Observações
    notes TEXT
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_ncm_rules_ncm ON ncm_rules(ncm);
CREATE INDEX IF NOT EXISTS idx_ncm_rules_sector ON ncm_rules(sector);
CREATE INDEX IF NOT EXISTS idx_ncm_rules_valid ON ncm_rules(valid_from, valid_until);

-- =====================================================
-- 2. PIS/COFINS Rules
-- =====================================================
CREATE TABLE IF NOT EXISTS pis_cofins_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cst VARCHAR(2) NOT NULL UNIQUE,
    description TEXT NOT NULL,

    -- Tipo de situação
    situation_type VARCHAR(30) NOT NULL, -- TRIBUTADA, ISENTA, NAO_INCIDENCIA, SUSPENSA

    -- Alíquotas padrão
    pis_rate_standard DECIMAL(5,2),
    cofins_rate_standard DECIMAL(5,2),

    -- Alíquotas cumulativo (Simples/Presumido)
    pis_rate_cumulative DECIMAL(5,2),
    cofins_rate_cumulative DECIMAL(5,2),

    -- Regras
    requires_base_calculation BOOLEAN DEFAULT 1,
    allows_credit BOOLEAN DEFAULT 0,

    -- Base legal
    legal_reference VARCHAR(100),
    legal_article TEXT,

    -- Validação
    valid_for_operations TEXT, -- JSON array: ['VENDA', 'COMPRA', 'DEVOLUCAO']

    -- Metadata
    version VARCHAR(20) DEFAULT '1.0',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    notes TEXT
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_pis_cofins_cst ON pis_cofins_rules(cst);
CREATE INDEX IF NOT EXISTS idx_pis_cofins_situation ON pis_cofins_rules(situation_type);

-- =====================================================
-- 3. CFOP Rules (Código Fiscal de Operações)
-- =====================================================
CREATE TABLE IF NOT EXISTS cfop_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cfop VARCHAR(4) NOT NULL UNIQUE,
    description TEXT NOT NULL,

    -- Tipo de operação
    operation_type VARCHAR(20) NOT NULL, -- ENTRADA, SAIDA
    operation_scope VARCHAR(20) NOT NULL, -- INTERNO, INTERESTADUAL, EXTERIOR

    -- Classificação
    nature VARCHAR(50), -- VENDA, COMPRA, TRANSFERENCIA, DEVOLUCAO

    -- Validações
    requires_icms BOOLEAN DEFAULT 1,
    requires_ipi BOOLEAN DEFAULT 0,
    exempt_pis_cofins BOOLEAN DEFAULT 0, -- Exportação

    -- Uso comum
    common_for_sector VARCHAR(50), -- sucroalcooleiro, automotivo, etc

    -- Base legal
    legal_reference VARCHAR(100) DEFAULT 'Tabela CFOP - Ajuste SINIEF 07/05',

    -- Metadata
    version VARCHAR(20) DEFAULT '1.0',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    notes TEXT
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_cfop_cfop ON cfop_rules(cfop);
CREATE INDEX IF NOT EXISTS idx_cfop_scope ON cfop_rules(operation_scope);
CREATE INDEX IF NOT EXISTS idx_cfop_sector ON cfop_rules(common_for_sector);

-- =====================================================
-- 4. State Overrides (Regras Estaduais - SP + PE)
-- =====================================================
CREATE TABLE IF NOT EXISTS state_overrides (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    state VARCHAR(2) NOT NULL, -- SP, PE, MG, RJ, etc

    -- Tipo de override
    override_type VARCHAR(30) NOT NULL, -- ICMS, SUBSTITUICAO_TRIBUTARIA, REDUCAO_BC

    -- Aplicável a
    ncm VARCHAR(8), -- Específico para NCM
    cfop VARCHAR(4), -- Específico para CFOP
    sector VARCHAR(50), -- Específico para setor

    -- Regra
    rule_name VARCHAR(100) NOT NULL,
    rule_description TEXT NOT NULL,

    -- Valores
    icms_rate DECIMAL(5,2),
    icms_reduction_rate DECIMAL(5,2), -- Redução de base de cálculo

    -- Substituição Tributária
    is_st BOOLEAN DEFAULT 0,
    st_mva DECIMAL(5,2), -- Margem de Valor Agregado

    -- Base legal estadual
    legal_reference VARCHAR(200),
    legal_article TEXT,
    decree_number VARCHAR(50),

    -- Vigência
    valid_from DATE,
    valid_until DATE,

    -- Metadata
    version VARCHAR(20) DEFAULT '1.0',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Severidade (MVP: apenas warnings)
    severity VARCHAR(20) DEFAULT 'WARNING', -- INFO, WARNING, ERROR, CRITICAL

    notes TEXT
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_state_overrides_state ON state_overrides(state);
CREATE INDEX IF NOT EXISTS idx_state_overrides_ncm ON state_overrides(ncm);
CREATE INDEX IF NOT EXISTS idx_state_overrides_type ON state_overrides(override_type);
CREATE INDEX IF NOT EXISTS idx_state_overrides_valid ON state_overrides(valid_from, valid_until);

-- =====================================================
-- 5. Legal References (Referências Legais)
-- =====================================================
CREATE TABLE IF NOT EXISTS legal_refs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code VARCHAR(50) NOT NULL UNIQUE, -- LEI_10637, LEI_10833, IN_2121, TIPI_17

    -- Identificação
    ref_type VARCHAR(30) NOT NULL, -- LEI, DECRETO, INSTRUCAO_NORMATIVA, CONVENIO, PORTARIA
    number VARCHAR(50) NOT NULL,
    year INTEGER NOT NULL,

    -- Descrição
    title TEXT NOT NULL,
    summary TEXT,

    -- Órgão emissor
    issuing_body VARCHAR(100), -- RECEITA_FEDERAL, CONFAZ, etc

    -- Escopo
    scope VARCHAR(20) NOT NULL, -- FEDERAL, ESTADUAL, MUNICIPAL
    applicable_states TEXT, -- JSON array se estadual: ['SP', 'PE']

    -- Conteúdo
    full_text TEXT, -- Texto completo ou link
    url TEXT, -- URL oficial

    -- Artigos/Seções relevantes (JSON)
    relevant_articles TEXT,

    -- Relação com tributos
    affects_taxes TEXT, -- JSON: ['PIS', 'COFINS', 'ICMS', 'IPI']

    -- Vigência
    published_date DATE,
    effective_date DATE,
    revoked_date DATE,

    -- Metadata
    version VARCHAR(20) DEFAULT '1.0',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    notes TEXT
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_legal_refs_code ON legal_refs(code);
CREATE INDEX IF NOT EXISTS idx_legal_refs_type ON legal_refs(ref_type);
CREATE INDEX IF NOT EXISTS idx_legal_refs_scope ON legal_refs(scope);
CREATE INDEX IF NOT EXISTS idx_legal_refs_effective ON legal_refs(effective_date);

-- =====================================================
-- 6. Validation Log (Auditoria - opcional para MVP)
-- =====================================================
CREATE TABLE IF NOT EXISTS validation_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nfe_chave VARCHAR(44) NOT NULL,

    -- Validação
    validation_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    validator_version VARCHAR(20),

    -- Resultado
    status VARCHAR(20), -- VALID, INVALID, ERROR
    total_errors INTEGER DEFAULT 0,
    critical_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    warning_count INTEGER DEFAULT 0,

    -- Impacto
    financial_impact DECIMAL(15,2) DEFAULT 0.00,

    -- Dados JSON
    errors_json TEXT, -- JSON com lista de erros

    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_validation_log_chave ON validation_log(nfe_chave);
CREATE INDEX IF NOT EXISTS idx_validation_log_timestamp ON validation_log(validation_timestamp);

-- =====================================================
-- Views úteis
-- =====================================================

-- View: NCMs de açúcar ativos
CREATE VIEW IF NOT EXISTS v_sugar_ncms AS
SELECT
    ncm,
    description,
    product_type,
    pis_cofins_regime,
    keywords
FROM ncm_rules
WHERE sector = 'sucroalcooleiro'
  AND (valid_until IS NULL OR valid_until >= DATE('now'))
ORDER BY ncm;

-- View: CSTs PIS/COFINS válidos
CREATE VIEW IF NOT EXISTS v_valid_csts AS
SELECT
    cst,
    description,
    situation_type,
    pis_rate_standard,
    cofins_rate_standard,
    legal_reference
FROM pis_cofins_rules
WHERE version = '1.0'
ORDER BY cst;

-- View: CFOPs comuns para açúcar
CREATE VIEW IF NOT EXISTS v_sugar_cfops AS
SELECT
    cfop,
    description,
    operation_scope,
    nature,
    exempt_pis_cofins
FROM cfop_rules
WHERE common_for_sector = 'sucroalcooleiro'
   OR common_for_sector = 'geral'
ORDER BY cfop;

-- View: Regras SP + PE ativas
CREATE VIEW IF NOT EXISTS v_state_rules_active AS
SELECT
    state,
    override_type,
    ncm,
    rule_name,
    icms_rate,
    legal_reference,
    severity
FROM state_overrides
WHERE state IN ('SP', 'PE')
  AND (valid_until IS NULL OR valid_until >= DATE('now'))
ORDER BY state, override_type;

-- =====================================================
-- Triggers para atualização automática
-- =====================================================

-- Trigger: atualizar updated_at em ncm_rules
CREATE TRIGGER IF NOT EXISTS trg_ncm_rules_updated
AFTER UPDATE ON ncm_rules
FOR EACH ROW
BEGIN
    UPDATE ncm_rules
    SET updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
END;

-- Trigger: atualizar updated_at em pis_cofins_rules
CREATE TRIGGER IF NOT EXISTS trg_pis_cofins_updated
AFTER UPDATE ON pis_cofins_rules
FOR EACH ROW
BEGIN
    UPDATE pis_cofins_rules
    SET updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
END;

-- Trigger: atualizar updated_at em cfop_rules
CREATE TRIGGER IF NOT EXISTS trg_cfop_updated
AFTER UPDATE ON cfop_rules
FOR EACH ROW
BEGIN
    UPDATE cfop_rules
    SET updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
END;

-- Trigger: atualizar updated_at em state_overrides
CREATE TRIGGER IF NOT EXISTS trg_state_overrides_updated
AFTER UPDATE ON state_overrides
FOR EACH ROW
BEGIN
    UPDATE state_overrides
    SET updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
END;

-- =====================================================
-- Metadata da Database
-- =====================================================
CREATE TABLE IF NOT EXISTS db_metadata (
    key VARCHAR(50) PRIMARY KEY,
    value TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT OR REPLACE INTO db_metadata (key, value) VALUES
    ('schema_version', '1.0.0'),
    ('created_date', DATE('now')),
    ('mvp_scope', 'Sucroalcooleiro - Açúcar - SP+PE'),
    ('last_population', NULL);
