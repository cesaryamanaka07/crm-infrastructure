import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Users } from 'lucide-react'
import { buscarUsuarioLogado } from '../api/authService'
import { listarClientes } from '../api/clientesService'
import Sidebar from '../components/Sidebar'

function Dashboard() {
  const [usuario, setUsuario] = useState(null)
  const [clientes, setClientes] = useState([])
  const navigate = useNavigate()

  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (!token) { navigate('/login'); return }
    buscarUsuarioLogado(token).then(setUsuario).catch(() => { localStorage.removeItem('access_token'); navigate('/login') })
    listarClientes().then(setClientes).catch(() => setClientes([]))
  }, [navigate])

  if (!usuario) return <div className="tela-carregando">Carregando...</div>

  return <div className="layout-app"><Sidebar /><main className="conteudo-principal">
    <header className="topo-pagina"><h1>Dashboard</h1><button className="botao-primario" onClick={() => navigate('/criar-conteudo')}>+ Novo Post</button></header>
    <section className="grade-metricas"><div className="cartao-metrica"><div className="icone-metrica"><Users size={20} /></div><div><p className="rotulo-metrica">Clientes</p><p className="valor-metrica">{clientes.length}</p></div></div></section>
    <h2 className="titulo-secao">Clientes</h2>
    <section className="dashboard-clientes">
      {clientes.length === 0 && <p>Nenhum cliente cadastrado. Use a aba Clientes para começar.</p>}
      {clientes.map((cliente) => <article className="dashboard-cliente" key={cliente.id}><div className="nome-cliente"><Users size={19} /><div><h3>{cliente.nome}</h3><p>As conexões sociais deste cliente serão adicionadas futuramente.</p></div></div></article>)}
    </section>
  </main></div>
}

export default Dashboard
