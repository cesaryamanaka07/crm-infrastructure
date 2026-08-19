const BASE_URL = import.meta.env.VITE_SOCIAL_SERVICE_URL

async function request(path = '', options = {}) {
  const token = localStorage.getItem('access_token')
  if (!token) throw new Error('Sessão não encontrada. Faça login novamente.')
  const response = await fetch(`${BASE_URL}/clientes${path}`, {
    ...options,
    headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json', ...options.headers },
  })
  if (!response.ok) {
    let detail = 'Não foi possível concluir a operação.'
    try {
      const data = await response.json()
      detail = typeof data.detail === 'string' ? data.detail : data.detail?.[0]?.msg || detail
    } catch { /* sem JSON */ }
    throw new Error(detail)
  }
  return response.status === 204 ? null : response.json()
}

export const listarClientes = () => request()
export const criarCliente = (dados) => request('', { method: 'POST', body: JSON.stringify(dados) })
export const atualizarCliente = (id, dados) => request(`/${id}`, { method: 'PUT', body: JSON.stringify(dados) })
export const excluirCliente = (id) => request(`/${id}`, { method: 'DELETE' })
export const iniciarGoogleCliente = (id) => request(`/${id}/google/iniciar`)
export const desconectarGoogleCliente = (id) => request(`/${id}/google`, { method: 'DELETE' })
