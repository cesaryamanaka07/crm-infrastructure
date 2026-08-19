import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { LoaderCircle } from 'lucide-react'
import Sidebar from '../components/Sidebar'
import {
  criarConteudo,
  gerarConteudo,
  obterEstrategia,
  obterLinhaEditorial,
  gerarBriefingDaLinha,
  obterCacheConteudo,
  obterMarca,
} from '../api/contentService'
import { listarClientes } from '../api/clientesService'
import { escolherClienteInicial } from '../utils/clienteAtivo'

const FORMULARIO_INICIAL = {
  cliente_id: '',
  arsenal_campos: [],
  instrucoes_ia: null,
  usar_narrativa: true,
  intencao: '',
  tema: '',
  perspectiva: '',
  modelo: 'AIDA',
  tom_de_voz: 'Profissional',
  observacoes: null,
  hashtags_padrao: [],
  tecnicas: [],
  quantidades: {
    post_unico: 1,
    carrossel: 0,
    reels: 0,
    story: 0,
  },
  narrativas: {
    post_unico: 'Conversacional',
    carrossel: 'Conversacional',
    reels: 'Conversacional',
    story: 'Conversacional',
    legenda: 'Conversacional',
  },
  tamanho_legenda: 'media',
}

const NOMES_FORMATOS = {
  post_unico: 'Post único',
  carrossel: 'Carrossel',
  reels: 'Reels',
  story: 'Story',
}

const NARRATIVAS = [
  'Conversacional',
  'Direta',
  'Storytelling',
  'Educacional',
  'Emocional',
  'Provocativa',
  'Bastidores',
  'Tutorial passo a passo',
  'Antes e depois',
  'Problema e solução',
]

const TAMANHOS_LEGENDA = [
  { valor: 'ultracurta', nome: 'Ultracurta', limite: 'Até 100 caracteres · 15 a 20 palavras', uso: 'Frases impactantes, memes ou vídeos que falam por si.' },
  { valor: 'curta', nome: 'Curta', limite: '101 a 300 caracteres · 20 a 50 palavras', uso: 'Perguntas, avisos e chamadas para ação objetivas.' },
  { valor: 'media', nome: 'Média', limite: '301 a 800 caracteres · 50 a 130 palavras', uso: 'Contexto rápido, mini tutorial ou carrossel explicativo.' },
  { valor: 'longa', nome: 'Longa', limite: '801 a 1.500 caracteres · 130 a 250 palavras', uso: 'Conteúdo educativo, reflexões, bastidores e análises.' },
  { valor: 'maxima', nome: 'Máxima', limite: '1.501 a 2.200 caracteres · 250 a 350 palavras', uso: 'Histórias completas, estudos de caso e guias detalhados.' },
]

const FRAMEWORKS = ['AIDA', 'PAS', 'BAB', '4Ps', 'FAB', 'ACCA', 'QUEST', 'Storytelling', 'Jornada do Herói', 'Educacional', 'Lista', 'Comparação', 'Mito versus verdade', 'Problema e solução', 'Estudo de caso']
const TECNICAS = [
  ['copywriting', 'Copywriting'], ['storytelling', 'Storytelling'], ['persuasao', 'Persuasão'], ['pnl', 'PNL'],
  ['prova_social', 'Prova social'], ['autoridade', 'Autoridade'], ['curiosidade', 'Curiosidade'], ['escassez', 'Escassez'],
  ['urgencia', 'Urgência'], ['reciprocidade', 'Reciprocidade'], ['antecipacao', 'Antecipação'], ['aversao_perda', 'Aversão à perda'],
  ['identificacao', 'Identificação com o público'],
]

function ExibirConteudosGerados({ geracao }) {
  return (
    <div className="lista-conteudos-gerados">
      {geracao.conteudos.map((item, indice) => (
        <article key={`${item.formato}-${indice}`} className="conteudo-gerado">
          <span className="tipo-conteudo-gerado">{NOMES_FORMATOS[item.formato] || item.formato}</span>
          <h3>{item.titulo}</h3>
          {item.slides.length > 0 && <div className="partes-conteudo-gerado"><strong>Slides</strong>{item.slides.map((slide, parte) => <p key={parte}><b>{parte + 1}.</b> {slide}</p>)}</div>}
          {item.roteiro.length > 0 && <div className="partes-conteudo-gerado"><strong>Roteiro</strong>{item.roteiro.map((trecho, parte) => <p key={parte}><b>{parte + 1}.</b> {trecho}</p>)}</div>}
          {item.telas.length > 0 && <div className="partes-conteudo-gerado"><strong>Telas</strong>{item.telas.map((tela, parte) => <p key={parte}><b>{parte + 1}.</b> {tela}</p>)}</div>}
          <div className="legenda-conteudo-gerado"><strong>Legenda</strong><p>{item.legenda}</p></div>
          <p className="hashtags-conteudo-gerado">{item.hashtags.join(' ')}</p>
          <small>{item.contagem_caracteres} caracteres · {item.contagem_palavras} palavras</small>
        </article>
      ))}
    </div>
  )
}

function CriarConteudo() {
  const [formulario, setFormulario] = useState(FORMULARIO_INICIAL)
  const [clientes, setClientes] = useState([])
  const [linhaEditorial, setLinhaEditorial] = useState(null)
  const [ideiaSelecionada, setIdeiaSelecionada] = useState('')
  const [carregandoBriefing, setCarregandoBriefing] = useState(false)
  const [carregandoMarca, setCarregandoMarca] = useState(false)
  const [narrativaDisponivel, setNarrativaDisponivel] = useState(false)
  const [salvando, setSalvando] = useState(false)
  const [erro, setErro] = useState('')
  const [sucesso, setSucesso] = useState('')
  const [resultadoGeracao, setResultadoGeracao] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    listarClientes()
      .then((listaClientes) => {
        setClientes(listaClientes)
        setFormulario((atual) => ({ ...atual, cliente_id: escolherClienteInicial(listaClientes) }))
      })
      .catch((e) => { setErro(e.message); if (!localStorage.getItem('access_token')) navigate('/login') })
  }, [navigate])

  useEffect(() => {
    if (!formulario.cliente_id) {
      setLinhaEditorial(null)
      setIdeiaSelecionada('')
      setFormulario((atual) => ({ ...atual, hashtags_padrao: [] }))
      return
    }
    const linhaCache = obterCacheConteudo(`/estrategias/${formulario.cliente_id}/linha-editorial`)
    if (linhaCache) setLinhaEditorial(linhaCache.resultado)
    obterLinhaEditorial(formulario.cliente_id)
      .then((dados) => setLinhaEditorial(dados.resultado))
      .catch(() => { if (!linhaCache) setLinhaEditorial(null) })
    setIdeiaSelecionada('')
    setCarregandoMarca(true)
    obterMarca(formulario.cliente_id)
      .then((marca) => setFormulario((atual) => ({ ...atual, hashtags_padrao: Array.isArray(marca.hashtags_padrao) ? marca.hashtags_padrao : [] })))
      .catch(() => setFormulario((atual) => ({ ...atual, hashtags_padrao: [] })))
      .finally(() => setCarregandoMarca(false))
    obterEstrategia(formulario.cliente_id, 'narrativa')
      .then((dados) => {
        const disponivel = Boolean(dados.resultado)
        setNarrativaDisponivel(disponivel)
        setFormulario((atual) => ({ ...atual, usar_narrativa: disponivel }))
      })
      .catch(() => { setNarrativaDisponivel(false); setFormulario((atual) => ({ ...atual, usar_narrativa: false })) })
    setFormulario((atual) => ({ ...atual, arsenal_campos: [] }))
  }, [formulario.cliente_id])

  function alterarCampo(evento) {
    const { name, value } = evento.target
    setFormulario((atual) => ({ ...atual, [name]: value }))
  }

  function alterarHashtags(evento) {
    const itens = evento.target.value.split(/[\s,;]+/).map((item) => item.trim()).filter(Boolean)
    setFormulario((atual) => ({ ...atual, hashtags_padrao: itens }))
  }

  function alternarTecnica(slug) {
    setFormulario((atual) => {
      const selecionada = atual.tecnicas.includes(slug)
      if (selecionada) return { ...atual, tecnicas: atual.tecnicas.filter((tecnica) => tecnica !== slug) }
      if (atual.tecnicas.length >= 8) { setErro('Selecione no máximo 8 técnicas por conteúdo.'); return atual }
      setErro('')
      return { ...atual, tecnicas: [...atual.tecnicas, slug] }
    })
  }

  function ideiasDaLinha() {
    if (!linhaEditorial || typeof linhaEditorial !== 'object') return []
    return ['topo_funil', 'meio_funil', 'fundo_funil'].flatMap((etapa) => (Array.isArray(linhaEditorial[etapa]) ? linhaEditorial[etapa] : []).map((ideia, indice) => ({ ...ideia, etapa, chave: `${etapa}-${indice}` })))
  }

  async function selecionarIdeia(evento) {
    const chave = evento.target.value
    setIdeiaSelecionada(chave)
    const ideia = ideiasDaLinha().find((item) => item.chave === chave)
    if (!ideia || !formulario.cliente_id) return
    setCarregandoBriefing(true); setErro('')
    try {
      const briefing = await gerarBriefingDaLinha(formulario.cliente_id, ideia)
      setFormulario((atual) => ({ ...atual, tema: briefing.tema, intencao: briefing.intencao, perspectiva: briefing.perspectiva }))
    } catch (e) { setErro(e.message) } finally { setCarregandoBriefing(false) }
  }

  function alterarQuantidade(formato, valor) {
    const quantidade = Math.max(0, Math.min(10, Number(valor) || 0))
    setFormulario((atual) => {
      const novasQuantidades = { ...atual.quantidades, [formato]: quantidade }
      const total = Object.values(novasQuantidades).reduce((soma, item) => soma + item, 0)
      if (total > 20) { setErro('A quantidade total não pode ultrapassar 20 conteúdos.'); return atual }
      setErro(''); return { ...atual, quantidades: novasQuantidades }
    })
  }

  function alterarNarrativa(campo, valor) { setFormulario((atual) => ({ ...atual, narrativas: { ...atual.narrativas, [campo]: valor } })) }

  async function salvar(status) {
    setErro(''); setSucesso(''); setResultadoGeracao(null); setSalvando(true)
    try {
      const novoConteudo = await criarConteudo({ ...formulario, observacoes: null, instrucoes_ia: null, status })
      if (status === 'rascunho') {
        setFormulario({ ...FORMULARIO_INICIAL, cliente_id: formulario.cliente_id }); setSucesso('Briefing salvo como rascunho.')
      } else {
        setSucesso('Briefing salvo. Gerando os conteúdos com IA...')
        const geracao = await gerarConteudo(novoConteudo.id)
        setResultadoGeracao(geracao); setFormulario({ ...FORMULARIO_INICIAL, cliente_id: formulario.cliente_id }); setSucesso(`${geracao.conteudos.length} conteúdo(s) gerado(s) com sucesso.`)
      }
    } catch (e) { setErro(e.message); if (!localStorage.getItem('access_token')) navigate('/login') } finally { setSalvando(false) }
  }

  function enviar(evento) { evento.preventDefault(); salvar('pronto_para_gerar') }
  const hashtagsTexto = formulario.hashtags_padrao.join(' ')

  return (
    <div className="layout-app">
      <Sidebar />
      <main className="conteudo-principal pagina-conteudo">
        <header className="topo-pagina topo-criacao"><div><h1>Criar conteúdo</h1><p>Defina o briefing que será enviado para o serviço de IA.</p></div></header>
        <div className={`grade-criacao ${resultadoGeracao ? '' : 'grade-criacao-formulario'}`}>
          <form className="cartao-formulario" onSubmit={enviar}>
            <div className="campo-formulario campo-largo"><label htmlFor="cliente_id">Cliente</label><select id="cliente_id" name="cliente_id" value={formulario.cliente_id} onChange={alterarCampo} required><option value="">Selecione o cliente</option>{clientes.map((cliente) => <option key={cliente.id} value={cliente.id}>{cliente.nome}</option>)}</select><small>O briefing e todas as criações ficarão vinculados a este cliente.</small></div>
            <div className="campo-formulario campo-largo"><label htmlFor="hashtags-padrao-conteudo">Hashtags padrão do cliente</label><textarea id="hashtags-padrao-conteudo" name="hashtags_padrao" value={hashtagsTexto} onChange={alterarHashtags} placeholder="#minhamarca #segmento #cidade" /><small>{carregandoMarca ? 'Carregando hashtags da Marca...' : 'Vieram da Marca deste cliente. Você pode ajustar somente para este conteúdo; se salvar, serão preservadas junto dele.'}</small></div>
            <div className="campo-formulario campo-largo selecao-linha-editorial"><label htmlFor="linha-editorial-ideia">Ideia da Linha Editorial</label><select id="linha-editorial-ideia" value={ideiaSelecionada} onChange={selecionarIdeia} disabled={!formulario.cliente_id || carregandoBriefing}><option value="">Selecione uma ideia para preencher o briefing com IA</option>{ideiasDaLinha().map((ideia) => <option key={ideia.chave} value={ideia.chave}>{`[${ideia.etapa.replace('_', ' ')}] ${ideia.titulo || 'Ideia editorial'}`}</option>)}</select><small>{carregandoBriefing ? 'A IA está preparando Tema, Intenção e Perspectiva...' : 'A seleção usa o Arsenal de Copy e a Narrativa Estratégica automaticamente.'}</small></div>
            <div className="campo-formulario"><label htmlFor="intencao">Intenção</label><input id="intencao" name="intencao" value={formulario.intencao} onChange={alterarCampo} required minLength="3" maxLength="500" /></div>
            <div className="campo-formulario"><label htmlFor="tema">Tema</label><input id="tema" name="tema" value={formulario.tema} onChange={alterarCampo} required minLength="3" maxLength="300" /></div>
            <div className="campo-formulario campo-largo"><label htmlFor="perspectiva">Perspectiva</label><textarea id="perspectiva" name="perspectiva" value={formulario.perspectiva} onChange={alterarCampo} required minLength="3" maxLength="500" /></div>
            <div className="campo-formulario"><label htmlFor="modelo">Modelo de estrutura</label><select id="modelo" name="modelo" value={formulario.modelo} onChange={alterarCampo}>{FRAMEWORKS.map((modelo) => <option key={modelo}>{modelo}</option>)}</select></div>
            <div className="campo-formulario"><label htmlFor="tom_de_voz">Tom de voz</label><input id="tom_de_voz" name="tom_de_voz" value={formulario.tom_de_voz} onChange={alterarCampo} required minLength="2" maxLength="80" /></div>
            <div className="campo-formulario campo-largo"><label>Tamanho da legenda</label><div className="opcoes-tamanho-legenda">{TAMANHOS_LEGENDA.map((item) => <label key={item.valor}><input type="radio" name="tamanho_legenda" value={item.valor} checked={formulario.tamanho_legenda === item.valor} onChange={alterarCampo} /><span><b>{item.nome}</b><small>{item.limite}</small><em>{item.uso}</em></span></label>)}</div></div>
            <fieldset className="campo-formulario campo-largo"><legend>Narrativas por formato</legend><div className="grade-narrativas">{['post_unico', 'carrossel', 'reels', 'story', 'legenda'].map((campo) => <label key={campo}>{NOMES_FORMATOS[campo] || 'Legenda'}<select value={formulario.narrativas[campo]} onChange={(e) => alterarNarrativa(campo, e.target.value)}>{NARRATIVAS.map((narrativa) => <option key={narrativa}>{narrativa}</option>)}</select></label>)}</div>{narrativaDisponivel && <small>A Narrativa Estratégica salva também será usada como contexto da geração.</small>}</fieldset>
            <fieldset className="campo-formulario campo-largo"><legend>Quantidade por formato</legend><div className="grade-quantidades">{Object.keys(formulario.quantidades).map((formato) => <label key={formato}>{NOMES_FORMATOS[formato]}<input type="number" min="0" max="10" value={formulario.quantidades[formato]} onChange={(e) => alterarQuantidade(formato, e.target.value)} /></label>)}</div></fieldset>
            <fieldset className="campo-formulario campo-largo"><legend>Técnicas de copy (opcional)</legend><div className="lista-tecnicas">{TECNICAS.map(([slug, nome]) => <label key={slug}><input type="checkbox" checked={formulario.tecnicas.includes(slug)} onChange={() => alternarTecnica(slug)} />{nome}</label>)}</div></fieldset>
            {erro && <p className="mensagem-erro campo-largo">{erro}</p>}{sucesso && <p className="mensagem-sucesso campo-largo">{sucesso}</p>}
            <button className="botao-primario campo-largo" disabled={salvando}>{salvando && <LoaderCircle className="icone-girando" size={17} />}Gerar conteúdo</button>
          </form>
          {resultadoGeracao && <ExibirConteudosGerados geracao={resultadoGeracao} />}
        </div>
      </main>
    </div>
  )
}

export default CriarConteudo
