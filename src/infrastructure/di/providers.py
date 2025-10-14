# -*- coding: utf-8 -*-
"""
DI Providers - Provedores de dependências

Define diferentes estratégias para criação e fornecimento
de instâncias no sistema de injeção de dependências.
"""

from typing import Callable, Any, TypeVar, Type, Dict, Optional
import threading
from abc import ABC, abstractmethod

T = TypeVar('T')


class Provider(ABC):
    """Provedor base para instâncias"""

    @abstractmethod
    def provide(self) -> Any:
        """Fornece uma instância"""
        pass

    @abstractmethod
    def reset(self):
        """Reseta o estado do provider"""
        pass


class SingletonProvider(Provider):
    """
    Provedor singleton - uma única instância (thread-safe)

    Garante que apenas uma instância seja criada, mesmo em
    ambiente multi-thread.
    """

    def __init__(self, factory: Callable, *args, **kwargs):
        self.factory = factory
        self.args = args
        self.kwargs = kwargs
        self._instance = None
        self._lock = threading.Lock()

    def provide(self) -> Any:
        if self._instance is None:
            with self._lock:
                # Double-check locking pattern
                if self._instance is None:
                    self._instance = self.factory(*self.args, **self.kwargs)
        return self._instance

    def reset(self):
        """Reseta o singleton (força recriação na próxima chamada)"""
        with self._lock:
            self._instance = None


class FactoryProvider(Provider):
    """
    Provedor factory - nova instância a cada chamada

    Sempre cria uma nova instância quando solicitada.
    """

    def __init__(self, factory: Callable, *args, **kwargs):
        self.factory = factory
        self.args = args
        self.kwargs = kwargs

    def provide(self) -> Any:
        return self.factory(*self.args, **self.kwargs)

    def reset(self):
        """Factory não mantém estado"""
        pass


class InstanceProvider(Provider):
    """
    Provedor de instância - retorna instância já criada

    Armazena e retorna sempre a mesma instância pré-criada.
    """

    def __init__(self, instance: Any):
        self.instance = instance

    def provide(self) -> Any:
        return self.instance

    def reset(self):
        """Instance provider não pode ser resetado"""
        pass


class LazyProvider(Provider):
    """
    Provedor lazy - cria instância apenas quando solicitada

    Combina características de singleton e factory - cria apenas
    uma vez, mas só quando necessário.
    """

    def __init__(self, factory: Callable, *args, **kwargs):
        self.factory = factory
        self.args = args
        self.kwargs = kwargs
        self._instance = None
        self._created = False
        self._lock = threading.Lock()

    def provide(self) -> Any:
        if not self._created:
            with self._lock:
                if not self._created:
                    self._instance = self.factory(*self.args, **self.kwargs)
                    self._created = True
        return self._instance

    def reset(self):
        """Reseta o estado lazy"""
        with self._lock:
            self._instance = None
            self._created = False


class ScopedProvider(Provider):
    """
    Provedor com escopo - uma instância por escopo/contexto

    Mantém instâncias separadas por contexto/thread.
    """

    def __init__(self, factory: Callable, *args, **kwargs):
        self.factory = factory
        self.args = args
        self.kwargs = kwargs
        self._instances: Dict[int, Any] = {}
        self._lock = threading.Lock()

    def provide(self) -> Any:
        thread_id = threading.get_ident()

        if thread_id not in self._instances:
            with self._lock:
                if thread_id not in self._instances:
                    self._instances[thread_id] = self.factory(*self.args, **self.kwargs)

        return self._instances[thread_id]

    def reset(self):
        """Reseta todas as instâncias do escopo"""
        with self._lock:
            self._instances.clear()

    def reset_scope(self, thread_id: Optional[int] = None):
        """Reseta instância de um escopo específico"""
        if thread_id is None:
            thread_id = threading.get_ident()

        with self._lock:
            if thread_id in self._instances:
                del self._instances[thread_id]


class ConditionalProvider(Provider):
    """
    Provedor condicional - escolhe provider baseado em condição

    Permite diferentes estratégias de criação baseadas em condições runtime.
    """

    def __init__(
        self,
        condition: Callable[[], bool],
        true_provider: Provider,
        false_provider: Provider
    ):
        self.condition = condition
        self.true_provider = true_provider
        self.false_provider = false_provider

    def provide(self) -> Any:
        if self.condition():
            return self.true_provider.provide()
        else:
            return self.false_provider.provide()

    def reset(self):
        """Reseta ambos os providers"""
        self.true_provider.reset()
        self.false_provider.reset()


class CachedProvider(Provider):
    """
    Provedor com cache - cache inteligente baseado em TTL

    Mantém cache das instâncias com tempo de vida configurável.
    """

    def __init__(
        self,
        factory: Callable,
        cache_ttl_seconds: int = 300,  # 5 minutos
        *args,
        **kwargs
    ):
        self.factory = factory
        self.cache_ttl_seconds = cache_ttl_seconds
        self.args = args
        self.kwargs = kwargs
        self._instance = None
        self._created_at = None
        self._lock = threading.Lock()

    def provide(self) -> Any:
        import time

        current_time = time.time()

        # Verificar se precisa recriar (expirou ou nunca foi criado)
        needs_refresh = (
            self._instance is None or
            self._created_at is None or
            (current_time - self._created_at) > self.cache_ttl_seconds
        )

        if needs_refresh:
            with self._lock:
                # Double-check após lock
                current_time = time.time()
                needs_refresh = (
                    self._instance is None or
                    self._created_at is None or
                    (current_time - self._created_at) > self.cache_ttl_seconds
                )

                if needs_refresh:
                    self._instance = self.factory(*self.args, **self.kwargs)
                    self._created_at = current_time

        return self._instance

    def reset(self):
        """Força recriação do cache"""
        with self._lock:
            self._instance = None
            self._created_at = None


class MultiProvider(Provider):
    """
    Multi-provider - retorna lista de instâncias de múltiplos providers

    Útil para casos onde múltiplas implementações de uma interface
    devem ser fornecidas.
    """

    def __init__(self, providers: list[Provider]):
        self.providers = providers

    def provide(self) -> list:
        return [provider.provide() for provider in self.providers]

    def reset(self):
        """Reseta todos os providers"""
        for provider in self.providers:
            provider.reset()

    def add_provider(self, provider: Provider):
        """Adiciona um provider à lista"""
        self.providers.append(provider)

    def remove_provider(self, provider: Provider):
        """Remove um provider da lista"""
        if provider in self.providers:
            self.providers.remove(provider)