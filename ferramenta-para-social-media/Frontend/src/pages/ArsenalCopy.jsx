import { useEffect, useState } from 'react'
import { LoaderCircle, Save } from 'lucide-react'
import Sidebar from '../components/Sidebar'
import { listarClientes } from '../api/clientesService'
import { obterArsenal, salvarArsenal } from '../api/contentService'
import { GRUPOS_ARSENAL } from '../constants/arsenalCampos'

function ArsenalCopy() {
  const [clientes, setClientes] = useState([])
  const [clienteId, setClienteId] = useState('')
  const [informacoes, setInformacoes] = useState({})
  const [manualIa, setManualIa] = useState('')
  const [salvando, setSalvando] = useState(false)
  const [mensagem, setMensagem] = useState('')

  useEffect(() => {
    listarClientes().then((lista) => {
      setClientes(lista)
      if (lista[0]) setClienteId(lista[0].id)
    }).catch((erro) => setMensagem(erro.message))
  }, [])

  useEffect(() => {
    if (!clienteId) return
    setMensagem('')
    obterArsenal(clienteId).then((arsenal) => {
      setInformacoes(arsenal.informacoes || {})
      setManualIa(arsenal.manual_ia || '')
    }).catch((erro) => setMensagem(erro.message))
  }, [clienteId])

  async function enviar(evento) {
    evento.preventDefault(); setSalvando(true); setMensagem('')
    try {
      const arsenal = await salvarArsenal(clienteId, { informacoes, manual_ia: manualIa || null })
      setInformacoes(arsenal.informacoes || {})
      setMensagem('Arsenal de Copy salvo com sucesso.')
    } catch (erro) { setMensagem(erro.message) } finally { setSalvando(false) }
  }

  return <div className="layout-app"><Sidebar /><main className="conteudo-principal pagina-conteudo">
    <header className="topo-pagina"><div><h1>Arsenal de Copy</h1><p>Centralize a inteligência estratégica de cada cliente para orientar a IA.</p></div></header>
    {!clientes.length ? <p>Cadastre um cliente antes de criar o Arsenal de Copy.</p> : <form className="formulario-arsenal" onSubmit={enviar}>
      <div className="campo-formulario cartao-arsenal seletor-arsenal-cliente"><label>Cliente</label><select value={clienteId} onChange={(evento) => setClienteId(evento.target.value)}>{clientes.map((cliente) => <option key={cliente.id} value={cliente.id}>{cliente.nome}</option>)}</select></div>
      {GRUPOS_ARSENAL.map((grupo) => <fieldset key={grupo.titulo} className="cartao-arsenal grupo-arsenal"><legend>{grupo.titulo}</legend>{grupo.campos.map(([chave, rotulo]) => <label key={chave}><span>{rotulo}</span><textarea value={informacoes[chave] || ''} onChange={(evento) => setInformacoes((atual) => ({ ...atual, [chave]: evento.target.value }))} maxLength={10000} placeholder="Digite as informações conhecidas..." /></label>)}</fieldset>)}
      <fieldset className="cartao-arsenal grupo-arsenal manual-ia"><legend>Manual permanente para a IA</legend><p>Escreva regras, termos proibidos, padrões de escrita, estrutura, posicionamento e tudo que a IA deverá seguir para este cliente.</p><textarea value={manualIa} onChange={(evento) => setManualIa(evento.target.value)} maxLength={15000} placeholder="Ex.: nunca usar linguagem exagerada; preservar termos técnicos; sempre finalizar com uma pergunta..." /></fieldset>
      {mensagem && <p className="mensagem-integracao">{mensagem}</p>}
      <button className="botao-primario salvar-arsenal" disabled={salvando}>{salvando ? <LoaderCircle className="icone-girando" size={17} /> : <Save size={17} />}Salvar Arsenal de Copy</button>
    </form>}
  </main></div>
}

export default ArsenalCopy
