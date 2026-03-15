const { app, BrowserWindow } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let backendProcess = null;

function startBackend() {
  // Only attempt to start backend in production (packaged)
  if (!app.isPackaged) return;

  // Path to backend/main.py relative to the executable
  // In portable build, app.getAppPath() is inside a temp folder, 
  // but we want the folder next to the .exe
  const projectRoot = path.join(process.resourcesPath, '..', '..');
  const backendScript = path.join(projectRoot, 'backend', 'main.py');

  console.log('Attempting to start backend at:', backendScript);

  // Use 'python' or 'python3' based on environment
  backendProcess = spawn('python', [backendScript], {
    cwd: path.join(projectRoot, 'backend'),
    env: { ...process.env, PROJECT_ROOT: projectRoot }
  });

  backendProcess.stdout.on('data', (data) => console.log(`Backend: ${data}`));
  backendProcess.stderr.on('data', (data) => console.error(`Backend Error: ${data}`));
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1280,
    height: 900,
    minWidth: 900,
    minHeight: 600,
    title: 'SonoClarity',
    icon: path.join(__dirname, 'icon.ico'),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
    },
    autoHideMenuBar: true,
    backgroundColor: '#0a0a1a',
  });

  if (app.isPackaged) {
    win.loadFile(path.join(__dirname, '..', 'dist', 'index.html'));
  } else {
    win.loadURL('http://localhost:5173');
  }
}

app.whenReady().then(() => {
  startBackend();
  createWindow();
});

app.on('window-all-closed', () => {
  if (backendProcess) backendProcess.kill();
  if (process.platform !== 'darwin') app.quit();
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

