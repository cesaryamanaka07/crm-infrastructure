import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'
import './dark-mode.css'
import './dark-mode-overrides.css'
import './agendamento-postagem.css'

export const THEME_STORAGE_KEY = 'theme'
export const THEME_COLORS_STORAGE_KEY = 'theme-dark-colors'
const temaSalvo = localStorage.getItem(THEME_STORAGE_KEY)
const temaInicial = ['light', 'dark', 'custom'].includes(temaSalvo) ? temaSalvo : 'light'
document.documentElement.dataset.theme = temaInicial
document.documentElement.dataset.themePreference = temaSalvo || 'light'
if (temaInicial === 'custom') {
  try { const cores = JSON.parse(localStorage.getItem(THEME_COLORS_STORAGE_KEY) || '{}'); Object.entries(cores).forEach(([nome, valor]) => { if (typeof valor === 'string') document.documentElement.style.setProperty(`--${nome}`, valor) }) } catch { /* preferência inválida */ }
}
ReactDOM.createRoot(document.getElementById('root')).render(<React.StrictMode><App /></React.StrictMode>)
