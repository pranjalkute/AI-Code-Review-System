"""
Core Analyzer Engine for AI Code Review System.
CEP Project AD3 - AI Code Review System
Pranjal Kute, Janhavi Phadke, Siyona Pande, Anushka Kadam

Features:
- Syntax Analysis with detailed error localization
- AST-based code analysis (symbols, scopes, call graph, complexity)
- Unused Variable detection
- Cyclomatic Complexity calculation
- Long Function detection
- Missing Documentation detection (module, classes, functions)
- Deep Nesting detection
- Quality Score calculation (starts at 100, specific deductions)
- Actionable Suggestion generator
"""

import ast
import re
from typing import List, Dict, Set, Tuple, Optional, Any
from .models import (
    Issue,
    IssueType,
    IssueSeverity,
    CodeMetrics,
    ReviewReport,
    SCORE_DEDUCTIONS,
)


class ComplexityVisitor(ast.NodeVisitor):
    """Calculates McCabe Cyclomatic Complexity of a function AST node."""

    def __init__(self):
        self.complexity = 1  # Base complexity

    def visit_If(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_IfExp(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_For(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_AsyncFor(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_While(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_ExceptHandler(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_With(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_AsyncWith(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_Assert(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_BoolOp(self, node):
        # 'and' / 'or' with N values adds N-1 decision points
        self.complexity += len(node.values) - 1
        self.generic_visit(node)

    def visit_Match(self, node):
        # Python 3.10+ match statement
        if hasattr(node, 'cases'):
            self.complexity += max(0, len(node.cases) - 1)
        self.generic_visit(node)


class Scope:
    """Represents a lexical scope for tracking variable definitions and usages."""

    def __init__(self, name: str, scope_type: str = "function"):
        self.name = name
        self.scope_type = scope_type  # 'global', 'function', 'class', 'comprehension'
        # var_name -> (line, col, end_line)
        self.defined: Dict[str, Tuple[int, int, Optional[int]]] = {}
        # set of var_names used (loaded)
        self.used: Set[str] = set()
        # set of parameters to optionally treat differently
        self.parameters: Set[str] = set()
        # set of globals/nonlocals
        self.explicit_globals: Set[str] = set()


class VariableUsageVisitor(ast.NodeVisitor):
    """
    Traverses AST to track variable assignments vs usages across scopes.
    Accurately detects unused variables while avoiding false positives on:
    - standard convention throwaways (e.g. _, __)
    - dunder variables (__name__, etc.)
    - global/nonlocal declarations
    """

    def __init__(self):
        self.scopes: List[Scope] = [Scope("global", "global")]
        self.all_scopes: List[Scope] = [self.scopes[0]]

    @property
    def current_scope(self) -> Scope:
        return self.scopes[-1]

    def visit_FunctionDef(self, node):
        self._handle_func(node)

    def visit_AsyncFunctionDef(self, node):
        self._handle_func(node)

    def _handle_func(self, node):
        # Function name itself is defined in current scope
        self.current_scope.defined[node.name] = (node.lineno, node.col_offset, getattr(node, 'end_lineno', None))
        
        # Create function scope
        func_scope = Scope(node.name, "function")
        self.scopes.append(func_scope)
        self.all_scopes.append(func_scope)

        # Track parameters (note: unused parameters could be intentional for callbacks/interfaces,
        # but in student code unused local vars are the main target)
        for arg in node.args.posonlyargs + node.args.args + node.args.kwonlyargs:
            if arg.arg != "self" and arg.arg != "cls" and not arg.arg.startswith("_"):
                func_scope.defined[arg.arg] = (arg.lineno, arg.col_offset, getattr(arg, 'end_lineno', None))
                func_scope.parameters.add(arg.arg)
        if node.args.vararg and not node.args.vararg.arg.startswith("_"):
            func_scope.defined[node.args.vararg.arg] = (node.args.vararg.lineno, node.args.vararg.col_offset, None)
            func_scope.parameters.add(node.args.vararg.arg)
        if node.args.kwarg and not node.args.kwarg.arg.startswith("_"):
            func_scope.defined[node.args.kwarg.arg] = (node.args.kwarg.lineno, node.args.kwarg.col_offset, None)
            func_scope.parameters.add(node.args.kwarg.arg)

        # Visit body
        for stmt in node.body:
            self.visit(stmt)

        self.scopes.pop()

    def visit_ClassDef(self, node):
        self.current_scope.defined[node.name] = (node.lineno, node.col_offset, getattr(node, 'end_lineno', None))
        class_scope = Scope(node.name, "class")
        self.scopes.append(class_scope)
        self.all_scopes.append(class_scope)
        for stmt in node.body:
            self.visit(stmt)
        self.scopes.pop()

    def visit_Global(self, node):
        for name in node.names:
            self.current_scope.explicit_globals.add(name)

    def visit_Nonlocal(self, node):
        for name in node.names:
            self.current_scope.explicit_globals.add(name)

    def visit_Name(self, node):
        name = node.id
        if isinstance(node.ctx, ast.Store):
            # Assignment / definition
            # Ignore standard ignored names like '_' or '_unused'
            if not name.startswith("_"):
                self.current_scope.defined[name] = (node.lineno, node.col_offset, getattr(node, 'end_lineno', None))
        elif isinstance(node.ctx, ast.Load):
            # Usage
            # Mark as used in current scope and bubble up if not found locally
            self._mark_used(name)

    def _mark_used(self, name: str):
        # Walk down scopes from inner to outer
        for scope in reversed(self.scopes):
            scope.used.add(name)
            if name in scope.defined:
                break

    def get_unused_variables(self) -> List[Tuple[str, int, int, str]]:
        """Returns list of (var_name, lineno, col_offset, scope_name)."""
        unused = []
        for scope in self.all_scopes:
            # We focus on local function scopes for unused variable checks
            # (In global scopes or classes, module variables might be imported or consumed externally)
            if scope.scope_type == "function":
                for var_name, (lineno, col, _) in scope.defined.items():
                    if var_name not in scope.used:
                        # Exclude self, cls, and conventional throwaways
                        if var_name not in ("self", "cls") and not var_name.startswith("_"):
                            unused.append((var_name, lineno, col, scope.name))
        return unused


class NestingVisitor(ast.NodeVisitor):
    """Measures maximum block nesting depth and flags deep nesting (>3 levels)."""

    NESTING_NODES = (
        ast.If,
        ast.For,
        ast.AsyncFor,
        ast.While,
        ast.Try,
        ast.With,
        ast.AsyncWith,
    )

    def __init__(self, threshold: int = 3):
        self.threshold = threshold
        self.current_depth = 0
        self.max_depth = 0
        self.deep_nesting_nodes: List[Tuple[ast.AST, int, str]] = []  # (node, depth, func_context)
        self.current_func = "module"

    def visit_FunctionDef(self, node):
        old_func = self.current_func
        self.current_func = node.name
        self.generic_visit(node)
        self.current_func = old_func

    def visit_AsyncFunctionDef(self, node):
        old_func = self.current_func
        self.current_func = node.name
        self.generic_visit(node)
        self.current_func = old_func

    def generic_visit(self, node):
        is_nesting = isinstance(node, self.NESTING_NODES)
        if is_nesting:
            self.current_depth += 1
            if self.current_depth > self.max_depth:
                self.max_depth = self.current_depth
            if self.current_depth > self.threshold:
                self.deep_nesting_nodes.append((node, self.current_depth, self.current_func))

        super().generic_visit(node)

        if is_nesting:
            self.current_depth -= 1


class AICodeReviewer:
    """
    Main Code Review Engine.
    Coordinates AST analysis, metric computation, rule checking, scoring, and suggestions.
    """

    def __init__(
        self,
        max_func_lines: int = 25,
        max_complexity: int = 10,
        max_nesting: int = 3,
        require_module_docstring: bool = False,
    ):
        self.max_func_lines = max_func_lines
        self.max_complexity = max_complexity
        self.max_nesting = max_nesting
        self.require_module_docstring = require_module_docstring

    def review_code(self, source_code: str, filename: str = "<input>") -> ReviewReport:
        """Analyzes Python source code and returns a comprehensive ReviewReport."""
        metrics = self._compute_line_metrics(source_code)
        issues: List[Issue] = []
        deductions_breakdown: Dict[str, int] = {
            "Syntax Error": 0,
            "Unused Variable": 0,
            "High Complexity": 0,
            "Long Function": 0,
            "Missing Documentation": 0,
            "Deep Nesting": 0,
        }

        # 1. Syntax Analysis
        try:
            tree = ast.parse(source_code, filename=filename)
            metrics.syntax_valid = True
        except SyntaxError as e:
            metrics.syntax_valid = False
            line = e.lineno or 1
            col = e.offset or 1
            error_msg = f"Syntax Error at line {line}, col {col}: {e.msg}"
            suggestion = f"Fix syntax error on line {line}: {e.text.strip() if e.text else e.msg}"
            deduction = SCORE_DEDUCTIONS[IssueType.SYNTAX_ERROR]
            issues.append(
                Issue(
                    type=IssueType.SYNTAX_ERROR,
                    severity=IssueSeverity.ERROR,
                    line=line,
                    column=col,
                    message=error_msg,
                    suggestion=suggestion,
                    deduction=deduction,
                    context=e.text.strip() if e.text else None,
                )
            )
            deductions_breakdown["Syntax Error"] += deduction

            # Calculate score with syntax deduction (starts at 100, -50 for syntax error = 50)
            score = max(0, 100 - deduction)
            grade = self._calculate_grade(score)
            summary = f"Syntax analysis failed: 1 syntax error found. Resolve syntax errors before full AST analysis."

            return ReviewReport(
                syntax_valid=False,
                total_score=score,
                grade=grade,
                metrics=metrics,
                issues=issues,
                suggestions=[suggestion],
                deductions_breakdown=deductions_breakdown,
                summary=summary,
                ast_tree=None,
            )

        # 2. AST Code Analysis (Syntax is valid)
        ast_dump_str = self._generate_ast_dump(tree)

        # Count functions and classes
        functions: List[ast.FunctionDef] = []
        classes: List[ast.ClassDef] = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append(node)
            elif isinstance(node, ast.ClassDef):
                classes.append(node)

        metrics.num_functions = len(functions)
        metrics.num_classes = len(classes)

        # 3. Issue Detection: Unused Variables
        var_visitor = VariableUsageVisitor()
        var_visitor.visit(tree)
        unused_vars = var_visitor.get_unused_variables()

        for var_name, lineno, col, scope_name in unused_vars:
            deduction = SCORE_DEDUCTIONS[IssueType.UNUSED_VARIABLE]
            issues.append(
                Issue(
                    type=IssueType.UNUSED_VARIABLE,
                    severity=IssueSeverity.WARNING,
                    line=lineno,
                    column=col,
                    message=f"Unused variable '{var_name}' in function '{scope_name}'",
                    suggestion=f"Remove unused variable '{var_name}' or prefix with '_' if intentional",
                    deduction=deduction,
                    context=var_name,
                )
            )
            deductions_breakdown["Unused Variable"] += deduction

        # 4. Issue Detection: Complexity & Function Length & Documentation
        complexities = []
        for func in functions:
            # Cyclomatic complexity
            comp_visitor = ComplexityVisitor()
            comp_visitor.visit(func)
            func_complexity = comp_visitor.complexity
            complexities.append(func_complexity)

            if func_complexity > self.max_complexity:
                deduction = SCORE_DEDUCTIONS[IssueType.HIGH_COMPLEXITY]
                issues.append(
                    Issue(
                        type=IssueType.HIGH_COMPLEXITY,
                        severity=IssueSeverity.WARNING,
                        line=func.lineno,
                        column=func.col_offset,
                        message=f"Function '{func.name}' has high cyclomatic complexity ({func_complexity} > {self.max_complexity})",
                        suggestion=f"Simplify function '{func.name}' by breaking down branching logic into smaller helper functions",
                        deduction=deduction,
                        context=func.name,
                        end_line=getattr(func, 'end_lineno', None),
                    )
                )
                deductions_breakdown["High Complexity"] += deduction

            # Function length
            end_lineno = getattr(func, 'end_lineno', func.lineno)
            func_lines = end_lineno - func.lineno + 1
            if func_lines > self.max_func_lines:
                deduction = SCORE_DEDUCTIONS[IssueType.LONG_FUNCTION]
                issues.append(
                    Issue(
                        type=IssueType.LONG_FUNCTION,
                        severity=IssueSeverity.WARNING,
                        line=func.lineno,
                        column=func.col_offset,
                        message=f"Function '{func.name}' is too long ({func_lines} lines > {self.max_func_lines} limit)",
                        suggestion=f"Refactor function '{func.name}' into smaller modular functions (recommended <= {self.max_func_lines} lines)",
                        deduction=deduction,
                        context=func.name,
                        end_line=end_lineno,
                    )
                )
                deductions_breakdown["Long Function"] += deduction

            # Missing Documentation on Function
            docstring = ast.get_docstring(func)
            if not docstring or not docstring.strip():
                deduction = SCORE_DEDUCTIONS[IssueType.MISSING_DOCSTRING]
                issues.append(
                    Issue(
                        type=IssueType.MISSING_DOCSTRING,
                        severity=IssueSeverity.INFO,
                        line=func.lineno,
                        column=func.col_offset,
                        message=f"Missing docstring in function '{func.name}'",
                        suggestion=f"Consider adding a docstring to function '{func.name}' explaining its purpose, arguments, and return value",
                        deduction=deduction,
                        context=func.name,
                    )
                )
                deductions_breakdown["Missing Documentation"] += deduction

        # Missing Documentation on Classes
        for cls in classes:
            docstring = ast.get_docstring(cls)
            if not docstring or not docstring.strip():
                deduction = SCORE_DEDUCTIONS[IssueType.MISSING_DOCSTRING]
                issues.append(
                    Issue(
                        type=IssueType.MISSING_DOCSTRING,
                        severity=IssueSeverity.INFO,
                        line=cls.lineno,
                        column=cls.col_offset,
                        message=f"Missing docstring in class '{cls.name}'",
                        suggestion=f"Add a docstring to class '{cls.name}' explaining its purpose and responsibilities",
                        deduction=deduction,
                        context=cls.name,
                    )
                )
                deductions_breakdown["Missing Documentation"] += deduction

        # Optional: Module Docstring
        if self.require_module_docstring and not ast.get_docstring(tree):
            deduction = SCORE_DEDUCTIONS[IssueType.MISSING_DOCSTRING]
            issues.append(
                Issue(
                    type=IssueType.MISSING_DOCSTRING,
                    severity=IssueSeverity.INFO,
                    line=1,
                    column=1,
                    message="Missing module docstring at top of file",
                    suggestion="Add a top-level module docstring summarizing the module's contents and purpose",
                    deduction=deduction,
                )
            )
            deductions_breakdown["Missing Documentation"] += deduction

        metrics.max_complexity = max(complexities) if complexities else 1
        metrics.average_complexity = round(sum(complexities) / len(complexities), 2) if complexities else 1.0

        # 5. Issue Detection: Deep Nesting
        nesting_visitor = NestingVisitor(threshold=self.max_nesting)
        nesting_visitor.visit(tree)
        metrics.max_nesting_depth = nesting_visitor.max_depth

        # Report deep nesting nodes (deduplicate by line)
        seen_lines = set()
        for node, depth, func_context in nesting_visitor.deep_nesting_nodes:
            lineno = getattr(node, 'lineno', 1)
            if lineno in seen_lines:
                continue
            seen_lines.add(lineno)
            deduction = SCORE_DEDUCTIONS[IssueType.DEEP_NESTING]
            issues.append(
                Issue(
                    type=IssueType.DEEP_NESTING,
                    severity=IssueSeverity.WARNING,
                    line=lineno,
                    column=getattr(node, 'col_offset', 1),
                    message=f"Deeply nested block (nesting depth {depth} > {self.max_nesting}) in '{func_context}'",
                    suggestion="Flatten nested logic using guard clauses, early returns, or helper functions",
                    deduction=deduction,
                    context=func_context,
                )
            )
            deductions_breakdown["Deep Nesting"] += deduction

        # 6. Quality Score Calculation
        total_deductions = sum(issue.deduction for issue in issues)
        score = max(0, 100 - total_deductions)
        grade = self._calculate_grade(score)

        # 7. Suggestions List
        suggestions = [issue.suggestion for issue in issues]
        if not suggestions:
            suggestions.append("Outstanding code! No issues detected. Clean, readable, and well-structured.")

        # Summary Generation
        summary = self._build_summary(score, grade, metrics, issues)

        return ReviewReport(
            syntax_valid=True,
            total_score=score,
            grade=grade,
            metrics=metrics,
            issues=issues,
            suggestions=suggestions,
            deductions_breakdown=deductions_breakdown,
            summary=summary,
            ast_tree=ast_dump_str,
        )

    def _compute_line_metrics(self, code: str) -> CodeMetrics:
        lines = code.splitlines()
        total_lines = len(lines)
        blank_lines = 0
        comment_lines = 0
        code_lines = 0

        for line in lines:
            stripped = line.strip()
            if not stripped:
                blank_lines += 1
            elif stripped.startswith("#"):
                comment_lines += 1
            else:
                code_lines += 1

        return CodeMetrics(
            total_lines=total_lines,
            code_lines=code_lines,
            blank_lines=blank_lines,
            comment_lines=comment_lines,
        )

    def _calculate_grade(self, score: int) -> str:
        if score >= 90:
            return "A+ (Excellent)"
        elif score >= 80:
            return "A (Very Good)"
        elif score >= 70:
            return "B (Good)"
        elif score >= 60:
            return "C (Fair)"
        elif score >= 50:
            return "D (Needs Improvement)"
        else:
            return "F (Poor Quality)"

    def _build_summary(
        self, score: int, grade: str, metrics: CodeMetrics, issues: List[Issue]
    ) -> str:
        complexity_label = (
            "Low" if metrics.max_complexity <= 5
            else "Moderate" if metrics.max_complexity <= 10
            else "High"
        )
        issue_counts = {
            IssueType.UNUSED_VARIABLE.value: sum(1 for i in issues if i.type == IssueType.UNUSED_VARIABLE),
            IssueType.HIGH_COMPLEXITY.value: sum(1 for i in issues if i.type == IssueType.HIGH_COMPLEXITY),
            IssueType.LONG_FUNCTION.value: sum(1 for i in issues if i.type == IssueType.LONG_FUNCTION),
            IssueType.MISSING_DOCSTRING.value: sum(1 for i in issues if i.type == IssueType.MISSING_DOCSTRING),
            IssueType.DEEP_NESTING.value: sum(1 for i in issues if i.type == IssueType.DEEP_NESTING),
        }

        parts = [
            f"Code Quality Score: {score}/100 [{grade}]",
            f"Syntax: Valid | Functions: {metrics.num_functions} | Max Complexity: {complexity_label} ({metrics.max_complexity})",
            f"Total Issues Found: {len(issues)} (Unused: {issue_counts[IssueType.UNUSED_VARIABLE.value]}, Docs: {issue_counts[IssueType.MISSING_DOCSTRING.value]}, Nesting: {issue_counts[IssueType.DEEP_NESTING.value]})",
        ]
        return "\n".join(parts)

    def _generate_ast_dump(self, tree: ast.AST) -> str:
        """Generates a clean, indented visual representation of the AST nodes."""
        lines = []

        def recurse(node, indent=0):
            prefix = "  " * indent
            node_name = node.__class__.__name__

            # Pick interesting attributes
            details = []
            if hasattr(node, 'name'):
                details.append(f"name='{node.name}'")
            if hasattr(node, 'id'):
                details.append(f"id='{node.id}'")
            if hasattr(node, 'value') and isinstance(node.value, (int, float, str, bool)):
                details.append(f"val={repr(node.value)}")
            if hasattr(node, 'lineno'):
                details.append(f"L{node.lineno}")

            detail_str = f" ({', '.join(details)})" if details else ""
            lines.append(f"{prefix}- {node_name}{detail_str}")

            # Recurse on children up to reasonable depth
            if indent < 8:
                for child in ast.iter_child_nodes(node):
                    recurse(child, indent + 1)

        recurse(tree)
        return "\n".join(lines[:120])  # limit display to first 120 lines for responsiveness
