/**
 * AI Code Review Assistant - VS Code Extension
 * CEP Project AD3 - AI Code Review System
 * Team: Pranjal Kute, Janhavi Phadke, Siyona Pande, Anushka Kadam
 */

const vscode = require('vscode');
const { spawn } = require('child_process');
const path = require('path');

let diagnosticCollection;
let statusBarItem;
let currentReport = null;
let currentWebviewPanel = null;

/**
 * Activates the extension.
 * @param {vscode.ExtensionContext} context
 */
function activate(context) {
    console.log('AI Code Review Assistant is now active in VS Code!');

    // Initialize Diagnostics Collection (populates VS Code Problems pane)
    diagnosticCollection = vscode.languages.createDiagnosticCollection('ai-code-reviewer');
    context.subscriptions.push(diagnosticCollection);

    // Initialize Status Bar Item
    statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
    statusBarItem.command = 'aiReviewer.showReport';
    statusBarItem.text = '$(zap) AI Review: --';
    statusBarItem.tooltip = 'Click to open AI Code Review Dashboard';
    context.subscriptions.push(statusBarItem);

    // Register Commands
    const reviewCmd = vscode.commands.registerCommand('aiReviewer.reviewCurrentFile', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showInformationMessage('No active editor to review.');
            return;
        }
        await reviewDocument(editor.document, true);
    });

    const showReportCmd = vscode.commands.registerCommand('aiReviewer.showReport', () => {
        openOrUpdateWebview(context);
    });

    const clearCmd = vscode.commands.registerCommand('aiReviewer.clearDiagnostics', () => {
        diagnosticCollection.clear();
        statusBarItem.text = '$(zap) AI Review: --';
        vscode.window.showInformationMessage('AI Review diagnostics cleared.');
    });

    context.subscriptions.push(reviewCmd, showReportCmd, clearCmd);

    // Hook into file save
    context.subscriptions.push(
        vscode.workspace.onDidSaveTextDocument((doc) => {
            const config = vscode.workspace.getConfiguration('aiReviewer');
            if (doc.languageId === 'python' && config.get('reviewOnSave', true)) {
                reviewDocument(doc, false);
            }
        })
    );

    // Hook into active editor change
    context.subscriptions.push(
        vscode.window.onDidChangeActiveTextEditor((editor) => {
            if (editor && editor.document.languageId === 'python') {
                statusBarItem.show();
                const config = vscode.workspace.getConfiguration('aiReviewer');
                if (config.get('reviewOnSave', true)) {
                    reviewDocument(editor.document, false);
                }
            } else {
                statusBarItem.hide();
            }
        })
    );

    // Initial check if python file currently open
    if (vscode.window.activeTextEditor && vscode.window.activeTextEditor.document.languageId === 'python') {
        statusBarItem.show();
        reviewDocument(vscode.window.activeTextEditor.document, false);
    }
}

/**
 * Finds the absolute path to cli.py
 */
function getCliPath() {
    // 1. Try relative to extension or workspace
    const workspaceFolders = vscode.workspace.workspaceFolders;
    if (workspaceFolders && workspaceFolders.length > 0) {
        const root = workspaceFolders[0].uri.fsPath;
        const candidate = path.join(root, 'cli.py');
        return candidate;
    }
    // 2. Default scratch location
    return '/Users/apple/.gemini/antigravity/scratch/ai-code-reviewer/cli.py';
}

/**
 * Executes Python analyzer on the given text document.
 * @param {vscode.TextDocument} document
 * @param {boolean} notifyUser
 */
async function reviewDocument(document, notifyUser = false) {
    if (document.languageId !== 'python') return;

    const config = vscode.workspace.getConfiguration('aiReviewer');
    const pythonPath = config.get('pythonPath', 'python3');
    const maxComplexity = config.get('maxComplexity', 10);
    const maxFuncLines = config.get('maxFunctionLines', 25);
    const maxNesting = config.get('maxNesting', 3);
    const cliPath = getCliPath();

    const code = document.getText();
    const args = [
        cliPath,
        '-',
        '--json',
        '--max-complexity', String(maxComplexity),
        '--max-func-lines', String(maxFuncLines),
        '--max-nesting', String(maxNesting)
    ];

    try {
        const jsonResult = await runProcessWithStdin(pythonPath, args, code);
        const report = JSON.parse(jsonResult);
        currentReport = report;

        // Apply Diagnostics
        applyDiagnostics(document, report);

        // Update Status Bar
        updateStatusBar(report);

        // Refresh Webview if active
        if (currentWebviewPanel) {
            currentWebviewPanel.webview.html = getWebviewContent(report, document.fileName);
        }

        if (notifyUser) {
            const gradeShort = report.grade.split(' ')[0];
            const issueCount = report.issues.length;
            const message = `AI Review Complete: Score ${report.total_score}/100 (${gradeShort}) with ${issueCount} issue(s).`;
            if (report.total_score >= 80) {
                vscode.window.showInformationMessage(message, 'View Report').then((choice) => {
                    if (choice === 'View Report') openOrUpdateWebview();
                });
            } else {
                vscode.window.showWarningMessage(message, 'View Report').then((choice) => {
                    if (choice === 'View Report') openOrUpdateWebview();
                });
            }
        }
    } catch (err) {
        console.error('AI Reviewer Error:', err);
        if (notifyUser) {
            vscode.window.showErrorMessage(`AI Reviewer failed: ${err.message}`);
        }
    }
}

/**
 * Spawns child process, pipes stdin, and returns stdout string.
 */
function runProcessWithStdin(command, args, stdinData) {
    return new Promise((resolve, reject) => {
        const proc = spawn(command, args);
        let stdout = '';
        let stderr = '';

        proc.stdout.on('data', (data) => { stdout += data.toString(); });
        proc.stderr.on('data', (data) => { stderr += data.toString(); });

        proc.on('close', (code) => {
            // CLI returns 0 on score >=70, 1 on score <50 or syntax error, but always prints valid JSON when --json passed
            if (stdout.trim().startsWith('{')) {
                resolve(stdout);
            } else {
                reject(new Error(stderr || `Process exited with code ${code}`));
            }
        });

        proc.on('error', (err) => {
            reject(err);
        });

        proc.stdin.write(stdinData);
        proc.stdin.end();
    });
}

/**
 * Converts review report issues to VS Code Diagnostics and marks them in the editor.
 */
function applyDiagnostics(document, report) {
    const diagnostics = [];

    for (const issue of report.issues) {
        const line = Math.max(0, (issue.line || 1) - 1);
        const col = Math.max(0, (issue.column || 1));
        const endLine = Math.max(line, (issue.end_line || issue.line || 1) - 1);

        // Find line length to highlight
        const lineText = document.lineAt(Math.min(line, document.lineCount - 1)).text;
        const endCol = Math.max(col + 1, lineText.length);

        const range = new vscode.Range(line, col, endLine, endCol);

        let severity = vscode.DiagnosticSeverity.Warning;
        if (issue.severity === 'ERROR') {
            severity = vscode.DiagnosticSeverity.Error;
        } else if (issue.severity === 'INFO') {
            severity = vscode.DiagnosticSeverity.Information;
        }

        const message = `[${issue.type}] ${issue.message} (-${issue.deduction} pts)\n💡 Suggestion: ${issue.suggestion}`;
        const diagnostic = new vscode.Diagnostic(range, message, severity);
        diagnostic.source = 'AI Reviewer';
        diagnostic.code = issue.type;
        diagnostics.push(diagnostic);
    }

    diagnosticCollection.set(document.uri, diagnostics);
}

/**
 * Updates the status bar item.
 */
function updateStatusBar(report) {
    statusBarItem.show();
    const score = report.total_score;
    const gradeShort = report.grade.split(' ')[0];

    if (score >= 90) {
        statusBarItem.text = `$(check) AI Review: ${score}/100 (${gradeShort})`;
        statusBarItem.backgroundColor = undefined;
    } else if (score >= 70) {
        statusBarItem.text = `$(warning) AI Review: ${score}/100 (${gradeShort})`;
        statusBarItem.backgroundColor = undefined;
    } else {
        statusBarItem.text = `$(error) AI Review: ${score}/100 (${gradeShort})`;
        statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.errorBackground');
    }

    statusBarItem.tooltip = `AI Code Quality: ${score}/100 [${report.grade}]\nIssues: ${report.issues.length}\nClick to view full report.`;
}

/**
 * Opens or updates the interactive Webview panel.
 */
function openOrUpdateWebview(context) {
    const column = vscode.window.activeTextEditor ? vscode.ViewColumn.Beside : vscode.ViewColumn.One;

    if (currentWebviewPanel) {
        currentWebviewPanel.reveal(column);
    } else {
        currentWebviewPanel = vscode.window.createWebviewPanel(
            'aiReviewReport',
            'AI Code Review Report',
            column,
            {
                enableScripts: true,
                retainContextWhenHidden: true
            }
        );

        currentWebviewPanel.onDidDispose(() => {
            currentWebviewPanel = null;
        });
    }

    const fileName = vscode.window.activeTextEditor ? path.basename(vscode.window.activeTextEditor.document.fileName) : 'active_file.py';
    currentWebviewPanel.webview.html = getWebviewContent(currentReport, fileName);
}

/**
 * Generates HTML for the VS Code Webview panel.
 */
function getWebviewContent(report, fileName) {
    if (!report) {
        return `<!DOCTYPE html><html><body style="font-family: var(--vscode-font-family); color: var(--vscode-foreground); padding: 2rem;">
            <h2>AI Code Review Report</h2>
            <p>No active report yet. Open a Python file and run <strong>AI Code Review: Analyze Current File</strong>.</p>
        </body></html>`;
    }

    const score = report.total_score;
    const scoreColor = score >= 85 ? '#10b981' : (score >= 70 ? '#f59e0b' : '#ef4444');
    const compLabel = report.metrics.max_complexity <= 5 ? 'Low' : (report.metrics.max_complexity <= 10 ? 'Moderate' : 'High');

    const issuesHtml = report.issues.map(iss => {
        const borderCol = iss.severity === 'ERROR' ? '#ef4444' : (iss.severity === 'WARNING' ? '#f59e0b' : '#3b82f6');
        return `
            <div style="border-left: 4px solid ${borderCol}; background: var(--vscode-editor-inactiveSelectionBackground); padding: 10px 14px; margin-bottom: 10px; border-radius: 4px;">
                <div style="display: flex; justify-content: space-between; font-weight: 600; font-size: 0.9rem;">
                    <span>[${escapeHtml(iss.type)}] Line ${iss.line}:${iss.column}</span>
                    <span style="color: #ef4444;">-${iss.deduction} pts</span>
                </div>
                <div style="margin-top: 4px; font-size: 0.95rem;">${escapeHtml(iss.message)}</div>
                <div style="margin-top: 4px; font-size: 0.85rem; color: var(--vscode-descriptionForeground); font-style: italic;">
                    💡 <strong>Tip:</strong> ${escapeHtml(iss.suggestion)}
                </div>
            </div>
        `;
    }).join('') || '<p style="color: #10b981; font-weight: 600;">✓ Outstanding code! No quality violations found.</p>';

    const deductionsHtml = Object.entries(report.deductions_breakdown)
        .filter(([_, pts]) => pts > 0)
        .map(([cat, pts]) => `<li>${escapeHtml(cat)}: <strong>-${pts} pts</strong></li>`)
        .join('') || '<li>No deductions applied (100/100)!</li>';

    return `<!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <style>
            body {
                font-family: var(--vscode-font-family);
                color: var(--vscode-foreground);
                background-color: var(--vscode-editor-background);
                padding: 1.5rem;
                line-height: 1.5;
            }
            .header-box {
                display: flex;
                align-items: center;
                gap: 1.5rem;
                background: var(--vscode-sideBar-background);
                border: 1px solid var(--vscode-panel-border);
                border-radius: 10px;
                padding: 1.25rem;
                margin-bottom: 1.5rem;
            }
            .score-circle {
                width: 90px;
                height: 90px;
                border-radius: 50%;
                background: ${scoreColor};
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                color: white;
                font-weight: 800;
                box-shadow: 0 4px 10px rgba(0,0,0,0.3);
            }
            .score-num { font-size: 2rem; line-height: 1; }
            .score-denom { font-size: 0.75rem; opacity: 0.9; }
            .grid {
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 10px;
                margin-bottom: 1.5rem;
            }
            .card {
                background: var(--vscode-sideBar-background);
                border: 1px solid var(--vscode-panel-border);
                padding: 10px;
                border-radius: 6px;
                text-align: center;
            }
            .card-val { font-size: 1.25rem; font-weight: 700; color: var(--vscode-editor-foreground); }
            .card-lbl { font-size: 0.75rem; color: var(--vscode-descriptionForeground); }
            h3 { margin-top: 1.5rem; margin-bottom: 0.75rem; border-bottom: 1px solid var(--vscode-panel-border); padding-bottom: 4px; }
            pre {
                background: var(--vscode-textCodeBlock-background);
                padding: 12px;
                border-radius: 6px;
                font-family: var(--vscode-editor-font-family);
                font-size: 0.85rem;
                max-height: 200px;
                overflow: auto;
            }
        </style>
    </head>
    <body>
        <div class="header-box">
            <div class="score-circle">
                <span class="score-num">${score}</span>
                <span class="score-denom">/100</span>
            </div>
            <div>
                <h2 style="margin: 0; font-size: 1.3rem;">AI Code Review: ${escapeHtml(fileName)}</h2>
                <div style="font-size: 1.05rem; font-weight: 600; color: ${scoreColor}; margin-top: 4px;">
                    ${escapeHtml(report.grade)}
                </div>
                <div style="font-size: 0.8rem; color: var(--vscode-descriptionForeground); margin-top: 2px;">
                    CEP Project AD3 • Syntax: ${report.syntax_valid ? '✓ Valid' : '✗ Invalid'}
                </div>
            </div>
        </div>

        <div class="grid">
            <div class="card">
                <div class="card-val">${report.syntax_valid ? '✓ Valid' : '✗ Error'}</div>
                <div class="card-lbl">Syntax</div>
            </div>
            <div class="card">
                <div class="card-val">${report.metrics.num_functions}</div>
                <div class="card-lbl">Functions</div>
            </div>
            <div class="card">
                <div class="card-val">${compLabel} (${report.metrics.max_complexity})</div>
                <div class="card-lbl">Max Complexity</div>
            </div>
            <div class="card">
                <div class="card-val">${report.issues.length}</div>
                <div class="card-lbl">Issues Found</div>
            </div>
        </div>

        <h3>⚠️ Issues & Diagnostics (${report.issues.length})</h3>
        ${issuesHtml}

        <h3>📉 Deductions Breakdown</h3>
        <ul>${deductionsHtml}</ul>

        <h3>🌳 AST Code Hierarchy</h3>
        <pre>${report.ast_tree ? escapeHtml(report.ast_tree) : 'No AST generated due to syntax error.'}</pre>
    </body>
    </html>`;
}

function escapeHtml(str) {
    return (str || '').replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function deactivate() {
    if (diagnosticCollection) {
        diagnosticCollection.clear();
        diagnosticCollection.dispose();
    }
    if (statusBarItem) {
        statusBarItem.dispose();
    }
}

module.exports = {
    activate,
    deactivate
};
