import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  base: './',
  // Liefert die bestehenden resources/audio/*.mp3 als audio/*.mp3 aus
  publicDir: '../resources',
});
