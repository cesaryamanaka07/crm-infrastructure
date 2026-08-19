import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { BarChart3, Facebook, Instagram, LoaderCircle, RefreshCw, Users } from 'lucide-react'
import { buscarUsuarioLogado } from '../api/authService'
import { listarClientes } from '../api/clientesService'
import { buscarInsights, listarConexoes } from '../api/socialService'
import Sidebar from '../components/Sidebar'
import { obterClienteAtivo } from '../utils/clienteAtivo'

const REDES = {
  facebook_page: { nome: 'Facebook Página', Icone: Facebook }, facebook_profile: { nome: 'Facebook Perfil', Icone: Facebook },
  instagram: { nome: 'Instagram', Icone: Instagram }, linkedin: { nome: 'LinkedIn', Icone: BarChart3 },
}
const ROTULOS = {
  seguidores: 'Seguidores', seguindo: 'Seguindo', publicacoes: 'Publicações', reach: 'Alcance', views: 'Visualizações',
  profile_views: 'Visitas ao perfil', accounts_engaged: 'Contas engajadas', total_interactions: 'Interações',
  curtidas_pagina: 'Curtidas da página', page_impressions: 'Impressões', page_post_engagements: 'Engajamentos',
  page_views_total: 'Visualizações da página',
  impressoes: 'Impressões', alcance: 'Alcance', reacoes: 'Reações', comentarios: 'Comentários', compartilhamentos: 'Compartilhamentos',
}
const PROVEDORES_COM_INSIGHTS = ['instagram', 'facebook_page']

function Dashboard() {
  const [usuario, setUsuario] = useState(null)
  const [clientes, setClientes] = useState([])
  const [conexoes, setConexoes] = useState([])
  const [selecionadas, setSelecionadas] = useState([])
  const [insights, setInsights] = useState([])
  const [carregandoInsights, setCarregandoInsights] = useState(false)
  const [mensagem, setMensagem] = useState('')
  const navigate = useNavigate()

  async function atualizarDashboard() {
    setCarregandoInsights(true); setMensagem('')
    try {
      const [listaClientes, listaConexoes] = await Promise.all([listarClientes(), listarConexoes()])
      const clienteAtivo = obterClienteAtivo()
      const clientesVisiveis = clienteAtivo ? listaClientes.filter((item) => item.id === clienteAtivo) : listaClientes
      const contas = listaConexoes.filter((item) => PROVEDORES_COM_INSIGHTS.includes(item.provider) && (!clienteAtivo || item.cliente_id === clienteAtivo))
      const idsAtuais = contas.map((item) => item.id)
      setClientes(clientesVisiveis); setConexoes(contas); setSelecionadas(idsAtuais)
      if (!idsAtuais.length) setInsights([])
    } catch (e) { setMensagem(e.message) }
    finally { setCarregandoInsights(false) }
  }

  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (!token) { navigate('/login'); return }
    buscarUsuarioLogado(token).then(setUsuario).catch(() => { localStorage.removeItem('access_token'); navigate('/login') })
    atualizarDashboard()
  }, [navigate])

  useEffect(() => {
    if (!selecionadas.length) { setInsights([]); return }
    let cancelado = false
    setCarregandoInsights(true); setMensagem('')
    buscarInsights(selecionadas).then((dados) => { if (!cancelado) setInsights(dados) })
      .catch((e) => { if (!cancelado) setMensagem(e.message) })
      .finally(() => { if (!cancelado) setCarregandoInsights(false) })
    return () => { cancelado = true }
  }, [selecionadas])

  const insightsPorId = useMemo(() => Object.fromEntries(insights.map((item) => [item.id, item])), [insights])
  function alternarConta(id) { setSelecionadas((atuais) => atuais.includes(id) ? atuais.filter((item) => item !== id) : [...atuais, id]) }
  if (!usuario) return <div className="tela-carregando">Carregando...</div>
  return <div className="layout-app"><Sidebar /><main className="conteudo-principal">
    <header className="topo-pagina"><div><h1>Dashboard</h1><p>Insights separados por cliente.</p></div><div className="acoes-topo"><button className="botao-secundario botao-atualizar" onClick={atualizarDashboard} disabled={carregandoInsights}><RefreshCw className={carregandoInsights ? 'icone-girando' : ''} size={16} /> Atualizar dados</button><button className="botao-primario" onClick={() => navigate('/criar-conteudo')}>+ Novo Post</button></div></header>
    {mensagem && <p className="mensagem-integracao">{mensagem}</p>}
    {carregandoInsights && <span className="status-carregando-insights"><LoaderCircle className="icone-girando" size={16} /> Atualizando insights...</span>}
    <h2 className="titulo-secao">Clientes</h2><section className="dashboard-clientes">
      {clientes.length === 0 && <p>Nenhum cliente cadastrado. Use a aba Clientes para começar.</p>}
      {clientes.map((cliente) => { const contas = conexoes.filter((item) => item.cliente_id === cliente.id); return <article className="dashboard-cliente" key={cliente.id}><div className="nome-cliente"><Users size={19} /><div><h3>{cliente.nome}</h3><p>{contas.length} conta(s) conectada(s)</p></div></div><div className="grade-insights-contas">
        {contas.length === 0 && <p>Nenhuma conta de Instagram ou Facebook Página conectada.</p>}{contas.map((conta) => { const rede = REDES[conta.provider] || { nome: conta.provider, Icone: BarChart3 }; const Icone = rede.Icone; const dados = insightsPorId[conta.id]; return <section className="cartao-insight-conta" key={conta.id}><header><Icone size={19} /><div><strong>{conta.nome}</strong><small>{rede.nome}</small></div></header>{!selecionadas.includes(conta.id) ? <p>Conta não selecionada para consulta.</p> : !dados ? <p>Carregando dados da conta...</p> : dados.status !== 'ok' ? <><p className="erro-insight">{dados.erro}</p>{conta.provider === 'instagram' && <button className="botao-secundario" onClick={() => navigate('/redes-sociais')}>Reconectar Instagram</button>}</> : <><div className="metricas-conta">{Object.entries(dados.metricas).map(([chave, valor]) => <div key={chave}><small>{ROTULOS[chave] || chave}</small><strong>{valor ?? 'Não disponível'}</strong></div>)}</div><div className="melhores-conteudos"><h4>5 melhores conteúdos</h4>{dados.melhores_conteudos?.length ? <ol>{dados.melhores_conteudos.map((conteudo) => <li key={conteudo.id}>{conteudo.thumbnail_url && <img src={conteudo.thumbnail_url} alt={`Capa de ${conteudo.tipo}`} loading="lazy" referrerPolicy="no-referrer" />}<div className="dados-melhor-conteudo"><span className="tipo-conteudo">{conteudo.tipo}</span><strong>{conteudo.titulo}</strong><small>{conteudo.curtidas} curtidas · {conteudo.comentarios} comentários{conteudo.compartilhamentos != null ? ` · ${conteudo.compartilhamentos} compartilhamentos` : ''}</small>{conteudo.url && <a href={conteudo.url} target="_blank" rel="noreferrer">Abrir publicação</a>}</div></li>)}</ol> : <p>Nenhuma publicação disponível para análise.</p>}</div></>}</section> })}
      </div></article> })}
    </section>
  </main></div>
}
export default Dashboard
