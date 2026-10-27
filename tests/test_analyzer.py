"""
Unit test suite for AI Code Review System.
CEP Project AD3 - AI Code Review System
"""

import unittest
import sys
import os

# Add root directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.analyzer import AICodeReviewer
from core.models import IssueType, IssueSeverity


class TestAICodeReviewer(unittest.TestCase):

    def setUp(self):
        self.reviewer = AICodeReviewer(
            max_func_lines=25,
            max_complexity=10,
            max_nesting=3,
        )

    def test_slide_prototype(self):
        """Tests the exact prototype code from the project presentation slide."""
        code = """def calculate(a, b):
    result = a + b
    unused_variable = 10
    return result
"""
        report = self.reviewer.review_code(code)

        self.assertTrue(report.syntax_valid)
        self.assertEqual(report.total_score, 90)
        self.assertEqual(report.metrics.num_functions, 1)
        self.assertEqual(report.metrics.max_complexity, 1)

        # Check detected issues
        issue_types = [i.type for i in report.issues]
        self.assertIn(IssueType.UNUSED_VARIABLE, issue_types)
        self.assertIn(IssueType.MISSING_DOCSTRING, issue_types)

        # Check deductions breakdown
        self.assertEqual(report.deductions_breakdown["Unused Variable"], 5)
        self.assertEqual(report.deductions_breakdown["Missing Documentation"], 5)

        # Check suggestions
        suggestions_text = " ".join(report.suggestions)
        self.assertIn("unused_variable", suggestions_text)
        self.assertIn("docstring", suggestions_text)

    def test_syntax_error(self):
        """Tests code with syntax errors (-50 deduction)."""
        broken_code = """def broken_func(a, b)
    return a + b
"""
        report = self.reviewer.review_code(broken_code)

        self.assertFalse(report.syntax_valid)
        self.assertEqual(report.total_score, 50)
        self.assertEqual(len(report.issues), 1)
        self.assertEqual(report.issues[0].type, IssueType.SYNTAX_ERROR)
        self.assertEqual(report.issues[0].deduction, 50)

    def test_clean_code_full_score(self):
        """Tests clean, well-documented code with 100/100 score."""
        clean_code = '''"""Module docstring."""

def multiply(x: int, y: int) -> int:
    """Multiplies two integers."""
    product = x * y
    return product
'''
        report = self.reviewer.review_code(clean_code)

        self.assertTrue(report.syntax_valid)
        self.assertEqual(report.total_score, 100)
        self.assertEqual(len(report.issues), 0)
        self.assertEqual(report.grade, "A+ (Excellent)")

    def test_high_complexity_detection(self):
        """Tests McCabe cyclomatic complexity calculation and penalty."""
        # 11 decision points in function
        complex_code = '''def complex_decision(a, b, c, d):
    """Docstring present."""
    if a > 1:
        pass
    if a > 2:
        pass
    if a > 3:
        pass
    if a > 4:
        pass
    if a > 5:
        pass
    if a > 6:
        pass
    if a > 7:
        pass
    if a > 8:
        pass
    if a > 9:
        pass
    if a > 10:
        pass
    return a
'''
        report = self.reviewer.review_code(complex_code)
        self.assertTrue(report.metrics.max_complexity > 10)
        self.assertEqual(report.deductions_breakdown["High Complexity"], 10)

    def test_long_function_detection(self):
        """Tests function length exceeding max_func_lines (25)."""
        body_lines = ["    x = x + 1" for _ in range(30)]
        long_func_code = 'def very_long_function(x):\n    """Doc."""\n' + "\n".join(body_lines) + "\n    return x\n"

        report = self.reviewer.review_code(long_func_code)
        self.assertEqual(report.deductions_breakdown["Long Function"], 10)
        long_issues = [i for i in report.issues if i.type == IssueType.LONG_FUNCTION]
        self.assertEqual(len(long_issues), 1)

    def test_deep_nesting_detection(self):
        """Tests deep nesting of control flow blocks (> 3 levels)."""
        nested_code = '''def nested_demo(data):
    """Docstring present."""
    if data:
        for x in data:
            if x > 0:
                while x > 5:
                    x -= 1
    return data
'''
        report = self.reviewer.review_code(nested_code)
        self.assertTrue(report.metrics.max_nesting_depth >= 4)
        self.assertEqual(report.deductions_breakdown["Deep Nesting"], 10)

    def test_score_floor_at_zero(self):
        """Tests that score cannot go negative even with numerous violations."""
        terrible_code = '''def disaster(a, b):
    x1 = 1
    x2 = 2
    x3 = 3
    x4 = 4
    x5 = 5
    x6 = 6
    x7 = 7
    x8 = 8
    x9 = 9
    x10 = 10
    x11 = 11
    x12 = 12
    x13 = 13
    x14 = 14
    x15 = 15
    if a:
        if b:
            if a > 1:
                if b > 1:
                    if a > 2:
                        return a
    return b
'''
        report = self.reviewer.review_code(terrible_code)
        self.assertGreaterEqual(report.total_score, 0)
        self.assertEqual(report.total_score, 0)


if __name__ == "__main__":
    unittest.main()
