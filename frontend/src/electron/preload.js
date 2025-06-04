// src/electron/preload.js
import { contextBridge } from 'electron';

contextBridge.exposeInMainWorld('api', {
  // future IPC-safe functions
});
