import importlib.util
import os
import sys
from typing import Dict, Any, Type
from backend.strategies.base_strategy import BaseStrategy

class PluginManager:
    """
    Dynamically loads and manages Strategy and Risk Model plugins.
    Supports Hot-Reloading by clearing module cache.
    """
    def __init__(self, plugin_dir: str = "backend/plugins"):
        self.plugin_dir = plugin_dir
        self.active_plugins: Dict[str, Any] = {} # instance_id -> instance
        self.class_registry: Dict[str, Type] = {} # name -> class

    def load_plugin_class(self, file_path: str, class_name: str) -> Type:
        """
        Loads a python file and extracts the class.
        """
        module_name = os.path.splitext(os.path.basename(file_path))[0]
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if not spec or not spec.loader:
            raise ImportError(f"Could not load spec for {file_path}")

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        if not hasattr(module, class_name):
            raise AttributeError(f"Class {class_name} not found in {file_path}")

        return getattr(module, class_name)

    def register_from_db(self, strategy_record: Any) -> Any:
        """
        Instantiates a plugin based on a DB record (Strategy model).
        """
        # 1. Determine File Path (Mocking: In real world, we might write source_code to a temp file or import)
        # For this MVP, we assume the plugins exist in the fs or we write them.
        # If source_code is provided, we should ideally write it to backend/plugins/dynamic/

        # Simplification: specific logic mapping name to existing files for the "Institutional Library" task
        # "VolatilityArbitrage" -> backend/plugins/strategies/volatility_arbitrage.py

        type_dir = "strategies" if strategy_record.type == "STRATEGY" else "risk"
        filename = strategy_record.name.lower().replace(" ", "_") + ".py" # e.g. "Volatility Arbitrage" -> "volatility_arbitrage.py"
        file_path = os.path.join(self.plugin_dir, type_dir, filename)

        # If file doesn't exist but we have source_code, write it (Hot Reload Scenario)
        if not os.path.exists(file_path) and strategy_record.source_code:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w") as f:
                f.write(strategy_record.source_code)

        # Load Class
        # Assumption: Class Name matches Strategy Name (PascalCase) usually, but let's assume standard normalization
        class_name = strategy_record.name.replace(" ", "")

        cls = self.load_plugin_class(file_path, class_name)
        self.class_registry[strategy_record.name] = cls

        # Instantiate
        instance = cls(name=strategy_record.name, config=strategy_record.config_json)
        self.active_plugins[str(strategy_record.id)] = instance
        return instance

    def reload_plugin(self, strategy_record: Any) -> Any:
        """
        Hot-Reloads a plugin.
        """
        if str(strategy_record.id) in self.active_plugins:
            del self.active_plugins[str(strategy_record.id)]

        return self.register_from_db(strategy_record)

    def get_active_instance(self, strategy_id: str) -> Any:
        return self.active_plugins.get(strategy_id)
