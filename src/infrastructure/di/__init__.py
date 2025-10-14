# -*- coding: utf-8 -*-
"""
Dependency Injection - Sistema de injeção de dependências

Este pacote implementa um container de injeção de dependências
simples mas poderoso para gerenciar as dependências da aplicação.
"""

from .container import DIContainer
from .decorators import inject, singleton
from .providers import Provider, SingletonProvider, FactoryProvider

__all__ = [
    'DIContainer',
    'inject',
    'singleton',
    'Provider',
    'SingletonProvider',
    'FactoryProvider'
]