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
            from backend.models.stats import StatArbAlphaEngine, ZScoreFilter, CointegrationAuditor
            cls.register(StatArbAlphaEngine)
            cls.register(ZScoreFilter)
            cls.register(CointegrationAuditor)
        except Exception as e: print(f"[REGISTRY] Error loading Stats Models: {e}")

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

        try:
            from backend.risk.models.factor import FactorExposureModel
            cls.register(FactorExposureModel)
        except Exception as e: print(f"[REGISTRY] Error loading Factor Models: {e}")

        # 5. Ingest
        try:
            from backend.ingest.toolbox.data_gateway import DataGateway
            cls.register(DataGateway)
        except Exception as e: print(f"[REGISTRY] Error loading Data Gateway: {e}")

        print(f"[REGISTRY] Discovery Complete. Total Tools: {len(cls._registry)}")
