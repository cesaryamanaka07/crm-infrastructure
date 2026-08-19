const SOCIAL_SERVICE_URL = import.meta.env.VITE_SOCIAL_SERVICE_URL

async function request(path, options = {}) {
  const token = localStorage.getItem('access_token')
  if (!token) throw new Error('Sessão não encontrada. Faça login novamente.')
  const resposta = await fetch(`${SOCIAL_SERVICE_URL}${path}`, { ...options, headers: { Authorization: `Bearer ${token}`, ...(options.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }), ...options.headers } })
  if (!resposta.ok) {
    let detalhe = 'Não foi possível concluir a operação.'
    try { detalhe = (await resposta.json()).detail || detalhe } catch { /* sem JSON */ }
    throw new Error(detalhe)
  }
  return resposta.status === 204 ? null : resposta.json()
}

export const listarConexoes = () => request('/conexoes')
export const buscarInsights = (conexaoIds) => request('/insights', { method: 'POST', body: JSON.stringify({ conexao_ids: conexaoIds }) })
export const iniciarConexao = (provider, clienteId) => request(`/oauth/${provider}/iniciar`, { method: 'POST', body: JSON.stringify({ cliente_id: clienteId }) })
export const selecionarConexao = (id) => request(`/conexoes/${id}/selecionar`, { method: 'PUT' })
export const desconectarRede = (id) => request(`/conexoes/${id}`, { method: 'DELETE' })
export const gerarBriefingPostagem = (ideia, formato) => { const form = new FormData(); form.append('ideia', JSON.stringify(ideia)); form.append('formato', formato); return request('/publicacoes/briefing', { method: 'POST', body: form }) }
export const criarPublicacao = (form) => request('/publicacoes', { method: 'POST', body: form })
export const listarPublicacoes = (clienteId) => request(`/publicacoes${clienteId ? `?cliente_id=${encodeURIComponent(clienteId)}` : ''}`)
export const publicarAgora = (id) => request(`/publicacoes/${id}/publicar`, { method: 'POST' })
export const cancelarPublicacao = (id) => request(`/publicacoes/${id}/cancelar`, { method: 'POST' })
