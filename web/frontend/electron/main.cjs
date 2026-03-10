const { app, BrowserWindow } = require('electron');
const path = require('path');

function createWindow() {
  const win = new BrowserWindow({
    width: 1280,
    height: 900,
    minWidth: 900,
    minHeight: 600,
    title: 'SonoClarity',
    icon: path.join(__dirname, 'icon.png'),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
    },
    autoHideMenuBar: true,
    backgroundColor: '#0a0a1a',
  });

  // In production, load the built React files
  // In dev, we could load localhost, but for the packaged app we load the build
  if (app.isPackaged) {
    win.loadFile(path.join(__dirname, '..', 'dist', 'index.html'));
  } else {
    // When running electron in dev mode, load from Vite dev server
    win.loadURL('http://localhost:5173');
  }
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  app.quit();
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});
