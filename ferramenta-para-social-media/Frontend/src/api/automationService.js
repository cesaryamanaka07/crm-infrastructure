const BASE_URL = import.meta.env.VITE_AUTOMATION_SERVICE_URL

function detalheDaResposta(dados, fallback) {
  if (typeof dados?.detail === 'string') return dados.detail
  if (Array.isArray(dados?.detail)) return dados.detail.map((item) => item.msg).filter(Boolean).join('; ') || fallback
  return typeof dados?.message === 'string' ? dados.message : fallback
}

async function request(path, options = {}) {
  const token = localStorage.getItem('access_token')
  if (!token) throw new Error('Sessão não encontrada. Faça login novamente.')

  let response
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      ...options,
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
        ...options.headers,
      },
    })
  } catch {
    throw new Error('O serviço de automações está indisponível. Verifique o gateway da plataforma.')
  }

  if (response.status === 401) {
    localStorage.removeItem('access_token')
    throw new Error('Sessão expirada. Faça login novamente.')
  }

  if (!response.ok) {
    const fallback = response.status === 502
      ? 'O n8n não está acessível pelo endereço configurado ou a API pública está bloqueada pelo proxy.'
      : response.status === 503
        ? 'A integração do n8n ainda não está configurada no servidor. Gere uma N8N_API_KEY no painel do n8n.'
        : 'Não foi possível concluir a operação.'
    let detail = fallback
    try { detail = detalheDaResposta(await response.json(), fallback) } catch { /* resposta sem JSON */ }
    if (response.status === 502 && detail === 'Não foi possível concluir a operação.') detail = fallback
    throw new Error(detail)
  }

  return response.status === 204 ? null : response.json()
}

export const listarFluxos = (clienteId = '', canal = '') => request(`/fluxos?${new URLSearchParams({ ...(clienteId && { cliente_id: clienteId }), ...(canal && { canal }) })}`)
export const criarFluxo = (dados) => request('/fluxos', { method: 'POST', body: JSON.stringify(dados) })
export const salvarFluxo = (id, dados) => request(`/fluxos/${id}`, { method: 'PUT', body: JSON.stringify(dados) })
export const excluirFluxo = (id) => request(`/fluxos/${id}`, { method: 'DELETE' })
export const listarContatos = (clienteId = '') => request(`/contatos${clienteId ? `?cliente_id=${clienteId}` : ''}`)
export const criarContato = (dados) => request('/contatos', { method: 'POST', body: JSON.stringify(dados) })
export const salvarContato = (id, dados) => request(`/contatos/${id}`, { method: 'PUT', body: JSON.stringify(dados) })
export const excluirContato = (id) => request(`/contatos/${id}`, { method: 'DELETE' })
export const obterConfiguracoesCrm = (clienteId) => request(`/crm/configuracoes/${clienteId}`)
export const salvarConfiguracoesCrm = (clienteId, dados) => request(`/crm/configuracoes/${clienteId}`, { method: 'PUT', body: JSON.stringify(dados) })
export const listarAtividades = (clienteId = '', inicio = '', fim = '') => request(`/crm/atividades?${new URLSearchParams({ ...(clienteId && { cliente_id: clienteId }), ...(inicio && { inicio }), ...(fim && { fim }) })}`)
export const criarAtividade = (dados) => request('/crm/atividades', { method: 'POST', body: JSON.stringify(dados) })
export const salvarAtividade = (id, dados) => request(`/crm/atividades/${id}`, { method: 'PUT', body: JSON.stringify(dados) })
export const excluirAtividade = (id) => request(`/crm/atividades/${id}`, { method: 'DELETE' })
export const obterIntegracaoCalendario = (clienteId) => request(`/crm/calendario/integracao/${clienteId}`)
export const salvarIntegracaoCalendario = (clienteId, dados) => request(`/crm/calendario/integracao/${clienteId}`, { method: 'PUT', body: JSON.stringify(dados) })
export const iniciarGoogleOAuth = (clienteId) => request(`/oauth/google/iniciar/${clienteId}`)
export const desconectarGoogleOAuth = (clienteId) => request(`/oauth/google/${clienteId}`, { method: 'DELETE' })
export const obterConfiguracoes = (clienteId) => request(`/configuracoes/${clienteId}`)
export const salvarConfiguracoes = (clienteId, cores) => request(`/configuracoes/${clienteId}`, { method: 'PUT', body: JSON.stringify({ cores }) })
export const obterIntegracoes = (clienteId) => request(`/integracoes/${clienteId}`)
export const obterWhatsapp = (clienteId) => request(`/integracoes/${clienteId}/whatsapp`)
export const criarWhatsapp = (clienteId) => request(`/integracoes/${clienteId}/whatsapp`, { method: 'POST' })
export const obterQrCodeWhatsapp = (clienteId) => request(`/integracoes/${clienteId}/whatsapp/qrcode`)
export const excluirWhatsapp = (clienteId) => request(`/integracoes/${clienteId}/whatsapp`, { method: 'DELETE' })
export const salvarTypebots = (clienteId, bots) => request(`/integracoes/${clienteId}/typebots`, { method: 'PUT', body: JSON.stringify(bots) })
export const listarN8nWorkflows = (clienteId, todos = false) => request(`/integracoes/${clienteId}/n8n/workflows?todos=${todos}`)
export const criarN8nWorkflow = (clienteId, nome) => request(`/integracoes/${clienteId}/n8n/workflows`, { method: 'POST', body: JSON.stringify({ nome }) })
export const vincularN8nWorkflows = (clienteId, workflowIds) => request(`/integracoes/${clienteId}/n8n/workflows`, { method: 'PUT', body: JSON.stringify({ workflow_ids: workflowIds }) })
export const acionarN8nWorkflow = (clienteId, workflowId, acao) => request(`/integracoes/${clienteId}/n8n/workflows/${workflowId}/${acao}`, { method: 'POST' })
export const listarN8nExecucoes = (clienteId) => request(`/integracoes/${clienteId}/n8n/execucoes`)
