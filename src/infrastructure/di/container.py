# -*- coding: utf-8 -*-
"""
DI Container - Container de injeção de dependências

Implementa um container simples mas robusto para gerenciar
dependências e promover inversão de controle.
"""

from typing import Dict, Any, TypeVar, Type, Callable, Optional, Union
import inspect
from functools import wraps

T = TypeVar('T')


class Provider:
    """Provedor base para instâncias"""

    def provide(self) -> Any:
        """Fornece uma instância"""
        raise NotImplementedError


class SingletonProvider(Provider):
    """Provedor singleton - uma única instância"""

    def __init__(self, factory: Callable, *args, **kwargs):
        self.factory = factory
        self.args = args
        self.kwargs = kwargs
        self._instance = None

    def provide(self) -> Any:
        if self._instance is None:
            self._instance = self.factory(*self.args, **self.kwargs)
        return self._instance


class FactoryProvider(Provider):
    """Provedor factory - nova instância a cada chamada"""

    def __init__(self, factory: Callable, *args, **kwargs):
        self.factory = factory
        self.args = args
        self.kwargs = kwargs

    def provide(self) -> Any:
        return self.factory(*self.args, **self.kwargs)


class InstanceProvider(Provider):
    """Provedor de instância - retorna instância já criada"""

    def __init__(self, instance: Any):
        self.instance = instance

    def provide(self) -> Any:
        return self.instance


class DIContainer:
    """Container de injeção de dependências"""

    def __init__(self):
        self._providers: Dict[str, Provider] = {}
        self._singletons: Dict[str, Any] = {}

    def register_singleton(
        self,
        interface: Type[T],
        implementation: Type[T],
        *args,
        **kwargs
    ) -> 'DIContainer':
        """
        Registra um singleton

        Args:
            interface: Interface ou tipo abstrato
            implementation: Implementação concreta
            *args: Argumentos para o construtor
            **kwargs: Argumentos nomeados para o construtor

        Returns:
            Self para chaining
        """
        key = self._get_key(interface)
        self._providers[key] = SingletonProvider(implementation, *args, **kwargs)
        return self

    def register_factory(
        self,
        interface: Type[T],
        implementation: Type[T],
        *args,
        **kwargs
    ) -> 'DIContainer':
        """
        Registra uma factory

        Args:
            interface: Interface ou tipo abstrato
            implementation: Implementação concreta
            *args: Argumentos para o construtor
            **kwargs: Argumentos nomeados para o construtor

        Returns:
            Self para chaining
        """
        key = self._get_key(interface)
        self._providers[key] = FactoryProvider(implementation, *args, **kwargs)
        return self

    def register_instance(
        self,
        interface: Type[T],
        instance: T
    ) -> 'DIContainer':
        """
        Registra uma instância específica

        Args:
            interface: Interface ou tipo
            instance: Instância já criada

        Returns:
            Self para chaining
        """
        key = self._get_key(interface)
        self._providers[key] = InstanceProvider(instance)
        return self

    def register_factory_func(
        self,
        interface: Type[T],
        factory_func: Callable[[], T]
    ) -> 'DIContainer':
        """
        Registra uma função factory

        Args:
            interface: Interface ou tipo
            factory_func: Função que retorna instância

        Returns:
            Self para chaining
        """
        key = self._get_key(interface)
        self._providers[key] = FactoryProvider(factory_func)
        return self

    def resolve(self, interface: Type[T]) -> T:
        """
        Resolve uma dependência

        Args:
            interface: Interface ou tipo a ser resolvido

        Returns:
            Instância da implementação

        Raises:
            ValueError: Se dependência não estiver registrada
        """
        key = self._get_key(interface)

        if key not in self._providers:
            # Tentar auto-wire se for uma classe concreta
            if inspect.isclass(interface) and not inspect.isabstract(interface):
                return self._auto_wire(interface)
            else:
                raise ValueError(f"Dependência não registrada: {interface}")

        return self._providers[key].provide()

    def _auto_wire(self, cls: Type[T]) -> T:
        """
        Tenta fazer auto-wire de uma classe analisando seu construtor

        Args:
            cls: Classe para auto-wire

        Returns:
            Instância criada com dependências injetadas
        """
        try:
            # Analisar construtor
            signature = inspect.signature(cls.__init__)
            args = {}

            for param_name, param in signature.parameters.items():
                if param_name == 'self':
                    continue

                # Se tem type annotation, tentar resolver
                if param.annotation != inspect.Parameter.empty:
                    try:
                        args[param_name] = self.resolve(param.annotation)
                    except ValueError:
                        # Se não conseguir resolver e não tem default, falha
                        if param.default == inspect.Parameter.empty:
                            raise ValueError(
                                f"Não foi possível resolver parâmetro '{param_name}' "
                                f"do tipo '{param.annotation}' para classe '{cls}'"
                            )

            return cls(**args)

        except Exception as e:
            raise ValueError(f"Erro no auto-wire da classe {cls}: {str(e)}")

    def _get_key(self, interface: Type) -> str:
        """Gera chave única para um tipo"""
        if hasattr(interface, '__module__') and hasattr(interface, '__name__'):
            return f"{interface.__module__}.{interface.__name__}"
        else:
            return str(interface)

    def is_registered(self, interface: Type) -> bool:
        """Verifica se uma interface está registrada"""
        key = self._get_key(interface)
        return key in self._providers

    def unregister(self, interface: Type) -> bool:
        """
        Remove registro de uma interface

        Args:
            interface: Interface a ser removida

        Returns:
            True se foi removida, False se não existia
        """
        key = self._get_key(interface)
        if key in self._providers:
            del self._providers[key]
            return True
        return False

    def clear(self):
        """Remove todos os registros"""
        self._providers.clear()
        self._singletons.clear()

    def get_registered_types(self) -> list:
        """Retorna lista dos tipos registrados"""
        return list(self._providers.keys())


# Container global padrão
_default_container = DIContainer()


def get_container() -> DIContainer:
    """Obtém o container padrão"""
    return _default_container


def configure_container() -> DIContainer:
    """Configura e retorna um novo container"""
    return DIContainer()