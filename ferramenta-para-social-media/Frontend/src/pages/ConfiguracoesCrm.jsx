import { useEffect, useMemo, useState } from 'react'
import { Check, Eye, Plus, RotateCcw, Save, Trash2 } from 'lucide-react'
import Sidebar from '../components/Sidebar'
import { listarClientes } from '../api/clientesService'
import { obterConfiguracoesCrm, salvarConfiguracoesCrm } from '../api/automationService'
import { escolherClienteInicial } from '../utils/clienteAtivo'

const THEME_STORAGE_KEY = 'theme'
const THEME_COLORS_STORAGE_KEY = 'theme-dark-colors'

const DEFAULT_DARK_COLORS = {
  'app-bg': '#0b1220',
  'sidebar-bg': '#111827',
  'surface': '#172033',
  'surface-elevated': '#1f2a3d',
  'input-bg': '#0f172a',
  'border': '#334155',
  'text': '#f8fafc',
  'text-muted': '#cbd5e1',
  'accent': '#60a5fa',
  'primary': '#2563eb',
  'primary-hover': '#3b82f6',
  'success': '#34d399',
  'warning': '#fbbf24',
  'danger': '#f87171',
}

const COLOR_FIELDS = [
  ['app-bg', 'Fundo geral'],
  ['sidebar-bg', 'Barra lateral'],
  ['surface', 'Painéis e cards'],
  ['surface-elevated', 'Modais e painéis elevados'],
  ['input-bg', 'Campos de formulário'],
  ['border', 'Bordas'],
  ['text', 'Texto principal'],
  ['text-muted', 'Texto secundário'],
  ['accent', 'Links e destaques'],
  ['primary', 'Botão primário'],
  ['primary-hover', 'Botão primário ao passar o mouse'],
  ['success', 'Sucesso'],
  ['warning', 'Aviso'],
  ['danger', 'Erro'],
]

const novo = (prefixo) => ({ id: `${prefixo}_${crypto.randomUUID()}`, nome: 'Nova opção', cor_fundo: '#e2e8f0', cor_texto: '#334155' })

function luminancia(hex) {
  const valor = hex.replace('#', '')
  if (!/^[0-9a-f]{6}$/i.test(valor)) return 0
  const rgb = [0, 2, 4].map(i => parseInt(valor.slice(i, i + 2), 16) / 255).map(c => c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4)
  return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]
}

function contraste(a, b) {
  const claro = Math.max(luminancia(a), luminancia(b))
  const escuro = Math.min(luminancia(a), luminancia(b))
  return (claro + 0.05) / (escuro + 0.05)
}

function aplicarCores(cores) {
  Object.entries(cores).forEach(([nome, valor]) => document.documentElement.style.setProperty(`--${nome}`, valor))
}

function ConfiguracoesCrm() {
  const [clientes, setClientes] = useState([])
  const [clienteId, setClienteId] = useState('')
  const [aba, setAba] = useState('etapas')
  const [config, setConfig] = useState({ etapas: [], tags: [], qualidades: [] })
  const [msg, setMsg] = useState('')
  const [tema, setTema] = useState(() => localStorage.getItem(THEME_STORAGE_KEY) || 'system')
  const [cores, setCores] = useState(() => {
    try { return { ...DEFAULT_DARK_COLORS, ...JSON.parse(localStorage.getItem(THEME_COLORS_STORAGE_KEY) || '{}') } } catch { return DEFAULT_DARK_COLORS }
  })

  useEffect(() => { listarClientes().then(x => { setClientes(x); setClienteId(escolherClienteInicial(x)) }) }, [])
  useEffect(() => { if (clienteId) obterConfiguracoesCrm(clienteId).then(setConfig).catch(e => setMsg(e.message)) }, [clienteId])

  const atualizar = (i, chave, valor) => setConfig(c => ({ ...c, [aba]: c[aba].map((x, n) => n === i ? { ...x, [chave]: valor } : x) }))
  const salvar = async () => { try { setConfig(await salvarConfiguracoesCrm(clienteId, config)); setMsg('Configurações do CRM salvas.') } catch (e) { setMsg(e.message) } }

  const alterarTema = valor => {
    setTema(valor)
    localStorage.setItem(THEME_STORAGE_KEY, valor)
    document.documentElement.dataset.themePreference = valor
    document.documentElement.dataset.theme = valor === 'system' ? (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light') : valor
  }
  const alterarCor = (nome, valor) => {
    const novas = { ...cores, [nome]: valor }
    setCores(novas)
    aplicarCores(novas)
  }
  const salvarAparencia = () => {
    localStorage.setItem(THEME_STORAGE_KEY, tema)
    localStorage.setItem(THEME_COLORS_STORAGE_KEY, JSON.stringify(cores))
    setMsg('Aparência salva neste navegador.')
  }
  const restaurarAparencia = () => {
    setCores(DEFAULT_DARK_COLORS)
    aplicarCores(DEFAULT_DARK_COLORS)
    localStorage.removeItem(THEME_COLORS_STORAGE_KEY)
    setMsg('Cores restauradas. Você pode salvar para manter esta configuração.')
  }

  const alertasContraste = useMemo(() => {
    const pares = [['text', 'app-bg'], ['text-muted', 'surface'], ['text', 'surface'], ['accent', 'app-bg']]
    return pares.filter(([texto, fundo]) => contraste(cores[texto], cores[fundo]) < 4.5)
  }, [cores])

  return <div className="layout-app"><Sidebar/><main className="conteudo-principal pagina-crm">
    <header className="topo-pagina"><div><h1>Configurações</h1><p>Personalize o CRM e a aparência da plataforma.</p></div><button className="botao-primario" onClick={salvar}>Salvar CRM</button></header>
    {msg && <p className="mensagem-integracao">{msg}</p>}
    <section className="aparencia-config-painel">
      <header className="aparencia-config-cabecalho"><div><h2>Aparência personalizada</h2><p>As cores são aplicadas ao vivo enquanto você edita.</p></div><Eye size={22}/></header>
      <div className="aparencia-config-controles"><label>Modo de exibição<select value={tema} onChange={e => alterarTema(e.target.value)}><option value="system">Seguir sistema</option><option value="light">Claro</option><option value="dark">Escuro</option></select></label><div className="aparencia-config-acoes"><button className="botao-secundario" onClick={restaurarAparencia}><RotateCcw size={16}/> Restaurar cores</button><button className="botao-primario" onClick={salvarAparencia}><Save size={16}/> Salvar aparência</button></div></div>
      {alertasContraste.length > 0 && <p className="aparencia-contraste-alerta">Algumas combinações podem ter pouco contraste. A prévia abaixo ajuda a ajustar as cores.</p>}
      <div className="aparencia-cores-grid">{COLOR_FIELDS.map(([nome, rotulo]) => <label className="aparencia-cor-campo" key={nome}><span>{rotulo}</span><input type="color" value={cores[nome]} onChange={e => alterarCor(nome, e.target.value)}/><code>{cores[nome]}</code></label>)}</div>
      <div className="aparencia-preview"><div><strong>Pré-visualização</strong><p>Texto principal e texto secundário sobre um painel.</p></div><div className="aparencia-preview-acoes"><button className="botao-primario"><Check size={15}/> Ação principal</button><button className="botao-secundario">Ação secundária</button></div></div>
    </section>
    <label className="filtro-contatos">Cliente<select value={clienteId} onChange={e => setClienteId(e.target.value)}>{clientes.map(x => <option key={x.id} value={x.id}>{x.nome}</option>)}</select></label>
    <nav className="crm-config-tabs">{[['etapas', 'Etapas do funil'], ['tags', 'Tags'], ['qualidades', 'Qualidade do lead']].map(([id, nome]) => <button className={aba === id ? 'ativo' : ''} key={id} onClick={() => setAba(id)}>{nome}</button>)}</nav>
    <section className="crm-config-painel"><header><h2>{aba === 'etapas' ? 'Etapas do funil' : aba === 'tags' ? 'Tags' : 'Qualidades'}</h2><button className="botao-secundario" onClick={() => setConfig(c => ({ ...c, [aba]: [...c[aba], novo(aba)] }))}><Plus size={16}/> Adicionar</button></header>{config[aba].map((x, i) => <div className="crm-config-item" key={x.id}><span className="crm-preview" style={{ background: x.cor_fundo, color: x.cor_texto }}>{x.nome}</span><label>Nome<input value={x.nome} onChange={e => atualizar(i, 'nome', e.target.value)}/></label><label>Fundo<input type="color" value={x.cor_fundo} onChange={e => atualizar(i, 'cor_fundo', e.target.value)}/></label><label>Texto<input type="color" value={x.cor_texto} onChange={e => atualizar(i, 'cor_texto', e.target.value)}/></label><button className="botao-icone-remover" onClick={() => setConfig(c => ({ ...c, [aba]: c[aba].filter((_, n) => n !== i) }))}><Trash2/></button></div>)}</section>
  </main></div>
}

export default ConfiguracoesCrm
