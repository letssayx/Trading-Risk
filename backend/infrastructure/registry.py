import inspect
import importlib
import pkgutil
from typing import List, Dict, Any, Type
from backend.domain.toolbox.base import BaseSovereignTool

class ToolboxRegistry:
    """
    Master Registry for all Sovereign Tools.
    Auto-discovers and indexes tools for the "Photoshop" Sidebar.
    """

    _registry: Dict[str, BaseSovereignTool] = {}

    @classmethod
    def register(cls, tool_cls: Type[BaseSovereignTool]):
        """Registers a tool class (instantiates it)."""
        try:
            tool = tool_cls()
            cls._registry[tool.name] = tool
            print(f"[REGISTRY] Registered: {tool.name}")
        except Exception as e:
            print(f"[REGISTRY] Failed to register {tool_cls}: {e}")

    @classmethod
    def get_all_tools(cls) -> List[Dict[str, Any]]:
        """Returns metadata for all registered tools."""
        return [tool.get_metadata() for tool in cls._registry.values()]

    @classmethod
    def get_tool(cls, name: str) -> BaseSovereignTool:
        return cls._registry.get(name)

    @classmethod
    def get_widgets(cls) -> List[Dict[str, Any]]:
        return [tool.to_widget() for tool in cls._registry.values()]

    @classmethod
    def auto_discover(cls):
        """
        Recursively finds BaseSovereignTool implementations in backend modules.
        Wrapped in try/except blocks to prevent partial failures from crashing the UI.
        """
        print("[REGISTRY] Starting Auto-Discovery...")

        # 1. Core & Math
        try:
            from backend.models.math import CompoundingAuditor
            cls.register(CompoundingAuditor)
        except Exception as e: print(f"[REGISTRY] Error loading Math Models: {e}")

        try:
            from backend.models.stats import CointegrationAuditor
            cls.register(CointegrationAuditor)
        except Exception as e: print(f"[REGISTRY] Error loading Stats Models: {e}")

        # 1.1 Strategy Components (Refactored)
        try:
            from backend.strategies.stat_arb.alpha_engine import StatArbAlphaEngine
            cls.register(StatArbAlphaEngine)
        except Exception as e: print(f"[REGISTRY] Error loading Strategy Components: {e}")

        try:
            from backend.strategies.toolbox.filters import ZScoreFilter
            cls.register(ZScoreFilter)
        except Exception as e: print(f"[REGISTRY] Error loading Filters: {e}")

        # 2. Analysis & Intelligence
        try:
            from backend.analysis.toolbox.volatility_tools import VolatilitySurfaceTool
            cls.register(VolatilitySurfaceTool)
        except Exception as e: print(f"[REGISTRY] Error loading Vol Tools: {e}")

        try:
            from backend.analysis.toolbox.flow_tools import InstitutionalPulse
            cls.register(InstitutionalPulse)
        except Exception as e: print(f"[REGISTRY] Error loading Flow Tools: {e}")

        try:
            from backend.analysis.toolbox.spread_tools import SpreadSynthesizer, FICOTool
            cls.register(SpreadSynthesizer)
            cls.register(FICOTool)
        except Exception as e: print(f"[REGISTRY] Error loading Spread Tools: {e}")

        # 3. Risk & Governance
        try:
            from backend.risk.governance import GovernanceAuditor
            cls.register(GovernanceAuditor)
        except Exception as e: print(f"[REGISTRY] Error loading Governance Tools: {e}")

        # 4. Strategies (Layers)
        try:
            from backend.strategies.toolbox.turtle_suite import TurtleNCalculator, TurtlePyramiding, TurtleStopLoss
            cls.register(TurtleNCalculator)
            cls.register(TurtlePyramiding)
            cls.register(TurtleStopLoss)
        except Exception as e: print(f"[REGISTRY] Error loading Turtle Suite: {e}")

        # 4.1 Risk Models (Refactored)
        try:
            from backend.models.factor import FactorExposureModel
            cls.register(FactorExposureModel)
        except Exception as e: print(f"[REGISTRY] Error loading Factor Models: {e}")

        # 5. Ingest
        try:
            from backend.ingest.toolbox.data_gateway import DataGateway
            cls.register(DataGateway)
        except Exception as e: print(f"[REGISTRY] Error loading Data Gateway: {e}")

        # 6. Standard Tools (New Batch - Missing 20+)
        try:
            import backend.analysis.toolbox.std_tools as std
            for name, obj in inspect.getmembers(std):
                if inspect.isclass(obj) and issubclass(obj, BaseSovereignTool) and obj is not BaseSovereignTool:
                    cls.register(obj)
        except Exception as e: print(f"[REGISTRY] Error loading Std Tools: {e}")

        print(f"[REGISTRY] Discovery Complete. Total Tools: {len(cls._registry)}")
