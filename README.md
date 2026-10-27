# AI-Code-Review-System
An AI code review system built with AST. Featuring zero-install VS Code integration, a real-time Flask web dashboard with a live editor, a multi-format CLI, and a presentation-ready Streamlit app, this tool transforms messy codebases into pristine, production-ready software in milliseconds.
# ⚡ AI Code Review System
> **CEP Project AD3** • *Pranjal Kute, Janhavi Phadke, Siyona Pande, and Anushka Kadam*

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-7%2F7%20passing-success.svg)]()
[![VS Code Extension](https://img.shields.io/badge/VS%20Code-Integrated-blueviolet.svg)]()

---

## 🚀 Overview
The **AI Code Review System** is a robust, lightweight, and extensible code quality assurance platform. Designed to catch architectural smells, stylistic anti-patterns, and syntax vulnerabilities before they reach production, it delivers instant, actionable feedback across your entire development workflow—whether you're working inside the terminal, your IDE, or a web browser.

---

## ✨ Key Features

- **🔍 Deep AST & Complexity Analysis:** Goes beyond basic linters by evaluating McCabe Cyclomatic Complexity, control-block nesting depth, function length, unused variables, and documentation coverage.
- **🎯 Intelligent Scoring Engine:** Uses a transparent deduction-based scoring algorithm (out of 100) with custom severity weights to grade code health instantly.
- **🔌 Deep IDE Integration (VS Code):** 
  - **Zero-Install Task:** Instant Problem Matcher integration (`Cmd+Shift+B`) mapping issues straight to VS Code's Problems tab.
  - **Native Extension:** Real-time diagnostics, squiggly highlights, status bar score widget, and interactive webview dashboards.
- **🌐 Multiple User Interfaces:**
  - **Flask Web Dashboard:** Live code editor, animated score gauges, and a built-in REST API (`/api/review`).
  - **Streamlit Presentation App:** Sleek slide and demo interface built for presentations and code walk-throughs.
  - **Multi-Format CLI:** Terminal interface supporting colored text, JSON output, and VS Code-compatible formats.
- **🛡️ Battle-Tested:** 100% passing automated test suite covering edge cases, syntax failures, and score floor clamping.

---

## 📊 Scoring & Deduction Rules

| Issue Type | Severity | Penalty | Detection Condition |
| :--- | :--- | :--- | :--- |
| **Syntax Error** | `ERROR` | **-50 pts** | Invalid Python syntax / parse failure |
| **High Complexity** | `WARNING` | **-10 pts** | McCabe Cyclomatic Complexity $> 10$ |
| **Long Function** | `WARNING` | **-10 pts** | Function body length $> 25$ lines |
| **Deep Nesting** | `WARNING` | **-10 pts** | Control blocks nested $> 3$ levels deep |
| **Unused Variable** | `WARNING` | **-5 pts** | Local variable declared but never referenced |
| **Missing Docstring** | `INFO` | **-5 pts** | Functions or classes lacking docstrings |

---

## 🏁 Quick Start

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/YOUR_USERNAME/ai-code-reviewer.git](https://github.com/YOUR_USERNAME/ai-code-reviewer.git)
   cd ai-code-reviewer
