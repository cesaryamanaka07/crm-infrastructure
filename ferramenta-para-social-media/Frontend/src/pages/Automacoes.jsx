import { useEffect, useState } from 'react'
import { Bot, Facebook, Instagram } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import Sidebar from '../components/Sidebar'
import { listarClientes } from '../api/clientesService'
import { listarFluxos } from '../api/automationService'
import { escolherClienteInicial } from '../utils/clienteAtivo'

function Automacoes() {
  const [clientes, setClientes] = useState([]); const [fluxos, setFluxos] = useState([]); const [filtro, setFiltro] = useState(''); const [mensagem, setMensagem] = useState(''); const navigate = useNavigate()
  useEffect(() => { Promise.all([listarClientes(), listarFluxos()]).then(([c, f]) => { setClientes(c); setFluxos(f); setFiltro(escolherClienteInicial(c)) }).catch((e) => setMensagem(e.message)) }, [])
  const visiveis = filtro ? clientes.filter((c) => c.id === filtro) : clientes
  function abrir(fluxo) { navigate(`/automacao-${fluxo.canal}?cliente=${fluxo.cliente_id}&fluxo=${fluxo.id}`) }
  return <div className="layout-app"><Sidebar /><main className="conteudo-principal pagina-conteudo"><header className="topo-pagina"><div><h1>Todas as automações</h1><p>Fluxos de Facebook e Instagram organizados por cliente.</p></div></header>{mensagem && <p className="mensagem-integracao">{mensagem}</p>}<label className="filtro-contatos">Cliente<select value={filtro} onChange={(e) => setFiltro(e.target.value)}><option value="">Todos os clientes</option>{clientes.map((c) => <option key={c.id} value={c.id}>{c.nome}</option>)}</select></label><section className="lista-automacoes">{visiveis.map((cliente) => { const itens = fluxos.filter((f) => f.cliente_id === cliente.id); return <article className="grupo-automacoes" key={cliente.id}><h2>{cliente.nome}</h2>{itens.length === 0 && <p>Nenhuma automação criada.</p>}<div>{itens.map((f) => <button key={f.id} onClick={() => abrir(f)}>{f.canal === 'facebook' ? <Facebook size={20} /> : <Instagram size={20} />}<span><strong>{f.nome}</strong><small>{f.canal} · {f.status} · {f.blocos.length} bloco(s)</small></span><Bot size={18} /></button>)}</div></article> })}</section></main></div>
}
export default Automacoes
