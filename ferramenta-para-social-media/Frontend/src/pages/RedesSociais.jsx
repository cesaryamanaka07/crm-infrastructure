import { useEffect, useState } from 'react'
import { CheckCircle2, Facebook, Instagram, Linkedin, Link2, LoaderCircle, Unlink } from 'lucide-react'
import Sidebar from '../components/Sidebar'
import { desconectarRede, iniciarConexao, listarConexoes, selecionarConexao } from '../api/socialService'
import { listarClientes } from '../api/clientesService'
import { escolherClienteInicial } from '../utils/clienteAtivo'

const REDES = [
  { provider: 'facebook_page', nome: 'Facebook Página', descricao: 'Conecte Páginas administradas para métricas e futura publicação automática.', Icone: Facebook },
  { provider: 'facebook_profile', nome: 'Facebook Perfil Pessoal', descricao: 'Autenticação e identificação básica. A Meta não permite publicação automática no perfil pessoal.', Icone: Facebook },
  { provider: 'instagram', nome: 'Instagram', descricao: 'Conecte diretamente uma conta profissional do Instagram.', Icone: Instagram },
  { provider: 'linkedin', nome: 'LinkedIn', descricao: 'Conecte seu perfil para publicar conteúdos autorizados.', Icone: Linkedin },
]

function RedesSociais() {
  const [conexoes, setConexoes] = useState([])
  const [clientes, setClientes] = useState([])
  const [clienteId, setClienteId] = useState('')
  const [carregando, setCarregando] = useState(true)
  const [processando, setProcessando] = useState('')
  const [mensagem, setMensagem] = useState('')

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const conectado = params.get('conectado')
    const erro = params.get('erro')
    const rede = params.get('rede')
    if ((conectado || erro) && (window.opener || window.name === 'social-oauth')) {
      if (window.opener) window.opener.postMessage({ type: 'social-oauth-result', conectado, erro, rede }, window.location.origin)
      window.close()
      return
    }
    if (conectado) setMensagem('Rede social conectada com sucesso.')
    if (erro) {
      const prefixo = rede ? `${rede[0].toUpperCase()}${rede.slice(1)}: ` : ''
      setMensagem(`${prefixo}${erro}`)
    }
    if (params.has('conectado') || params.has('erro')) {
      window.history.replaceState({}, '', window.location.pathname)
    }
    Promise.all([listarConexoes(), listarClientes()]).then(([listaConexoes, listaClientes]) => {
      setConexoes(listaConexoes)
      setClientes(listaClientes)
      setClienteId(escolherClienteInicial(listaClientes))
    }).catch((e) => setMensagem(e.message)).finally(() => setCarregando(false))
  }, [])

  useEffect(() => {
    function receberResultadoOAuth(evento) {
      if (evento.origin !== window.location.origin || evento.data?.type !== 'social-oauth-result') return
      const { conectado, erro, rede } = evento.data
      if (conectado) {
        setMensagem('Rede social conectada com sucesso.')
        listarConexoes().then(setConexoes).catch((e) => setMensagem(e.message))
      } else if (erro) {
        const prefixo = rede ? `${rede[0].toUpperCase()}${rede.slice(1)}: ` : ''
        setMensagem(`${prefixo}${erro}`)
      }
      setProcessando('')
    }
    window.addEventListener('message', receberResultadoOAuth)
    return () => window.removeEventListener('message', receberResultadoOAuth)
  }, [])

  async function conectar(provider) {
    if (!clienteId) { setMensagem('Selecione um cliente antes de conectar a rede social.'); return }
    const popup = window.open('', 'social-oauth', 'popup=yes,width=620,height=760,resizable=yes,scrollbars=yes')
    setProcessando(provider); setMensagem('')
    try {
      const data = await iniciarConexao(provider, clienteId)
      if (popup) {
        popup.location.assign(data.authorization_url)
        const acompanharPopup = window.setInterval(() => {
          if (!popup.closed) return
          window.clearInterval(acompanharPopup)
          listarConexoes().then(setConexoes).catch((e) => setMensagem(e.message)).finally(() => setProcessando(''))
        }, 700)
      }
      else window.location.assign(data.authorization_url)
    } catch (e) {
      if (popup) popup.close()
      setMensagem(e.message); setProcessando('')
    }
  }

  async function remover(id) {
    setProcessando(id)
    try { await desconectarRede(id); setConexoes((atuais) => atuais.filter((item) => item.id !== id)); setMensagem('Rede desconectada.') }
    catch (e) { setMensagem(e.message) } finally { setProcessando('') }
  }

  async function selecionar(id, provider) {
    setProcessando(id); setMensagem('')
    try {
      await selecionarConexao(id)
      setConexoes((atuais) => atuais.map((item) => ({
        ...item,
        selecionada: item.provider === provider && item.cliente_id === clienteId ? item.id === id : item.selecionada,
      })))
      setMensagem('Conta selecionada para uso nessa rede social.')
    } catch (e) { setMensagem(e.message) } finally { setProcessando('') }
  }

  return <div className="layout-app"><Sidebar /><main className="conteudo-principal pagina-conteudo">
    <header className="topo-pagina"><div><h1>Redes sociais</h1><p>Autorize as contas que serão usadas pela ferramenta.</p></div></header>
    {mensagem && <p className="mensagem-integracao">{mensagem}</p>}
    <div className="seletor-cliente-conexao campo-formulario">
      <label htmlFor="cliente-conexao">Cliente das conexões</label>
      <select id="cliente-conexao" value={clienteId} onChange={(evento) => setClienteId(evento.target.value)} required>
        <option value="">Selecione o cliente</option>
        {clientes.map((cliente) => <option key={cliente.id} value={cliente.id}>{cliente.nome}</option>)}
      </select>
      <small>As contas conectadas abaixo pertencerão ao cliente selecionado.</small>
    </div>
    <div className="grade-redes-sociais">
      {REDES.map(({ provider, nome, descricao, Icone, iconeExtra: IconeExtra }) => {
        const contas = conexoes.filter((item) => item.provider === provider && item.cliente_id === clienteId)
        return <article key={provider} className="cartao-rede-social">
          <div className="icones-rede"><Icone size={28} />{IconeExtra && <IconeExtra size={24} />}</div>
          <div><h2>{nome}</h2><p>{descricao}</p></div>
          {carregando ? <LoaderCircle className="icone-girando" /> : <>
            {contas.length > 0 && <div className="lista-contas-sociais">
              {contas.map((conta) => <div key={conta.id} className={`conta-social ${conta.selecionada ? 'conta-social-ativa' : ''}`}>
                <button className="seletor-conta" onClick={() => selecionar(conta.id, provider)} disabled={conta.selecionada || processando === conta.id}>
                  <CheckCircle2 size={18} />
                  <span><strong>{conta.nome}</strong><small>{conta.tipo_token === 'temporario' ? 'Conexão temporária — Acesso Avançado pendente' : conta.selecionada ? 'Selecionada' : 'Selecionar esta conta'}</small></span>
                </button>
                <button className="botao-icone-remover" aria-label={`Desconectar ${conta.nome}`} onClick={() => remover(conta.id)} disabled={processando === conta.id}><Unlink size={16} /></button>
              </div>)}
            </div>}
            {contas.length === 0 && <small>Nenhuma conta conectada.</small>}
            {provider === 'instagram' ? <div className="acoes-conexao-instagram">
              <button className={contas.length ? 'botao-secundario' : 'botao-primario'} onClick={() => conectar('instagram')} disabled={Boolean(processando)}>
                {processando === 'instagram' ? <LoaderCircle className="icone-girando" size={16} /> : <Instagram size={16} />}
                Entrar com Instagram
              </button>
              <button className="botao-secundario" onClick={() => conectar('instagram_facebook')} disabled={Boolean(processando)}>
                {processando === 'instagram_facebook' ? <LoaderCircle className="icone-girando" size={16} /> : <Facebook size={16} />}
                Conectar via Facebook
              </button>
              <small>Use o botão via Facebook quando o Instagram profissional estiver vinculado a uma Página administrada. A conta pessoal do Facebook será usada apenas para autorizar o acesso.</small>
            </div> : <button className={contas.length ? 'botao-secundario' : 'botao-primario'} onClick={() => conectar(provider)} disabled={processando === provider}>
              {processando === provider ? <LoaderCircle className="icone-girando" size={16} /> : <Link2 size={16} />}
              {contas.length ? 'Conectar outra conta' : 'Conectar'}
            </button>}
          </>}
        </article>
      })}
    </div>
  </main></div>
}

export default RedesSociais
