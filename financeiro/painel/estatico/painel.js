// Painel: só busca os números prontos na API e desenha.
// Nenhuma conta de negócio acontece aqui (lucro, margem e totais vêm do servidor).

const reais = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
const MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"];
const graficos = {};

async function buscar(caminho) {
  const resposta = await fetch(caminho, { credentials: "same-origin" });
  if (resposta.status === 401) throw new Error("sem-login");
  if (!resposta.ok) throw new Error(`erro ${resposta.status} em ${caminho}`);
  return resposta.json();
}

function mostrarValor(id, valor) {
  const elemento = document.getElementById(id);
  elemento.textContent = reais.format(Number(valor));
  elemento.classList.toggle("negativo", Number(valor) < 0);
}

function desenhar(id, configuracao) {
  graficos[id]?.destroy(); // troca o gráfico antigo quando o mês muda
  graficos[id] = new Chart(document.getElementById(id), configuracao);
}

async function carregarMes(valorDoCampo) {
  const dados = await buscar(`/painel/api/mes?dia=${valorDoCampo}-01`);
  mostrarValor("faturamento", dados.negocio.faturamento);
  mostrarValor("custos", dados.negocio.custos);
  mostrarValor("lucro", dados.negocio.lucro);
  mostrarValor("saldo", dados.saldo_pessoal);
  document.getElementById("margem").textContent =
    `margem de ${Number(dados.negocio.margem).toLocaleString("pt-BR")}%`;

  const categorias = dados.gastos_por_categoria;
  document.getElementById("sem-gastos").hidden = categorias.length > 0;
  desenhar("grafico-categorias", {
    type: "bar",
    data: {
      labels: categorias.map((c) => c.categoria),
      datasets: [{ label: "Gasto", data: categorias.map((c) => Number(c.total)), backgroundColor: "#3b6fd8" }],
    },
    options: {
      indexAxis: "y",
      plugins: { legend: { display: false }, tooltip: { callbacks: { label: (c) => reais.format(c.raw) } } },
      scales: { x: { ticks: { callback: (v) => reais.format(v) } } },
    },
  });
}

async function carregarLucro(valorDoCampo) {
  const meses = await buscar(`/painel/api/lucro?ate=${valorDoCampo}-01&meses=12`);
  desenhar("grafico-lucro", {
    type: "line",
    data: {
      labels: meses.map((m) => `${MESES[m.mes - 1]}/${String(m.ano).slice(2)}`),
      datasets: [
        { label: "Lucro", data: meses.map((m) => Number(m.lucro)), borderColor: "#1f7a5c" },
        { label: "Faturamento", data: meses.map((m) => Number(m.faturamento)), borderColor: "#9aa5b8", borderDash: [4, 4] },
      ],
    },
    options: {
      plugins: { tooltip: { callbacks: { label: (c) => `${c.dataset.label}: ${reais.format(c.raw)}` } } },
      scales: { y: { ticks: { callback: (v) => reais.format(v) } } },
    },
  });
}

async function iniciar() {
  try {
    const eu = await buscar("/painel/api/eu");
    document.getElementById("nome").textContent = eu.nome;
    document.getElementById("usuario").hidden = false;
    document.getElementById("conteudo").hidden = false;
  } catch (erro) {
    document.getElementById("login").hidden = false;
    return;
  }

  const campoMes = document.getElementById("mes");
  const hoje = new Date(); // data local (toISOString usaria o fuso UTC)
  campoMes.value = `${hoje.getFullYear()}-${String(hoje.getMonth() + 1).padStart(2, "0")}`;
  const atualizar = () => Promise.all([carregarMes(campoMes.value), carregarLucro(campoMes.value)]);
  campoMes.addEventListener("change", atualizar);
  await atualizar();
}

iniciar();
