import math
from typing import Dict, Any
from .tool_orchestration import MCPTool

class CalculatorTool(MCPTool):
    """A calculator tool that safely evaluates mathematical expressions."""
    
    def __init__(self):
        super().__init__(
            name="calculator",
            description="Performs mathematical calculations",
            parameters={
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "The mathematical expression to evaluate"
                    }
                },
                "required": ["expression"]
            }
        )
        
        # Define safe mathematical functions and constants
        self.safe_dict = {
            # Basic arithmetic is handled by eval
            
            # Mathematical functions
            'abs': abs,
            'round': round,
            'pow': self.safe_pow,  # Use our safe power function
            'sum': sum,
            
            # Trigonometric functions
            'sin': math.sin,
            'cos': math.cos,
            'tan': math.tan,
            'asin': math.asin,
            'acos': math.acos,
            'atan': math.atan,
            'degrees': math.degrees,
            'radians': math.radians,
            
            # Exponential and logarithmic functions
            'exp': math.exp,
            'log': math.log,
            'log10': math.log10,
            'sqrt': math.sqrt,
            
            # Constants
            'pi': math.pi,
            'e': math.e,
            'inf': math.inf,
            'nan': math.nan
        }

    def safe_pow(self, base: float, exponent: float) -> float:
        """Safely compute power, checking for overflow"""
        try:
            # For large exponents, check if result would be too large
            if abs(exponent) > 100:
                # Quick check using logarithm
                if abs(base) > 1:
                    return math.inf  # Will cause overflow
                elif abs(base) < 1:
                    return 0.0  # Will underflow to 0
                else:
                    return 1.0  # base is exactly 1
            return pow(base, exponent)
        except OverflowError:
            return math.inf

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the calculator tool with the given parameters."""
        try:
            expression = params.get("expression", "").strip()
            
            # Security checks
            if not expression:
                return {"error": "Expression cannot be empty"}
            
            if any(keyword in expression for keyword in [
                'import', 'exec', 'eval', 'open', '__', 'lambda', 
                'global', 'locals', 'getattr', 'setattr'
            ]):
                return {"error": "Invalid expression: contains forbidden keywords"}
            
            # Handle power operator separately
            if '**' in expression:
                try:
                    base, exp = expression.split('**')
                    base = float(eval(base, {"__builtins__": {}}, self.safe_dict))
                    exp = float(eval(exp, {"__builtins__": {}}, self.safe_dict))
                    result = self.safe_pow(base, exp)
                    if math.isinf(result):
                        return {"error": "Result is infinite"}
                    return {"result": result}
                except Exception:
                    pass  # Fall through to normal evaluation
            
            # Create a safe evaluation environment
            safe_env = {
                "__builtins__": {},  # Remove built-in functions
                **self.safe_dict     # Add our safe mathematical functions
            }
            
            # Evaluate the expression
            result = eval(expression, safe_env)
            
            # Format the result
            if isinstance(result, (int, float)):
                # Handle special cases
                if math.isnan(result):
                    return {"error": "Result is not a number (NaN)"}
                elif math.isinf(result):
                    return {"error": "Result is infinite"}
                # Check for very large numbers that might cause overflow
                elif isinstance(result, int) and abs(result) > 1e308:
                    return {"error": "Result is infinite"}
                elif isinstance(result, float) and (abs(result) > 1e308 or abs(result) < 1e-308 and result != 0):
                    return {"error": "Result is infinite"}
                else:
                    # Round to 10 decimal places to avoid floating point issues
                    if isinstance(result, float):
                        result = round(result, 10)
                    return {"result": result}
            else:
                return {"error": "Invalid result type"}
                
        except ZeroDivisionError:
            return {"error": "Division by zero"}
        except (SyntaxError, NameError, TypeError) as e:
            return {"error": f"Invalid expression: {str(e)}"}
        except OverflowError:
            return {"error": "Result is infinite"}
        except Exception as e:
            return {"error": f"Error evaluating expression: {str(e)}"} 