"""
Data models and schemas for the AI Code Review System.
CEP Project AD3 - AI Code Review System
"""

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import List, Dict, Any, Optional


class IssueType(str, Enum):
    SYNTAX_ERROR = "Syntax Error"
    UNUSED_VARIABLE = "Unused Variable"
    HIGH_COMPLEXITY = "High Complexity"
    LONG_FUNCTION = "Long Function"
    MISSING_DOCSTRING = "Missing Documentation"
    DEEP_NESTING = "Deep Nesting"


class IssueSeverity(str, Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


# Standard point deductions as specified in CEP Project AD3
SCORE_DEDUCTIONS = {
    IssueType.SYNTAX_ERROR: 50,
    IssueType.UNUSED_VARIABLE: 5,
    IssueType.HIGH_COMPLEXITY: 10,
    IssueType.LONG_FUNCTION: 10,
    IssueType.MISSING_DOCSTRING: 5,
    IssueType.DEEP_NESTING: 10,
}


@dataclass
class Issue:
    type: IssueType
    severity: IssueSeverity
    line: int
    column: int
    message: str
    suggestion: str
    deduction: int
    context: Optional[str] = None
    end_line: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['type'] = self.type.value
        data['severity'] = self.severity.value
        return data


@dataclass
class CodeMetrics:
    total_lines: int = 0
    code_lines: int = 0
    blank_lines: int = 0
    comment_lines: int = 0
    num_functions: int = 0
    num_classes: int = 0
    max_complexity: int = 1
    average_complexity: float = 1.0
    max_nesting_depth: int = 0
    syntax_valid: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ReviewReport:
    syntax_valid: bool
    total_score: int
    grade: str
    metrics: CodeMetrics
    issues: List[Issue] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    deductions_breakdown: Dict[str, int] = field(default_factory=dict)
    summary: str = ""
    ast_tree: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "syntax_valid": self.syntax_valid,
            "total_score": self.total_score,
            "grade": self.grade,
            "summary": self.summary,
            "metrics": self.metrics.to_dict(),
            "issues": [issue.to_dict() for issue in self.issues],
            "suggestions": self.suggestions,
            "deductions_breakdown": self.deductions_breakdown,
            "ast_tree": self.ast_tree,
        }
