import { useEffect, useState } from 'react'
import { Image, LoaderCircle, Trash2 } from 'lucide-react'
import Sidebar from '../components/Sidebar'
import { aprovarImagem, gerarMidiaImagem, listarBiblioteca, obterMarca } from '../api/contentService'
import { listarClientes } from '../api/clientesService'

function Midias() {
  const [clientes, setClientes] = useState([])
  const [clienteId, setClienteId] = useState('')
  const [formato, setFormato] = useState('post_unico')
  const [descricao, setDescricao] = useState('')
  const [tomVisual, setTomVisual] = useState('')
  const [tomVisualPadrao, setTomVisualPadrao] = useState('Profissional e equilibrado')
  const [tamanho, setTamanho] = useState('1080x1080')
  const [quantidade, setQuantidade] = useState(2)
  const [textosCarrossel, setTextosCarrossel] = useState(['', ''])
  const [descricoesCarrossel, setDescricoesCarrossel] = useState(['', ''])
  const [referencia, setReferencia] = useState(null)
  const [referenciasCarrossel, setReferenciasCarrossel] = useState([null, null])
  const [resultado, setResultado] = useState(null)
  const [textosCriados, setTextosCriados] = useState([])
  const [origemTexto, setOrigemTexto] = useState('')
  const [instrucaoAlteracao, setInstrucaoAlteracao] = useState('')
  const [aprovando, setAprovando] = useState(null)
  const [mensagem, setMensagem] = useState('')
  const [erro, setErro] = useState('')
  const [gerando, setGerando] = useState(false)

  useEffect(() => { listarClientes().then((itens) => { setClientes(itens); if (itens[0]) setClienteId(itens[0].id) }).catch((e) => setErro(e.message)) }, [])
  useEffect(() => {
    if (!clienteId) return
    obterMarca(clienteId).then((marca) => {
      setTomVisualPadrao(marca.diretrizes_visuais?.tom_visual || 'Profissional e equilibrado')
      setTomVisual('')
    }).catch(() => { setTomVisualPadrao('Profissional e equilibrado'); setTomVisual('') })
    listarBiblioteca(clienteId).then((itens) => setTextosCriados(itens.filter((item) => item.conteudos?.length))).catch(() => setTextosCriados([]))
    setOrigemTexto('')
  }, [clienteId])

  async function gerar(evento) {
    evento.preventDefault()
    setGerando(true); setErro(''); setMensagem(''); setResultado(null)
    const dados = new FormData()
    const descricaoGeracao = instrucaoAlteracao.trim() ? `${descricao}\n\nALTERAÇÕES SOLICITADAS: ${instrucaoAlteracao.trim()}` : descricao
    dados.append('cliente_id', clienteId); dados.append('formato', formato); dados.append('descricao', descricaoGeracao); dados.append('tom_visual', tomVisual); dados.append('tamanho', tamanho)
    dados.append('quantidade', formato === 'carrossel' ? quantidade : 1)
    if (origemTexto) {
      const [geracaoId, indice] = origemTexto.split(':')
      dados.append('geracao_texto_id', geracaoId); dados.append('conteudo_indice', indice)
    }
    if (formato === 'carrossel') {
      dados.append('textos_carrossel', JSON.stringify(textosCarrossel))
      dados.append('descricoes_carrossel', JSON.stringify(descricoesCarrossel))
    }
    if (formato === 'carrossel') {
      const indices = []
      referenciasCarrossel.forEach((arquivo, indice) => { if (arquivo) { dados.append('referencias_carrossel', arquivo); indices.push(indice) } })
      dados.append('indices_referencias', JSON.stringify(indices))
    } else if (referencia) dados.append('referencia', referencia)
    try {
      const gerado = await gerarMidiaImagem(dados)
      setResultado({ ...gerado, contexto: { clienteId, origemTexto, descricao: descricaoGeracao, formato, tamanho } })
    } catch (e) { setErro(e.message) } finally { setGerando(false) }
  }

  function alterarQuantidade(novaQuantidade) {
    const total = Math.max(1, Math.min(20, Number(novaQuantidade) || 1))
    setQuantidade(total)
    setTextosCarrossel((atuais) => Array.from(
      { length: total },
      (_, indice) => atuais[indice] || ''
    ))
    setDescricoesCarrossel((atuais) => Array.from({ length: total }, (_, indice) => atuais[indice] || ''))
    setReferenciasCarrossel((atuais) => Array.from({ length: total }, (_, indice) => atuais[indice] || null))
  }

  function alterarTextoCarrossel(indice, texto) {
    setTextosCarrossel((atuais) => atuais.map((item, i) => (i === indice ? texto : item)))
  }

  function importarTexto(valor) {
    setOrigemTexto(valor)
    if (!valor) return
    const [geracaoId, indiceTexto] = valor.split(':')
    const geracao = textosCriados.find((item) => item.id === geracaoId)
    const item = geracao?.conteudos[Number(indiceTexto)]
    if (!item) return
    setFormato(item.formato)
    setDescricao(`${item.titulo}\n\n${item.legenda}`)
    if (item.formato === 'carrossel') {
      const slides = item.slides.length ? item.slides : [item.titulo]
      alterarQuantidade(slides.length)
      setTextosCarrossel(slides)
      setDescricoesCarrossel(slides.map((slide) => `Crie uma composição visual coerente com este texto: ${slide}`))
    }
  }

  function removerImagemGerada(indice) {
    setResultado((atual) => ({ ...atual, imagens: atual.imagens.filter((_, i) => i !== indice), pacote_zip: null }))
  }

  async function aprovar(indice) {
    setAprovando(indice); setErro(''); setMensagem('')
    const contexto = resultado.contexto
    const [geracaoTextoId, conteudoIndice] = contexto.origemTexto ? contexto.origemTexto.split(':') : [null, null]
    try {
      await aprovarImagem({
        cliente_id: contexto.clienteId,
        data_url: resultado.imagens[indice],
        formato: contexto.formato,
        tamanho: contexto.tamanho,
        modelo: resultado.modelo,
        descricao: contexto.descricao,
        nome: `${contexto.formato}-${indice + 1}.png`,
        geracao_texto_id: geracaoTextoId,
        conteudo_indice: conteudoIndice === null ? null : Number(conteudoIndice),
      })
      setResultado((atual) => ({ ...atual, imagens: atual.imagens.filter((_, i) => i !== indice), pacote_zip: null }))
      setMensagem('Imagem aprovada e salva em Conteúdos Criados.')
    } catch (e) { setErro(e.message) } finally { setAprovando(null) }
  }

  return (
    <div className="layout-app"><Sidebar /><main className="conteudo-principal pagina-conteudo">
      <header className="topo-pagina"><div><h1>Criar imagens</h1><p>Crie imagens seguindo automaticamente sua marca.</p></div></header>
      <div className="grade-criacao">
        <form className="cartao-formulario" onSubmit={gerar}>
          <div className="campo-formulario campo-largo"><label>Cliente</label><select required value={clienteId} onChange={(e) => setClienteId(e.target.value)}><option value="">Selecione</option>{clientes.map((cliente) => <option key={cliente.id} value={cliente.id}>{cliente.nome}</option>)}</select><small>A identidade visual configurada para esse cliente será aplicada.</small></div>
          <div className="campo-formulario campo-largo"><label>Importar um conteúdo de texto — opcional</label><select value={origemTexto} onChange={(e) => importarTexto(e.target.value)}><option value="">Criar imagem manualmente</option>{textosCriados.flatMap((geracao) => geracao.conteudos.map((item, indice) => item.formato === 'reels' ? null : <option key={`${geracao.id}:${indice}`} value={`${geracao.id}:${indice}`}>{geracao.tema} · {item.titulo} · {item.formato === 'post_unico' ? 'Post único' : item.formato}</option>)).filter(Boolean)}</select><small>Ao selecionar, o formato, título, legenda e slides serão importados automaticamente.</small></div>
          <div className="campo-formulario campo-largo"><label>Tipo do post</label><select value={formato} onChange={(e) => setFormato(e.target.value)}><option value="post_unico">Post único</option><option value="carrossel">Carrossel</option><option value="story">Story</option></select></div>
          <div className="campo-formulario campo-largo"><label>Descrição da imagem</label><textarea value={descricao} onChange={(e) => setDescricao(e.target.value)} minLength={3} maxLength={1500} required placeholder="Descreva a cena, o objetivo e os elementos visuais" /></div>
          <div className="campo-formulario campo-largo"><label>Tom visual desta geração</label><select value={tomVisual} onChange={(e) => setTomVisual(e.target.value)}><option value="">Usar padrão da marca — {tomVisualPadrao}</option><option>Profissional e equilibrado</option><option>Pastel, suave e delicado</option><option>Escuro, dramático e contrastado</option><option>Claro, leve e minimalista</option><option>Vibrante, colorido e energético</option><option>Elegante, sofisticado e premium</option><option>Natural, orgânico e acolhedor</option><option>Futurista, tecnológico e neon</option></select><small>Altere somente quando esta campanha precisar fugir do padrão visual do cliente.</small></div>
          <div className="campo-formulario"><label>Tamanho final</label><select value={tamanho} onChange={(e) => setTamanho(e.target.value)}><option value="1080x1080">Quadrado · 1080 × 1080</option><option value="1080x1350">Retrato · 1080 × 1350</option><option value="1080x1920">Story · 1080 × 1920</option></select></div>
          {formato === 'carrossel' && <><div className="campo-formulario"><label>Quantidade de imagens</label><input type="number" min="1" max="20" value={quantidade} onChange={(e) => alterarQuantidade(e.target.value)} /><small>De 1 a 20 imagens por carrossel.</small></div><fieldset className="campo-formulario campo-largo textos-carrossel"><legend>Slides do carrossel</legend><p className="ajuda-campo">Cada slide possui texto, composição visual e referência próprios.</p>{textosCarrossel.map((texto, indice) => <div className="configuracao-slide" key={indice}><label htmlFor={`texto-slide-${indice}`}><span>Texto do slide {indice + 1}</span><textarea id={`texto-slide-${indice}`} value={texto} onChange={(e) => alterarTextoCarrossel(indice, e.target.value)} required maxLength={500} placeholder={`Texto que aparecerá no slide ${indice + 1}`} /></label><label htmlFor={`imagem-slide-${indice}`}><span>Como será a imagem do slide {indice + 1}</span><textarea id={`imagem-slide-${indice}`} value={descricoesCarrossel[indice]} onChange={(e) => setDescricoesCarrossel((atuais) => atuais.map((item, i) => i === indice ? e.target.value : item))} required maxLength={800} placeholder="Descreva cenário, pessoas, objetos, enquadramento e composição" /></label><label><span>Referência do slide {indice + 1} — opcional</span><input type="file" accept="image/png,image/jpeg,image/webp" onChange={(e) => setReferenciasCarrossel((atuais) => atuais.map((item, i) => i === indice ? e.target.files[0] || null : item))} />{referenciasCarrossel[indice] && <button type="button" className="botao-remover-arquivo" onClick={() => setReferenciasCarrossel((atuais) => atuais.map((item, i) => i === indice ? null : item))}><Trash2 size={14} />Remover {referenciasCarrossel[indice].name}</button>}</label></div>)}</fieldset></>}
          {formato !== 'carrossel' && <div className="campo-formulario campo-largo"><label>Imagem de referência</label><input type="file" accept="image/png,image/jpeg,image/webp" onChange={(e) => setReferencia(e.target.files[0] || null)} />{referencia && <button type="button" className="botao-remover-arquivo" onClick={() => setReferencia(null)}><Trash2 size={14} />Remover {referencia.name}</button>}<small>A referência será incorporada à composição final.</small></div>}
          <div className="campo-formulario campo-largo"><label>O que deve ser alterado na próxima versão?</label><textarea value={instrucaoAlteracao} onChange={(e) => setInstrucaoAlteracao(e.target.value)} maxLength={1500} placeholder="Ex.: deixar o fundo mais claro, trocar o personagem, aumentar o contraste e reduzir os elementos decorativos." /><small>Preencha após analisar o rascunho e clique em Recriar. A versão anterior será descartada sem ser salva.</small></div>
          {erro && <p className="mensagem-erro campo-largo">{erro}</p>}
          {mensagem && <p className="mensagem-sucesso campo-largo">{mensagem}</p>}
          <button className="botao-primario campo-largo" disabled={gerando}>{gerando ? <LoaderCircle className="icone-girando" size={17} /> : <Image size={17} />}{resultado ? 'Recriar imagens' : 'Gerar imagens para aprovação'}</button>
        </form>
        <aside className="painel-rascunhos"><h2>Aprovação provisória</h2><p className="texto-apoio">Nada desta área será salvo até você aprovar.</p>{resultado?.imagens.length ? <>{resultado.pacote_zip && <a className="botao-primario baixar-pacote" href={resultado.pacote_zip} download={`${formato}-rascunhos.zip`}>Baixar rascunhos em ZIP</a>}<div className="lista-imagens-geradas">{resultado.imagens.map((imagem, indice) => <figure key={indice} className="imagem-gerada"><img src={imagem} alt={`Imagem ${indice + 1}`} /><a href={imagem} download={`${formato}-${indice + 1}.png`}>Baixar rascunho {indice + 1}</a><button type="button" className="botao-aprovar-imagem" onClick={() => aprovar(indice)} disabled={aprovando !== null}>{aprovando === indice ? <LoaderCircle className="icone-girando" size={14} /> : null}Aprovar e salvar</button><button type="button" className="botao-remover-arquivo" onClick={() => removerImagemGerada(indice)}><Trash2 size={14} />Descartar rascunho</button></figure>)}</div></> : <div className="estado-vazio"><Image size={32} /><p>Os rascunhos para aprovação aparecerão aqui.</p></div>}</aside>
      </div>
    </main></div>
  )
}

export default Midias
