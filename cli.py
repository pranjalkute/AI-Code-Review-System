#!/usr/bin/env python3
"""
Command Line Interface for AI Code Review System.
CEP Project AD3 - AI Code Review System
Team: Pranjal Kute, Janhavi Phadke, Siyona Pande, Anushka Kadam
"""

import sys
import os
import json
import argparse
from typing import Optional

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.analyzer import AICodeReviewer
from core.models import ReviewReport, IssueSeverity


# ANSI terminal colors for presentation-ready terminal output
class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    RESET = "\033[0m"


def format_colored_report(report: ReviewReport, filename: str) -> str:
    lines = []
    lines.append(f"{Colors.BOLD}{Colors.CYAN}{'=' * 65}{Colors.RESET}")
    lines.append(f"{Colors.BOLD}{Colors.HEADER}  AI CODE REVIEW SYSTEM - ANALYSIS REPORT{Colors.RESET}")
    lines.append(f"{Colors.BOLD}{Colors.CYAN}{'=' * 65}{Colors.RESET}")
    lines.append(f"Target File: {Colors.BOLD}{filename}{Colors.RESET}")

    # Syntax status
    if report.syntax_valid:
        syntax_badge = f"{Colors.GREEN}✓ VALID{Colors.RESET}"
    else:
        syntax_badge = f"{Colors.RED}✗ INVALID (Syntax Error){Colors.RESET}"
    lines.append(f"Syntax: {syntax_badge}")

    # Score & Grade
    score = report.total_score
    if score >= 90:
        score_color = Colors.GREEN
    elif score >= 70:
        score_color = Colors.YELLOW
    else:
        score_color = Colors.RED

    lines.append(
        f"Quality Score: {Colors.BOLD}{score_color}{score}/100{Colors.RESET} ({report.grade})"
    )

    # Metrics
    m = report.metrics
    lines.append(f"\n{Colors.BOLD}{Colors.BLUE}▶ CODE METRICS:{Colors.RESET}")
    lines.append(
        f"  • Total Lines: {m.total_lines}  (Code: {m.code_lines}, Comments: {m.comment_lines}, Blank: {m.blank_lines})"
    )
    lines.append(f"  • Functions: {m.num_functions}")
    lines.append(f"  • Classes: {m.num_classes}")
    comp_label = "Low" if m.max_complexity <= 5 else ("Moderate" if m.max_complexity <= 10 else "High")
    lines.append(
        f"  • Cyclomatic Complexity: Max {m.max_complexity} ({comp_label}), Avg {m.average_complexity}"
    )
    lines.append(f"  • Max Nesting Depth: {m.max_nesting_depth}")

    # Issues
    lines.append(f"\n{Colors.BOLD}{Colors.BLUE}▶ ISSUES DETECTED ({len(report.issues)}):{Colors.RESET}")
    if not report.issues:
        lines.append(f"  {Colors.GREEN}✓ No issues found! Clean code.{Colors.RESET}")
    else:
        for i, issue in enumerate(report.issues, 1):
            if issue.severity == IssueSeverity.ERROR:
                sev_color = Colors.RED
                icon = "✗"
            elif issue.severity == IssueSeverity.WARNING:
                sev_color = Colors.YELLOW
                icon = "⚠"
            else:
                sev_color = Colors.CYAN
                icon = "ℹ"

            lines.append(
                f"  {icon} {sev_color}[Line {issue.line}:{issue.column}] {issue.type.value} (-{issue.deduction} pts){Colors.RESET}"
            )
            lines.append(f"     Message: {issue.message}")
            lines.append(f"     {Colors.BOLD}Suggestion:{Colors.RESET} {issue.suggestion}")

    # Deductions Breakdown
    lines.append(f"\n{Colors.BOLD}{Colors.BLUE}▶ SCORE DEDUCTION BREAKDOWN:{Colors.RESET}")
    lines.append("  Initial Score: 100")
    for category, points in report.deductions_breakdown.items():
        if points > 0:
            lines.append(f"  - {category}: -{points}")
    lines.append(f"  --------------------------")
    lines.append(f"  {Colors.BOLD}Final Score:   {score_color}{score}/100{Colors.RESET}")

    lines.append(f"{Colors.BOLD}{Colors.CYAN}{'=' * 65}{Colors.RESET}\n")
    return "\n".join(lines)


def format_vscode_diagnostics(report: ReviewReport, filename: str) -> str:
    """
    Formats issues in standard GCC/Clang/Linter format readable by VS Code:
    file:line:col: severity: [IssueType] message
    """
    output_lines = []
    abs_path = os.path.abspath(filename)
    for issue in report.issues:
        sev = issue.severity.value.lower()
        if sev == "error":
            diag_sev = "error"
        elif sev == "warning":
            diag_sev = "warning"
        else:
            diag_sev = "info"
        output_lines.append(
            f"{abs_path}:{issue.line}:{issue.column}: {diag_sev}: [{issue.type.value}] {issue.message} (Suggestion: {issue.suggestion})"
        )
    return "\n".join(output_lines)


def main():
    parser = argparse.ArgumentParser(
        description="AI Code Review System (CEP Project AD3) - Automated Python Code Reviewer & AST Analyzer"
    )
    parser.add_argument("file", nargs="?", default=None, help="Python source file to review (or '-' for stdin)")
    parser.add_argument("--code", type=str, default=None, help="Python code string to review directly")
    parser.add_argument("--json", action="store_true", help="Output report in JSON format (for VS Code integration)")
    parser.add_argument(
        "--format",
        choices=["terminal", "json", "vscode"],
        default="terminal",
        help="Output format: terminal (colored), json, or vscode (diagnostics format)",
    )
    parser.add_argument("--max-complexity", type=int, default=10, help="Max allowed cyclomatic complexity")
    parser.add_argument("--max-func-lines", type=int, default=25, help="Max lines for a single function")
    parser.add_argument("--max-nesting", type=int, default=3, help="Max allowed block nesting depth")

    args = parser.parse_args()

    # Determine source code
    source_code = ""
    filename = "<string>"

    if args.code is not None:
        source_code = args.code
        filename = "<string>"
    elif args.file == "-" or (args.file is None and not sys.stdin.isatty()):
        source_code = sys.stdin.read()
        filename = "<stdin>"
    elif args.file:
        filename = args.file
        if not os.path.exists(filename):
            print(f"Error: File '{filename}' not found.", file=sys.stderr)
            sys.exit(1)
        with open(filename, "r", encoding="utf-8") as f:
            source_code = f.read()
    else:
        parser.print_help()
        sys.exit(1)

    reviewer = AICodeReviewer(
        max_func_lines=args.max_func_lines,
        max_complexity=args.max_complexity,
        max_nesting=args.max_nesting,
    )

    report = reviewer.review_code(source_code, filename=filename)

    if args.json or args.format == "json":
        print(json.dumps(report.to_dict(), indent=2))
    elif args.format == "vscode":
        output = format_vscode_diagnostics(report, filename)
        if output:
            print(output)
    else:
        print(format_colored_report(report, filename))

    # Exit code: 0 if valid & score >= 70, 1 if syntax error or score < 50
    if not report.syntax_valid or report.total_score < 50:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
