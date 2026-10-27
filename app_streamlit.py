"""
AI Code Review System - Streamlit Web Application
CEP Project AD3 - AI Code Review System
Team: Pranjal Kute, Janhavi Phadke, Siyona Pande, Anushka Kadam
"""

import streamlit as st
import sys
import os

# Ensure local imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.analyzer import AICodeReviewer
from core.models import IssueSeverity, IssueType

# Page Configuration
st.set_page_config(
    page_title="AI Code Review Assistant | CEP Project AD3",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for styling
st.markdown(
    """
    <style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .subtitle {
        font-size: 1rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .score-box {
        background: linear-gradient(135deg, #1e3a8a, #3b82f6);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .score-number {
        font-size: 3.5rem;
        font-weight: 800;
        line-height: 1;
    }
    .score-grade {
        font-size: 1.2rem;
        font-weight: 600;
        margin-top: 0.5rem;
        opacity: 0.95;
    }
    .metric-card {
        background-color: #F3F4F6;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #3B82F6;
    }
    .metric-val {
        font-size: 1.5rem;
        font-weight: 700;
        color: #1F2937;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #6B7280;
    }
    .issue-card {
        border-radius: 8px;
        padding: 0.75rem 1rem;
        margin-bottom: 0.75rem;
        border-left: 5px solid #EF4444;
        background-color: #FEF2F2;
    }
    .issue-warning {
        border-left-color: #F59E0B;
        background-color: #FFFBEB;
    }
    .issue-info {
        border-left-color: #3B82F6;
        background-color: #EFF6FF;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Preset sample codes for instant testing
SAMPLE_PROTOTYPE = '''def calculate(a, b):
    result = a + b
    unused_variable = 10
    return result
'''

SAMPLE_CLEAN = '''"""Clean utility functions for mathematical operations."""

def calculate_average(grades: list) -> float:
    """
    Computes the arithmetic mean of student grades.
    
    Args:
        grades: List of numerical marks.
        
    Returns:
        The average score as float.
    """
    if not grades:
        return 0.0
    return sum(grades) / len(grades)
'''

SAMPLE_COMPLEX = '''def process_transactions(records, fee_rate, active_only):
    temp_counter = 0
    unused_log = "starting"
    total = 0

    if records:
        for rec in records:
            if rec.get("valid"):
                if rec.get("amount") > 100:
                    for item in rec.get("items", []):
                        if item.get("in_stock"):
                            total += item.get("price", 0)
                else:
                    if active_only:
                        total += 5
            elif rec.get("flagged"):
                total += 0
    return total
'''

SAMPLE_SYNTAX_ERROR = '''def faulty_function(x, y)
    print("Forgot colon on function header")
    return x * y
'''

# Sidebar configuration
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/source-code.png", width=64)
    st.title("Settings & Presets")
    st.markdown("**CEP Project AD3**")
    st.markdown("*Team Members:*")
    st.caption("• Pranjal Kute (B25AD1183)")
    st.caption("• Janhavi Phadke (B25AD1181)")
    st.caption("• Siyona Pande (B25AD1180)")
    st.caption("• Anushka Kadam (B25AD1160)")

    st.markdown("---")
    st.subheader("Load Preset Example")
    preset_choice = st.selectbox(
        "Choose sample code:",
        [
            "1. Example Prototype (calculate)",
            "2. Clean Code (100/100)",
            "3. Complex & Nested Code",
            "4. Syntax Error Sample",
            "5. Custom Code",
        ],
    )

    initial_code = SAMPLE_PROTOTYPE
    if preset_choice.startswith("1."):
        initial_code = SAMPLE_PROTOTYPE
    elif preset_choice.startswith("2."):
        initial_code = SAMPLE_CLEAN
    elif preset_choice.startswith("3."):
        initial_code = SAMPLE_COMPLEX
    elif preset_choice.startswith("4."):
        initial_code = SAMPLE_SYNTAX_ERROR
    elif preset_choice.startswith("5."):
        initial_code = ""

    st.markdown("---")
    st.subheader("Review Rules & Deductions")
    st.markdown("""
    | Issue | Penalty |
    | :--- | :--- |
    | **Syntax Error** | -50 pts |
    | **Unused Variable** | -5 pts |
    | **High Complexity** | -10 pts |
    | **Long Function (>25 lines)** | -10 pts |
    | **Missing Docstring** | -5 pts |
    | **Deep Nesting (>3 levels)** | -10 pts |
    """)

# Header
st.markdown('<div class="main-title">⚡ AI Code Review Assistant</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Automated Python AST code quality analyzer, complexity auditor, and suggestion engine</div>',
    unsafe_allow_html=True,
)

# Main layout: Left = Code Input, Right = Analysis Report
col_code, col_report = st.columns([1.1, 0.9])

with col_code:
    st.markdown("### 📝 Source Code Input")
    code_input = st.text_area(
        label="Paste Python code below:",
        value=initial_code,
        height=380,
        placeholder="def my_function(x):\n    ...",
    )
    analyze_btn = st.button("🚀 Analyze Code with AST", type="primary", use_container_width=True)

if analyze_btn or code_input:
    reviewer = AICodeReviewer(max_func_lines=25, max_complexity=10, max_nesting=3)
    report = reviewer.review_code(code_input, filename="active_editor.py")

    with col_report:
        st.markdown("### 📊 Code Quality Report")

        # Big score display
        score_gradient = (
            "linear-gradient(135deg, #10B981, #059669)"
            if report.total_score >= 85
            else (
                "linear-gradient(135deg, #F59E0B, #D97706)"
                if report.total_score >= 70
                else "linear-gradient(135deg, #EF4444, #DC2626)"
            )
        )

        st.markdown(
            f"""
            <div class="score-box" style="background: {score_gradient};">
                <div style="font-size: 0.9rem; letter-spacing: 1px; text-transform: uppercase;">Overall Code Quality Score</div>
                <div class="score-number">{report.total_score}<span style="font-size: 1.8rem; font-weight: 400;">/100</span></div>
                <div class="score-grade">{report.grade}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.write("")

        # 4 Mini metrics cards
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            syntax_icon = "✓" if report.syntax_valid else "✗"
            st.metric("Syntax", f"{syntax_icon} {'Valid' if report.syntax_valid else 'Error'}")
        with m2:
            st.metric("Functions", report.metrics.num_functions)
        with m3:
            comp_txt = "Low" if report.metrics.max_complexity <= 5 else ("Mod" if report.metrics.max_complexity <= 10 else "High")
            st.metric("Complexity", f"{comp_txt} ({report.metrics.max_complexity})")
        with m4:
            st.metric("Issues", len(report.issues))

    # Bottom Sections: Detailed Findings & AST Explorer
    st.markdown("---")
    tab_issues, tab_suggestions, tab_ast, tab_deductions = st.tabs(
        ["⚠️ Issues & Diagnostics", "💡 Improvement Suggestions", "🌳 AST Code Explorer", "📉 Deduction Breakdown"]
    )

    with tab_issues:
        if not report.issues:
            st.success("🎉 Great job! No syntax errors, unused variables, or complexity violations found.")
        else:
            for issue in report.issues:
                card_class = (
                    "issue-card"
                    if issue.severity == IssueSeverity.ERROR
                    else ("issue-card issue-warning" if issue.severity == IssueSeverity.WARNING else "issue-card issue-info")
                )
                icon = "✗" if issue.severity == IssueSeverity.ERROR else ("⚠" if issue.severity == IssueSeverity.WARNING else "ℹ")
                st.markdown(
                    f"""
                    <div class="{card_class}">
                        <strong>{icon} [{issue.type.value}] Line {issue.line}:{issue.column}</strong> 
                        <span style="float: right; font-weight: bold; color: #DC2626;">-{issue.deduction} pts</span>
                        <div style="margin-top: 4px; font-size: 0.95rem;">{issue.message}</div>
                        <div style="margin-top: 4px; font-size: 0.85rem; color: #4B5563;"><em>Tip: {issue.suggestion}</em></div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    with tab_suggestions:
        st.subheader("Actionable Recommendations")
        for i, s in enumerate(report.suggestions, 1):
            st.markdown(f"**{i}.** {s}")

    with tab_ast:
        st.subheader("Abstract Syntax Tree (AST) Visualization")
        st.info("The AST converts Python source code into a programmatic node tree, enabling structural inspections without regex heuristics.")
        if report.ast_tree:
            st.code(report.ast_tree, language="text")
        else:
            st.warning("AST could not be generated due to syntax errors.")

    with tab_deductions:
        st.subheader("Points Calculation")
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            st.write("**Starting Score:** 100 / 100")
            for cat, pts in report.deductions_breakdown.items():
                if pts > 0:
                    st.write(f"- {cat}: **-{pts} pts**")
            st.markdown(f"### Final Score: **{report.total_score} / 100**")
        with col_d2:
            st.write("**Summary String:**")
            st.text(report.summary)
