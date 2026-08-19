import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Layers } from 'lucide-react'
import { login } from '../api/authService'

function Login() {
  const [email, setEmail] = useState('')
  const [senha, setSenha] = useState('')
  const [erro, setErro] = useState('')
  const [carregando, setCarregando] = useState(false)

  const navigate = useNavigate()

  async function lidarComEnvio(evento) {
    evento.preventDefault()
    setErro('')
    setCarregando(true)

    try {
      const token = await login(email, senha)
      localStorage.setItem('access_token', token)
      navigate('/dashboard')
    } catch (erroCapturado) {
      setErro(erroCapturado.message)
    } finally {
      setCarregando(false)
    }
  }

  return (
    <div className="tela-login-fundo">
      <form className="cartao-login" onSubmit={lidarComEnvio}>
        <div className="marca-login">
          <div className="icone-marca">
            <Layers size={22} strokeWidth={2.5} />
          </div>
          <span className="texto-marca">Minha Ferramenta de Criação de Conteúdo<span className="ponto-marca">.</span></span>
        </div>

        <h1>Painel de Conteúdo</h1>
        <p className="subtitulo-login">Entre para gerenciar seus posts</p>

        <label htmlFor="email">E-mail</label>
        <input
          id="email"
          type="email"
          placeholder="seu@email.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />

        <label htmlFor="senha">Senha</label>
        <input
          id="senha"
          type="password"
          placeholder="Digite sua senha"
          value={senha}
          onChange={(e) => setSenha(e.target.value)}
          required
        />

        {erro && <p className="mensagem-erro">{erro}</p>}

        <button type="submit" disabled={carregando}>
          {carregando ? 'Entrando...' : 'Entrar'}
        </button>
      </form>
    </div>
  )
}

export default Login