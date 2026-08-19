import { useEffect, useMemo, useState } from 'react'
import { Check, ChevronLeft, ChevronRight, Cloud, Pencil, Plus, Trash2, X } from 'lucide-react'
import Sidebar from '../components/Sidebar'
import { listarClientes } from '../api/clientesService'
import { criarAtividade, excluirAtividade, listarAtividades, listarContatos, salvarAtividade } from '../api/automationService'
import { escolherClienteInicial } from '../utils/clienteAtivo'

const DIA = 86400000
const inicioDia = d => new Date(d.getFullYear(), d.getMonth(), d.getDate())
const isoLocal = d => new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 16)
const chaveDia = d => new Date(d).toLocaleDateString('sv-SE')

function CartaoAtividade({ item, contatos, concluir, excluir, editar }) {
  const local = item.origem !== 'google'
  return <div className={`cal-evento ${item.concluida ? 'concluida' : ''}`}>
    <span className={`atividade-tipo ${item.tipo}`}>{item.tipo}</span>
    <section><strong>{item.titulo}</strong><small>{new Date(item.inicio_em).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}{item.fim_em && `–${new Date(item.fim_em).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}`} {item.contato_id && `· ${contatos.find(c => c.id === item.contato_id)?.nome || 'Lead'}`}</small>{item.descricao && <p>{item.descricao}</p>}{item.origem === 'google' && <em><Cloud size={12}/> Google Agenda</em>}</section>
    {local && <><button title="Editar ou remarcar" onClick={() => editar(item)}><Pencil size={17}/></button><button title="Concluir" onClick={() => concluir(item)}><Check size={17}/></button><button title="Cancelar e excluir" onClick={() => excluir(item)}><Trash2 size={17}/></button></>}
  </div>
}

function CalendarioCrm() {
  const [clientes, setClientes] = useState([]), [clienteId, setClienteId] = useState(''), [contatos, setContatos] = useState([])
  const [itens, setItens] = useState([]), [form, setForm] = useState(null), [msg, setMsg] = useState(''), [carregando, setCarregando] = useState(false)
  const [modo, setModo] = useState('mes'), [dias, setDias] = useState(7), [referencia, setReferencia] = useState(inicioDia(new Date()))
  useEffect(() => { listarClientes().then(x => { setClientes(x); setClienteId(escolherClienteInicial(x)) }).catch(e => setMsg(e.message)) }, [])
  useEffect(() => { const status = new URLSearchParams(location.search).get('google'); if (status) { setMsg(status === 'conectado' ? 'Conta Google conectada com sucesso.' : status === 'cancelado' ? 'A conexão com o Google foi cancelada.' : 'Não foi possível concluir a conexão com o Google.'); history.replaceState({}, '', location.pathname) } }, [])
  const intervalo = useMemo(() => {
    if (modo === 'mes') { const primeiro = new Date(referencia.getFullYear(), referencia.getMonth(), 1), inicio = new Date(primeiro); inicio.setDate(1 - primeiro.getDay()); return [inicio, new Date(inicio.getTime() + 42 * DIA)] }
    if (modo === 'dia') return [inicioDia(referencia), new Date(inicioDia(referencia).getTime() + DIA)]
    return [inicioDia(referencia), new Date(inicioDia(referencia).getTime() + dias * DIA)]
  }, [modo, referencia, dias])
  async function carregar(id = clienteId) {
    if (!id) return
    setCarregando(true); setMsg('')
    try { const [a, c] = await Promise.all([listarAtividades(id, intervalo[0].toISOString(), intervalo[1].toISOString()), listarContatos(id)]); setItens(a); setContatos(c) }
    catch (e) { setMsg(e.message) } finally { setCarregando(false) }
  }
  useEffect(() => { carregar(clienteId) }, [clienteId, intervalo[0].getTime(), intervalo[1].getTime()])
  const porDia = useMemo(() => itens.reduce((acc, x) => { (acc[chaveDia(x.inicio_em)] ??= []).push(x); return acc }, {}), [itens])
  const datasVisiveis = useMemo(() => Array.from({ length: modo === 'mes' ? 42 : modo === 'dia' ? 1 : dias }, (_, i) => new Date(intervalo[0].getTime() + i * DIA)), [intervalo, modo, dias])
  function navegar(sentido) { const d = new Date(referencia); modo === 'mes' ? d.setMonth(d.getMonth() + sentido) : d.setDate(d.getDate() + sentido * (modo === 'dia' ? 1 : dias)); setReferencia(d) }
  function nova(data = referencia) { const inicio = new Date(data); inicio.setHours(9, 0, 0, 0); setForm({ tipo: 'tarefa', titulo: '', descricao: '', inicio_em: isoLocal(inicio), fim_em: isoLocal(new Date(inicio.getTime() + 3600000)), contato_id: null, concluida: false, convidados_texto: '' }) }
  async function salvar(e) { e.preventDefault(); setMsg(''); try { const convidados = form.convidados_texto.split(/[;,\n]/).map(x => x.trim()).filter(Boolean); const dados={ ...form, convidados, cliente_id: clienteId, inicio_em: new Date(form.inicio_em).toISOString(), fim_em: new Date(form.fim_em).toISOString() }; form.id ? await salvarAtividade(form.id,dados) : await criarAtividade(dados); setForm(null); await carregar() } catch (erro) { setMsg(erro.message) } }
  async function concluir(x) { await salvarAtividade(x.id, { cliente_id: clienteId, contato_id: x.contato_id, tipo: x.tipo, titulo: x.titulo, descricao: x.descricao || '', inicio_em: x.inicio_em, fim_em: x.fim_em, convidados: x.convidados || [], concluida: !x.concluida }); await carregar() }
  async function excluir(x) { if (!confirm(`Excluir “${x.titulo}”?`)) return; await excluirAtividade(x.id); await carregar() }
  function editar(x){setForm({...x,inicio_em:isoLocal(new Date(x.inicio_em)),fim_em:isoLocal(new Date(x.fim_em)),convidados_texto:(x.convidados||[]).join(', ')})}
  const titulo = modo === 'dia' ? referencia.toLocaleDateString('pt-BR', { weekday: 'long', day: '2-digit', month: 'long', year: 'numeric' }) : referencia.toLocaleDateString('pt-BR', { month: 'long', year: 'numeric' })

  return <div className="layout-app"><Sidebar/><main className="conteudo-principal pagina-crm pagina-calendario">
    <header className="topo-pagina"><div><h1>Calendário</h1><p>Tarefas, agendamentos e compromissos do cliente, sincronizados com a conta Google cadastrada em Clientes.</p></div><button className="botao-primario" disabled={!clienteId} onClick={() => nova()}><Plus size={16}/> Novo evento</button></header>
    {msg && <p className="mensagem-integracao">{msg}</p>}
    <section className="cal-toolbar"><label>Cliente<select value={clienteId} onChange={e => setClienteId(e.target.value)}>{clientes.map(x => <option key={x.id} value={x.id}>{x.nome}</option>)}</select></label><nav><button onClick={() => navegar(-1)} aria-label="Anterior"><ChevronLeft/></button><button onClick={() => setReferencia(inicioDia(new Date()))}>Hoje</button><button onClick={() => navegar(1)} aria-label="Próximo"><ChevronRight/></button></nav><h2>{titulo}</h2><div className="cal-modos"><button className={modo === 'mes' ? 'ativo' : ''} onClick={() => setModo('mes')}>Mês</button><button className={modo === 'dias' ? 'ativo' : ''} onClick={() => setModo('dias')}>Dias</button><button className={modo === 'dia' ? 'ativo' : ''} onClick={() => setModo('dia')}>Dia</button>{modo === 'dias' && <select value={dias} onChange={e => setDias(Number(e.target.value))}>{[3,5,7,14].map(x => <option key={x} value={x}>{x} dias</option>)}</select>}</div></section>
    {carregando && <p>Atualizando calendário…</p>}
    {modo === 'mes' && <><div className="cal-semana">{['Dom','Seg','Ter','Qua','Qui','Sex','Sáb'].map(x => <strong key={x}>{x}</strong>)}</div><section className="cal-mes">{datasVisiveis.map(d => { const eventos = porDia[chaveDia(d)] || []; return <article key={d.toISOString()} className={d.getMonth() !== referencia.getMonth() ? 'fora-mes' : ''} onDoubleClick={() => nova(d)}><button className="cal-numero" onClick={() => { setReferencia(d); setModo('dia') }}>{d.getDate()}</button>{eventos.slice(0,3).map(x => <button key={x.id} className={`cal-resumo ${x.tipo}`} title={x.titulo} onClick={() => { setReferencia(d); setModo('dia') }}><time>{new Date(x.inicio_em).toLocaleTimeString('pt-BR',{hour:'2-digit',minute:'2-digit'})}</time> {x.titulo}</button>)}{eventos.length > 3 && <small>+ {eventos.length - 3} itens</small>}</article> })}</section></>}
    {modo !== 'mes' && <section className={`cal-dias ${modo === 'dia' ? 'cal-dia-unico' : ''}`}>{datasVisiveis.map(d => <article key={d.toISOString()}><header><button onClick={() => nova(d)}><Plus size={15}/></button><strong>{d.toLocaleDateString('pt-BR',{weekday:'short',day:'2-digit',month:'short'})}</strong></header>{(porDia[chaveDia(d)] || []).map(x => <CartaoAtividade key={x.id} item={x} contatos={contatos} concluir={concluir} excluir={excluir} editar={editar}/>)}{!(porDia[chaveDia(d)] || []).length && <p className="cal-vazio">Nenhum compromisso.</p>}</article>)}</section>}
    {form && <div className="crm-modal-fundo"><form className="crm-modal" onSubmit={salvar}><header><h2>Nova atividade</h2><button type="button" onClick={() => setForm(null)}><X/></button></header><div className="crm-form-grid"><label>Tipo<select value={form.tipo} onChange={e => setForm({...form,tipo:e.target.value})}><option value="agendamento">Agendamento</option><option value="compromisso">Compromisso</option><option value="tarefa">Tarefa</option><option value="recado">Recado</option></select></label><label>Lead<select value={form.contato_id || ''} onChange={e => setForm({...form,contato_id:e.target.value || null})}><option value="">Sem lead</option>{contatos.map(c => <option key={c.id} value={c.id}>{c.nome} {c.sobrenome}</option>)}</select></label><label>Início<input required type="datetime-local" value={form.inicio_em} onChange={e => setForm({...form,inicio_em:e.target.value})}/></label><label>Término<input required type="datetime-local" min={form.inicio_em} value={form.fim_em} onChange={e => setForm({...form,fim_em:e.target.value})}/></label></div><label>Título<input required value={form.titulo} onChange={e => setForm({...form,titulo:e.target.value})}/></label><label>Convidados por e-mail<textarea value={form.convidados_texto} onChange={e => setForm({...form,convidados_texto:e.target.value})} placeholder="email1@gmail.com, email2@gmail.com"/><small>Separe os e-mails por vírgula. Eles receberão o convite e as atualizações do evento.</small></label><label>Descrição<textarea value={form.descricao} onChange={e => setForm({...form,descricao:e.target.value})}/></label><footer><button type="button" className="botao-secundario" onClick={() => setForm(null)}>Cancelar</button><button className="botao-primario">Salvar e sincronizar</button></footer></form></div>}
  </main></div>
}
export default CalendarioCrm
