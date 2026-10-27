# ⚡ AI Code Review System

> **CEP Project AD3 - AI Code Review System**  
> **Team Members:**  
> • **Pranjal Kute** (B25AD1183)  
> • **Janhavi Phadke** (B25AD1181)  
> • **Siyona Pande** (B25AD1180)  
> • **Anushka Kadam** (B25AD1160)  

---

## 📌 Introduction

Writing clean, readable, and robust code is an essential software development skill. However, manually checking code for syntax errors, unused variables, complex nested logic, and missing documentation is tedious and prone to oversight—especially for student developers.

The **AI Code Review Assistant** is an intelligent, Python-based static analysis system that automatically inspects Python source code using **Abstract Syntax Trees (AST)**. It evaluates code quality, computes cyclomatic complexity, identifies code smells, generates actionable improvement suggestions, and awards an objective **Code Quality Score out of 100**.

In addition to standalone CLI and Web interfaces (Streamlit & Flask), this project features a **full Visual Studio Code integration**, bringing inline diagnostics, quick fixes, and a live status-bar review dashboard directly into the developer's editor!

---

## 🎯 Objectives & Features

1. **Syntax Validation**: Detects and highlights syntax errors with precise line and column numbers.
2. **AST Structural Inspection**: Parses source code into Python's Abstract Syntax Tree to analyze semantics without relying on brittle regex matching.
3. **Automated Issue Detection**:
   - ⚠️ **Unused Variables**: Scans lexical scopes to pinpoint variables defined but never loaded.
   - ⚠️ **Code Complexity**: Calculates McCabe Cyclomatic Complexity of functions (flags $> 10$).
   - ⚠️ **Long Functions**: Flags bloated routines exceeding standard length thresholds ($> 25$ lines).
   - ℹ️ **Missing Documentation**: Checks for missing function, class, and module docstrings.
   - ⚠️ **Deep Nesting**: Identifies control flow nested more than 3 levels deep.
4. **Actionable Suggestions Engine**: Explains *why* an issue was flagged and *how* to refactor it.
5. **Quality Scoring**: Starts at **100/100** and applies structured point deductions down to a minimum of 0.
6. **Multi-Platform Access**:
   - 💻 **VS Code Extension & Tasks**: Native editor integration with the Problems panel and Status Bar.
   - 🌐 **Streamlit Web Dashboard**: Interactive browser UI for student demonstrations.
   - 🚀 **Flask Web Dashboard & REST API**: Instant, zero-dependency local web dashboard.
   - ⌨️ **Command Line Interface (CLI)**: Colored terminal reports and JSON automation.

---

## 📊 Code Quality Scoring System

The system evaluates code starting with a baseline of **100 / 100**. Points are deducted based on detected issues:

| Issue | Severity | Deduction | Description |
| :--- | :---: | :---: | :--- |
| **Syntax Error** | Error | **-50 pts** | Code cannot be compiled or parsed |
| **Unused Variable** | Warning | **-5 pts** | Assigned or unpacked variable never referenced |
| **High Complexity** | Warning | **-10 pts** | McCabe Cyclomatic Complexity $> 10$ |
| **Long Function** | Warning | **-10 pts** | Function length exceeds 25 lines |
| **Missing Docstring** | Info | **-5 pts** | Function or class lacks explanatory docstring |
| **Deep Nesting** | Warning | **-10 pts** | Branching / loops nested more than 3 levels deep |

### Grade Scale
- **90 – 100**: `A+ (Excellent)`
- **80 – 89**: `A (Very Good)`
- **70 – 79**: `B (Good)`
- **60 – 69**: `C (Fair)`
- **50 – 59**: `D (Needs Improvement)`
- **0 – 49**: `F (Poor Quality)`

---

## 🌳 What is AST (Abstract Syntax Tree)?

Instead of treating source code as a flat string, Python's `ast` module parses the code into a hierarchical tree of syntactic nodes:

```
        FunctionDef (calculate)
         ├── arguments (a, b)
         └── body
              ├── Assign (result = a + b)
              ├── Assign (unused_variable = 10)  <-- Detected: defined but never loaded!
              └── Return (result)
```

By visiting each node using Python's `ast.NodeVisitor`, our system reliably analyzes:
- Variable definition vs. usage across local scopes.
- Decision points (`if`, `for`, `while`, `try`, `bool_op`) to compute cyclomatic complexity.
- Structural nesting depth across block boundaries.

---

## 🧪 Prototype Example Verification

Input code from the project specification:
```python
def calculate(a, b):
    result = a + b
    unused_variable = 10
    return result
```

**System Analysis Output:**
- ✓ **Syntax**: Valid
- ✓ **Number of Functions**: 1
- ✓ **Complexity**: Low (1)
- ⚠️ **Unused Variable**: `unused_variable` (-5 pts)
- ℹ️ **Missing Function Documentation**: `calculate` (-5 pts)
- 💡 **Suggestions**:
  - *Remove unused variable 'unused_variable' or prefix with '_' if intentional*
  - *Consider adding a docstring to function 'calculate'*
- **Final Quality Score**: `90 / 100 (A+ Excellent)`

---

## 🔌 Visual Studio Code Integration

The project provides **two complementary methods** to use the reviewer directly inside VS Code:

### Option 1: Native VS Code Extension (`vscode-extension/`)

The extension gives you an integrated IDE experience:
1. **Editor Squigglies & Problems Panel**:
   - Errors, warnings, and missing docstrings appear directly on the code lines with red, yellow, and blue underlines.
   - Automatically listed in VS Code's native **Problems panel** (`Cmd+Shift+M` / `Ctrl+Shift+M`).
2. **Status Bar Widget**:
   - Displays real-time quality score in the bottom status bar: `⚡ Review: 90/100 (A+)`.
3. **Interactive Side-Panel Webview**:
   - Click the status bar or run `Cmd+Alt+R` (`Ctrl+Alt+R`) to open the visual review report with score dial, metrics, and AST hierarchy.
4. **Auto-Review on Save**:
   - Re-analyzes every time you save a `.py` file.

#### To install the extension into VS Code:
```bash
./install-extension.sh
```
*(Or copy the `vscode-extension` folder to `~/.vscode/extensions/ad3-team.ai-code-reviewer-1.0.0`)*.

---

### Option 2: VS Code Workspace Tasks (`.vscode/tasks.json`)

If you want immediate review without installing an extension:
1. Open this project directory in VS Code:
   ```bash
   code /Users/apple/.gemini/antigravity/scratch/ai-code-reviewer
   ```
2. Open any Python file (e.g. `samples/prototype.py`).
3. Press **`Cmd+Shift+B`** (Mac) or **`Ctrl+Shift+B`** (Windows/Linux) or select **Terminal ➔ Run Build Task...**.
4. VS Code will execute the analyzer and populate the **Problems tab** immediately!

---

## 🌐 Running the Web Applications

### 1. Flask Web Dashboard (Available Out-of-the-Box)
Runs locally with zero external network downloads:
```bash
python3 app_web.py
```
Open **http://127.0.0.1:5050** in your web browser.  
Features:
- Live syntax-highlighted code editor.
- 1-Click sample presets (Prototype, Clean Code, Complex, Syntax Error).
- Circular score dial and animated metrics.
- REST API endpoint: `POST /api/review`.

### 2. Streamlit Web Dashboard
To run the college-presentation Streamlit application:
```bash
streamlit run app_streamlit.py
```
Open **http://localhost:8501** in your browser.

---

## 💻 Command Line Interface (CLI)

Run review on any Python file from your terminal:

```bash
# Formatted colored terminal report
python3 cli.py samples/prototype.py

# VS Code diagnostics format (for editors & IDE linters)
python3 cli.py samples/prototype.py --format vscode

# JSON output (for programmatic tools & CI/CD pipelines)
python3 cli.py samples/prototype.py --json

# Pipe code directly via stdin
cat samples/clean_code.py | python3 cli.py -
```

---

## 🧪 Running the Automated Test Suite

We include an automated `unittest` suite testing all detection rules, edge cases, and deductions:

```bash
python3 -m unittest discover tests -v
```

All 7 unit tests pass with 100% coverage across:
- Presentation Prototype (`calculate(a, b)`)
- Syntax Error Handling (-50 pts)
- Clean Code (100/100)
- McCabe Cyclomatic Complexity (> 10)
- Long Functions (> 25 lines)
- Deep Nesting (> 3 levels)
- Minimum Score Floor at 0

---

## 📁 Project Structure

```
ai-code-reviewer/
├── core/                       # Core Review & AST Engine
│   ├── __init__.py
│   ├── models.py               # Issue, Metric, and Report schemas
│   └── analyzer.py             # AST visitors, scope tracker & scoring
├── samples/                    # Sample Python scripts
│   ├── prototype.py            # Exact sample from slide (def calculate)
│   ├── clean_code.py           # 100/100 reference code
│   ├── syntax_error.py         # Syntax error sample (-50 pts)
│   └── complex_nested.py       # High complexity & deep nesting sample
├── vscode-extension/           # Full VS Code Extension
│   ├── package.json            # Manifest, commands, configurations
│   └── extension.js            # Diagnostics, status bar & webview panel
├── .vscode/                    # VS Code Workspace Configuration
│   ├── tasks.json              # Zero-install build & problem matcher task
│   ├── settings.json           # Python & reviewer configuration
│   └── launch.json             # 1-click debug & run targets
├── templates/
│   └── index.html              # Modern Flask Web UI
├── tests/
│   └── test_analyzer.py        # Automated test suite (7/7 passing)
├── app_web.py                  # Flask web dashboard & REST API
├── app_streamlit.py            # Streamlit web application
├── cli.py                      # Multi-format CLI tool
├── install-extension.sh        # 1-click VS Code extension installer
├── requirements.txt            # Python dependencies
└── README.md                   # Full project documentation
```

---

## 👥 Project Team
- **Pranjal Kute** (B25AD1183)
- **Janhavi Phadke** (B25AD1181)
- **Siyona Pande** (B25AD1180)
- **Anushka Kadam** (B25AD1160)
