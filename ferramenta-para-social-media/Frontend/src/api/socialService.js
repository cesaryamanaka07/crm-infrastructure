const SOCIAL_SERVICE_URL = import.meta.env.VITE_SOCIAL_SERVICE_URL

async function request(path, options = {}) {
  const token = localStorage.getItem('access_token')
  if (!token) throw new Error('Sessão não encontrada. Faça login novamente.')
  const response = await fetch(`${SOCIAL_SERVICE_URL}${path}`, {
    ...options,
    headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json', ...options.headers },
  })
  if (!response.ok) {
    let detail = 'Não foi possível concluir a operação.'
    try { detail = (await response.json()).detail || detail } catch { /* sem JSON */ }
    throw new Error(detail)
  }
  return response.status === 204 ? null : response.json()
}

export const listarConexoes = () => request('/conexoes')
export const iniciarConexao = (provider, clienteId) => request(`/oauth/${provider}/iniciar`, {
  method: 'POST', body: JSON.stringify({ cliente_id: clienteId }),
})
export const selecionarConexao = (id) => request(`/conexoes/${id}/selecionar`, { method: 'PUT' })
export const desconectarRede = (id) => request(`/conexoes/${id}`, { method: 'DELETE' })
