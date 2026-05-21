"""Environment registry for AgenticRL.

Provides a central registry to register and look up environments by name.
"""

from typing import Callable, Type

from agenticrl.environment.base import Env

# Global registry: name → Env class or factory function
_ENV_REGISTRY: dict[str, type[Env] | Callable[..., Env]] = {}


def register(name: str, env_cls: type[Env] | Callable[..., Env]) -> None:
    """Register an environment.

    Args:
        name: Unique name for the environment.
        env_cls: Environment class or factory function.

    Raises:
        ValueError: If the name is already registered.

    Example:
        >>> from agenticrl.environment import register
        >>> register("my_env", MyEnv)
    """
    if name in _ENV_REGISTRY:
        raise ValueError(f"Environment '{name}' is already registered.")
    _ENV_REGISTRY[name] = env_cls


def get(name: str) -> type[Env] | Callable[..., Env]:
    """Retrieve a registered environment by name.

    Args:
        name: Environment name.

    Returns:
        The registered class or factory.

    Raises:
        KeyError: If the name is not found.

    Example:
        >>> from agenticrl.environment import get
        >>> env_cls = get("my_env")
    """
    if name not in _ENV_REGISTRY:
        available = ", ".join(sorted(_ENV_REGISTRY.keys()))
        raise KeyError(
            f"Environment '{name}' not found. Available: {available or '(none)'}"
        )
    return _ENV_REGISTRY[name]


def list_all() -> list[str]:
    """List all registered environment names.

    Returns:
        Sorted list of registered environment names.
    """
    return sorted(_ENV_REGISTRY.keys())


def unregister(name: str) -> None:
    """Remove an environment from the registry.

    Args:
        name: Environment name to remove.

    Raises:
        KeyError: If not found.
    """
    if name not in _ENV_REGISTRY:
        raise KeyError(f"Environment '{name}' not found.")
    del _ENV_REGISTRY[name]
