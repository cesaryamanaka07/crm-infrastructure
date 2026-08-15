import { useEffect, useMemo, useState } from 'react'
import { ChevronDown, ChevronUp, Download, FilePenLine, Save, Search, Trash2, X } from 'lucide-react'
import Sidebar from '../components/Sidebar'
import { listarClientes } from '../api/clientesService'
import { atualizarGeracao, excluirGeracao, excluirImagem, listarBiblioteca } from '../api/contentService'

const NOMES_FORMATOS = { post_unico: 'Post único', carrossel: 'Carrossel', reels: 'Reels', story: 'Story' }

function contarPalavras(texto) { return texto.trim() ? texto.trim().split(/\s+/).length : 0 }

function ConteudosCriados() {
  const [clientes, setClientes] = useState([])
  const [geracoes, setGeracoes] = useState([])
  const [clienteId, setClienteId] = useState('todos')
  const [formato, setFormato] = useState('todos')
  const [busca, setBusca] = useState('')
  const [aberta, setAberta] = useState('')
  const [editando, setEditando] = useState('')
  const [rascunho, setRascunho] = useState([])
  const [mensagem, setMensagem] = useState('')
  const [carregando, setCarregando] = useState(true)

  useEffect(() => {
    Promise.all([listarClientes(), listarBiblioteca()]).then(([listaClientes, listaGeracoes]) => {
      setClientes(listaClientes); setGeracoes(listaGeracoes)
    }).catch((erro) => setMensagem(erro.message)).finally(() => setCarregando(false))
  }, [])

  const filtradas = useMemo(() => geracoes.filter((geracao) => {
    const correspondeCliente = clienteId === 'todos' || (clienteId === 'sem-cliente' ? !geracao.cliente_id : geracao.cliente_id === clienteId)
    const correspondeFormato = formato === 'todos' || geracao.formato_imagem === formato || geracao.conteudos.some((item) => item.formato === formato)
    const termo = busca.trim().toLowerCase()
    const correspondeBusca = !termo || geracao.tema.toLowerCase().includes(termo) || geracao.conteudos.some((item) => `${item.titulo} ${item.legenda}`.toLowerCase().includes(termo))
    return correspondeCliente && correspondeFormato && correspondeBusca
  }), [geracoes, clienteId, formato, busca])

  function iniciarEdicao(geracao) { setAberta(geracao.id); setEditando(geracao.id); setRascunho(structuredClone(geracao.conteudos)); setMensagem('') }
  function alterar(indice, campo, valor) { setRascunho((atual) => atual.map((item, i) => i === indice ? { ...item, [campo]: valor } : item)) }

  async function salvar(geracao) {
    const normalizados = rascunho.map((item) => ({ ...item, contagem_caracteres: item.legenda.length, contagem_palavras: contarPalavras(item.legenda) }))
    try {
      const atualizada = await atualizarGeracao(geracao.conteudo_id, geracao.id, normalizados)
      setGeracoes((atuais) => atuais.map((item) => item.id === geracao.id ? { ...item, conteudos: atualizada.conteudos } : item))
      setEditando(''); setMensagem('Conteúdo atualizado e salvo.')
    } catch (erro) { setMensagem(erro.message) }
  }

  async function excluir(geracao) {
    if (!window.confirm('Deseja excluir definitivamente esta criação?')) return
    try { await excluirGeracao(geracao.conteudo_id, geracao.id); setGeracoes((atuais) => atuais.filter((item) => item.id !== geracao.id)); setMensagem('Criação excluída.') }
    catch (erro) { setMensagem(erro.message) }
  }

  async function removerImagem(geracaoId, imagemId) {
    if (!window.confirm('Deseja excluir definitivamente esta imagem?')) return
    try {
      await excluirImagem(imagemId)
      setGeracoes((atuais) => atuais.map((geracao) => {
        if (geracao.id !== geracaoId) return geracao
        const imagensPorPost = Object.fromEntries(Object.entries(geracao.imagens_por_post || {}).map(([indice, imagens]) => [indice, imagens.filter((imagem) => imagem.id !== imagemId)]))
        return { ...geracao, imagens_por_post: imagensPorPost, imagens_avulsas: (geracao.imagens_avulsas || []).filter((imagem) => imagem.id !== imagemId) }
      }).filter((geracao) => geracao.conteudos.length || (geracao.imagens_avulsas || []).length))
      setMensagem('Imagem excluída.')
    } catch (erro) { setMensagem(erro.message) }
  }

  function baixar(geracao) {
    const cliente = clientes.find((item) => item.id === geracao.cliente_id)?.nome || 'Sem cliente'
    const texto = geracao.conteudos.map((item, indice) => [
      `${cliente} — ${geracao.tema}`, `CONTEÚDO ${indice + 1} — ${NOMES_FORMATOS[item.formato] || item.formato}`, `Título: ${item.titulo}`,
      item.slides.length ? `Slides:\n${item.slides.map((parte, i) => `${i + 1}. ${parte}`).join('\n')}` : '',
      item.roteiro.length ? `Roteiro:\n${item.roteiro.map((parte, i) => `${i + 1}. ${parte}`).join('\n')}` : '',
      item.telas.length ? `Telas:\n${item.telas.map((parte, i) => `${i + 1}. ${parte}`).join('\n')}` : '',
      `Legenda:\n${item.legenda}`, `Hashtags: ${item.hashtags.join(' ')}`, `${item.contagem_caracteres} caracteres · ${item.contagem_palavras} palavras`, '\n---\n',
    ].filter(Boolean).join('\n\n')).join('\n')
    const url = URL.createObjectURL(new Blob([texto], { type: 'text/plain;charset=utf-8' }))
    const link = document.createElement('a'); link.href = url; link.download = `${geracao.tema.replace(/[^a-zA-Z0-9À-ÿ_-]+/g, '-').toLowerCase()}.txt`; link.click(); URL.revokeObjectURL(url)
  }

  return <div className="layout-app"><Sidebar /><main className="conteudo-principal pagina-conteudo">
    <header className="topo-pagina"><div><h1>Conteúdos criados</h1><p>Visualize, edite e organize as criações de cada cliente.</p></div></header>
    <section className="filtros-biblioteca">
      <label><span>Cliente</span><select value={clienteId} onChange={(e) => setClienteId(e.target.value)}><option value="todos">Todos</option>{clientes.map((cliente) => <option key={cliente.id} value={cliente.id}>{cliente.nome}</option>)}<option value="sem-cliente">Antigos sem cliente</option></select></label>
      <label><span>Formato</span><select value={formato} onChange={(e) => setFormato(e.target.value)}><option value="todos">Todos</option>{Object.entries(NOMES_FORMATOS).map(([valor, nome]) => <option key={valor} value={valor}>{nome}</option>)}</select></label>
      <label className="busca-biblioteca"><span>Pesquisar</span><div><Search size={16} /><input value={busca} onChange={(e) => setBusca(e.target.value)} placeholder="Tema, título ou legenda" /></div></label>
    </section>
    {mensagem && <p className="mensagem-integracao">{mensagem}</p>}
    {carregando ? <p>Carregando conteúdos...</p> : <div className="biblioteca-conteudos">
      {!filtradas.length && <div className="estado-vazio"><p>Nenhum conteúdo encontrado com esses filtros.</p></div>}
      {filtradas.map((geracao) => <article key={geracao.id} className="cartao-biblioteca">
        <div className="cabecalho-item-biblioteca"><div><span>{clientes.find((cliente) => cliente.id === geracao.cliente_id)?.nome || 'Sem cliente'}</span><h2>{geracao.tema}</h2><small>{new Date(geracao.criado_em).toLocaleString('pt-BR')} · {geracao.conteudos.length ? `${geracao.conteudos.length} conteúdo(s)` : 'Criação de imagens'}</small></div><button onClick={() => setAberta(aberta === geracao.id ? '' : geracao.id)}>{aberta === geracao.id ? <ChevronUp /> : <ChevronDown />}</button></div>
        {geracao.conteudos.length > 0 && <div className="acoes-biblioteca"><button onClick={() => iniciarEdicao(geracao)}><FilePenLine size={15} />Editar</button><button onClick={() => baixar(geracao)}><Download size={15} />Baixar</button><button className="acao-excluir-geracao" onClick={() => excluir(geracao)}><Trash2 size={15} />Excluir</button></div>}
        {aberta === geracao.id && <div className="itens-biblioteca">{(editando === geracao.id ? rascunho : geracao.conteudos).map((item, indice) => <section key={indice} className="item-editavel-biblioteca"><strong>{NOMES_FORMATOS[item.formato] || item.formato} {indice + 1}</strong>{editando === geracao.id ? <>
          <label>Título<input value={item.titulo} onChange={(e) => alterar(indice, 'titulo', e.target.value)} /></label>
          {item.slides.length > 0 && <label>Slides — um por linha<textarea value={item.slides.join('\n')} onChange={(e) => alterar(indice, 'slides', e.target.value.split('\n'))} /></label>}
          {item.roteiro.length > 0 && <label>Roteiro — um trecho por linha<textarea value={item.roteiro.join('\n')} onChange={(e) => alterar(indice, 'roteiro', e.target.value.split('\n'))} /></label>}
          {item.telas.length > 0 && <label>Telas — uma por linha<textarea value={item.telas.join('\n')} onChange={(e) => alterar(indice, 'telas', e.target.value.split('\n'))} /></label>}
          <label>Legenda<textarea value={item.legenda} onChange={(e) => alterar(indice, 'legenda', e.target.value)} /></label><label>Hashtags — separadas por espaço<input value={item.hashtags.join(' ')} onChange={(e) => alterar(indice, 'hashtags', e.target.value.split(/\s+/).filter(Boolean))} /></label>
        </> : <><h3>{item.titulo}</h3>{item.slides.map((parte, i) => <p key={`s${i}`}><b>{i + 1}.</b> {parte}</p>)}{item.roteiro.map((parte, i) => <p key={`r${i}`}><b>{i + 1}.</b> {parte}</p>)}{item.telas.map((parte, i) => <p key={`t${i}`}><b>{i + 1}.</b> {parte}</p>)}<div className="legenda-biblioteca"><b>Legenda</b><p>{item.legenda}</p></div><p className="hashtags-conteudo-gerado">{item.hashtags.join(' ')}</p>{(geracao.imagens_por_post?.[String(indice)] || []).length > 0 && <div className="imagens-post-biblioteca">{geracao.imagens_por_post[String(indice)].map((imagem) => <figure key={imagem.id}><img src={imagem.data_url} alt={imagem.nome} /><a href={imagem.data_url} download={imagem.nome}>Baixar</a><button onClick={() => removerImagem(geracao.id, imagem.id)}><Trash2 size={14} />Excluir</button></figure>)}</div>}</>}</section>)}{(geracao.imagens_avulsas || []).length > 0 && <section className="item-editavel-biblioteca"><strong>{NOMES_FORMATOS[geracao.formato_imagem] || geracao.formato_imagem}</strong><div className="imagens-post-biblioteca">{geracao.imagens_avulsas.map((imagem) => <figure key={imagem.id}><img src={imagem.data_url} alt={imagem.nome} /><a href={imagem.data_url} download={imagem.nome}>Baixar</a><button onClick={() => removerImagem(geracao.id, imagem.id)}><Trash2 size={14} />Excluir</button></figure>)}</div></section>}</div>}
        {editando === geracao.id && <div className="salvar-edicao-biblioteca"><button className="botao-secundario" onClick={() => setEditando('')}><X size={15} />Cancelar</button><button className="botao-primario" onClick={() => salvar(geracao)}><Save size={15} />Salvar alterações</button></div>}
      </article>)}
    </div>}
  </main></div>
}

export default ConteudosCriados
