from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseSovereignTool(ABC):
    """
    Abstract Base Class for all Sovereign Toolbox Objects.
    Ensures every tool is identifiable, discoverable, and executable.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique Name of the Tool"""
        pass

    @property
    @abstractmethod
    def category(self) -> str:
        """Category: Indicator, Strategy, Risk, Math, Governance"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Financial Intuition / Description"""
        pass

    @abstractmethod
    def calculate(self, data: Any) -> Dict[str, Any]:
        """The Math Engine: Inputs Data -> Outputs Metrics"""
        pass

    def get_metadata(self) -> Dict[str, Any]:
        """Returns standard metadata for the Registry"""
        return {
            "name": self.name,
            "category": self.category,
            "description": self.description
        }

    def to_widget(self) -> Dict[str, Any]:
        """Returns UI configuration for the Drag-and-Drop Canvas"""
        return {
            "type": "tool-widget",
            "title": self.name,
            "icon": self._get_icon(),
            "draggable": True
        }

    def _get_icon(self) -> str:
        icons = {
            "Strategy": "♟️",
            "Risk": "🛡️",
            "Indicator": "📊",
            "Governance": "⚖️",
            "Math": "🧮"
        }
        return icons.get(self.category, "📦")
