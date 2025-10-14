# -*- coding: utf-8 -*-
"""
Logging Structure - Sistema de logging estruturado com Loguru

Este módulo configura logging JSON estruturado para auditoria,
debugging e observabilidade da aplicação.
"""

import sys
from pathlib import Path
from loguru import logger
from typing import Dict, Any, Optional
import json


class StructuredLogger:
    """Logger estruturado para a aplicação CSVEDA"""

    def __init__(self, log_level: str = "INFO"):
        self.log_level = log_level
        self._setup_logger()

    def _setup_logger(self):
        """Configurar loguru com formato JSON estruturado"""
        # Remover configuração padrão
        logger.remove()

        # Criar diretório de logs
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        # Formato JSON estruturado
        json_format = (
            "{"
            '"timestamp": "{time:YYYY-MM-DD HH:mm:ss.SSS}", '
            '"level": "{level}", '
            '"module": "{module}", '
            '"function": "{function}", '
            '"line": {line}, '
            '"message": "{message}", '
            '"extra": {extra}'
            "}"
        )

        # Console (desenvolvimento)
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                   "<level>{level: <8}</level> | "
                   "<cyan>{module}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                   "<level>{message}</level>",
            level=self.log_level,
            colorize=True
        )

        # Arquivo JSON (produção)
        logger.add(
            log_dir / "csveda.log",
            format=json_format,
            level=self.log_level,
            rotation="10 MB",
            retention="30 days",
            compression="gz",
            serialize=False
        )

        # Arquivo de erros específico
        logger.add(
            log_dir / "errors.log",
            format=json_format,
            level="ERROR",
            rotation="10 MB",
            retention="60 days",
            compression="gz",
            serialize=False
        )

    def log_user_action(self, action: str, user_id: Optional[str] = None, **kwargs):
        """Log de ações do usuário para auditoria"""
        logger.info(
            f"User action: {action}",
            action=action,
            user_id=user_id or "anonymous",
            **kwargs
        )

    def log_agent_interaction(self, model: str, query: str, success: bool,
                            response_time: float, **kwargs):
        """Log de interações com agentes IA"""
        logger.info(
            f"Agent interaction: {model}",
            model=model,
            query=query[:100] + "..." if len(query) > 100 else query,
            success=success,
            response_time=response_time,
            **kwargs
        )

    def log_data_operation(self, operation: str, file_name: str,
                          rows: int, columns: int, **kwargs):
        """Log de operações com dados"""
        logger.info(
            f"Data operation: {operation}",
            operation=operation,
            file_name=file_name,
            rows=rows,
            columns=columns,
            **kwargs
        )

    def log_error(self, error: Exception, context: Dict[str, Any] = None):
        """Log estruturado de erros"""
        logger.error(
            f"Error: {str(error)}",
            error_type=type(error).__name__,
            error_message=str(error),
            context=context or {}
        )

    def log_performance(self, operation: str, duration: float, **kwargs):
        """Log de métricas de performance"""
        logger.info(
            f"Performance: {operation}",
            operation=operation,
            duration=duration,
            **kwargs
        )


# Instância global do logger
app_logger = StructuredLogger()

# Funções de conveniência
def log_user_action(action: str, **kwargs):
    """Log de ação do usuário"""
    app_logger.log_user_action(action, **kwargs)

def log_agent_interaction(model: str, query: str, success: bool,
                         response_time: float, **kwargs):
    """Log de interação com agente"""
    app_logger.log_agent_interaction(model, query, success, response_time, **kwargs)

def log_data_operation(operation: str, file_name: str, rows: int, columns: int, **kwargs):
    """Log de operação com dados"""
    app_logger.log_data_operation(operation, file_name, rows, columns, **kwargs)

def log_error(error: Exception, context: Dict[str, Any] = None):
    """Log de erro"""
    app_logger.log_error(error, context)

def log_performance(operation: str, duration: float, **kwargs):
    """Log de performance"""
    app_logger.log_performance(operation, duration, **kwargs)

# Logger direto para uso avançado
def get_logger():
    """Retorna instância do logger para uso direto"""
    return logger