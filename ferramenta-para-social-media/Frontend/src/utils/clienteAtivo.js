const CHAVE = 'cliente_ativo_id'

export function obterClienteAtivo() { return localStorage.getItem(CHAVE) || '' }

export function escolherClienteInicial(clientes, fallback = '') {
  const salvo = obterClienteAtivo()
  return clientes.some((cliente) => cliente.id === salvo) ? salvo : (fallback || clientes[0]?.id || '')
}

export function definirClienteAtivo(id) {
  if (id) localStorage.setItem(CHAVE, id)
  else localStorage.removeItem(CHAVE)
  window.dispatchEvent(new CustomEvent('cliente-ativo-alterado', { detail: id }))
}

