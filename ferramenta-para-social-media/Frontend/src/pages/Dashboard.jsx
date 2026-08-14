import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Eye, Heart, TrendingUp } from 'lucide-react'
import { buscarUsuarioLogado } from '../api/authService'
import Sidebar from '../components/Sidebar'

// Dados de exemplo (mock), só para termos algo visual enquanto o
// metrics-service ainda não existe. Quando ele estiver pronto, isso
// vira uma chamada de API real, igual buscarUsuarioLogado().
const METRICAS_EXEMPLO = {
  visualizacoes: 48200,
  curtidas: 3150,
  seguidoresGanhos: 214,
}

const TOP_POSTS_EXEMPLO = [
  { id: 1, titulo: 'Como organizar sua rotina de conteúdo', visualizacoes: 12400, curtidas: 890 },
  { id: 2, titulo: '5 erros que travam seu crescimento', visualizacoes: 9800, curtidas: 720 },
  { id: 3, titulo: 'Bastidores: como crio meus posts', visualizacoes: 8100, curtidas: 640 },
  { id: 4, titulo: 'Reels que realmente funcionam em 2026', visualizacoes: 6300, curtidas: 510 },
  { id: 5, titulo: 'O que aprendi em 1 ano postando todo dia', visualizacoes: 5900, curtidas: 470 },
]

function formatarNumero(numero) {
  return numero.toLocaleString('pt-BR')
}

function Dashboard() {
  const [usuario, setUsuario] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    const token = localStorage.getItem('access_token')

    if (!token) {
      navigate('/login')
      return
    }

    buscarUsuarioLogado(token)
      .then(setUsuario)
      .catch(() => {
        localStorage.removeItem('access_token')
        navigate('/login')
      })
  }, [navigate])

  if (!usuario) {
    return <div className="tela-carregando">Carregando...</div>
  }

  return (
    <div className="layout-app">
      <Sidebar />

      <main className="conteudo-principal">
        <header className="topo-pagina">
          <h1>Dashboard</h1>
          <button className="botao-primario" onClick={() => navigate('/criar-conteudo')}>
            + Novo Post
          </button>
        </header>

        <section className="grade-metricas">
          <div className="cartao-metrica">
            <div className="icone-metrica"><Eye size={20} /></div>
            <div>
              <p className="rotulo-metrica">Visualizações</p>
              <p className="valor-metrica">{formatarNumero(METRICAS_EXEMPLO.visualizacoes)}</p>
            </div>
          </div>

          <div className="cartao-metrica">
            <div className="icone-metrica"><Heart size={20} /></div>
            <div>
              <p className="rotulo-metrica">Curtidas</p>
              <p className="valor-metrica">{formatarNumero(METRICAS_EXEMPLO.curtidas)}</p>
            </div>
          </div>

          <div className="cartao-metrica">
            <div className="icone-metrica"><TrendingUp size={20} /></div>
            <div>
              <p className="rotulo-metrica">Novos seguidores</p>
              <p className="valor-metrica">{formatarNumero(METRICAS_EXEMPLO.seguidoresGanhos)}</p>
            </div>
          </div>
        </section>

        <h2 className="titulo-secao">Top 5 posts</h2>
        <section className="grade-posts">
          {TOP_POSTS_EXEMPLO.map((post, indice) => (
            <div className="cartao-post" key={post.id}>
              <div className="cabecalho-cartao-post">
                <span className="selo-posicao">#{indice + 1}</span>
              </div>
              <h3>{post.titulo}</h3>
              <div className="estatisticas-post">
                <span><Eye size={14} /> {formatarNumero(post.visualizacoes)}</span>
                <span><Heart size={14} /> {formatarNumero(post.curtidas)}</span>
              </div>
            </div>
          ))}
        </section>
      </main>
    </div>
  )
}

export default Dashboard