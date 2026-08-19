import { useEffect, useState } from 'react'
import { Activity, ExternalLink, Plus, Power, RefreshCw, Workflow } from 'lucide-react'
import Sidebar from '../components/Sidebar'
import { listarClientes } from '../api/clientesService'
import { acionarN8nWorkflow, criarN8nWorkflow, listarN8nExecucoes, listarN8nWorkflows, vincularN8nWorkflows } from '../api/automationService'
import { escolherClienteInicial } from '../utils/clienteAtivo'

const N8N_URL = (import.meta.env.VITE_N8N_PUBLIC_URL || 'https://workflow.cesaryamanaka.com.br').replace(/\/$/, '')

export default function N8n() {
  const [clientes, setClientes] = useState([])
  const [clienteId, setClienteId] = useState('')
  const [workflows, setWorkflows] = useState([])
  const [execucoes, setExecucoes] = useState([])
  const [mensagem, setMensagem] = useState('')
  const [carregando, setCarregando] = useState(false)
  const [criando, setCriando] = useState(false)

  useEffect(() => {
    listarClientes()
      .then((lista) => { setClientes(lista); setClienteId(escolherClienteInicial(lista)) })
      .catch((e) => setMensagem(e.message))
  }, [])

  useEffect(() => { if (clienteId) carregar() }, [clienteId])

  async function carregar() {
    setCarregando(true)
    setMensagem('')
    try {
      const [w, e] = await Promise.all([listarN8nWorkflows(clienteId, true), listarN8nExecucoes(clienteId)])
      setWorkflows(w)
      setExecucoes(e)
    } catch (err) {
      setWorkflows([])
      setExecucoes([])
      setMensagem(err.message)
    } finally { setCarregando(false) }
  }

  async function criarWorkflow() {
    const nome = window.prompt('Nome do novo workflow no n8n:', 'WhatsApp - EvolutionAPI')?.trim()
    if (!nome) return
    setCriando(true)
    setMensagem('')
    try {
      await criarN8nWorkflow(clienteId, nome)
      setMensagem('Workflow criado no n8n e vinculado ao cliente. Abra o designer para editar os nós e publicar o fluxo.')
      await carregar()
    } catch (e) { setMensagem(e.message) } finally { setCriando(false) }
  }

  async function alternarVinculo(item) {
    const ids = workflows.map((w) => w.id === item.id ? { ...w, vinculado: !w.vinculado } : w).filter((w) => w.vinculado).map((w) => w.id)
    try {
      await vincularN8nWorkflows(clienteId, ids)
      setWorkflows((lista) => lista.map((w) => w.id === item.id ? { ...w, vinculado: !w.vinculado } : w))
      setMensagem(item.vinculado ? 'Workflow desvinculado deste cliente.' : 'Workflow vinculado ao cliente. As execuções dele aparecerão abaixo.')
      if (item.vinculado) setExecucoes((atuais) => atuais.filter((execucao) => execucao.workflowId !== item.id))
      else await carregar()
    } catch (e) { setMensagem(e.message) }
  }

  async function alternarAtivo(item) {
    try {
      await acionarN8nWorkflow(clienteId, item.id, item.active ? 'deactivate' : 'activate')
      await carregar()
    } catch (e) { setMensagem(e.message) }
  }

  function abrirDesigner(workflow) {
    if (!workflow?.id) {
      setMensagem('Este workflow não possui um ID válido para abrir o designer.')
      return
    }
    window.open(`${N8N_URL}/workflow/${encodeURIComponent(workflow.id)}`, '_blank', 'noopener,noreferrer')
  }

  return <div className="layout-app"><Sidebar/><main className="conteudo-principal pagina-conteudo integracao-pagina">
    <header className="topo-pagina"><div><h1>n8n</h1><p>Workflows e execuções do n8n associados aos clientes.</p></div><div className="acoes-topo"><a className="botao-secundario" href={N8N_URL} target="_blank" rel="noreferrer"><ExternalLink size={17}/> Abrir painel n8n</a><button className="botao-secundario" onClick={carregar} disabled={!clienteId || carregando}><RefreshCw size={17}/> Atualizar</button></div></header>
    <label className="integracao-cliente">Cliente<select value={clienteId} onChange={(e) => setClienteId(e.target.value)}><option value="">Selecione um cliente</option>{clientes.map((c) => <option key={c.id} value={c.id}>{c.nome}</option>)}</select></label>
    <div className="mensagem-integracao n8n-orientacao"><strong>Como a sincronização funciona</strong><p>Workflows criados diretamente no site do n8n aparecem aqui depois de clicar em <strong>Atualizar</strong>. Para organizar por cliente, marque o workflow como vinculado. As execuções exibidas abaixo são as dos workflows vinculados ao cliente selecionado.</p></div>
    {mensagem && <div className="mensagem-integracao"><strong>Integração n8n:</strong> {mensagem}<p>Para listar ou criar workflows, gere uma <code>N8N_API_KEY</code> no painel do n8n e configure-a no automation-service. A <code>N8N_ENCRYPTION_KEY</code> é exclusiva do servidor n8n.</p></div>}
    <section className="integracao-card"><div className="integracao-titulo"><Workflow size={26}/><div><h2>Workflows disponíveis</h2><p>Os workflows são lidos do n8n pela API. Use o designer externo para montar os nós e o botão Atualizar para trazer alterações recentes.</p></div><button className="botao-primario botao-n8n-criar" onClick={criarWorkflow} disabled={!clienteId || carregando || criando}><Plus size={17}/>{criando ? 'Criando...' : 'Criar workflow'}</button></div>{!carregando && !mensagem && workflows.length === 0 && <div className="estado-vazio"><p>Nenhum workflow disponível. Crie um workflow no n8n ou pela plataforma e clique em Atualizar.</p></div>}<div className="n8n-lista">{workflows.map((w) => <article key={w.id}><label><input type="checkbox" checked={w.vinculado} onChange={() => alternarVinculo(w)}/><span><strong>{w.name}</strong><small>ID {w.id}</small></span></label><span className={`status-pill ${w.active ? 'status-open' : ''}`}>{w.active ? 'Ativo' : 'Inativo'}</span><button className="botao-secundario" disabled={!w.vinculado} onClick={() => alternarAtivo(w)}><Power size={16}/>{w.active ? 'Pausar' : 'Ativar'}</button><button className="botao-secundario" onClick={() => abrirDesigner(w)}><ExternalLink size={16}/>Designer</button></article>)}</div></section>
    <section className="integracao-card"><div className="integracao-titulo"><Activity size={26}/><div><h2>Execuções recentes</h2><p>Histórico retornado pela API do n8n para os workflows vinculados ao cliente selecionado.</p></div></div><div className="n8n-execucoes">{execucoes.length === 0 && <p>Nenhuma execução encontrada para os workflows vinculados.</p>}{execucoes.map((e) => <article key={e.id}><strong>Execução #{e.id}</strong><span>{e.status || (e.finished ? 'concluída' : 'em andamento')}</span><small>{e.startedAt ? new Date(e.startedAt).toLocaleString('pt-BR') : ''}</small></article>)}</div></section>
  </main></div>
}
