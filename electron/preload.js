const { contextBridge, ipcRenderer } = require('electron');
const PIXI = require('pixi.js');
const { Live2DModel } = require('pixi-live2d-display');

console.log('🔧 Preload script loaded');

contextBridge.exposeInMainWorld('electronAPI', {
    onAvatarCommand: (callback) => {
        console.log('🎯 Avatar command listener registered');
        ipcRenderer.on('avatar-command', (event, data) => {
            console.log('📨 Received avatar command:', data);
            callback(data);
        });
    },
    PIXI: PIXI,
    Live2DModel: Live2DModel
});