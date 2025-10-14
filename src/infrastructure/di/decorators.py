# -*- coding: utf-8 -*-
"""
DI Decorators - Decoradores para injeção de dependências

Fornece decoradores convenientes para automatizar a injeção
de dependências em métodos e classes.
"""

from typing import TypeVar, Type, Callable, Any
from functools import wraps
import inspect

from .container import get_container

T = TypeVar('T')


def inject(container=None):
    """
    Decorator para injeção automática de dependências

    Args:
        container: Container específico (usa o padrão se None)

    Usage:
        @inject()
        def some_function(service: IService):
            pass

        @inject()
        class SomeClass:
            def __init__(self, service: IService):
                pass
    """

    def decorator(target):
        if inspect.isclass(target):
            return _inject_class(target, container)
        elif inspect.isfunction(target) or inspect.ismethod(target):
            return _inject_function(target, container)
        else:
            raise ValueError("@inject só pode ser usado em classes ou funções")

    return decorator


def _inject_class(cls: Type[T], container=None) -> Type[T]:
    """Injeta dependências no construtor de uma classe"""
    original_init = cls.__init__
    di_container = container or get_container()

    @wraps(original_init)
    def new_init(self, *args, **kwargs):
        # Analisar signature do construtor original
        signature = inspect.signature(original_init)
        bound_args = signature.bind_partial(self, *args, **kwargs)

        # Resolver dependências não fornecidas
        for param_name, param in signature.parameters.items():
            if param_name == 'self':
                continue

            # Se parâmetro não foi fornecido e tem type annotation
            if (param_name not in bound_args.arguments and
                param.annotation != inspect.Parameter.empty):
                try:
                    dependency = di_container.resolve(param.annotation)
                    bound_args.arguments[param_name] = dependency
                except ValueError:
                    # Se não conseguir resolver e não tem default, deixa para falhar naturalmente
                    if param.default == inspect.Parameter.empty:
                        pass

        # Chamar construtor original com dependências resolvidas
        original_init(**bound_args.arguments)

    cls.__init__ = new_init
    return cls


def _inject_function(func: Callable, container=None) -> Callable:
    """Injeta dependências em uma função"""
    di_container = container or get_container()

    @wraps(func)
    def wrapper(*args, **kwargs):
        # Analisar signature da função
        signature = inspect.signature(func)
        bound_args = signature.bind_partial(*args, **kwargs)

        # Resolver dependências não fornecidas
        for param_name, param in signature.parameters.items():
            # Se parâmetro não foi fornecido e tem type annotation
            if (param_name not in bound_args.arguments and
                param.annotation != inspect.Parameter.empty):
                try:
                    dependency = di_container.resolve(param.annotation)
                    bound_args.arguments[param_name] = dependency
                except ValueError:
                    # Se não conseguir resolver e não tem default, deixa para falhar naturalmente
                    if param.default == inspect.Parameter.empty:
                        pass

        # Chamar função original com dependências resolvidas
        return func(**bound_args.arguments)

    return wrapper


def singleton(cls: Type[T]) -> Type[T]:
    """
    Decorator para marcar uma classe como singleton

    A classe será automaticamente registrada como singleton
    no container padrão quando for importada.

    Usage:
        @singleton
        class MyService:
            pass
    """
    container = get_container()

    # Registrar como singleton no container
    if not container.is_registered(cls):
        container.register_singleton(cls, cls)

    return cls


def autowire(container=None):
    """
    Decorator para auto-wire completo de uma classe

    Automaticamente resolve todas as dependências do construtor
    e registra a classe no container.

    Usage:
        @autowire()
        class MyService:
            def __init__(self, repo: IRepository):
                self.repo = repo
    """
    di_container = container or get_container()

    def decorator(cls: Type[T]) -> Type[T]:
        # Aplicar injeção de dependências
        injected_cls = _inject_class(cls, di_container)

        # Registrar no container se ainda não estiver
        if not di_container.is_registered(cls):
            di_container.register_factory(cls, injected_cls)

        return injected_cls

    return decorator


def provided_by(provider_func: Callable[[], Any], container=None):
    """
    Decorator para registrar uma classe com função de provider customizada

    Usage:
        def create_special_service():
            return SpecialService(custom_config=True)

        @provided_by(create_special_service)
        class SpecialService:
            pass
    """
    di_container = container or get_container()

    def decorator(cls: Type[T]) -> Type[T]:
        di_container.register_factory_func(cls, provider_func)
        return cls

    return decorator