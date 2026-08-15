export const GRUPOS_ARSENAL = [
  { titulo: 'Informações do cliente — especialista', campos: [
    ['super_autoridade', 'Por que confiar? (Super Autoridade)'],
    ['missao_storytelling', 'Por que o produto foi desenvolvido? (Storytelling da missão)'],
  ] },
  { titulo: 'Informações do mercado — atualidade', campos: [
    ['concorrentes', 'Quem vende algo similar? Como? No que estão falhando?'],
    ['usp_puv', 'Qual é a USP/PUV (Proposta Única de Valor)?'],
    ['big_idea', 'Qual é a Big Idea?'],
  ] },
  { titulo: 'Informações da audiência — público-alvo', campos: [
    ['publico_alvo', 'Público-alvo'],
    ['problemas_publico', 'Maiores problemas do público — o que tira o sono?'],
    ['mitos_publico', 'Quais são os mitos em que acreditam?'],
    ['desejos_sonhos', 'Quais são os desejos e sonhos, inclusive secretos?'],
    ['objecoes_argumentos', 'Objeções e argumentos para quebrá-las'],
    ['provas_sociais', 'Links das provas sociais'],
  ] },
  { titulo: 'Informações do produto ou serviço', campos: [
    ['nome_produto', 'Nome do produto ou serviço'],
    ['entregaveis', 'Entregáveis do produto'],
    ['beneficios_entregaveis', 'Benefícios dos entregáveis'],
    ['como_funciona', 'Como funciona — ferramentas, módulos e entregáveis'],
    ['transformacao', 'Transformação que o produto traz'],
    ['super_promessa', 'Super-promessa'],
    ['bonus', 'Bônus'],
    ['mecanismo_unico', 'Novidades e mecanismo único'],
    ['investimento', 'Investimento'],
    ['custo_nao_investir', 'Quanto custa não investir nesse produto?'],
    ['links_provas', 'Links das provas do produto'],
  ] },
  { titulo: 'Comunicação', campos: [
    ['comunicacao_especialista', 'Maneira com que o especialista se comunica'],
  ] },
]

export const CAMPOS_ARSENAL = GRUPOS_ARSENAL.flatMap((grupo) => grupo.campos)
