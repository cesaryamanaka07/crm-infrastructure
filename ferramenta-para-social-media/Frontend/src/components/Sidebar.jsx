import { useEffect, useState } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { BookOpenText, Bot, CalendarDays, ContactRound, Files, Filter, GitBranch, Instagram, LayoutDashboard, MessageCircle, MessageSquareQuote, Newspaper, Settings, Share2, PenSquare, LogOut, Palette, Users, Workflow, CalendarClock } from 'lucide-react'
import ThemeToggle from './ThemeToggle'
import { listarClientes } from '../api/clientesService'
import { definirClienteAtivo, escolherClienteInicial } from '../utils/clienteAtivo'

const ITENS_NAV = [
  { rota: '/dashboard', rotulo: 'Dashboard', Icone: LayoutDashboard }, { rota: '/clientes', rotulo: 'Clientes', Icone: Users }, { rota: '/arsenal-copy', rotulo: 'Arsenal de Copy', Icone: BookOpenText }, { rota: '/narrativa-estrategica', rotulo: 'Narrativa Estratégica', Icone: MessageSquareQuote }, { rota: '/linha-editorial', rotulo: 'Linha Editorial', Icone: Filter }, { rota: '/redes-sociais', rotulo: 'Redes Sociais', Icone: Share2 }, { rota: '/criar-conteudo', rotulo: 'Criar Conteúdo', Icone: PenSquare }, { rota: '/conteudos-criados', rotulo: 'Conteúdos Criados', Icone: Files }, { rota: '/marca', rotulo: 'Marca', Icone: Palette }, { rota: '/midias', rotulo: 'AGENDAMENTO POSTAGEM', Icone: CalendarClock }, { rota: '/blog', rotulo: 'Artigos de Blog', Icone: Newspaper }, { rota: '/automacao-facebook', rotulo: 'Automação Facebook', Icone: Bot }, { rota: '/automacao-instagram', rotulo: 'Automação Instagram', Icone: Instagram }, { rota: '/automacoes', rotulo: 'Todas as automações', Icone: GitBranch }, { rota: '/whatsapp', rotulo: 'WhatsApp', Icone: MessageCircle }, { rota: '/n8n', rotulo: 'n8n', Icone: Workflow }, { rota: '/crm', rotulo: 'CRM', Icone: ContactRound }, { rota: '/crm/calendario', rotulo: 'Calendário', Icone: CalendarDays }, { rota: '/crm/configuracoes', rotulo: 'CONFIGURAÇÕES', Icone: Settings },
]

function Sidebar() {
  const navigate = useNavigate(); const [clientes, setClientes] = useState([]); const [clienteAtivo, setClienteAtivo] = useState('')
  useEffect(() => { listarClientes().then((lista) => { setClientes(lista); setClienteAtivo(escolherClienteInicial(lista)) }).catch(() => {}) }, [])
  function trocarCliente(id) { definirClienteAtivo(id); setClienteAtivo(id) }
  function sair() { localStorage.removeItem('access_token'); navigate('/login') }
  return <aside className="barra-lateral"><div className="topo-sidebar"><div className="marca">Conteúdo<span>.</span></div><ThemeToggle /></div>{clientes.length > 0 && <label className="cliente-ativo-sidebar"><span>Cliente ativo</span><select value={clienteAtivo} onChange={(e) => trocarCliente(e.target.value)}>{clientes.map((cliente) => <option key={cliente.id} value={cliente.id}>{cliente.nome}</option>)}</select></label>}<nav className="navegacao-lateral">{ITENS_NAV.map(({ rota, rotulo, Icone }) => <NavLink key={rota} to={rota} className={({ isActive }) => 'item-nav' + (isActive ? ' item-nav-ativo' : '')}><Icone size={18} strokeWidth={2} />{rotulo}</NavLink>)}</nav><button className="item-nav item-sair" onClick={sair}><LogOut size={18} strokeWidth={2} />Sair</button></aside>
}
export default Sidebar
