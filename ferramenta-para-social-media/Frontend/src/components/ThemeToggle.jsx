import { Moon, Sun } from 'lucide-react'
import { useState } from 'react'

function ThemeToggle() {
  const [tema, setTema] = useState(() => document.documentElement.dataset.theme || 'light')
  function alternar() {
    const novo = tema === 'dark' ? 'light' : 'dark'
    document.documentElement.dataset.theme = novo
    localStorage.setItem('theme', novo)
    setTema(novo)
  }
  return <button className="botao-tema" onClick={alternar} title={tema === 'dark' ? 'Usar tema claro' : 'Usar tema escuro'} aria-label="Alternar tema">{tema === 'dark' ? <Sun size={18} /> : <Moon size={18} />}</button>
}
export default ThemeToggle
