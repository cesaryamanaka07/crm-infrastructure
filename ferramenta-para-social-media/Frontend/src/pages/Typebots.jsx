import { useEffect, useState } from 'react'
import { Bot, Eye, Plus, Save, Trash2 } from 'lucide-react'
import Sidebar from '../components/Sidebar'
import { listarClientes } from '../api/clientesService'
import { obterIntegracoes, salvarTypebots } from '../api/automationService'
import { escolherClienteInicial } from '../utils/clienteAtivo'

export default function Typebots() {
  const [clientes, setClientes] = useState([]); const [clienteId, setClienteId] = useState(''); const [bots, setBots] = useState([]); const [selecionado, setSelecionado] = useState(null); const [mensagem, setMensagem] = useState('')
  useEffect(() => { listarClientes().then((lista) => { setClientes(lista); setClienteId(escolherClienteInicial(lista)) }).catch((e) => setMensagem(e.message)) }, [])
  useEffect(() => { if (clienteId) obterIntegracoes(clienteId).then((d) => { setBots(d.typebot.bots || []); setSelecionado(null) }).catch((e) => setMensagem(e.message)) }, [clienteId])
  function adicionar() { setBots((atual) => [...atual, { nome: 'Novo chatbot', url_publica: '' }]) }
  function alterar(indice, campo, valor) { setBots((atual) => atual.map((b, i) => i === indice ? { ...b, [campo]: valor } : b)) }
  async function salvar() { try { const dados = await salvarTypebots(clienteId, bots.map(({ nome, url_publica }) => ({ nome, url_publica }))); setBots(dados); setMensagem('Chatbots salvos para este cliente.') } catch (e) { setMensagem(e.message) } }
  return <div className="layout-app"><Sidebar/><main className="conteudo-principal pagina-conteudo integracao-pagina"><header className="topo-pagina"><div><h1>Chatbots</h1><p>Cadastre e visualize os Typebots publicados de cada cliente.</p></div><button className="botao-primario" onClick={adicionar}><Plus size={17}/> Chatbot</button></header>
    <label className="integracao-cliente">Cliente<select value={clienteId} onChange={(e) => setClienteId(e.target.value)}>{clientes.map((c) => <option key={c.id} value={c.id}>{c.nome}</option>)}</select></label>{mensagem && <p className="mensagem-integracao">{mensagem}</p>}
    <div className="typebot-layout"><section className="integracao-card"><div className="integracao-titulo"><Bot size={26}/><div><h2>Typebots do cliente</h2><p>Use o endereço publicado em bot.cesaryamanaka.com.br.</p></div></div>{bots.length === 0 && <p>Nenhum chatbot cadastrado.</p>}{bots.map((bot, i) => <article className="typebot-item" key={bot.id || i}><input value={bot.nome} onChange={(e) => alterar(i, 'nome', e.target.value)} aria-label="Nome do chatbot"/><input value={bot.url_publica} onChange={(e) => alterar(i, 'url_publica', e.target.value)} placeholder="Endereço público do chatbot" aria-label="Endereço do chatbot"/><button title="Visualizar" onClick={() => setSelecionado(bot)} disabled={!bot.url_publica}><Eye size={18}/></button><button title="Excluir" onClick={() => setBots((x) => x.filter((_, n) => n !== i))}><Trash2 size={18}/></button></article>)}<button className="botao-primario" onClick={salvar} disabled={!bots.length}><Save size={17}/> Salvar</button></section>
      <section className="integracao-card typebot-preview"><h2>Pré-visualização</h2>{selecionado?.url_publica ? <iframe src={selecionado.url_publica} title={`Pré-visualização de ${selecionado.nome}`} allow="clipboard-write; microphone"/> : <p>Selecione o ícone de visualização de um chatbot.</p>}</section></div></main></div>
}
