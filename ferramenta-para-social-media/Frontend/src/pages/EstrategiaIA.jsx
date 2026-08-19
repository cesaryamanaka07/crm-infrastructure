import { useEffect, useState } from 'react'
import { Download, LoaderCircle, Sparkles } from 'lucide-react'
import Sidebar from '../components/Sidebar'
import { listarClientes } from '../api/clientesService'
import { gerarEstrategia, obterEstrategia, obterCacheConteudo } from '../api/contentService'
import { escolherClienteInicial } from '../utils/clienteAtivo'

function Bloco({ nome, valor }) {
  const titulo = String(nome).replaceAll('_', ' ')
  if (Array.isArray(valor)) return <section className="bloco-estrategia"><h3>{titulo}</h3><div className="lista-estrategia">{valor.map((item, indice) => typeof item === 'object' ? <Bloco key={indice} nome={`Item ${indice + 1}`} valor={item} /> : <p key={indice}>{item}</p>)}</div></section>
  if (valor && typeof valor === 'object') return <section className="bloco-estrategia"><h3>{titulo}</h3>{Object.entries(valor).map(([chave, item]) => <Bloco key={chave} nome={chave} valor={item} />)}</section>
  return <div className="campo-estrategia"><strong>{titulo}</strong><p>{String(valor ?? '')}</p></div>
}

function EstrategiaIA({ tipo }) {
  const narrativa = tipo === 'narrativa'
  const titulo = narrativa ? 'Diagnóstico e Narrativa Estratégica' : 'Linha Editorial de Funil'
  const [clientes, setClientes] = useState([]); const [clienteId, setClienteId] = useState('')
  const [resultado, setResultado] = useState(null); const [gerando, setGerando] = useState(false); const [mensagem, setMensagem] = useState('')

  useEffect(() => { listarClientes().then((lista) => { setClientes(lista); setClienteId(escolherClienteInicial(lista)) }).catch((e) => setMensagem(e.message)) }, [])
  useEffect(() => {
    if (!clienteId) return
    const caminho = `/estrategias/${clienteId}/${tipo}`
    const cache = obterCacheConteudo(caminho)
    if (cache?.resultado) setResultado(cache.resultado)
    setMensagem('')
    obterEstrategia(clienteId, tipo).then((dados) => setResultado(dados.resultado)).catch((e) => { if (!cache) setMensagem(e.message) })
  }, [clienteId, tipo])
  async function gerar() { setGerando(true); setMensagem(''); try { const dados = await gerarEstrategia(clienteId, tipo); setResultado(dados.resultado); setMensagem('Estratégia criada e salva para este cliente.') } catch (e) { setMensagem(e.message) } finally { setGerando(false) } }
  function baixar() { const url = URL.createObjectURL(new Blob([JSON.stringify(resultado, null, 2)], { type: 'application/json' })); const link = document.createElement('a'); link.href = url; link.download = `${tipo}-${clienteId}.json`; link.click(); URL.revokeObjectURL(url) }

  return <div className="layout-app"><Sidebar /><main className="conteudo-principal pagina-conteudo"><header className="topo-pagina"><div><h1>{titulo}</h1><p>{narrativa ? 'Diagnostique a comunicação e construa a narrativa central de conversão.' : 'Transforme a narrativa em conteúdo para atração, nutrição e vendas.'}</p></div></header>
    <section className="controles-estrategia"><label>Cliente<select value={clienteId} onChange={(e) => setClienteId(e.target.value)}><option value="">Selecione</option>{clientes.map((cliente) => <option key={cliente.id} value={cliente.id}>{cliente.nome}</option>)}</select></label><button className="botao-primario" onClick={gerar} disabled={!clienteId || gerando}>{gerando ? <LoaderCircle className="icone-girando" size={17} /> : <Sparkles size={17} />}{resultado ? 'Gerar novamente' : `Gerar ${narrativa ? 'narrativa' : 'linha editorial'}`}</button>{resultado && <button className="botao-secundario" onClick={baixar}><Download size={16} />Baixar JSON</button>}</section>
    {mensagem && <p className="mensagem-integracao">{mensagem}</p>}{resultado ? <article className="resultado-estrategia">{Object.entries(resultado).map(([chave, valor]) => <Bloco key={chave} nome={chave} valor={valor} />)}</article> : <div className="estado-vazio"><Sparkles size={32} /><p>{narrativa ? 'A IA usará o Arsenal de Copy e as contas conectadas deste cliente.' : 'Gere primeiro a Narrativa Estratégica para criar a linha editorial.'}</p></div>}
  </main></div>
}
export default EstrategiaIA
