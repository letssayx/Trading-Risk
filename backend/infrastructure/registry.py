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
        except Exception as e:
            print(f"Failed to register {tool_cls}: {e}")

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
        """
        # Manual registration for now to ensure order and stability
        # In a real dynamic system, we'd walk packages.

        # Core
        from backend.core.toolbox.math_tools import CompoundingAuditor
        from backend.core.toolbox.stats_tools import StatArbAlphaEngine
        cls.register(CompoundingAuditor)
        cls.register(StatArbAlphaEngine)

        # Analysis
        from backend.analysis.toolbox.volatility_tools import VolatilitySurfaceTool
        from backend.analysis.toolbox.flow_tools import InstitutionalPulse
        cls.register(VolatilitySurfaceTool)
        cls.register(InstitutionalPulse)

        # Risk
        from backend.risk.toolbox.governance_tools import GovernanceAuditor
        cls.register(GovernanceAuditor)

        # Strategies (Turtle Suite)
        from backend.strategies.toolbox.turtle_suite import TurtleNCalculator, TurtlePyramiding, TurtleStopLoss
        cls.register(TurtleNCalculator)
        cls.register(TurtlePyramiding)
        cls.register(TurtleStopLoss)

        # Factor Models
        from backend.strategies.toolbox.factor_model import FactorExposureModel
        cls.register(FactorExposureModel)

        # Ingest
        from backend.ingest.toolbox.data_gateway import DataGateway
        cls.register(DataGateway)
