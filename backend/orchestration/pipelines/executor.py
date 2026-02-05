import io
import contextlib
from typing import Dict, Any, List
from backend.orchestration.gemini.interface import GeminiInterface
from backend.orchestration.gemini.sanitizer import validate_imports
from backend.orchestration.policies.audit import log_action

class Executor:
    """
    Orchestrates the interaction between User, Gemini, and Local Engine.
    """

    def __init__(self, context: Dict[str, Any]):
        """
        :param context: The 'Globals' dictionary to be passed to exec().
                        Should contain the MarketSnapshot, MarketState, etc.
        """
        self.context = context
        self.gemini = GeminiInterface()

    def execute_query(self, user_id: str, query: str) -> str:
        # 1. Audit Entry
        log_action(user_id, "QUERY_RECEIVED", {"query": query})

        # 2. Translate Query (Gemini Code Gen)
        generated_code = self.gemini.translate_query(query)

        if generated_code == "OUT_OF_SCOPE":
            msg = "This query falls outside the scope of the Derivatives Analysis & Risk System."
            log_action(user_id, "QUERY_REJECTED", {"reason": "Out of Scope"})
            return msg

        if not generated_code:
            return "I could not generate a valid analysis for that request."

        # 3. Sanitize Code
        if not validate_imports(generated_code):
            log_action(user_id, "CODE_REJECTED", {"code": generated_code, "reason": "Unsafe Imports"})
            return "Security Alert: Generated code violates safety policies."

        # 4. Execute Code in Sandbox
        output_capture = io.StringIO()

        try:
            with contextlib.redirect_stdout(output_capture):
                # exec is dangerous; using restricted globals helps but isn't bulletproof.
                # In prod, use a proper container/sandbox.
                exec(generated_code, self.context)
        except Exception as e:
            log_action(user_id, "EXECUTION_ERROR", {"error": str(e)})
            return f"Error executing analysis: {e}"

        result = output_capture.getvalue()

        # 5. Audit Execution
        log_action(user_id, "CODE_EXECUTED", {"code": generated_code, "result": result})

        # 6. Synthesize/Explain (Optional, if result needs separate explanation)
        # In our mock, the code prints the narrative directly.

        return result
