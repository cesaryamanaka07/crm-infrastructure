const AUTH_SERVICE_URL = import.meta.env.VITE_AUTH_SERVICE_URL

if (!AUTH_SERVICE_URL) {
  throw new Error(
    'VITE_AUTH_SERVICE_URL não foi definida nas variáveis de ambiente.'
  )
}

/**
 * Realiza o login no auth-service.
 *
 * @param {string} email
 * @param {string} senha
 * @returns {Promise<string>} access_token
 */
export async function login(email, senha) {
  const resposta = await fetch(`${AUTH_SERVICE_URL}/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      email,
      senha,
    }),
  })

  if (!resposta.ok) {
    if (resposta.status === 401) {
      throw new Error('E-mail ou senha inválidos.')
    }

    if (resposta.status === 422) {
      throw new Error('Os dados informados são inválidos.')
    }

    if (resposta.status >= 500) {
      throw new Error('O serviço de autenticação está indisponível.')
    }

    throw new Error('Não foi possível realizar o login.')
  }

  const dados = await resposta.json()

  if (!dados.access_token) {
    throw new Error('O servidor não retornou um token de acesso.')
  }

  return dados.access_token
}


/**
 * Busca os dados do usuário autenticado.
 *
 * @param {string} token
 * @returns {Promise<object>}
 */
export async function buscarUsuarioLogado(token) {
  if (!token) {
    throw new Error('Token de autenticação não informado.')
  }

  const resposta = await fetch(`${AUTH_SERVICE_URL}/me`, {
    method: 'GET',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  })

  if (!resposta.ok) {
    if (resposta.status === 401) {
      throw new Error('Sessão expirada. Faça login novamente.')
    }

    if (resposta.status === 403) {
      throw new Error('Você não possui permissão para acessar este recurso.')
    }

    if (resposta.status >= 500) {
      throw new Error('O serviço de autenticação está indisponível.')
    }

    throw new Error('Não foi possível carregar os dados do usuário.')
  }

  return resposta.json()
}
