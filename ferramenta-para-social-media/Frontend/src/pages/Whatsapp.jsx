import { useEffect, useState } from 'react'
import { ExternalLink, LoaderCircle, MessageCircle, QrCode, RefreshCw, Trash2 } from 'lucide-react'
import Sidebar from '../components/Sidebar'
import { listarClientes } from '../api/clientesService'
import { criarWhatsapp, excluirWhatsapp, obterQrCodeWhatsapp, obterWhatsapp } from '../api/automationService'
import { escolherClienteInicial } from '../utils/clienteAtivo'

const TYPEBOT_BUILDER_URL = (import.meta.env.VITE_TYPEBOT_BUILDER_URL || 'https://chatbot.cesaryamanaka.com.br').replace(/\/$/, '')
const TYPEBOT_VIEWER_URL = (import.meta.env.VITE_TYPEBOT_VIEWER_URL || 'https://bot.cesaryamanaka.com.br').replace(/\/$/, '')

function qrImagem(dados) {
  const valor = dados?.base64 || dados?.qrcode?.base64 || dados?.data?.base64 || dados?.data?.qrcode?.base64 || dados?.code || dados?.pairingCode
  if (!valor) return ''
  return valor.startsWith('data:') ? valor : `data:image/png;base64,${valor}`
}

export default function Whatsapp() {
  const [clientes, setClientes] = useState([]); const [clienteId, setClienteId] = useState('')
  const [status, setStatus] = useState(null); const [qr, setQr] = useState(''); const [mensagem, setMensagem] = useState(''); const [carregando, setCarregando] = useState(false)
  useEffect(() => { listarClientes().then((lista) => { setClientes(lista); setClienteId(escolherClienteInicial(lista)) }).catch((e) => setMensagem(e.message)) }, [])
  useEffect(() => { if (clienteId) atualizar() }, [clienteId])
  async function atualizar() { setCarregando(true); setMensagem(''); try { setStatus(await obterWhatsapp(clienteId)) } catch (e) { setMensagem(e.message) } finally { setCarregando(false) } }
  async function conectar() { setCarregando(true); setMensagem(''); try { await criarWhatsapp(clienteId); const dados = await obterQrCodeWhatsapp(clienteId); setQr(qrImagem(dados)); await atualizar() } catch (e) { setMensagem(e.message); setCarregando(false) } }
  async function mostrarQr() { setCarregando(true); try { const dados = await obterQrCodeWhatsapp(clienteId); setQr(qrImagem(dados)); if (!qrImagem(dados)) setMensagem('A Evolution não retornou uma imagem de QR Code. Verifique se a instância já está conectada.') } catch (e) { setMensagem(e.message) } finally { setCarregando(false) } }
  async function remover() { if (!confirm('Desconectar e excluir esta instância do WhatsApp?')) return; setCarregando(true); try { await excluirWhatsapp(clienteId); setQr(''); await atualizar() } catch (e) { setMensagem(e.message); setCarregando(false) } }
  return <div className="layout-app"><Sidebar /><main className="conteudo-principal pagina-conteudo integracao-pagina"><header className="topo-pagina"><div><h1>WhatsApp</h1><p>Conecte o WhatsApp e acesse os seus Typebots sem sair da plataforma.</p></div></header>
    <label className="integracao-cliente">Cliente<select value={clienteId} onChange={(e) => { setClienteId(e.target.value); setQr('') }}>{clientes.map((c) => <option key={c.id} value={c.id}>{c.nome}</option>)}</select></label>
    {mensagem && <p className="mensagem-integracao">{mensagem}</p>}
    <section className="integracao-card"><div className="integracao-titulo"><MessageCircle size={28}/><div><h2>Evolution API</h2><p>Estado: <strong>{status?.estado || 'carregando'}</strong></p></div><span className={`status-pill status-${status?.estado}`}>{status?.configurada ? 'Servidor configurado' : 'Configuração pendente'}</span></div>
      {status?.instancia && <p className="integracao-identificador">Instância: <code>{status.instancia}</code></p>}
      <div className="integracao-acoes">{!status?.instancia && <button className="botao-primario" onClick={conectar} disabled={carregando || !clienteId}>Criar conexão</button>}{status?.instancia && <button className="botao-primario" onClick={mostrarQr} disabled={carregando}><QrCode size={17}/> Mostrar QR Code</button>}<button className="botao-secundario" onClick={atualizar} disabled={carregando}><RefreshCw size={17}/> Atualizar</button>{status?.instancia && <button className="botao-perigo" onClick={remover} disabled={carregando}><Trash2 size={17}/> Desconectar</button>}{carregando && <LoaderCircle className="girando"/>}</div>
      {qr && <div className="whatsapp-qr"><img src={qr} alt="QR Code para conectar o WhatsApp"/><p>Abra o WhatsApp no celular, acesse aparelhos conectados e leia este código.</p></div>}
    </section>
    <section className="integracao-card typebot-acessos-whatsapp"><div className="integracao-titulo"><MessageCircle size={26}/><div><h2>Typebot</h2><p>Abra o editor para criar e editar bots ou o viewer para visualizar os bots publicados.</p></div></div><div className="integracao-acoes"><a className="botao-primario" href={TYPEBOT_BUILDER_URL} target="_blank" rel="noreferrer"><ExternalLink size={17}/> Abrir editor Typebot</a><a className="botao-secundario" href={TYPEBOT_VIEWER_URL} target="_blank" rel="noreferrer"><ExternalLink size={17}/> Abrir viewer dos bots</a></div></section>
  </main></div>
}
