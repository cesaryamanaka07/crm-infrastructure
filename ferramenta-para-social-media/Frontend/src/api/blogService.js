const BASE = import.meta.env.VITE_BLOG_SERVICE_URL

async function request(path, options = {}) {
  if (!BASE) throw new Error('VITE_BLOG_SERVICE_URL não foi configurada.')
  const token = localStorage.getItem('access_token')
  if (!token) throw new Error('Sessão não encontrada. Faça login novamente.')
  const response = await fetch(`${BASE}${path}`, { ...options, headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json', ...options.headers } })
  if (response.status === 401) { localStorage.removeItem('access_token'); throw new Error('Sessão expirada.') }
  if (!response.ok) {
    let detail = 'Não foi possível concluir a operação.'
    try { const data = await response.json(); detail = typeof data.detail === 'string' ? data.detail : detail } catch { /* sem JSON */ }
    throw new Error(detail)
  }
  return response.status === 204 ? null : response.json()
}

export const obterIntegracaoBlog = (cliente) => request(`/integracoes/${cliente}`)
export const salvarIntegracaoBlog = (cliente, data) => request(`/integracoes/${cliente}`, { method: 'PUT', body: JSON.stringify(data) })
export const testarWordpress = (cliente) => request(`/integracoes/${cliente}/testar-wordpress`, { method: 'POST' })
export const iniciarGoogleSheetsOAuth = (cliente) => request(`/oauth/google/iniciar/${cliente}`)
export const desconectarGoogleSheetsOAuth = (cliente) => request(`/oauth/google/${cliente}`, { method: 'DELETE' })
export const listarPlanilhasGoogle = (cliente) => request(`/integracoes/${cliente}/planilhas-google`)
export const listarIdeiasBlog = (cliente) => request(`/clientes/${cliente}/ideias`)
export const criarIdeiaBlog = (cliente, data) => request(`/clientes/${cliente}/ideias`, { method: 'POST', body: JSON.stringify(data) })
export const gerarIdeiasBlog = (cliente, data) => request(`/clientes/${cliente}/ideias/gerar`, { method: 'POST', body: JSON.stringify(data) })
export const gerarArtigoBlog = (ideia) => request(`/ideias/${ideia}/gerar-artigo`, { method: 'POST' })
export const excluirIdeiaBlog = (ideia) => request(`/ideias/${ideia}`, { method: 'DELETE' })
export const listarArtigosBlog = (cliente) => request(`/clientes/${cliente}/artigos`)
export const obterArtigoBlog = (artigo) => request(`/artigos/${artigo}`)
export const salvarArtigoBlog = (artigo, data) => request(`/artigos/${artigo}`, { method: 'PUT', body: JSON.stringify(data) })
export const publicarArtigoWordpress = (artigo, data) => request(`/artigos/${artigo}/wordpress`, { method: 'POST', body: JSON.stringify(data) })
export const excluirArtigoBlog = (artigo) => request(`/artigos/${artigo}`, { method: 'DELETE' })
