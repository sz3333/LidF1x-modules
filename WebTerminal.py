from .. import loader, utils
from telethon.tl.types import Message
import subprocess
import os
import psutil
import platform
import datetime
import logging
import json
import shutil
import socket
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file
import asyncio
import threading

app = Flask(__name__)
app.secret_key = os.urandom(24)

@loader.tds
class WebTerminalMod(loader.Module):
    """Web Terminal Module"""
    strings = {"name": "WebTerminal"}

    def __init__(self):
        self.config = loader.ModuleConfig(
            "PORT", 5000, "Port for web terminal"
        )
        
        self.BASE_DIR = os.getcwd()
        self.TEMPLATES_DIR = os.path.join(self.BASE_DIR, 'templates')
        self.LOGS_DIR = os.path.join(self.BASE_DIR, 'logs')
        self.DOWNLOADS_DIR = os.path.join(self.BASE_DIR, 'downloads')
        
        for directory in [self.TEMPLATES_DIR, self.LOGS_DIR, self.DOWNLOADS_DIR]:
            if not os.path.exists(directory):
                os.makedirs(directory)

        logging.basicConfig(
            filename=os.path.join(self.LOGS_DIR, 'terminal.log'),
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] - %(message)s'
        )

        self.command_history = []
        self.MAX_HISTORY = 1000

        self.HTML_CONTENT = '''<!DOCTYPE html>
<html>
<head>
    <title>Advanced Web Terminal</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500&display=swap" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        :root {
            --bg-color: #1a1b1e;
            --terminal-bg: #000000;
            --text-color: #ffffff;
            --accent-color: #00ff00;
            --error-color: #ff3333;
            --warning-color: #ffcc00;
            --info-color: #00ccff;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            background-color: var(--bg-color);
            color: var(--text-color);
            font-family: 'Fira Code', monospace;
            display: flex;
            height: 100vh;
            overflow: hidden;
        }

        #workspace {
            display: flex;
            flex: 1;
            height: 100vh;
        }

        #sidebar {
            width: 300px;
            background-color: #242528;
            padding: 20px;
            border-right: 1px solid #333;
            display: flex;
            flex-direction: column;
            overflow-y: auto;
        }

        #main-content {
            flex: 1;
            display: flex;
            flex-direction: column;
            padding: 20px;
        }

        #toolbar {
            display: flex;
            gap: 10px;
            margin-bottom: 10px;
            padding: 10px;
            background-color: #242528;
            border-radius: 8px;
        }

        .tool-button {
            background-color: #333;
            border: none;
            color: var(--text-color);
            padding: 8px 15px;
            border-radius: 4px;
            cursor: pointer;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            gap: 5px;
        }

        .tool-button:hover {
            background-color: #444;
            transform: translateY(-1px);
        }

        .tool-button i {
            font-size: 14px;
        }

        #terminal {
            flex: 1;
            background-color: var(--terminal-bg);
            padding: 20px;
            border-radius: 8px;
            overflow-y: auto;
            margin-bottom: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            font-size: 14px;
            line-height: 1.6;
        }

        #input-area {
            display: flex;
            background-color: var(--terminal-bg);
            padding: 10px;
            border-radius: 8px;
            align-items: center;
        }

        #prompt {
            color: var(--accent-color);
            margin-right: 10px;
            font-weight: 500;
        }

        #command-input {
            flex: 1;
            background: transparent;
            border: none;
            color: var(--text-color);
            font-family: 'Fira Code', monospace;
            font-size: 14px;
            outline: none;
        }

        .output-line {
            margin: 2px 0;
            word-wrap: break-word;
            white-space: pre-wrap;
        }

        .error { color: var(--error-color); }
        .success { color: var(--accent-color); }
        .warning { color: var(--warning-color); }
        .info { color: var(--info-color); }

        .system-info {
            background-color: #2a2b2e;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }

        .system-info h3 {
            margin-bottom: 10px;
            color: var(--accent-color);
        }

        .info-item {
            display: flex;
            justify-content: space-between;
            margin: 5px 0;
            padding: 5px 0;
            border-bottom: 1px solid #333;
        }

        .history-container {
            background-color: #2a2b2e;
            padding: 15px;
            border-radius: 8px;
            margin-top: 20px;
            flex: 1;
            overflow-y: auto;
        }

        .history-item {
            padding: 8px;
            margin: 5px 0;
            background-color: #333;
            border-radius: 4px;
            cursor: pointer;
            transition: all 0.2s;
        }

        .history-item:hover {
            background-color: #444;
            transform: translateX(5px);
        }

        ::-webkit-scrollbar {
            width: 8px;
        }

        ::-webkit-scrollbar-track {
            background: #1a1b1e;
        }

        ::-webkit-scrollbar-thumb {
            background: #333;
            border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: #444;
        }

        .progress-bar {
            height: 4px;
            background-color: #333;
            border-radius: 2px;
            margin-top: 5px;
        }

        .progress-fill {
            height: 100%;
            background-color: var(--accent-color);
            border-radius: 2px;
            transition: width 0.3s ease;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(-10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .fade-in {
            animation: fadeIn 0.3s ease;
        }

        .tooltip {
            position: relative;
        }

        .tooltip:hover::after {
            content: attr(data-tooltip);
            position: absolute;
            bottom: 100%;
            left: 50%;
            transform: translateX(-50%);
            padding: 5px 10px;
            background-color: #333;
            border-radius: 4px;
            font-size: 12px;
            white-space: nowrap;
            z-index: 1000;
        }
    </style>
</head>
<body>
    <div id="workspace">
        <div id="sidebar">
            <div class="system-info">
                <h3><i class="fas fa-microchip"></i> System Info</h3>
                <div id="sys-info"></div>
            </div>
            
            <div class="history-container">
                <h3><i class="fas fa-history"></i> Command History</h3>
                <div id="history-list"></div>
            </div>
        </div>
        
        <div id="main-content">
            <div id="toolbar">
                <button class="tool-button tooltip" onclick="clearTerminal()" data-tooltip="Clear terminal">
                    <i class="fas fa-eraser"></i> Clear
                </button>
                <button class="tool-button tooltip" onclick="toggleTheme()" data-tooltip="Toggle theme">
                    <i class="fas fa-moon"></i> Theme
                </button>
                <button class="tool-button tooltip" onclick="downloadHistory()" data-tooltip="Save history">
                    <i class="fas fa-download"></i> Save
                </button>
                <button class="tool-button tooltip" onclick="showHelp()" data-tooltip="Show help">
                    <i class="fas fa-question-circle"></i> Help
                </button>
            </div>
            
            <div id="terminal"></div>
            
            <div id="input-area">
                <span id="prompt">$</span>
                <input type="text" id="command-input" autofocus spellcheck="false" autocomplete="off">
            </div>
        </div>
    </div>

    <script>
        const terminal = document.getElementById('terminal');
        const commandInput = document.getElementById('command-input');
        let commandHistory = [];
        let historyIndex = -1;
        let darkTheme = true;

        async function updateSystemInfo() {
            try {
                const response = await fetch('/system-info');
                const data = await response.json();
                
                const sysInfo = document.getElementById('sys-info');
                sysInfo.innerHTML = `
                    <div class="info-item">
                        <span>CPU Usage:</span>
                        <span>${data.cpu_usage}%</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${data.cpu_usage}%"></div>
                    </div>
                    
                    <div class="info-item">
                        <span>RAM Usage:</span>
                        <span>${data.ram_usage}%</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${data.ram_usage}%"></div>
                    </div>
                    
                    <div class="info-item">
                        <span>Disk Usage:</span>
                        <span>${data.disk_usage}%</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${data.disk_usage}%"></div>
                    </div>
                    
                    <div class="info-item">
                        <span>OS:</span>
                        <span>${data.os}</span>
                    </div>
                `;
            } catch (error) {
                console.error('Error updating system info:', error);
            }
        }

        function addToTerminal(text, className = '') {
            const line = document.createElement('div');
            line.className = `output-line ${className} fade-in`;
            line.textContent = text;
            terminal.appendChild(line);
            terminal.scrollTop = terminal.scrollHeight;
        }

        async function executeCommand(command) {
            if (!command) return;
            
            addToTerminal(`$ ${command}`);
            commandHistory.push(command);
            updateHistoryList();

            try {
                const response = await fetch('/execute', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ command })
                });
                
                const data = await response.json();
                
                if (data.error) {
                    addToTerminal(data.error, 'error');
                } else {
                    addToTerminal(data.output, 'success');
                }
            } catch (error) {
                addToTerminal(`Error: ${error.message}`, 'error');
            }

            updateSystemInfo();
        }

        function updateHistoryList() {
            const historyList = document.getElementById('history-list');
            historyList.innerHTML = '';
            
            commandHistory.slice(-10).reverse().forEach(cmd => {
                const item = document.createElement('div');
                item.className = 'history-item fade-in';
                item.textContent = cmd;
                item.onclick = () => {
                    commandInput.value = cmd;
                    commandInput.focus();
                };
                historyList.appendChild(item);
            });
        }

        function clearTerminal() {
            terminal.innerHTML = '';
            addToTerminal('Terminal cleared', 'info');
        }

        function toggleTheme() {
            darkTheme = !darkTheme;
            document.documentElement.style.setProperty('--bg-color', 
                darkTheme ? '#1a1b1e' : '#ffffff');
            document.documentElement.style.setProperty('--text-color', 
                darkTheme ? '#ffffff' : '#000000');
            addToTerminal(`Theme switched to ${darkTheme ? 'dark' : 'light'}`, 'info');
        }

        function downloadHistory() {
            const blob = new Blob(
                [JSON.stringify(commandHistory, null, 2)], 
                {type: 'application/json'}
            );
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `terminal-history-${new Date().toISOString()}.json`;
            a.click();
            addToTerminal('History saved to file', 'info');
        }

        function showHelp() {
            const helpText = `
Available commands:
- All system commands are supported
- Use Up/Down arrows to navigate command history
- Clear terminal: clear or click Clear button
- Toggle theme: click Theme button
- Save history: click Save button
- Click on history items to reuse commands
            `.trim();
            addToTerminal(helpText, 'info');
        }

        commandInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                const command = commandInput.value.trim();
                executeCommand(command);
                commandInput.value = '';
                historyIndex = -1;
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                if (historyIndex < commandHistory.length - 1) {
                    historyIndex++;
                    commandInput.value = commandHistory[commandHistory.length - 1 - historyIndex];
                }
            } else if (e.key === 'ArrowDown') {
                e.preventDefault();
                if (historyIndex > 0) {
                    historyIndex--;
                    commandInput.value = commandHistory[commandHistory.length - 1 - historyIndex];
                } else {
                    historyIndex = -1;
                    commandInput.value = '';
                }
            }
        });

        document.addEventListener('click', () => {
            commandInput.focus();
        });

        updateSystemInfo();
        setInterval(updateSystemInfo, 5000);
        addToTerminal('Terminal initialized. Type help or click Help button for available commands.', 'info');
    </script>
</body>
</html>'''

        self.TEMPLATE_PATH = os.path.join(self.TEMPLATES_DIR, 'terminal.html')
        with open(self.TEMPLATE_PATH, 'w') as f:
            f.write(self.HTML_CONTENT)
            
    async def client_ready(self, client, db):
        self.client = client
        self.db = db

    def start_server(self):
        app.run(host='0.0.0.0', port=self.config["PORT"])

    @loader.owner
    async def wtcmd(self, message: Message):
        """Start web terminal"""
        try:
            server_thread = threading.Thread(target=self.start_server)
            server_thread.daemon = True
            server_thread.start()
            await utils.answer(message, f"🌐 Web terminal started on port {self.config['PORT']}")
        except Exception as e:
            await utils.answer(message, f"❌ Error: {str(e)}")

    @staticmethod
    @app.route('/')
    def home():
        return render_template('terminal.html')

    @staticmethod
    @app.route('/execute', methods=['POST'])
    def execute_command():
        command = request.json.get('command', '').strip()
        if not command:
            return jsonify({'error': 'No command provided'})

        try:
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            try:
                output, error = process.communicate(timeout=30)
            except subprocess.TimeoutExpired:
                process.kill()
                return jsonify({'error': 'Command execution timed out'})
                
            if error:
                return jsonify({'error': error})
            
            return jsonify({'output': output})
        
        except Exception as e:
            logging.error(f"Error executing command: {str(e)}")
            return jsonify({'error': str(e)})

    @staticmethod
    @app.route('/system-info')
    def system_info():
        try:
            cpu_usage = psutil.cpu_percent()
            ram = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return jsonify({
                'cpu_usage': cpu_usage,
                'ram_usage': ram.percent,
                'disk_usage': disk.percent,
                'os': f"{platform.system()} {platform.release()}",
                'hostname': socket.gethostname(),
                'python_version': platform.python_version()
            })
        except Exception as e:
            logging.error(f"Error getting system info: {str(e)}")
            return jsonify({'error': str(e)})

    @app.route('/download-history')
    def download_history(self):
        try:
            history_file = os.path.join(self.DOWNLOADS_DIR, 'terminal_history.json')
            with open(history_file, 'w') as f:
                json.dump(self.command_history, f, indent=2)
            return send_file(history_file, as_attachment=True)
        except Exception as e:
            logging.error(f"Error downloading history: {str(e)}")
            return jsonify({'error': str(e)})
            
