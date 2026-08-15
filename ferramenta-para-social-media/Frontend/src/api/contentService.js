const CONTENT_SERVICE_URL = import.meta.env.VITE_CONTENT_SERVICE_URL

if (!CONTENT_SERVICE_URL) {
  throw new Error(
    'VITE_CONTENT_SERVICE_URL não foi definida nas variáveis de ambiente.'
  )
}

async function requisicaoAutenticada(caminho, opcoes = {}) {
  const token = localStorage.getItem('access_token')
  if (!token) {
    throw new Error('Sessão não encontrada. Faça login novamente.')
  }

  const resposta = await fetch(`${CONTENT_SERVICE_URL}${caminho}`, {
    ...opcoes,
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
      ...opcoes.headers,
    },
  })

  if (resposta.status === 401) {
    localStorage.removeItem('access_token')
    throw new Error('Sessão expirada. Faça login novamente.')
  }

  if (!resposta.ok) {
    let detalhe
    try {
      detalhe = (await resposta.json()).detail
    } catch {
      detalhe = null
    }
    throw new Error(
      typeof detalhe === 'string' ? detalhe : 'Não foi possível concluir a operação.'
    )
  }

  return resposta.status === 204 ? null : resposta.json()
}

async function requisicaoMultipart(caminho, formulario, metodo = 'POST') {
  const token = localStorage.getItem('access_token')
  if (!token) throw new Error('Sessão não encontrada. Faça login novamente.')
  const resposta = await fetch(`${CONTENT_SERVICE_URL}${caminho}`, {
    method: metodo,
    headers: { Authorization: `Bearer ${token}` },
    body: formulario,
  })
  if (!resposta.ok) {
    let detalhe = 'Não foi possível concluir a operação.'
    try { detalhe = (await resposta.json()).detail || detalhe } catch { /* resposta sem JSON */ }
    throw new Error(detalhe)
  }
  return resposta.json()
}

export function criarConteudo(dados) {
  return requisicaoAutenticada('/conteudos', {
    method: 'POST',
    body: JSON.stringify(dados),
  })
}

export function listarConteudos() {
  return requisicaoAutenticada('/conteudos')
}

export function gerarConteudo(conteudoId) {
  return requisicaoAutenticada(`/conteudos/${conteudoId}/gerar`, {
    method: 'POST',
  })
}

export function listarGeracoes(conteudoId) {
  return requisicaoAutenticada(`/conteudos/${conteudoId}/geracoes`)
}

export function excluirGeracao(conteudoId, geracaoId) {
  return requisicaoAutenticada(`/conteudos/${conteudoId}/geracoes/${geracaoId}`, {
    method: 'DELETE',
  })
}

export function listarBiblioteca(clienteId = '') {
  const consulta = clienteId ? `?cliente_id=${encodeURIComponent(clienteId)}` : ''
  return requisicaoAutenticada(`/conteudos/biblioteca${consulta}`)
}

export function atualizarGeracao(conteudoId, geracaoId, conteudos) {
  return requisicaoAutenticada(`/conteudos/${conteudoId}/geracoes/${geracaoId}`, {
    method: 'PATCH',
    body: JSON.stringify({ conteudos }),
  })
}

export function gerarImagens(conteudoId, opcoes) {
  return requisicaoAutenticada(`/conteudos/${conteudoId}/gerar-imagens`, {
    method: 'POST',
    body: JSON.stringify(opcoes),
  })
}

export function obterMarca(clienteId) {
  return requisicaoAutenticada(`/marcas/${clienteId}`)
}

export function salvarMarca(clienteId, formulario) {
  return requisicaoMultipart(`/marcas/${clienteId}`, formulario, 'PUT')
}

export function excluirLogo(clienteId, logoId) {
  return requisicaoAutenticada(`/marcas/${clienteId}/logos/${logoId}`, { method: 'DELETE' })
}

export function gerarMidiaImagem(formulario) {
  return requisicaoMultipart('/midias/gerar-imagem', formulario)
}

export function excluirImagem(imagemId) {
  return requisicaoAutenticada(`/midias/imagens/${imagemId}`, { method: 'DELETE' })
}

export function aprovarImagem(dados) {
  return requisicaoAutenticada('/midias/aprovar-imagem', {
    method: 'POST', body: JSON.stringify(dados),
  })
}

export function obterArsenal(clienteId) {
  return requisicaoAutenticada(`/arsenais/${clienteId}`)
}

export function salvarArsenal(clienteId, dados) {
  return requisicaoAutenticada(`/arsenais/${clienteId}`, {
    method: 'PUT',
    body: JSON.stringify(dados),
  })
}
