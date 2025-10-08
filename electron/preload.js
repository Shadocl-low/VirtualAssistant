const { contextBridge, ipcRenderer } = require('electron');

console.log('🔧 Preload script loaded');

contextBridge.exposeInMainWorld('electronAPI', {
    onAvatarCommand: (callback) => {
        console.log('🎯 Avatar command listener registered');
        ipcRenderer.on('avatar-command', (event, data) => {
            console.log('📨 Received avatar command:', data);
            callback(data);
        });
    }
});