from typing import Any, Dict

class ComponentRegistry:
    """
    Singleton Registry for all Universal Framework Objects.
    Allows dynamic lookup of Indicators, Stats, and Strategies.
    """
    _instance = None
    _registry = {
        "indicators": {},
        "strategies": {},
        "risk": {},
        "stats": {}
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ComponentRegistry, cls).__new__(cls)
        return cls._instance

    def register(self, category: str, name: str, cls_obj: Any):
        if category in self._registry:
            self._registry[category][name] = cls_obj

    def get(self, category: str, name: str) -> Any:
        return self._registry.get(category, {}).get(name)

    def list_components(self, category: str) -> list:
        return list(self._registry.get(category, {}).keys())

# Global Instance
registry = ComponentRegistry()
