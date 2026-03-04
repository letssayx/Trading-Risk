import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
import logging
from typing import Dict, List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Module-level cache for available models to avoid redundant API calls
# Keyed by API key to handle key changes correctly
_MODELS_CACHE: Dict[str, List[str]] = {}

class JulesAssistant:
    def __init__(self):
        self.client = None
        self.model_name = 'gemini-1.5-flash'
        self._load_key()

    def _load_key(self):
        # Reload key from file/env
        load_dotenv(override=True)
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
            self._select_best_model()
        else:
            self.client = None
            logger.warning("Jules: No Google API Key found.")

    def _select_best_model(self):
        """
        Dynamically selects the best available model for generateContent.
        """
        try:
            # Check cache first
            if self.api_key in _MODELS_CACHE:
                available_models = _MODELS_CACHE[self.api_key]
                logger.info(f"Jules: Using cached models for key: {self.api_key[:8]}...")
            else:
                available_models = []
                # Use the new SDK's list models method
                models = self.client.models.list()
                for m in models:
                    if 'generateContent' in m.supported_generation_methods:
                        available_models.append(m.name)

                # Cache the results
                if available_models:
                    _MODELS_CACHE[self.api_key] = available_models

            logger.info(f"Jules: Available Models: {available_models}")

            # Preference list
            preferences = [
                'gemini-2.0-flash',
                'gemini-1.5-flash',
                'gemini-1.5-pro',
                'gemini-pro'
            ]

            selected = None

            # 1. Try preferences first
            for pref in preferences:
                for am in available_models:
                    # Check for exact match or suffix match (to handle 'models/' prefix)
                    if am == pref or am.endswith('/' + pref):
                        selected = am
                        break
                if selected:
                    break

            # 2. If no preference found, pick the first available 'gemini' model
            if not selected:
                for m in available_models:
                    if 'gemini' in m.lower():
                        selected = m
                        break

            # 3. Fallback to anything
            if not selected and available_models:
                selected = available_models[0]

            if selected:
                logger.info(f"Jules: Selected Model -> {selected}")
                self.model_name = selected
            else:
                logger.error("Jules: No suitable model found in list.")
                # Fallback to hardcoded if list fails (e.g. permission issue on list)
                self.model_name = 'gemini-1.5-flash'

        except Exception as e:
            logger.error(f"Jules: Error selecting model: {e}")
            self.model_name = 'gemini-1.5-flash'

    def _scan_directory(self, root_path: str, max_depth: int = 2) -> dict:
        """
        Recursively scans directory for .py files and their content summary.
        Returns a dict of {filepath: content}.
        Limits content size to avoid context overflow.
        """
        file_map = {}
        for root, dirs, files in os.walk(root_path):
            # Calculate depth
            depth = root[len(root_path):].count(os.sep)
            if depth > max_depth:
                continue

            # Skip common junk
            if '__pycache__' in root or 'tests' in root:
                continue

            for file in files:
                if file.endswith('.py') or file.endswith('.md'):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                            # If file is too large, just take header/imports/class defs (simplistic)
                            if len(content) > 3000:
                                # Truncate but keep head
                                file_map[filepath] = content[:1500] + "\n... [Content Truncated] ...\n" + content[-500:]
                            else:
                                file_map[filepath] = content
                    except Exception:
                        pass
        return file_map

    def _get_context(self) -> str:
        """
        Reads key codebase files to provide context to the AI.
        Uses a recursive scan of critical directories.
        """
        context = "\n\n--- PROJECT CONTEXT ---\n"

        # Directories to include in scan
        scan_dirs = [
            "backend/domain",
            "backend/analysis",
            "backend/risk",
            "backend/backtest",
            "backend/strategies"
        ]

        # Core Index (Structure)
        context += "Directory Structure Summary:\n"
        for d in scan_dirs:
            if os.path.exists(d):
                context += f"- {d}/\n"
                for f in os.listdir(d):
                    if not f.startswith("__"):
                        context += f"  - {f}\n"

        context += "\n--- CORE MODULES ---\n"

        # 1. Map File if exists
        if os.path.exists("backend/MAP.md"):
            with open("backend/MAP.md", 'r') as f:
                context += f"System Map:\n{f.read()}\n"

        # 2. Critical Files (Full Read)
        critical_files = [
            "backend/strategies/turtle.py",
            "backend/strategies/adapters/turtle_adapter.py",
            "backend/domain/portfolio/models.py",
            "backend/risk/greeks.py"
        ]

        for filepath in critical_files:
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    context += f"\nFile: {filepath}\n```python\n{f.read()}\n```\n"

        # 3. Dynamic Scan (Truncated/Selective)
        # Only scan 'domain' and 'strategies' deeply for now to save tokens
        scanned_files = {}
        for d in ["backend/domain", "backend/strategies"]:
            if os.path.exists(d):
                scanned_files.update(self._scan_directory(d))

        for fp, content in scanned_files.items():
            if fp not in critical_files: # Avoid dupes
                context += f"\nFile (Ref): {fp}\n```python\n{content}\n```\n"

        context += "\n--- INSTRUCTIONS ---\n"
        context += "1. When asked to generate a Strategy, create a class inheriting from `BaseStrategy` or following the `TurtleLegacyStrategy` pattern.\n"
        context += "2. Implement the `Adapter` pattern (like `TurtleAdapter`) to expose the strategy to the UI.\n"
        context += "3. Use `PortfolioManager` for position sizing and capital tracking.\n"
        context += "4. Check existing `backend/domain` models before creating new ones.\n"

        return context

    async def get_response(self, message: str) -> str:
        # Always reload key before request to catch config changes
        if not self.client:
             self._load_key()

        if not self.client:
            return "Please configure your Google API Key in Settings to use Jules."

        try:
            # Load dynamic context
            code_context = self._get_context()

            # System Prompt to enforce context and format
            system_instruction = (
                "You are Jules, an AI Assistant for the Turtle Terminal trading platform. "
                "Your role is to assist with quantitative finance, python coding for strategies, and market analysis. "
                "You have FULL visibility into the system's architecture via the Context provided below. "
                "Use the existing modules (Risk, Domain, Analysis) whenever possible. "
                "If you write Python code, enclose it strictly within ```python ... ``` blocks. "
                "Format output clearly. If a requested feature doesn't exist, propose a new Plugin class for it.\n"
                f"{code_context}"
            )

            # Using the new genai client format
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=[
                    types.Content(role="user", parts=[types.Part.from_text(system_instruction)]),
                    types.Content(role="model", parts=[types.Part.from_text("Understood. I am Jules, system-aware architect for Turtle Terminal. I see the modules and strategies.")]),
                    types.Content(role="user", parts=[types.Part.from_text(message)])
                ]
            )
            return response.text
        except Exception as e:
            logger.error(f"Jules: Generation Error: {e}")
            return f"I encountered an error: {str(e)}"

# Singleton instance
jules = JulesAssistant()
