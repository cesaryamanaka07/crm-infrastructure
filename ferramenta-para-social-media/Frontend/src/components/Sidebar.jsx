import { NavLink, useNavigate } from 'react-router-dom'
import { BookOpenText, Files, LayoutDashboard, Share2, PenSquare, LogOut, Palette, Images, Users } from 'lucide-react'

const ITENS_NAV = [
  { rota: '/dashboard', rotulo: 'Dashboard', Icone: LayoutDashboard },
  { rota: '/clientes', rotulo: 'Clientes', Icone: Users },
  { rota: '/arsenal-copy', rotulo: 'Arsenal de Copy', Icone: BookOpenText },
  { rota: '/redes-sociais', rotulo: 'Redes Sociais', Icone: Share2 },
  { rota: '/criar-conteudo', rotulo: 'Criar Conteúdo', Icone: PenSquare },
  { rota: '/conteudos-criados', rotulo: 'Conteúdos Criados', Icone: Files },
  { rota: '/marca', rotulo: 'Marca', Icone: Palette },
  { rota: '/midias', rotulo: 'Criar imagens', Icone: Images },
]

function Sidebar() {
  const navigate = useNavigate()

  function sair() {
    localStorage.removeItem('access_token')
    navigate('/login')
  }

  return (
    <aside className="barra-lateral">
      <div className="marca">Conteúdo<span>.</span></div>

      <nav className="navegacao-lateral">
        {ITENS_NAV.map(({ rota, rotulo, Icone }) => (
          <NavLink
            key={rota}
            to={rota}
            className={({ isActive }) =>
              'item-nav' + (isActive ? ' item-nav-ativo' : '')
            }
          >
            <Icone size={18} strokeWidth={2} />
            {rotulo}
          </NavLink>
        ))}
      </nav>

      <button className="item-nav item-sair" onClick={sair}>
        <LogOut size={18} strokeWidth={2} />
        Sair
      </button>
    </aside>
  )
}

export default Sidebar
