import { useEffect, useRef, useState } from "react";
import {
  Bot,
  Clock,
  GitBranch,
  ListChecks,
  GripVertical,
  MessageSquare,
  Play,
  Plus,
  Save,
  Shuffle,
  Trash2,
} from "lucide-react";
import { useSearchParams } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import { listarClientes } from "../api/clientesService";
import { escolherClienteInicial } from "../utils/clienteAtivo";
import {
  criarFluxo,
  excluirFluxo,
  listarFluxos,
  obterConfiguracoes,
  salvarConfiguracoes,
  salvarFluxo,
} from "../api/automationService";

const RESPOSTAS = [
  "texto",
  "número",
  "sim/não",
  "celular",
  "data",
  "hora",
  "e-mail",
  "URL",
  "múltipla escolha",
];
const TIPOS = {
  mensagem: ["Mensagem", MessageSquare],
  pergunta: ["Pergunta", Bot],
  botoes: ["Botões", ListChecks],
  espera: ["Espera", Clock],
  decisao: ["Decisão", GitBranch],
  randomizacao: ["Randomização", Shuffle],
  gatilho: ["Gatilho", Play],
};
const CORES_PADRAO = {
  mensagem: "#4f46e5",
  pergunta: "#0891b2",
  botoes: "#db2777",
  espera: "#64748b",
  decisao: "#d97706",
  randomizacao: "#7c3aed",
  gatilho: "#059669",
};
const GATILHOS = [
  "Comentário em post",
  "Comentário em Reels",
  "Resposta ao Story",
  "Menção no Story",
  "Palavra-chave no Direct",
];
const novoId = () => crypto.randomUUID();

function Automacao({ canal }) {
  const [clientes, setClientes] = useState([]);
  const [clienteId, setClienteId] = useState("");
  const [fluxos, setFluxos] = useState([]);
  const [fluxoId, setFluxoId] = useState("");
  const [nome, setNome] = useState("");
  const [status, setStatus] = useState("rascunho");
  const [blocos, setBlocos] = useState([]);
  const [conexoes, setConexoes] = useState([]);
  const [origem, setOrigem] = useState(null);
  const [cores, setCores] = useState(CORES_PADRAO);
  const [mensagem, setMensagem] = useState("");
  const [proximoNumero, setProximoNumero] = useState(1);
  const [mouse, setMouse] = useState({ x: 0, y: 0 });
  const [menu, setMenu] = useState(null);
  const [menuLinha, setMenuLinha] = useState(null);
  const [linhaSelecionada, setLinhaSelecionada] = useState(null);
  const [selecionados, setSelecionados] = useState([]);
  const [selecaoArea, setSelecaoArea] = useState(null);
  const [copiados, setCopiados] = useState(null);
  const arraste = useRef(null);
  const [params] = useSearchParams();
  const tituloCanal = canal === "facebook" ? "Facebook" : "Instagram";
  useEffect(() => {
    listarClientes()
      .then((x) => {
        setClientes(x);
        setClienteId(params.get("cliente") || escolherClienteInicial(x));
      })
      .catch((e) => setMensagem(e.message));
  }, []);
  useEffect(() => {
    if (!clienteId) return;
    Promise.all([listarFluxos(clienteId, canal), obterConfiguracoes(clienteId)])
      .then(([f, c]) => {
        setFluxos(f);
        setCores(c.cores);
        const solicitado = params.get("fluxo");
        const item = solicitado && f.find((x) => x.id === solicitado);
        if (item) abrir(item);
      })
      .catch((e) => setMensagem(e.message));
  }, [clienteId, canal]);
  function novoFluxo() {
    setFluxoId("");
    setNome(`Nova automação ${tituloCanal}`);
    setStatus("rascunho");
    setBlocos([]);
    setConexoes([]);
    setOrigem(null);
    setProximoNumero(1);
  }
  function abrir(x) {
    const normalizados = (x.blocos || []).map((b, i) => ({
      ...b,
      numero: b.numero || i + 1,
    }));
    const seguinte = Math.max(
      x.proximo_numero || 1,
      Math.max(0, ...normalizados.map((b) => b.numero)) + 1,
    );
    setFluxoId(x.id);
    setNome(x.nome);
    setStatus(x.status);
    setBlocos(normalizados);
    setConexoes(x.conexoes || []);
    setProximoNumero(seguinte);
    setOrigem(null);
  }
  function adicionar(tipo, x = 80, y = 60, base = null) {
    const numero = proximoNumero;
    setProximoNumero((n) => n + 1);
    setBlocos((atuais) => [
      ...atuais,
      {
        id: novoId(),
        numero,
        tipo,
        titulo: base?.titulo || TIPOS[tipo][0],
        conteudo: base?.conteudo || "",
        identificador: tipo === "pergunta" ? `resposta_${numero}` : "",
        resposta_tipo: base?.resposta_tipo || "texto",
        selecao_tipo: base?.selecao_tipo || "simples",
        opcoes: base?.opcoes?.length
          ? base.opcoes
          : tipo === "botoes"
            ? ["Opção 1", "Opção 2"]
            : [],
        quantidade: base?.quantidade || 2,
        unidade_espera: base?.unidade_espera || "segundos",
        simular_digitacao: base?.simular_digitacao ?? true,
        tempo_digitacao: base?.tempo_digitacao || 3,
        gatilho:
          base?.gatilho || (canal === "instagram" ? GATILHOS[0] : GATILHOS[1]),
        campo: base?.campo || "",
        operador: base?.operador || "igual a",
        valor: base?.valor || "",
        x,
        y,
      },
    ]);
    setMenu(null);
  }
  function atualizar(id, chave, valor) {
    setBlocos((x) =>
      x.map((b) => (b.id === id ? { ...b, [chave]: valor } : b)),
    );
  }
  function iniciarArraste(e, bloco) {
    if (
      e.button !== 0 ||
      e.target.closest("input, textarea, select, button, label, .portas-bloco")
    )
      return;
    const area = e.currentTarget
      .closest(".canvas-automacao")
      .getBoundingClientRect();
    arraste.current = {
      id: bloco.id,
      area,
      deslocamentoX: e.clientX - area.left - bloco.x,
      deslocamentoY: e.clientY - area.top - bloco.y,
    };
    e.preventDefault();
    e.stopPropagation();
    setSelecionados((atuais) =>
      atuais.includes(bloco.id) ? atuais : [bloco.id],
    );
    setLinhaSelecionada(null);
  }
  useEffect(() => {
    function moverBloco(e) {
      const atual = arraste.current;
      if (!atual) return;
      atualizar(
        atual.id,
        "x",
        Math.max(0, e.clientX - atual.area.left - atual.deslocamentoX),
      );
      atualizar(
        atual.id,
        "y",
        Math.max(0, e.clientY - atual.area.top - atual.deslocamentoY),
      );
    }
    function terminarArraste() {
      arraste.current = null;
    }
    window.addEventListener("mousemove", moverBloco);
    window.addEventListener("mouseup", terminarArraste);
    return () => {
      window.removeEventListener("mousemove", moverBloco);
      window.removeEventListener("mouseup", terminarArraste);
    };
  }, []);
  function iniciarConexao(id, saida) {
    setOrigem({ id, saida });
  }
  function finalizarConexao(id) {
    if (!origem || origem.id === id) return;
    setConexoes((x) => [
      ...x,
      { id: novoId(), origem: origem.id, destino: id, saida: origem.saida },
    ]);
    setOrigem(null);
  }
  function saidas(bloco) {
    if (bloco.tipo === "decisao") return ["sim", "não"];
    if (bloco.tipo === "randomizacao")
      return Array.from(
        { length: bloco.quantidade || 2 },
        (_, i) => `rota ${i + 1}`,
      );
    if (bloco.tipo === "botoes") return bloco.opcoes?.filter(Boolean) || [];
    return [""];
  }
  async function salvar() {
    const dados = {
      cliente_id: clienteId,
      canal,
      nome,
      status,
      blocos,
      conexoes,
      proximo_numero: proximoNumero,
    };
    try {
      const salvo = fluxoId
        ? await salvarFluxo(fluxoId, dados)
        : await criarFluxo(dados);
      setFluxoId(salvo.id);
      setFluxos(await listarFluxos(clienteId, canal));
      setMensagem("Automação salva.");
    } catch (e) {
      setMensagem(e.message);
    }
  }
  async function salvarCores() {
    try {
      setCores((await salvarConfiguracoes(clienteId, cores)).cores);
      setMensagem("Cores do cliente salvas.");
    } catch (e) {
      setMensagem(e.message);
    }
  }
  async function removerFluxo() {
    if (!fluxoId || !confirm("Excluir esta automação?")) return;
    await excluirFluxo(fluxoId);
    novoFluxo();
    setFluxos(await listarFluxos(clienteId, canal));
  }
  function soltar(e) {
    e.preventDefault();
    const tipo = e.dataTransfer.getData("tipo-bloco");
    if (!tipo) return;
    const area = e.currentTarget.getBoundingClientRect();
    adicionar(tipo, e.clientX - area.left - 100, e.clientY - area.top - 30);
  }

  function copiarSelecionados() {
    if (!selecionados.length) return;
    const ids = new Set(selecionados);
    setCopiados({
      blocos: blocos.filter((b) => ids.has(b.id)),
      conexoes: conexoes.filter((c) => ids.has(c.origem) && ids.has(c.destino)),
    });
  }
  function colarSelecionados() {
    if (!copiados?.blocos.length) return;
    const mapa = {};
    const inicio = proximoNumero;
    const novos = copiados.blocos.map((b, i) => {
      const id = novoId();
      mapa[b.id] = id;
      return {
        ...b,
        id,
        numero: inicio + i,
        x: b.x + 45,
        y: b.y + 45,
        identificador:
          b.tipo === "pergunta"
            ? `${b.identificador || "resposta"}_copia_${inicio + i}`
            : b.identificador,
      };
    });
    const novasConexoes = copiados.conexoes.map((c) => ({
      ...c,
      id: novoId(),
      origem: mapa[c.origem],
      destino: mapa[c.destino],
    }));
    setBlocos((x) => [...x, ...novos]);
    setConexoes((x) => [...x, ...novasConexoes]);
    setSelecionados(novos.map((b) => b.id));
    setProximoNumero(inicio + novos.length);
    setCopiados({ blocos: novos, conexoes: novasConexoes });
  }
  useEffect(() => {
    function atalhos(e) {
      if (
        ["INPUT", "TEXTAREA", "SELECT"].includes(
          document.activeElement?.tagName,
        )
      )
        return;
      if (e.key === "Delete") {
        if (!selecionados.length && !linhaSelecionada) return;
        e.preventDefault();
        const ids = new Set(selecionados);
        if (ids.size) {
          setBlocos((x) => x.filter((b) => !ids.has(b.id)));
          setConexoes((x) =>
            x.filter((c) => !ids.has(c.origem) && !ids.has(c.destino)),
          );
        }
        if (linhaSelecionada)
          setConexoes((x) => x.filter((c) => c.id !== linhaSelecionada));
        setSelecionados([]);
        setLinhaSelecionada(null);
        setMenuLinha(null);
        setMenu(null);
        return;
      }
      if (!e.ctrlKey && !e.metaKey) return;
      if (e.key.toLowerCase() === "c") {
        e.preventDefault();
        copiarSelecionados();
      }
      if (e.key.toLowerCase() === "v") {
        e.preventDefault();
        colarSelecionados();
      }
    }
    window.addEventListener("keydown", atalhos);
    return () => window.removeEventListener("keydown", atalhos);
  }, [
    selecionados,
    linhaSelecionada,
    blocos,
    conexoes,
    copiados,
    proximoNumero,
  ]);

  function iniciarSelecao(e) {
    if (
      e.button !== 0 ||
      !["canvas-automacao", "conexoes-svg"].some((classe) =>
        e.target.classList?.contains(classe),
      )
    )
      return;
    const area = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - area.left;
    const y = e.clientY - area.top;
    setSelecaoArea({ inicioX: x, inicioY: y, x, y });
    setSelecionados([]);
    setLinhaSelecionada(null);
    setMenu(null);
    setMenuLinha(null);
  }
  function finalizarSelecao() {
    if (!selecaoArea) return;
    const esquerda = Math.min(selecaoArea.inicioX, selecaoArea.x);
    const direita = Math.max(selecaoArea.inicioX, selecaoArea.x);
    const topo = Math.min(selecaoArea.inicioY, selecaoArea.y);
    const base = Math.max(selecaoArea.inicioY, selecaoArea.y);
    setSelecionados(
      blocos
        .filter(
          (b) =>
            b.x < direita &&
            b.x + 230 > esquerda &&
            b.y < base &&
            b.y + 220 > topo,
        )
        .map((b) => b.id),
    );
    setSelecaoArea(null);
  }

  return (
    <div className="layout-app">
      <Sidebar />
      <main className="conteudo-principal pagina-automacao">
        <header className="topo-pagina">
          <div>
            <h1>Automação do {tituloCanal}</h1>
            <p>
              Fluxos por cliente com mensagens, decisões, sorteios e gatilhos.
            </p>
          </div>
          <button className="botao-primario" onClick={novoFluxo}>
            <Plus size={16} /> Nova automação
          </button>
        </header>
        {mensagem && <p className="mensagem-integracao">{mensagem}</p>}
        <section className="barra-editor-automacao">
          <label>
            Cliente
            <select
              value={clienteId}
              onChange={(e) => setClienteId(e.target.value)}
            >
              {clientes.map((x) => (
                <option key={x.id} value={x.id}>
                  {x.nome}
                </option>
              ))}
            </select>
          </label>
          <label>
            Automação
            <select
              value={fluxoId}
              onChange={(e) => {
                const x = fluxos.find((f) => f.id === e.target.value);
                x ? abrir(x) : novoFluxo();
              }}
            >
              <option value="">Nova automação</option>
              {fluxos.map((x) => (
                <option key={x.id} value={x.id}>
                  {x.nome}
                </option>
              ))}
            </select>
          </label>
          <label>
            Nome
            <input value={nome} onChange={(e) => setNome(e.target.value)} />
          </label>
          <label>
            Status
            <select value={status} onChange={(e) => setStatus(e.target.value)}>
              <option value="rascunho">Rascunho</option>
              <option value="ativo">Ativo</option>
              <option value="pausado">Pausado</option>
            </select>
          </label>
          <button className="botao-primario" onClick={salvar}>
            <Save size={16} /> Salvar
          </button>
          {fluxoId && (
            <button className="botao-icone-remover" onClick={removerFluxo}>
              <Trash2 />
            </button>
          )}
        </section>
        <section className="cores-blocos">
          <strong>Cores dos blocos deste cliente</strong>
          {Object.entries(TIPOS).map(([tipo, [rotulo]]) => (
            <label key={tipo}>
              {rotulo}
              <input
                type="color"
                value={cores[tipo] || CORES_PADRAO[tipo]}
                onChange={(e) =>
                  setCores((x) => ({ ...x, [tipo]: e.target.value }))
                }
              />
            </label>
          ))}
          <button className="botao-secundario" onClick={salvarCores}>
            Salvar cores
          </button>
        </section>
        <section className="designer-automacao">
          <aside className="paleta-blocos">
            <h3>Blocos</h3>
            {Object.entries(TIPOS).map(([tipo, [rotulo, Icone]]) => (
              <button
                key={tipo}
                draggable
                onDragStart={(e) => e.dataTransfer.setData("tipo-bloco", tipo)}
                onClick={() => adicionar(tipo)}
                style={{ borderLeftColor: cores[tipo], borderLeftWidth: 5 }}
              >
                <Icone size={18} />
                <span>
                  <strong>{rotulo}</strong>
                  <small>Arraste para o fluxo</small>
                </span>
                <GripVertical size={16} />
              </button>
            ))}
            <div className="lista-conexoes">
              <h4>Conexões</h4>
              {conexoes.length === 0 && <small>Nenhuma conexão.</small>}
              {conexoes.map((c) => (
                <button
                  key={c.id}
                  onClick={() =>
                    setConexoes((x) => x.filter((i) => i.id !== c.id))
                  }
                >
                  <span>{c.saida}</span>
                  <Trash2 size={14} />
                </button>
              ))}
            </div>
          </aside>
          <div
            className="canvas-automacao"
            onDragOver={(e) => e.preventDefault()}
            onDrop={soltar}
            onMouseDown={iniciarSelecao}
            onMouseUp={finalizarSelecao}
            onMouseLeave={finalizarSelecao}
            onMouseMove={(e) => {
              const area = e.currentTarget.getBoundingClientRect();
              const ponto = {
                x: e.clientX - area.left,
                y: e.clientY - area.top,
              };
              setMouse(ponto);
              if (selecaoArea) setSelecaoArea((x) => ({ ...x, ...ponto }));
            }}
            onClick={() => {
              if (menu) setMenu(null);
              if (menuLinha) setMenuLinha(null);
            }}
          >
            {blocos.length === 0 && (
              <div className="canvas-vazio">Arraste um bloco para começar</div>
            )}
            <svg className="conexoes-svg">
              {conexoes.map((c) => {
                const a = blocos.find((b) => b.id === c.origem);
                const b = blocos.find((x) => x.id === c.destino);
                if (!a || !b) return null;
                const x1 = a.x + 230;
                const y1 = a.y + 36;
                const x2 = b.x;
                const y2 = b.y + 36;
                const curva = Math.max(70, Math.abs(x2 - x1) * 0.45);
                const d = `M ${x1} ${y1} C ${x1 + curva} ${y1}, ${x2 - curva} ${y2}, ${x2} ${y2}`;
                return (
                  <g key={c.id}>
                    <path
                      d={d}
                      stroke={cores[a.tipo]}
                      className={`caminho-fluxo ${linhaSelecionada === c.id ? "caminho-selecionado" : ""}`}
                    />
                    <path
                      d={d}
                      className="caminho-fluxo-clique"
                      onClick={(e) => {
                        e.stopPropagation();
                        setLinhaSelecionada(c.id);
                        setSelecionados([]);
                        setMenuLinha(null);
                      }}
                      onContextMenu={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        const area = e.currentTarget
                          .closest(".canvas-automacao")
                          .getBoundingClientRect();
                        setLinhaSelecionada(c.id);
                        setMenuLinha({
                          id: c.id,
                          x: e.clientX - area.left,
                          y: e.clientY - area.top,
                        });
                        setMenu(null);
                      }}
                    />
                  </g>
                );
              })}
              {origem &&
                (() => {
                  const a = blocos.find((b) => b.id === origem.id);
                  if (!a) return null;
                  const x1 = a.x + 230;
                  const y1 = a.y + 36;
                  const curva = Math.max(70, Math.abs(mouse.x - x1) * 0.45);
                  return (
                    <path
                      d={`M ${x1} ${y1} C ${x1 + curva} ${y1}, ${mouse.x - curva} ${mouse.y}, ${mouse.x} ${mouse.y}`}
                      stroke={cores[a.tipo]}
                      className="caminho-fluxo caminho-rascunho"
                    />
                  );
                })()}
            </svg>
            {blocos.map((b) => (
              <article
                className={`bloco-fluxo ${origem?.id === b.id ? "bloco-origem" : ""} ${selecionados.includes(b.id) ? "bloco-selecionado" : ""}`}
                key={b.id}
                style={{ left: b.x, top: b.y, borderColor: cores[b.tipo] }}
                onClick={(e) => {
                  e.stopPropagation();
                  setLinhaSelecionada(null);
                  setSelecionados((x) =>
                    e.ctrlKey || e.metaKey
                      ? x.includes(b.id)
                        ? x.filter((id) => id !== b.id)
                        : [...x, b.id]
                      : [b.id],
                  );
                }}
                onMouseDown={(e) => iniciarArraste(e, b)}
                onContextMenu={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  setMenu({ x: b.x + 40, y: b.y + 40, bloco: b });
                  setMenuLinha(null);
                }}
              >
                <button
                  className="ponto-entrada"
                  onClick={(e) => {
                    e.stopPropagation();
                    finalizarConexao(b.id);
                  }}
                  title="Ponto de entrada"
                  aria-label={`Entrada do bloco ${b.titulo}`}
                  style={{ borderColor: cores[b.tipo] }}
                />
                <header style={{ background: cores[b.tipo] }}>
                  <GripVertical size={16} />
                  <strong>
                    #{b.numero || "?"} · {TIPOS[b.tipo]?.[0]}
                  </strong>
                  <button
                    onClick={() => {
                      setBlocos((x) => x.filter((i) => i.id !== b.id));
                      setConexoes((x) =>
                        x.filter(
                          (c) => c.origem !== b.id && c.destino !== b.id,
                        ),
                      );
                    }}
                  >
                    <Trash2 size={15} />
                  </button>
                </header>
                <input
                  aria-label="Nome do bloco"
                  title="Clique para renomear"
                  value={b.titulo}
                  onChange={(e) => atualizar(b.id, "titulo", e.target.value)}
                />
                {["mensagem", "pergunta"].includes(b.tipo) && (
                  <textarea
                    placeholder="Conteúdo"
                    value={b.conteudo}
                    onChange={(e) =>
                      atualizar(b.id, "conteudo", e.target.value)
                    }
                  />
                )}
                {b.tipo === "pergunta" && (
                  <>
                    <label>
                      Identificação
                      <input
                        value={b.identificador}
                        onChange={(e) =>
                          atualizar(b.id, "identificador", e.target.value)
                        }
                      />
                    </label>
                    <label>
                      Resposta
                      <select
                        value={b.resposta_tipo}
                        onChange={(e) =>
                          atualizar(b.id, "resposta_tipo", e.target.value)
                        }
                      >
                        {RESPOSTAS.map((x) => (
                          <option key={x}>{x}</option>
                        ))}
                      </select>
                    </label>
                  </>
                )}
                {b.tipo === "mensagem" && (
                  <div className="config-digitacao">
                    <label className="opcao-checkbox">
                      <input
                        type="checkbox"
                        checked={b.simular_digitacao !== false}
                        onChange={(e) =>
                          atualizar(b.id, "simular_digitacao", e.target.checked)
                        }
                      />
                      Mostrar “digitando...” antes de enviar
                    </label>
                    {b.simular_digitacao !== false && (
                      <label>
                        Tempo digitando (segundos)
                        <input
                          type="number"
                          min="1"
                          max="20"
                          value={b.tempo_digitacao || 3}
                          onChange={(e) =>
                            atualizar(
                              b.id,
                              "tempo_digitacao",
                              Math.min(20, Math.max(1, Number(e.target.value))),
                            )
                          }
                        />
                      </label>
                    )}
                  </div>
                )}
                {b.tipo === "botoes" && (
                  <>
                    <textarea
                      placeholder="Mensagem antes dos botões"
                      value={b.conteudo}
                      onChange={(e) =>
                        atualizar(b.id, "conteudo", e.target.value)
                      }
                    />
                    <label>
                      Tipo de seleção
                      <select
                        value={b.selecao_tipo || "simples"}
                        onChange={(e) =>
                          atualizar(b.id, "selecao_tipo", e.target.value)
                        }
                      >
                        <option value="simples">Seleção simples</option>
                        <option value="multipla">Seleção múltipla</option>
                      </select>
                    </label>
                    <label>
                      Opções (uma por linha)
                      <textarea
                        value={(b.opcoes || []).join("\n")}
                        onChange={(e) =>
                          atualizar(
                            b.id,
                            "opcoes",
                            e.target.value.split("\n").slice(0, 20),
                          )
                        }
                      />
                    </label>
                  </>
                )}
                {b.tipo === "decisao" && (
                  <>
                    <label>
                      Campo
                      <input
                        value={b.campo}
                        onChange={(e) =>
                          atualizar(b.id, "campo", e.target.value)
                        }
                      />
                    </label>
                    <label>
                      Operador
                      <select
                        value={b.operador}
                        onChange={(e) =>
                          atualizar(b.id, "operador", e.target.value)
                        }
                      >
                        <option>igual a</option>
                        <option>diferente de</option>
                        <option>contém</option>
                        <option>maior que</option>
                        <option>menor que</option>
                      </select>
                    </label>
                    <label>
                      Valor
                      <input
                        value={b.valor}
                        onChange={(e) =>
                          atualizar(b.id, "valor", e.target.value)
                        }
                      />
                    </label>
                  </>
                )}
                {b.tipo === "randomizacao" && (
                  <label>
                    Quantidade de rotas
                    <input
                      type="number"
                      min="2"
                      max="10"
                      value={b.quantidade}
                      onChange={(e) =>
                        atualizar(
                          b.id,
                          "quantidade",
                          Math.min(10, Math.max(2, Number(e.target.value))),
                        )
                      }
                    />
                  </label>
                )}
                {b.tipo === "espera" && (
                  <div className="config-espera">
                    <label>
                      Tempo de espera
                      <input
                        type="number"
                        min="1"
                        max="1440"
                        value={b.quantidade || 2}
                        onChange={(e) =>
                          atualizar(
                            b.id,
                            "quantidade",
                            Math.min(1440, Math.max(1, Number(e.target.value))),
                          )
                        }
                      />
                    </label>
                    <label>
                      Unidade
                      <select
                        value={b.unidade_espera || "segundos"}
                        onChange={(e) =>
                          atualizar(b.id, "unidade_espera", e.target.value)
                        }
                      >
                        <option value="segundos">Segundos</option>
                        <option value="minutos">Minutos</option>
                        <option value="horas">Horas</option>
                      </select>
                    </label>
                  </div>
                )}
                {b.tipo === "gatilho" && (
                  <>
                    <label>
                      Evento
                      <select
                        value={b.gatilho}
                        onChange={(e) =>
                          atualizar(b.id, "gatilho", e.target.value)
                        }
                      >
                        {GATILHOS.map((x) => (
                          <option key={x}>{x}</option>
                        ))}
                      </select>
                    </label>
                    <label>
                      Post/Reel/Palavra-chave
                      <input
                        value={b.valor}
                        onChange={(e) =>
                          atualizar(b.id, "valor", e.target.value)
                        }
                      />
                    </label>
                  </>
                )}
                <div className="portas-bloco">
                  {saidas(b).map((saida, indice) => (
                    <span className="grupo-saida" key={`${saida}-${indice}`}>
                      {saida && <span>{saida}</span>}
                      <button
                        className="ponto-saida"
                        style={{ background: cores[b.tipo] }}
                        onClick={(e) => {
                          e.stopPropagation();
                          iniciarConexao(b.id, saida || "continua");
                        }}
                        title={
                          saida
                            ? `Conectar saída ${saida}`
                            : "Conectar próximo bloco"
                        }
                      />
                    </span>
                  ))}
                </div>
              </article>
            ))}
            {menu && (
              <div
                className="menu-contexto-bloco"
                style={{ left: menu.x, top: menu.y }}
                onClick={(e) => e.stopPropagation()}
              >
                <strong>Adicionar bloco</strong>
                <button
                  onClick={() =>
                    adicionar(menu.bloco.tipo, menu.x + 250, menu.y, menu.bloco)
                  }
                >
                  Duplicar #{menu.bloco.numero}
                </button>
                {Object.keys(TIPOS).map((tipo) => (
                  <button
                    key={tipo}
                    onClick={() => adicionar(tipo, menu.x + 250, menu.y)}
                  >
                    {TIPOS[tipo][0]}
                  </button>
                ))}
              </div>
            )}
            {menuLinha && (
              <div
                className="menu-contexto-bloco menu-linha"
                style={{ left: menuLinha.x, top: menuLinha.y }}
                onClick={(e) => e.stopPropagation()}
              >
                <strong>Conexão</strong>
                <button
                  onClick={() => {
                    setConexoes((x) => x.filter((i) => i.id !== menuLinha.id));
                    setLinhaSelecionada(null);
                    setMenuLinha(null);
                  }}
                >
                  <Trash2 size={14} /> Excluir linha
                </button>
              </div>
            )}
            {selecaoArea && (
              <div
                className="retangulo-selecao"
                style={{
                  left: Math.min(selecaoArea.inicioX, selecaoArea.x),
                  top: Math.min(selecaoArea.inicioY, selecaoArea.y),
                  width: Math.abs(selecaoArea.x - selecaoArea.inicioX),
                  height: Math.abs(selecaoArea.y - selecaoArea.inicioY),
                }}
              />
            )}
          </div>
        </section>
      </main>
    </div>
  );
}
export default Automacao;
