import unittest
import math
import sys
import os

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.calculator_tool import CalculatorTool

class TestCalculatorTool(unittest.TestCase):
    def setUp(self):
        self.calculator = CalculatorTool()
    
    def test_basic_arithmetic(self):
        """Test basic arithmetic operations"""
        test_cases = [
            ("2 + 2", 4),
            ("3 * 4", 12),
            ("10 / 2", 5),
            ("7 - 3", 4),
            ("2 + 3 * 4", 14),
            ("(2 + 3) * 4", 20)
        ]
        
        for expression, expected in test_cases:
            result = self.calculator.execute({"expression": expression})
            self.assertEqual(result["result"], expected)
    
    def test_mathematical_functions(self):
        """Test mathematical functions"""
        test_cases = [
            ("abs(-5)", 5),
            ("round(3.7)", 4),
            ("pow(2, 3)", 8),
            ("sqrt(16)", 4),
            ("sin(0)", 0),
            ("cos(0)", 1),
            ("log10(100)", 2)
        ]
        
        for expression, expected in test_cases:
            result = self.calculator.execute({"expression": expression})
            self.assertAlmostEqual(result["result"], expected, places=10)
    
    def test_constants(self):
        """Test mathematical constants"""
        # Test pi
        result = self.calculator.execute({"expression": "pi"})
        self.assertAlmostEqual(result["result"], round(math.pi, 10), places=10)
        
        # Test e
        result = self.calculator.execute({"expression": "e"})
        self.assertAlmostEqual(result["result"], round(math.e, 10), places=10)
    
    def test_complex_expressions(self):
        """Test more complex mathematical expressions"""
        test_cases = [
            ("2 * pi * 5", 2 * math.pi * 5),
            ("e ** 2", math.e ** 2),
            ("sin(pi/2)", 1),
            ("log10(100) + sqrt(16)", 6)
        ]
        
        for expression, expected in test_cases:
            result = self.calculator.execute({"expression": expression})
            self.assertAlmostEqual(result["result"], expected, places=10)
    
    def test_error_handling(self):
        """Test error handling"""
        test_cases = [
            ("", "Expression cannot be empty"),
            ("1/0", "Division by zero"),
            ("invalid", "Invalid expression"),
            ("import os", "Invalid expression: contains forbidden keywords"),
            ("__import__('os')", "Invalid expression: contains forbidden keywords")
        ]
        
        for expression, expected_error in test_cases:
            result = self.calculator.execute({"expression": expression})
            self.assertIn("error", result)
            self.assertTrue(result["error"].startswith(expected_error))
    
    def test_invalid_expressions(self):
        """Test invalid mathematical expressions"""
        test_cases = [
            ("2 ** 500", "Result is infinite"),  # Very large power
            ("2 ** -500", "Result is infinite"),  # Very small power
            ("1e308 * 2", "Result is infinite"),  # Overflow
            ("1e-308 / 2", "Result is infinite")  # Underflow
        ]
        
        for expression, expected_error in test_cases:
            result = self.calculator.execute({"expression": expression})
            self.assertIn("error", result, f"Expected error for expression: {expression}")
            self.assertEqual(result["error"], expected_error, 
                           f"For expression '{expression}', expected error '{expected_error}' but got '{result.get('error')}'")

if __name__ == '__main__':
    unittest.main() 