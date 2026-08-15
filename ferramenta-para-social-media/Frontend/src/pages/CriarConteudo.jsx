import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { LoaderCircle } from 'lucide-react'
import Sidebar from '../components/Sidebar'
import {
  criarConteudo,
  gerarConteudo,
  obterArsenal,
} from '../api/contentService'
import { listarClientes } from '../api/clientesService'
import { CAMPOS_ARSENAL } from '../constants/arsenalCampos'

const FORMULARIO_INICIAL = {
  cliente_id: '',
  arsenal_campos: [],
  instrucoes_ia: '',
  intencao: '',
  tema: '',
  perspectiva: '',
  modelo: 'AIDA',
  tom_de_voz: 'Profissional',
  observacoes: '',
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
  {
    valor: 'ultracurta',
    nome: 'Ultracurta',
    limite: 'Até 100 caracteres · 15 a 20 palavras',
    uso: 'Frases impactantes, memes ou vídeos que falam por si.',
  },
  {
    valor: 'curta',
    nome: 'Curta',
    limite: '101 a 300 caracteres · 20 a 50 palavras',
    uso: 'Perguntas, avisos e chamadas para ação objetivas.',
  },
  {
    valor: 'media',
    nome: 'Média',
    limite: '301 a 800 caracteres · 50 a 130 palavras',
    uso: 'Contexto rápido, mini tutorial ou carrossel explicativo.',
  },
  {
    valor: 'longa',
    nome: 'Longa',
    limite: '801 a 1.500 caracteres · 130 a 250 palavras',
    uso: 'Conteúdo educativo, reflexões, bastidores e análises.',
  },
  {
    valor: 'maxima',
    nome: 'Máxima',
    limite: '1.501 a 2.200 caracteres · 250 a 350 palavras',
    uso: 'Histórias completas, estudos de caso e guias detalhados.',
  },
]

const FRAMEWORKS = [
  'AIDA',
  'PAS',
  'BAB',
  '4Ps',
  'FAB',
  'ACCA',
  'QUEST',
  'Storytelling',
  'Jornada do Herói',
  'Educacional',
  'Lista',
  'Comparação',
  'Mito versus verdade',
  'Problema e solução',
  'Estudo de caso',
]

const TECNICAS = [
  ['copywriting', 'Copywriting'],
  ['storytelling', 'Storytelling'],
  ['persuasao', 'Persuasão'],
  ['pnl', 'PNL'],
  ['prova_social', 'Prova social'],
  ['autoridade', 'Autoridade'],
  ['curiosidade', 'Curiosidade'],
  ['escassez', 'Escassez'],
  ['urgencia', 'Urgência'],
  ['reciprocidade', 'Reciprocidade'],
  ['antecipacao', 'Antecipação'],
  ['aversao_perda', 'Aversão à perda'],
  ['identificacao', 'Identificação com o público'],
]

function ExibirConteudosGerados({ geracao }) {
  return (
    <div className="lista-conteudos-gerados">
      {geracao.conteudos.map((item, indice) => (
        <article key={`${item.formato}-${indice}`} className="conteudo-gerado">
          <span className="tipo-conteudo-gerado">
            {NOMES_FORMATOS[item.formato] || item.formato}
          </span>
          <h3>{item.titulo}</h3>

          {item.slides.length > 0 && (
            <div className="partes-conteudo-gerado">
              <strong>Slides</strong>
              {item.slides.map((slide, parte) => (
                <p key={parte}><b>{parte + 1}.</b> {slide}</p>
              ))}
            </div>
          )}

          {item.roteiro.length > 0 && (
            <div className="partes-conteudo-gerado">
              <strong>Roteiro</strong>
              {item.roteiro.map((trecho, parte) => (
                <p key={parte}><b>{parte + 1}.</b> {trecho}</p>
              ))}
            </div>
          )}

          {item.telas.length > 0 && (
            <div className="partes-conteudo-gerado">
              <strong>Telas</strong>
              {item.telas.map((tela, parte) => (
                <p key={parte}><b>{parte + 1}.</b> {tela}</p>
              ))}
            </div>
          )}

          <div className="legenda-conteudo-gerado">
            <strong>Legenda</strong>
            <p>{item.legenda}</p>
          </div>
          <p className="hashtags-conteudo-gerado">{item.hashtags.join(' ')}</p>
          <small>
            {item.contagem_caracteres} caracteres · {item.contagem_palavras} palavras
          </small>
        </article>
      ))}
    </div>
  )
}

function CriarConteudo() {
  const [formulario, setFormulario] = useState(FORMULARIO_INICIAL)
  const [clientes, setClientes] = useState([])
  const [arsenal, setArsenal] = useState({ informacoes: {}, manual_ia: '' })
  const [salvando, setSalvando] = useState(false)
  const [erro, setErro] = useState('')
  const [sucesso, setSucesso] = useState('')
  const [resultadoGeracao, setResultadoGeracao] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    listarClientes()
      .then((listaClientes) => {
        setClientes(listaClientes)
        if (listaClientes[0]) {
          setFormulario((atual) => ({ ...atual, cliente_id: listaClientes[0].id }))
        }
      })
      .catch((e) => {
        setErro(e.message)
        if (!localStorage.getItem('access_token')) navigate('/login')
      })
  }, [navigate])

  useEffect(() => {
    if (!formulario.cliente_id) {
      setArsenal({ informacoes: {}, manual_ia: '' })
      return
    }
    obterArsenal(formulario.cliente_id)
      .then(setArsenal)
      .catch(() => setArsenal({ informacoes: {}, manual_ia: '' }))
    setFormulario((atual) => ({ ...atual, arsenal_campos: [] }))
  }, [formulario.cliente_id])

  function alterarCampo(evento) {
    const { name, value } = evento.target
    setFormulario((atual) => ({ ...atual, [name]: value }))
  }

  function alternarTecnica(slug) {
    setFormulario((atual) => {
      const selecionada = atual.tecnicas.includes(slug)
      if (selecionada) {
        return {
          ...atual,
          tecnicas: atual.tecnicas.filter((tecnica) => tecnica !== slug),
        }
      }
      if (atual.tecnicas.length >= 8) {
        setErro('Selecione no máximo 8 técnicas por conteúdo.')
        return atual
      }
      setErro('')
      return { ...atual, tecnicas: [...atual.tecnicas, slug] }
    })
  }

  function alternarCampoArsenal(chave) {
    setFormulario((atual) => ({
      ...atual,
      arsenal_campos: atual.arsenal_campos.includes(chave)
        ? atual.arsenal_campos.filter((item) => item !== chave)
        : [...atual.arsenal_campos, chave],
    }))
  }

  function alterarQuantidade(formato, valor) {
    const quantidade = Math.max(0, Math.min(10, Number(valor) || 0))
    setFormulario((atual) => {
      const novasQuantidades = { ...atual.quantidades, [formato]: quantidade }
      const total = Object.values(novasQuantidades).reduce((soma, item) => soma + item, 0)
      if (total > 20) {
        setErro('A quantidade total não pode ultrapassar 20 conteúdos.')
        return atual
      }
      setErro('')
      return { ...atual, quantidades: novasQuantidades }
    })
  }

  function alterarNarrativa(campo, valor) {
    setFormulario((atual) => ({
      ...atual,
      narrativas: { ...atual.narrativas, [campo]: valor },
    }))
  }

  async function salvar(status) {
    setErro('')
    setSucesso('')
    setResultadoGeracao(null)
    setSalvando(true)

    try {
      const novoConteudo = await criarConteudo({
        ...formulario,
        observacoes: formulario.observacoes.trim() || null,
        instrucoes_ia: formulario.instrucoes_ia.trim() || null,
        status,
      })
      if (status === 'rascunho') {
        setFormulario({ ...FORMULARIO_INICIAL, cliente_id: formulario.cliente_id })
        setSucesso('Briefing salvo como rascunho.')
      } else {
        setSucesso('Briefing salvo. Gerando os conteúdos com IA...')
        const geracao = await gerarConteudo(novoConteudo.id)
        setResultadoGeracao(geracao)
        setFormulario({ ...FORMULARIO_INICIAL, cliente_id: formulario.cliente_id })
        setSucesso(`${geracao.conteudos.length} conteúdo(s) gerado(s) com sucesso.`)
      }
    } catch (e) {
      setErro(e.message)
      if (!localStorage.getItem('access_token')) navigate('/login')
    } finally {
      setSalvando(false)
    }
  }

  function enviar(evento) {
    evento.preventDefault()
    salvar('pronto_para_gerar')
  }

  return (
    <div className="layout-app">
      <Sidebar />

      <main className="conteudo-principal pagina-conteudo">
        <header className="topo-pagina topo-criacao">
          <div>
            <h1>Criar conteúdo</h1>
            <p>Defina o briefing que será enviado para o serviço de IA.</p>
          </div>
        </header>

        <div className={`grade-criacao ${resultadoGeracao ? '' : 'grade-criacao-formulario'}`}>
          <form className="cartao-formulario" onSubmit={enviar}>
            <div className="campo-formulario campo-largo">
              <label htmlFor="cliente_id">Cliente</label>
              <select
                id="cliente_id"
                name="cliente_id"
                value={formulario.cliente_id}
                onChange={alterarCampo}
                required
              >
                <option value="">Selecione o cliente</option>
                {clientes.map((cliente) => (
                  <option key={cliente.id} value={cliente.id}>{cliente.nome}</option>
                ))}
              </select>
              <small>O briefing e todas as criações ficarão vinculados a este cliente.</small>
            </div>

            <fieldset className="campo-formulario campo-largo grupo-tecnicas selecao-arsenal-briefing">
              <legend>Informações do Arsenal de Copy</legend>
              <p className="ajuda-campo">Selecione as informações salvas que a IA deverá usar. Os campos manuais abaixo continuam valendo normalmente.</p>
              {CAMPOS_ARSENAL.filter(([chave]) => arsenal.informacoes?.[chave]).length ? <div className="opcoes-tecnicas">
                {CAMPOS_ARSENAL.filter(([chave]) => arsenal.informacoes?.[chave]).map(([chave, rotulo]) => <label key={chave} className={formulario.arsenal_campos.includes(chave) ? 'tecnica-ativa' : ''}><input type="checkbox" checked={formulario.arsenal_campos.includes(chave)} onChange={() => alternarCampoArsenal(chave)} /><span>{rotulo}</span></label>)}
              </div> : <p className="texto-apoio">Este cliente ainda não possui informações no Arsenal de Copy.</p>}
              {arsenal.manual_ia && <small>O manual permanente deste cliente será aplicado automaticamente.</small>}
            </fieldset>
            <div className="campo-formulario campo-largo">
              <label htmlFor="intencao">Intenção</label>
              <textarea
                id="intencao"
                name="intencao"
                value={formulario.intencao}
                onChange={alterarCampo}
                placeholder="Ex.: ensinar empreendedores a organizar a produção de conteúdo"
                minLength={3}
                maxLength={500}
                required
              />
            </div>

            <div className="campo-formulario campo-largo">
              <label htmlFor="tema">Tema</label>
              <input
                id="tema"
                name="tema"
                value={formulario.tema}
                onChange={alterarCampo}
                placeholder="Ex.: calendário editorial"
                minLength={3}
                maxLength={300}
                required
              />
            </div>

            <div className="campo-formulario campo-largo">
              <label htmlFor="perspectiva">Perspectiva</label>
              <textarea
                id="perspectiva"
                name="perspectiva"
                value={formulario.perspectiva}
                onChange={alterarCampo}
                placeholder="Ex.: abordagem prática para quem trabalha sozinho"
                minLength={3}
                maxLength={500}
                required
              />
            </div>

            <div className="campo-formulario">
              <label htmlFor="modelo">Modelo</label>
              <select id="modelo" name="modelo" value={formulario.modelo} onChange={alterarCampo}>
                {FRAMEWORKS.map((framework) => (
                  <option key={framework} value={framework}>{framework}</option>
                ))}
              </select>
            </div>

            <div className="campo-formulario">
              <label htmlFor="tom_de_voz">Tom de voz</label>
              <select
                id="tom_de_voz"
                name="tom_de_voz"
                value={formulario.tom_de_voz}
                onChange={alterarCampo}
              >
                <option value="Profissional">Profissional</option>
                <option value="Educativo">Educativo</option>
                <option value="Inspirador">Inspirador</option>
                <option value="Descontraído">Descontraído</option>
                <option value="Persuasivo">Persuasivo</option>
              </select>
            </div>

            <fieldset className="campo-formulario campo-largo grupo-tecnicas">
              <legend>Técnicas de escrita</legend>
              <p className="ajuda-campo">
                Selecione até 8 técnicas que deverão orientar a criação do texto.
              </p>
              <div className="opcoes-tecnicas">
                {TECNICAS.map(([slug, nome]) => {
                  const selecionada = formulario.tecnicas.includes(slug)
                  return (
                    <label key={slug} className={selecionada ? 'tecnica-ativa' : ''}>
                      <input
                        type="checkbox"
                        checked={selecionada}
                        onChange={() => alternarTecnica(slug)}
                      />
                      <span>{nome}</span>
                    </label>
                  )
                })}
              </div>
              <span className="contador-tecnicas">
                {formulario.tecnicas.length}/8 selecionadas
              </span>
            </fieldset>

            <fieldset className="campo-formulario campo-largo grupo-formatos">
              <legend>Quantidade e narrativa por formato</legend>
              <p className="ajuda-campo">
                Escolha de 0 a 10 conteúdos por formato, com no máximo 20 no total.
              </p>
              <div className="grade-formatos-lote">
                {Object.entries(NOMES_FORMATOS).map(([formato, nome]) => (
                  <div
                    key={formato}
                    className={
                      'cartao-formato-lote' +
                      (formulario.quantidades[formato] > 0 ? ' formato-lote-ativo' : '')
                    }
                  >
                    <label htmlFor={`quantidade-${formato}`}>{nome}</label>
                    <input
                      id={`quantidade-${formato}`}
                      type="number"
                      min="0"
                      max="10"
                      value={formulario.quantidades[formato]}
                      onChange={(evento) => alterarQuantidade(formato, evento.target.value)}
                    />
                    <select
                      aria-label={`Narrativa de ${nome}`}
                      value={formulario.narrativas[formato]}
                      onChange={(evento) => alterarNarrativa(formato, evento.target.value)}
                      disabled={formulario.quantidades[formato] === 0}
                    >
                      {NARRATIVAS.map((narrativa) => (
                        <option key={narrativa} value={narrativa}>{narrativa}</option>
                      ))}
                    </select>
                  </div>
                ))}
              </div>
            </fieldset>

            <div className="campo-formulario campo-largo">
              <label htmlFor="narrativa-legenda">Narrativa das legendas</label>
              <select
                id="narrativa-legenda"
                value={formulario.narrativas.legenda}
                onChange={(evento) => alterarNarrativa('legenda', evento.target.value)}
              >
                {NARRATIVAS.map((narrativa) => (
                  <option key={narrativa} value={narrativa}>{narrativa}</option>
                ))}
              </select>
            </div>

            <fieldset className="campo-formulario campo-largo grupo-tamanho-legenda">
              <legend>Tamanho da legenda</legend>
              <div className="opcoes-tamanho-legenda">
                {TAMANHOS_LEGENDA.map((opcao) => (
                  <label
                    key={opcao.valor}
                    className={
                      formulario.tamanho_legenda === opcao.valor
                        ? 'tamanho-legenda-ativo'
                        : ''
                    }
                  >
                    <input
                      type="radio"
                      name="tamanho_legenda"
                      value={opcao.valor}
                      checked={formulario.tamanho_legenda === opcao.valor}
                      onChange={alterarCampo}
                    />
                    <strong>{opcao.nome}</strong>
                    <span>{opcao.limite}</span>
                    <small>{opcao.uso}</small>
                  </label>
                ))}
              </div>
            </fieldset>

            <div className="regras-fixas campo-largo">
              <strong>Regras aplicadas automaticamente</strong>
              <p>
                Voz ativa · comunicação de eu para você · hook nos primeiros 125
                caracteres · parágrafos curtos · contagem exata de caracteres e palavras.
              </p>
            </div>

            <div className="campo-formulario campo-largo">
              <label htmlFor="observacoes">Observações adicionais</label>
              <textarea
                id="observacoes"
                name="observacoes"
                value={formulario.observacoes}
                onChange={alterarCampo}
                placeholder="Restrições, público-alvo, chamada para ação ou outras informações"
                maxLength={2000}
              />
            </div>

            <div className="campo-formulario campo-largo">
              <label htmlFor="instrucoes_ia">Instruções específicas para a IA</label>
              <textarea id="instrucoes_ia" name="instrucoes_ia" value={formulario.instrucoes_ia} onChange={alterarCampo} maxLength={5000} placeholder="Manual opcional somente para esta criação: regras, palavras que devem ser usadas ou evitadas, estrutura e detalhes especiais." />
              <small>Estas instruções complementam o manual permanente salvo no Arsenal do cliente.</small>
            </div>

            {erro && <p className="mensagem-erro campo-largo">{erro}</p>}
            {sucesso && <p className="mensagem-sucesso campo-largo">{sucesso}</p>}

            <div className="acoes-formulario campo-largo">
              <button
                type="button"
                className="botao-secundario"
                disabled={salvando}
                onClick={() => salvar('rascunho')}
              >
                Salvar rascunho
              </button>
              <button type="submit" className="botao-primario" disabled={salvando}>
                {salvando ? <LoaderCircle className="icone-girando" size={17} /> : null}
                Preparar conteúdo
              </button>
            </div>
          </form>

          {resultadoGeracao && <aside className="painel-rascunhos">
              <section className="resultado-geracao">
                <div className="cabecalho-resultado-geracao">
                  <h2>Conteúdos gerados</h2>
                  <span>{resultadoGeracao.modelo}</span>
                </div>
                <ExibirConteudosGerados geracao={resultadoGeracao} />
              </section>
          </aside>}
        </div>
      </main>
    </div>
  )
}

export default CriarConteudo
