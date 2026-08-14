import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],

  server: {
    host: '0.0.0.0',
    port: 5173,
    strictPort: true,

    allowedHosts: [
      'meuappsm.cesaryamanaka.com.br',
    ],

    hmr: {
      protocol: 'wss',
      host: 'meuappsm.cesaryamanaka.com.br',
      clientPort: 443,
    },
  },
})