import { useEffect, useMemo, useState } from 'react'
import { CalendarClock, CheckCircle2, FileText, LoaderCircle, Send } from 'lucide-react'
import Sidebar from '../components/Sidebar'
import { listarClientes } from '../api/clientesService'
import { listarBiblioteca } from '../api/contentService'
import { criarPublicacao, listarConexoes, listarPublicacoes } from '../api/socialService'
import { escolherClienteInicial } from '../utils/clienteAtivo'

const FORMATOS = [{ id: 'post_unico', nome: 'Post único' }, { id: 'carrossel', nome: 'Carrossel' }, { id: 'reels', nome: 'Reels' }, { id: 'story', nome: 'Story' }]
const REDES = [{ id: 'facebook_page', nome: 'Facebook Página' }, { id: 'instagram', nome: 'Instagram' }, { id: 'linkedin', nome: 'LinkedIn' }]

function Midias() {
  const [clientes, setClientes] = useState([]); const [clienteId, setClienteId] = useState(''); const [formato, setFormato] = useState('post_unico')
  const [conteudosCriados, setConteudosCriados] = useState([]); const [conteudoSelecionado, setConteudoSelecionado] = useState('')
  const [titulo, setTitulo] = useState(''); const [legenda, setLegenda] = useState(''); const [hashtags, setHashtags] = useState(['', '', '', '', '']); const [prompts, setPrompts] = useState([]); const [arquivos, setArquivos] = useState([])
  const [roteiro, setRoteiro] = useState(''); const [duracao, setDuracao] = useState(30); const [redes, setRedes] = useState([]); const [agendar, setAgendar] = useState(false); const [publicarEm, setPublicarEm] = useState('')
  const [conexoes, setConexoes] = useState([]); const [historico, setHistorico] = useState([]); const [processando, setProcessando] = useState(false); const [mensagem, setMensagem] = useState(''); const [erro, setErro] = useState('')

  useEffect(() => { Promise.all([listarClientes(), listarConexoes()]).then(([cs, con]) => { setClientes(cs); setClienteId(escolherClienteInicial(cs)); setConexoes(con) }).catch((e) => setErro(e.message)) }, [])
  useEffect(() => {
    if (!clienteId) return
    Promise.all([listarBiblioteca(clienteId), listarPublicacoes(clienteId)]).then(([biblioteca, publicacoes]) => { setConteudosCriados(biblioteca.filter((registro) => registro.conteudos?.length)); setHistorico(publicacoes) }).catch(() => { setConteudosCriados([]); setHistorico([]) })
  }, [clienteId])
  const contasDisponiveis = useMemo(() => conexoes.filter((c) => c.cliente_id === clienteId && c.selecionada && REDES.some((r) => r.id === c.provider)), [conexoes, clienteId])
  const opcoesConteudo = useMemo(() => conteudosCriados.flatMap((registro) => (registro.conteudos || []).map((item, indice) => ({ registro, item, indice, chave: `${registro.id}:${indice}` }))), [conteudosCriados])

  function limparCamposConteudo() { setConteudoSelecionado(''); setPrompts([]); setArquivos([]); setTitulo(''); setLegenda(''); setHashtags(['', '', '', '', '']); setRoteiro('') }
  function mudarCliente(valor) { setClienteId(valor); limparCamposConteudo() }
  function mudarFormato(valor) { setFormato(valor); setConteudoSelecionado(''); setPrompts([]); setArquivos([]); setTitulo(''); setLegenda(''); setHashtags(['', '', '', '', '']); setRoteiro('') }
  function selecionarConteudo(valor) {
    setConteudoSelecionado(valor); setErro(''); setMensagem('')
    const selecionado = opcoesConteudo.find((opcao) => opcao.chave === valor)
    if (!selecionado) { limparCamposConteudo(); return }
    const item = selecionado.item; const novoFormato = item.formato || 'post_unico'; const slides = Array.isArray(item.slides) ? item.slides : []
    setFormato(novoFormato); setTitulo(item.titulo || ''); setLegenda(item.legenda || ''); setHashtags(Array.from({ length: 5 }, (_, i) => item.hashtags?.[i] || '')); setRoteiro(Array.isArray(item.roteiro) ? item.roteiro.join('\n') : (item.roteiro || ''))
    setPrompts(novoFormato === 'carrossel' ? slides.map((slide) => ({ titulo: slide || '', prompt: '' })) : [{ titulo: item.titulo || '', prompt: '' }])
    if (novoFormato === 'reels' && item.duracao_segundos) setDuracao(Math.min(90, Math.max(1, Number(item.duracao_segundos))))
    setMensagem('Conteúdo criado carregado. O título, a legenda e as hashtags vieram da criação selecionada. Preencha os prompts e envie os arquivos finais.')
  }
  function alterarPrompt(indice, campo, valor) { setPrompts((at) => at.map((p, i) => i === indice ? { ...p, [campo]: valor } : p)) }
  function selecionarArquivos(evento) { setArquivos(Array.from(evento.target.files || [])) }
  function alternarRede(id) { setRedes((at) => at.includes(id) ? at.filter((x) => x !== id) : [...at, id]) }
  function podeEnviar() { return clienteId && redes.length && arquivos.length && legenda.trim() && (formato !== 'carrossel' || arquivos.length >= 2) && (!agendar || publicarEm) }
  async function enviar(evento) { evento.preventDefault(); if (!podeEnviar()) { setErro('Preencha cliente, conteúdo, arquivos, legenda, redes e data quando o agendamento estiver ativo.'); return }; setProcessando(true); setErro(''); setMensagem('Enviando arquivos finais para a publicação...')
    const form = new FormData(); form.append('cliente_id', clienteId); form.append('formato', formato); form.append('titulo', titulo); form.append('legenda', legenda); form.append('hashtags', JSON.stringify(hashtags.filter(Boolean))); form.append('redes', JSON.stringify(redes)); form.append('roteiro', roteiro); form.append('duracao_segundos', formato === 'reels' ? String(duracao) : ''); form.append('titulos_itens', JSON.stringify(prompts.map((p) => p.titulo || ''))); form.append('prompts_itens', JSON.stringify(prompts.map((p) => p.prompt || ''))); if (agendar) form.append('publicar_em', new Date(publicarEm).toISOString()); arquivos.forEach((arquivo) => form.append('arquivos', arquivo))
    try { const resultado = await criarPublicacao(form); setHistorico((at) => [resultado, ...at]); setMensagem(agendar ? 'Postagem agendada com sucesso.' : 'Postagem enviada. Consulte o status por rede abaixo.'); if (!agendar) setHistorico((at) => at.map((item) => item.id === resultado.id ? resultado : item)) } catch (e) { setErro(e.message) } finally { setProcessando(false) }
  }
  const statusTexto = (status) => ({ publicada: 'Publicada', agendada: 'Agendada', pendente: 'Processando', parcial: 'Parcial', erro: 'Erro' }[status] || status)
  return <div className="layout-app"><Sidebar /><main className="conteudo-principal pagina-conteudo pagina-agendamento"><header className="topo-pagina"><div><h1>AGENDAMENTO POSTAGEM</h1><p>Selecione um conteúdo já criado, envie os arquivos finais e publique agora ou programe para depois.</p></div></header>
    <form className="cartao-formulario formulario-agendamento" onSubmit={enviar}>
      <div className="campo-formulario campo-largo"><label>Cliente</label><select value={clienteId} onChange={(e) => mudarCliente(e.target.value)} required><option value="">Selecione</option>{clientes.map((c) => <option key={c.id} value={c.id}>{c.nome}</option>)}</select></div>
      <div className="campo-formulario campo-largo"><label><FileText size={16} /> Conteúdo criado</label><select value={conteudoSelecionado} onChange={(e) => selecionarConteudo(e.target.value)} required><option value="">Selecione um conteúdo criado</option>{opcoesConteudo.map(({ registro, item, indice, chave }) => <option key={chave} value={chave}>{FORMATOS.find((f) => f.id === item.formato)?.nome || item.formato} · {item.titulo || registro.tema} · {new Date(registro.criado_em).toLocaleDateString('pt-BR')} · conteúdo {indice + 1}</option>)}</select><small>Os dados abaixo vêm do conteúdo criado. Você poderá ajustar os prompts e anexar os arquivos finais.</small></div>
      <div className="campo-formulario"><label>Tipo de postagem</label><select value={formato} onChange={(e) => mudarFormato(e.target.value)}>{FORMATOS.map((f) => <option key={f.id} value={f.id}>{f.nome}</option>)}</select></div>
      <div className="campo-formulario"><label>Título do post</label><input value={titulo} onChange={(e) => setTitulo(e.target.value)} placeholder="Título vindo do conteúdo criado" /></div>
      <div className="campo-formulario campo-largo"><label>Legenda</label><textarea value={legenda} onChange={(e) => setLegenda(e.target.value)} required placeholder="Legenda do conteúdo criado" /></div>
      <fieldset className="campo-formulario campo-largo campo-hashtags"><legend>5 hashtags do conteúdo criado</legend><div className="grade-hashtags">{hashtags.map((h, i) => <input key={i} value={h} onChange={(e) => setHashtags((at) => at.map((x, j) => j === i ? e.target.value : x))} placeholder={`#hashtag${i + 1}`} />)}</div></fieldset>
      {formato === 'reels' && <div className="campo-formulario campo-largo"><label>Roteiro do vídeo</label><textarea value={roteiro} onChange={(e) => setRoteiro(e.target.value)} placeholder="Texto falado + sugestões de cena" required /><label>Duração: {duracao} segundos</label><input type="range" min="1" max="90" value={duracao} onChange={(e) => setDuracao(Number(e.target.value))} /><small>Escolha de 1 segundo a 1 minuto e 30 segundos.</small></div>}
      <fieldset className="campo-formulario campo-largo"><legend>Arquivos finais da postagem</legend><input type="file" multiple={formato === 'carrossel'} accept={formato === 'reels' ? 'video/*' : 'image/*'} onChange={selecionarArquivos} required /><small>{formato === 'carrossel' ? 'Selecione as imagens dos slides na ordem correta.' : 'Envie o arquivo pronto que será publicado, sem recriação por IA.'}</small>{arquivos.length > 0 && <p className="arquivos-selecionados">{arquivos.map((a) => a.name).join(' · ')}</p>}</fieldset>
      {formato === 'carrossel' && <fieldset className="campo-formulario campo-largo"><legend>Slides do conteúdo e prompts copiáveis</legend>{Array.from({ length: Math.max(arquivos.length, prompts.length, 1) }, (_, i) => <div className="item-slide-postagem" key={i}><label>Slide {i + 1} — texto do conteúdo</label><input value={prompts[i]?.titulo || ''} onChange={(e) => alterarPrompt(i, 'titulo', e.target.value)} /><label>Prompt para criar a arte no ChatGPT/Gemini</label><textarea value={prompts[i]?.prompt || ''} onChange={(e) => alterarPrompt(i, 'prompt', e.target.value)} placeholder="Escreva ou cole aqui o prompt para este slide." /></div>)}</fieldset>}
      {formato !== 'carrossel' && <div className="campo-formulario campo-largo"><label>Prompt para criar a arte no ChatGPT/Gemini</label><textarea value={prompts[0]?.prompt || ''} onChange={(e) => alterarPrompt(0, 'prompt', e.target.value)} placeholder="Escreva ou cole aqui o prompt para criar a arte." /></div>}
      <fieldset className="campo-formulario campo-largo"><legend>Redes sociais</legend><div className="grade-redes-postagem">{REDES.map((rede) => { const conta = contasDisponiveis.find((c) => c.provider === rede.id); return <label key={rede.id} className={redes.includes(rede.id) ? 'rede-postagem-ativa' : ''}><input type="checkbox" checked={redes.includes(rede.id)} onChange={() => alternarRede(rede.id)} disabled={!conta} /><span>{rede.nome}</span><small>{conta ? conta.nome : 'Conta selecionada não encontrada'}</small></label> })}</div></fieldset>
      <label className="opcao-agendamento"><input type="checkbox" checked={agendar} onChange={(e) => setAgendar(e.target.checked)} /><span>Agendar postagem</span></label>{agendar && <div className="campo-formulario"><label>Dia e horário</label><input type="datetime-local" value={publicarEm} onChange={(e) => setPublicarEm(e.target.value)} required /></div>}
      {erro && <p className="mensagem-erro campo-largo">{erro}</p>}{mensagem && <p className="mensagem-sucesso campo-largo">{mensagem}</p>}
      <div className="acoes-agendamento campo-largo"><button className="botao-primario" type="submit" disabled={processando || agendar}>{processando ? <LoaderCircle className="icone-girando" size={17} /> : <Send size={17} />}POSTAR AGORA</button><button className="botao-secundario botao-agendar" type="submit" disabled={processando || !agendar}>{processando ? <LoaderCircle className="icone-girando" size={17} /> : <CalendarClock size={17} />}AGENDAR POSTAGEM</button></div>
    </form>
    <section className="historico-publicacoes"><h2>Histórico de postagens</h2>{historico.length === 0 ? <p className="texto-apoio">Nenhuma postagem criada para este cliente.</p> : historico.map((item) => <article className="cartao-publicacao" key={item.id}><header><strong>{item.titulo || item.formato}</strong><span className={`status-publicacao status-${item.status}`}>{statusTexto(item.status)}</span></header><p>{item.publicar_em ? new Date(item.publicar_em).toLocaleString('pt-BR') : 'Publicação imediata'}</p><div className="status-redes-publicacao">{item.redes?.map((r) => <span key={r.provider}><CheckCircle2 size={14} />{r.provider}: {statusTexto(r.status)}{r.erro ? ` — ${r.erro}` : ''}</span>)}</div></article>)}</section>
  </main></div>
}
export default Midias
