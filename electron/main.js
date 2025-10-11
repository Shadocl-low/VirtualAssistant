const { app, BrowserWindow } = require('electron');
const path = require('path');
const WebSocket = require('ws');

let win;

function createWindow() {
    win = new BrowserWindow({
        x: 1000,
        y: 375,
        width: 600,
        height: 500,
        transparent: false,
        frame: true,
        alwaysOnTop: true,
        webPreferences: {
            sandbox: false,
            preload: path.join(__dirname, 'preload.js'),
            nodeIntegration: false,
            contextIsolation: true,
        }
    });

    // win.setIgnoreMouseEvents(true);
    win.loadFile('index.html');

}

app.whenReady().then(() => {
    createWindow();

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) createWindow();
    });
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') app.quit();
});

// WebSocket сервер для зв'язку з Python
const wss = new WebSocket.Server({ port: 8765 });
wss.on('connection', ws => {
    ws.on('message', message => {
        try {
            const data = JSON.parse(message);
            win.webContents.send('avatar-command', data);
        } catch (e) {
            console.error(e);
        }
    });
});
