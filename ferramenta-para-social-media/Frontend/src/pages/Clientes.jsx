import { useEffect, useState } from 'react'
import { Cloud, Facebook, Instagram, Linkedin, Pencil, Plus, Save, Trash2, Users, X } from 'lucide-react'
import Sidebar from '../components/Sidebar'
import { atualizarCliente, criarCliente, desconectarGoogleCliente, excluirCliente, iniciarGoogleCliente, listarClientes } from '../api/clientesService'
import { listarConexoes } from '../api/socialService'
import { definirClienteAtivo, obterClienteAtivo } from '../utils/clienteAtivo'

const REDES = {
  facebook_page: { nome: 'Facebook Página', Icone: Facebook },
  facebook_profile: { nome: 'Facebook Perfil', Icone: Facebook },
  instagram: { nome: 'Instagram', Icone: Instagram },
  linkedin: { nome: 'LinkedIn', Icone: Linkedin },
}

function Clientes() {
  const [clientes, setClientes] = useState([])
  const [nome, setNome] = useState('')
  const [editando, setEditando] = useState(null)
  const [aberto, setAberto] = useState(false)
  const [mensagem, setMensagem] = useState('')
  const [conexoes, setConexoes] = useState([])
  const [clienteAtivo, setClienteAtivo] = useState(obterClienteAtivo())

  function ativar(cliente) { definirClienteAtivo(cliente.id); setClienteAtivo(cliente.id); setMensagem(`${cliente.nome} definido como cliente ativo em toda a ferramenta.`) }

  useEffect(() => {
    Promise.all([listarClientes(), listarConexoes()]).then(([listaClientes, listaConexoes]) => {
      setClientes(listaClientes); setConexoes(listaConexoes)
    }).catch((e) => setMensagem(e.message))
  }, [])
  useEffect(() => { const s=new URLSearchParams(location.search).get('google'); if(s){setMensagem(s==='conectado'?'Conta Google conectada ao cliente.':s==='cancelado'?'Conexão Google cancelada.':'Falha ao conectar a conta Google.');history.replaceState({},'',location.pathname)} },[])
  async function conectarGoogle(id,e){e.stopPropagation();try{const {url}=await iniciarGoogleCliente(id);location.href=url}catch(erro){setMensagem(erro.message)}}
  async function desconectarGoogle(id,e){e.stopPropagation();if(!confirm('Desconectar a conta Google deste cliente?'))return;await desconectarGoogleCliente(id);setClientes(await listarClientes());setMensagem('Conta Google desconectada.')}

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
      {clientes.map((cliente) => { const contas = conexoes.filter((item) => item.cliente_id === cliente.id); return <article className={`cartao-cliente ${clienteAtivo === cliente.id ? 'cliente-global-ativo' : ''}`} key={cliente.id} onClick={() => ativar(cliente)}>
        <div className="cabecalho-cliente"><div className="nome-cliente"><Users size={19} /><div><h2>{cliente.nome}</h2><small>{contas.length} conta(s) conectada(s)</small></div></div>
          <div>{clienteAtivo === cliente.id && <span className="selo-cliente-ativo">Ativo</span>}<button className="botao-icone-remover" onClick={(e) => { e.stopPropagation(); editar(cliente) }}><Pencil size={16} /></button><button className="botao-icone-remover" onClick={(e) => { e.stopPropagation(); remover(cliente.id) }}><Trash2 size={16} /></button></div>
        </div>
        <div className="chips-redes-cliente">
          <div className="cliente-google"><Cloud size={16}/>{cliente.google_conectado?<><span>Google: {cliente.google_email}</span><button className="botao-secundario" onClick={(e)=>conectarGoogle(cliente.id,e)}>Trocar</button><button className="botao-secundario" onClick={(e)=>desconectarGoogle(cliente.id,e)}>Desconectar</button></>:<><span>Google não conectado</span><button className="botao-primario" onClick={(e)=>conectarGoogle(cliente.id,e)}>Conectar Google</button></>}</div>
          {contas.length === 0 ? <small>Nenhuma rede social conectada.</small> : contas.map((conta) => {
            const rede = REDES[conta.provider] || { nome: conta.provider, Icone: Users }; const Icone = rede.Icone
            return <span className="chip-rede-cliente" key={conta.id}><Icone size={15} /> {rede.nome}: {conta.nome}</span>
          })}
        </div>
      </article> })}
    </section>
  </main></div>
}

export default Clientes
