import { useEffect, useState } from 'react'
import { LoaderCircle, Trash2, Upload } from 'lucide-react'
import Sidebar from '../components/Sidebar'
import { excluirLogo, obterMarca, salvarMarca } from '../api/contentService'
import { listarClientes } from '../api/clientesService'

const identidadeVazia = () => ({ cores: ['#6C5CE7', '#FFFFFF', '#111827'], tipografia: 'Montserrat', logosAtuais: [] })
const diretrizesVazias = () => ({
  tom_visual: 'Profissional e equilibrado', estilo: '', contraste: '', iluminacao: '',
  texturas: '', fundo: '', composicao: '', elementos: '', posicao_logo: 'Canto superior esquerdo',
  margens: '', manual_visual: '',
})

const TIPOGRAFIAS = [
  { grupo: 'Sem serifa — moderna e limpa', fontes: ['Montserrat', 'Inter', 'Roboto', 'Open Sans', 'Lato', 'Poppins', 'Nunito', 'Raleway', 'Work Sans', 'Source Sans 3', 'DM Sans', 'Ubuntu'] },
  { grupo: 'Serifada — clássica e editorial', fontes: ['Playfair Display', 'Merriweather', 'Lora', 'Libre Baskerville', 'Cormorant Garamond', 'Bitter', 'Noto Serif', 'Roboto Slab'] },
  { grupo: 'Display — marcante e publicitária', fontes: ['Bebas Neue', 'Oswald', 'Anton', 'Archivo Black', 'Abril Fatface', 'Cinzel', 'Alfa Slab One', 'Fjalla One'] },
  { grupo: 'Manuscrita — humana e informal', fontes: ['Dancing Script', 'Pacifico', 'Caveat', 'Satisfy', 'Great Vibes', 'Sacramento', 'Kalam'] },
  { grupo: 'Monoespaçada — técnica e tecnológica', fontes: ['Roboto Mono', 'Source Code Pro', 'Space Mono', 'IBM Plex Mono', 'JetBrains Mono', 'Ubuntu Mono'] },
]

const OPCOES_DIRETRIZES = {
  estilo: ['Fotografia realista', 'Fotografia editorial', 'Fotografia publicitária', 'Ilustração vetorial', 'Ilustração 3D', 'Colagem digital', 'Minimalista geométrico', 'Editorial com tipografia dominante'],
  contraste: ['Baixo — suave', 'Médio — equilibrado', 'Alto — impactante', 'Muito alto — dramático'],
  iluminacao: ['Natural e suave', 'Clara e difusa', 'Quente e acolhedora', 'Fria e tecnológica', 'Dramática lateral', 'Neon e colorida', 'Estúdio profissional'],
  texturas: ['Sem textura — acabamento limpo', 'Papel e granulação suave', 'Orgânica e natural', 'Concreto e urbana', 'Tecido e artesanal', 'Metálica e tecnológica', 'Gradientes suaves'],
  fundo: ['Fundo liso', 'Gradiente', 'Fotográfico desfocado', 'Cenário realista', 'Geométrico abstrato', 'Texturizado sutil', 'Transparente ou recortado'],
  composicao: ['Centralizada e simétrica', 'Assimétrica e dinâmica', 'Minimalista com espaço negativo', 'Editorial em grade', 'Imagem dominante com texto curto', 'Tipografia dominante', 'Recortes e sobreposições'],
  elementos: [
    'Somente elementos essenciais',
    'Ícones e formas geométricas',
    'Pessoas e cenas reais',
    'Objetos e produtos em destaque',
    'Ilustrações e personagens',
    'Paisagens naturais',
    'Paisagens urbanas',
    'Paisagens naturais e animais',
    'Cães',
    'Gatos',
    'Cavalos',
    'Cães e gatos',
    'Animais variados',
    'Tecnologia e inovação',
    'Programação e desenvolvimento de software',
    'Computadores, códigos e interfaces digitais',
    'Inteligência artificial e automação',
    'Dados, gráficos e painéis tecnológicos',
    'Sem pessoas',
    'Sem elementos decorativos',
  ],
  posicao_logo: ['Canto superior esquerdo', 'Canto superior direito', 'Canto inferior esquerdo', 'Canto inferior direito', 'Centro inferior', 'Não aplicar logo automaticamente'],
  margens: ['Compactas', 'Equilibradas', 'Amplas e minimalistas', 'Área segura reforçada para redes sociais'],
}

function OpcoesComValorAtual({ valores, atual }) {
  const opcoes = atual && !valores.includes(atual) ? [atual, ...valores] : valores
  return opcoes.map((opcao) => <option key={opcao} value={opcao}>{opcao}</option>)
}

function Marca() {
  const [clientes, setClientes] = useState([])
  const [clienteId, setClienteId] = useState('')
  const [cores, setCores] = useState(identidadeVazia().cores)
  const [tipografia, setTipografia] = useState(identidadeVazia().tipografia)
  const [logos, setLogos] = useState([])
  const [logosAtuais, setLogosAtuais] = useState([])
  const [diretrizes, setDiretrizes] = useState(diretrizesVazias())
  const [salvando, setSalvando] = useState(false)
  const [mensagem, setMensagem] = useState('')

  useEffect(() => { listarClientes().then((itens) => { setClientes(itens); if (itens[0]) setClienteId(itens[0].id) }).catch((e) => setMensagem(e.message)) }, [])
  useEffect(() => {
    if (!clienteId) return
    setMensagem(''); setLogos([])
    obterMarca(clienteId).then((marca) => { setCores(marca.paleta); setTipografia(marca.tipografia); setLogosAtuais(marca.logos || []); setDiretrizes({ ...diretrizesVazias(), ...(marca.diretrizes_visuais || {}) }) })
      .catch(() => { const vazia = identidadeVazia(); setCores(vazia.cores); setTipografia(vazia.tipografia); setLogosAtuais([]); setDiretrizes(diretrizesVazias()) })
  }, [clienteId])

  function alterarCor(indice, cor) { setCores((atuais) => atuais.map((item, i) => i === indice ? cor : item)) }

  async function enviar(evento) {
    evento.preventDefault(); setSalvando(true); setMensagem('')
    const dados = new FormData(); dados.append('paleta', JSON.stringify(cores)); dados.append('tipografia', tipografia); dados.append('diretrizes_visuais', JSON.stringify(diretrizes))
    logos.forEach((logo) => dados.append('logos', logo))
    try {
      const marca = await salvarMarca(clienteId, dados)
      setLogosAtuais(marca.logos || []); setLogos([]); setMensagem('Identidade do cliente salva com sucesso.')
    } catch (erro) { setMensagem(erro.message) } finally { setSalvando(false) }
  }

  async function removerLogoSalvo(logoId) {
    if (!window.confirm('Deseja excluir este logotipo da marca?')) return
    try {
      await excluirLogo(clienteId, logoId)
      setLogosAtuais((atuais) => atuais.filter((logo) => logo.id !== logoId))
      setMensagem('Logotipo excluído.')
    } catch (erro) { setMensagem(erro.message) }
  }

  return <div className="layout-app"><Sidebar /><main className="conteudo-principal pagina-conteudo">
    <header className="topo-pagina"><div><h1>Marca por cliente</h1><p>Cada cliente possui paleta, tipografia e logotipos próprios.</p></div></header>
    {clientes.length === 0 ? <p>Cadastre um cliente antes de configurar a marca.</p> : <form className="cartao-formulario formulario-marca" onSubmit={enviar}>
      <div className="campo-formulario campo-largo"><label>Cliente</label><select value={clienteId} onChange={(e) => setClienteId(e.target.value)}>{clientes.map((cliente) => <option key={cliente.id} value={cliente.id}>{cliente.nome}</option>)}</select></div>
      <fieldset className="campo-formulario campo-largo"><legend>Paleta de cores</legend><div className="lista-cores-marca">{cores.map((cor, indice) => <label key={indice}><input type="color" value={cor} onChange={(e) => alterarCor(indice, e.target.value.toUpperCase())} /><input value={cor} pattern="#[0-9A-Fa-f]{6}" onChange={(e) => alterarCor(indice, e.target.value)} />{cores.length > 1 && <button type="button" onClick={() => setCores((c) => c.filter((_, i) => i !== indice))}>Remover</button>}</label>)}</div>{cores.length < 8 && <button type="button" className="botao-secundario" onClick={() => setCores((c) => [...c, '#000000'])}>Adicionar cor</button>}</fieldset>
      <div className="campo-formulario campo-largo"><label>Tipografia principal da marca</label><select value={tipografia} onChange={(e) => setTipografia(e.target.value)} required>{!TIPOGRAFIAS.some((grupo) => grupo.fontes.includes(tipografia)) && tipografia && <option value={tipografia}>{tipografia} — configuração atual</option>}{TIPOGRAFIAS.map((grupo) => <optgroup key={grupo.grupo} label={grupo.grupo}>{grupo.fontes.map((fonte) => <option key={fonte} value={fonte}>{fonte}</option>)}</optgroup>)}</select><small>As fontes estão organizadas por estilo para facilitar a escolha da personalidade da marca.</small></div>
      <fieldset className="campo-formulario campo-largo diretrizes-marca"><legend>Direção visual permanente</legend>
        <label><span>Tom visual padrão</span><select value={diretrizes.tom_visual} onChange={(e) => setDiretrizes((d) => ({ ...d, tom_visual: e.target.value }))}><option>Profissional e equilibrado</option><option>Pastel, suave e delicado</option><option>Escuro, dramático e contrastado</option><option>Claro, leve e minimalista</option><option>Vibrante, colorido e energético</option><option>Elegante, sofisticado e premium</option><option>Natural, orgânico e acolhedor</option><option>Futurista, tecnológico e neon</option></select></label>
        {[['estilo','Estilo fotográfico ou ilustrativo'],['contraste','Nível de contraste'],['iluminacao','Iluminação'],['texturas','Texturas'],['fundo','Tipo de fundo'],['composicao','Composição preferida'],['elementos','Elementos predominantes'],['posicao_logo','Posicionamento da logo'],['margens','Margens e espaços']].map(([chave, rotulo]) => <label key={chave}><span>{rotulo}</span><select value={diretrizes[chave]} onChange={(e) => setDiretrizes((d) => ({ ...d, [chave]: e.target.value }))}><option value="">Selecione uma opção</option><OpcoesComValorAtual valores={OPCOES_DIRETRIZES[chave]} atual={diretrizes[chave]} /></select></label>)}
        <label className="diretriz-larga"><span>Manual visual para a IA</span><textarea value={diretrizes.manual_visual} onChange={(e) => setDiretrizes((d) => ({ ...d, manual_visual: e.target.value }))} maxLength={5000} placeholder="Regras visuais detalhadas que devem ser seguidas em todas as peças deste cliente." /></label>
      </fieldset>
      <div className="campo-formulario campo-largo"><label className="upload-marca"><Upload size={20} /><span>Adicionar logotipos — até 6 arquivos</span><input multiple type="file" accept="image/png,image/jpeg,image/webp" onChange={(e) => setLogos(Array.from(e.target.files || []))} /></label>
        <div className="grade-logos-marca">{logosAtuais.map((logo) => <figure key={logo.id} className="arquivo-marca"><img className="preview-logo-marca" src={logo.data_url} alt="Logotipo salvo" /><button type="button" onClick={() => removerLogoSalvo(logo.id)} aria-label="Excluir logotipo"><Trash2 size={15} />Excluir</button></figure>)}{logos.map((logo, indice) => <figure key={`${logo.name}-${logo.size}`} className="arquivo-marca"><img className="preview-logo-marca" src={URL.createObjectURL(logo)} alt="Novo logotipo" /><button type="button" onClick={() => setLogos((atuais) => atuais.filter((_, i) => i !== indice))} aria-label="Remover upload"><Trash2 size={15} />Remover</button></figure>)}</div>
      </div>
      {mensagem && <p className="campo-largo">{mensagem}</p>}
      <button className="botao-primario campo-largo" disabled={salvando}>{salvando && <LoaderCircle className="icone-girando" size={17} />}Salvar marca do cliente</button>
    </form>}
  </main></div>
}

export default Marca
