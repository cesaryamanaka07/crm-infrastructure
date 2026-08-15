import { useEffect, useState } from 'react'
import { Pencil, Plus, Save, Trash2, Users, X } from 'lucide-react'
import Sidebar from '../components/Sidebar'
import { atualizarCliente, criarCliente, excluirCliente, listarClientes } from '../api/clientesService'

function Clientes() {
  const [clientes, setClientes] = useState([])
  const [nome, setNome] = useState('')
  const [editando, setEditando] = useState(null)
  const [aberto, setAberto] = useState(false)
  const [mensagem, setMensagem] = useState('')

  useEffect(() => { listarClientes().then(setClientes).catch((e) => setMensagem(e.message)) }, [])

  async function salvar(evento) {
    evento.preventDefault(); setMensagem('')
    try {
      const salvo = editando ? await atualizarCliente(editando, { nome }) : await criarCliente({ nome })
      setClientes((atuais) => (editando ? atuais.map((item) => item.id === salvo.id ? salvo : item) : [...atuais, salvo]).sort((a, b) => a.nome.localeCompare(b.nome)))
      setNome(''); setEditando(null); setAberto(false); setMensagem('Cliente salvo com sucesso.')
    } catch (e) { setMensagem(e.message) }
  }

  function editar(cliente) { setNome(cliente.nome); setEditando(cliente.id); setAberto(true) }

  async function remover(id) {
    if (!window.confirm('Excluir este cliente?')) return
    try { await excluirCliente(id); setClientes((atuais) => atuais.filter((item) => item.id !== id)); setMensagem('Cliente excluído.') }
    catch (e) { setMensagem(e.message) }
  }

  return <div className="layout-app"><Sidebar /><main className="conteudo-principal pagina-conteudo">
    <header className="topo-pagina"><div><h1>Clientes</h1><p>Cadastre seus clientes para conectar as redes sociais deles futuramente.</p></div>
      <button className="botao-primario" onClick={() => { setNome(''); setEditando(null); setAberto(true) }}><Plus size={16} /> Novo cliente</button>
    </header>
    {mensagem && <p className="mensagem-integracao">{mensagem}</p>}
    {aberto && <form className="formulario-cliente" onSubmit={salvar}>
      <div className="cabecalho-formulario-cliente"><h2>{editando ? 'Editar cliente' : 'Novo cliente'}</h2><button type="button" className="botao-icone-remover" onClick={() => setAberto(false)}><X /></button></div>
      <label>Nome do cliente<input required minLength="2" value={nome} onChange={(e) => setNome(e.target.value)} /></label>
      <button className="botao-primario" type="submit"><Save size={16} /> Salvar cliente</button>
    </form>}
    <section className="lista-clientes">
      {clientes.length === 0 && <p>Nenhum cliente cadastrado.</p>}
      {clientes.map((cliente) => <article className="cartao-cliente" key={cliente.id}>
        <div className="cabecalho-cliente"><div className="nome-cliente"><Users size={19} /><div><h2>{cliente.nome}</h2><small>Redes sociais ainda não conectadas</small></div></div>
          <div><button className="botao-icone-remover" onClick={() => editar(cliente)}><Pencil size={16} /></button><button className="botao-icone-remover" onClick={() => remover(cliente.id)}><Trash2 size={16} /></button></div>
        </div>
      </article>)}
    </section>
  </main></div>
}

export default Clientes
