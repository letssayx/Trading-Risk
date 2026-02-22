import os
import pkgutil
import importlib
import inspect
from typing import Dict, List, Any

# OOTB Strategies Package
import backend.strategies as ootb_strategies

class StrategyRegistry:
    """
    Discovers and registers trading strategies.
    Distinguishes between "Out of the Box" (OOTB) and "User Developed" (Plugin) strategies.
    """

    PLUGIN_DIR = "backend/plugins/strategies"
    PLUGIN_PACKAGE = "backend.plugins.strategies"

    @classmethod
    def get_strategies(cls) -> Dict[str, List[Dict[str, Any]]]:
        """
        Returns a dictionary with 'ootb' and 'user' strategy lists.
        Each item contains: name, type, description (docstring).
        """
        return {
            "ootb": cls._discover_ootb(),
            "user": cls._discover_user_plugins()
        }

    @classmethod
    def _discover_ootb(cls) -> List[Dict[str, Any]]:
        strategies = []
        # Inspect the backend.strategies package
        for name, obj in inspect.getmembers(ootb_strategies):
            if inspect.isclass(obj) and (name.endswith("Strategy") or name.endswith("Engine")):
                # Filter out base classes if any, or verify module
                if obj.__module__.startswith("backend.strategies"):
                    strategies.append({
                        "name": name,
                        "type": "OOTB",
                        "description": (obj.__doc__ or "No description available.").strip().split('\n')[0]
                    })

        # Manual additions for Analysis Tools (treated as OOTB strategies)
        try:
            from backend.analysis.toolbox.price_oi import PriceOiAnalyzer
            strategies.append({
                "name": "PriceOiAnalyzer",
                "type": "OOTB",
                "description": (PriceOiAnalyzer.__doc__ or "Price vs OI Analysis").strip().split('\n')[0]
            })
        except ImportError:
            pass

        try:
            from backend.plugins.strategies.rollover import RolloverAnalyzer
            strategies.append({
                "name": "RolloverAnalyzer",
                "type": "OOTB",
                "description": (RolloverAnalyzer.__doc__ or "Rollover Analysis").strip().split('\n')[0]
            })
        except ImportError:
            pass

        return strategies

    @classmethod
    def _discover_user_plugins(cls) -> List[Dict[str, Any]]:
        strategies = []

        # Ensure plugin dir exists
        if not os.path.exists(cls.PLUGIN_DIR):
            try:
                os.makedirs(cls.PLUGIN_DIR)
                # Create __init__.py if missing
                init_path = os.path.join(cls.PLUGIN_DIR, "__init__.py")
                if not os.path.exists(init_path):
                    with open(init_path, 'w') as f:
                        f.write("")
            except Exception as e:
                print(f"Error creating plugin directory: {e}")
                return []

        # Walk through the directory
        for _, name, _ in pkgutil.iter_modules([cls.PLUGIN_DIR]):
            try:
                module_name = f"{cls.PLUGIN_PACKAGE}.{name}"
                module = importlib.import_module(module_name)

                for member_name, obj in inspect.getmembers(module):
                    # Exclude RolloverAnalyzer if we manually added it to OOTB
                    if member_name == "RolloverAnalyzer":
                        continue

                    if inspect.isclass(obj) and (member_name.endswith("Strategy") or member_name.endswith("Analyzer")):
                        # Ensure it's defined in this module (not imported)
                        if obj.__module__ == module_name:
                            strategies.append({
                                "name": member_name,
                                "type": "User",
                                "description": (obj.__doc__ or "No description available.").strip().split('\n')[0]
                            })
            except Exception as e:
                print(f"Error loading plugin {name}: {e}")
                continue

        return strategies
