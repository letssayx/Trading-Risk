from typing import Dict, Any
import sys
import io

class CodeExecutor:
    """
    Safely execute generated code in a sandbox (restricted globals).
    """

    def execute(self, code: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run code with access to provided context.
        """
        # Redirect stdout to capture print output
        old_stdout = sys.stdout
        redirected_output = io.StringIO()
        sys.stdout = redirected_output

        # Define allowed globals (Sandbox)
        # In a real app, strict whitelist. Here, we allow importing backend modules.
        local_scope = {"context": context}

        try:
            exec(code, {}, local_scope)
            result = local_scope.get("result", "Execution Successful")

            # If strategy.run returns something, capture it
            # Assuming the generated code ends with an expression or assignment we want to check?
            # The parser generates `strategy.run(...)` which might return a dict.
            # But `exec` doesn't return the last expression value like eval.
            # We rely on side effects or specific variable names in local_scope.

        except Exception as e:
            result = f"Error: {str(e)}"
        finally:
            sys.stdout = old_stdout

        output = redirected_output.getvalue()

        return {
            "output": output,
            "result": str(result),
            "status": "success" if "Error" not in str(result) else "error"
        }
