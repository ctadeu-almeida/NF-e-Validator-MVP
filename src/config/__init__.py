# -*- coding: utf-8 -*-
"""
Módulo de Configuração

Este módulo contém as configurações do sistema.
"""

from .settings import (
    Settings,
    get_settings,
    configure_api_key,
    setup_directories,
    get_chart_path,
    get_report_path,
    get_data_path
)

__all__ = [
    'Settings',
    'get_settings',
    'configure_api_key',
    'setup_directories',
    'get_chart_path',
    'get_report_path',
    'get_data_path'
]