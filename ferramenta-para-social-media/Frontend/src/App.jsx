import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import CriarConteudo from './pages/CriarConteudo'
import Marca from './pages/Marca'
import Midias from './pages/Midias'
import RedesSociais from './pages/RedesSociais'
import Clientes from './pages/Clientes'
import ArsenalCopy from './pages/ArsenalCopy'
import ConteudosCriados from './pages/ConteudosCriados'

// Placeholder simples para páginas que ainda vamos construir
function EmConstrucao({ titulo }) {
  return (
    <div style={{ padding: '2.5rem', color: '#6b7280' }}>
      <h1 style={{ color: '#111827', marginBottom: '0.5rem' }}>{titulo}</h1>
      <p>Essa página ainda está em construção.</p>
    </div>
  )
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/clientes" element={<Clientes />} />
        <Route path="/redes-sociais" element={<RedesSociais />} />
        <Route path="/criar-conteudo" element={<CriarConteudo />} />
        <Route path="/conteudos-criados" element={<ConteudosCriados />} />
        <Route path="/marca" element={<Marca />} />
        <Route path="/arsenal-copy" element={<ArsenalCopy />} />
        <Route path="/midias" element={<Midias />} />
        {/* Qualquer outra URL redireciona para o login por enquanto */}
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
