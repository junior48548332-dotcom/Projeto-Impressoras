/* =========================================================
   DADOS DAS IMPRESSORAS

   A lista começa vazia e é preenchida pela API.
   Enquanto ela não chega, a página mostra o que o
   servidor já montou no HTML.
========================================================== */

let impressoras = [];

// filtro escolhido pelo usuário (todos, online, offline, atencao, critico)
let filtroAtual = "todos";

// elemento que abriu a janela de detalhes, para devolver o foco
let elementoQueAbriuModal = null;


const configuracao =
    JSON.parse(
        document.getElementById(
            "config-dashboard"
        ).textContent
    );


/* =========================================================
   BUSCA NA API
========================================================== */

async function buscarNaApi(endereco) {

    const resposta =
        await fetch(endereco);


    if (!resposta.ok) {

        throw new Error(
            "Resposta " +
            resposta.status +
            " de " +
            endereco
        );
    }


    return resposta.json();
}


async function carregarImpressoras() {

    try {

        const dados =
            await buscarNaApi(
                configuracao.api_impressoras
            );


        aplicarDados(dados);


        return dados;

    } catch (erro) {

        console.error(
            "Não foi possível buscar os dados das impressoras:",
            erro
        );

        return null;
    }
}


/* =========================================================
   MONTAGEM DOS CARDS

   Os cards são recriados a partir da lista vinda da API,
   assim a tela reflete os dados mais recentes sem recarregar.
========================================================== */

// Ícone e texto de cada situação, para não depender só da cor
const SITUACOES = {
    normal: { icone: "✓", texto: "Normal" },
    atencao: { icone: "⚠", texto: "Atenção" },
    critico: { icone: "✕", texto: "Crítico" },
    offline: { icone: "⊘", texto: "Offline" }
};


function classeDoStatus(impressora) {

    const rede =
        String(impressora.status_rede || "").toLowerCase();

    const geral =
        String(impressora.status_geral || "").toLowerCase();


    if (rede === "offline") {
        return "offline";
    }

    if (geral === "critico") {
        return "critico";
    }

    if (geral === "atencao") {
        return "atencao";
    }

    return "normal";
}





function montarCards() {

    const grid =
        document.getElementById(
            "gridImpressoras"
        );


    if (!grid) {
        return;
    }


    grid.innerHTML = "";


    impressoras.forEach(
        function (impressora, indice) {

            const card =
                document.createElement("div");

            card.className =
                "impressora " +
                classeDoStatus(impressora);

            card.dataset.indice = indice;

            card.dataset.rede =
                String(impressora.status_rede || "").toLowerCase();

            card.dataset.geral =
                String(impressora.status_geral || "").toLowerCase();

            card.setAttribute("role", "button");

            card.setAttribute("tabindex", "0");

            card.addEventListener(
                "click",
                function () {
                    abrirDetalhes(indice);
                }
            );


            const nome =
                document.createElement("div");

            nome.className = "impressora-nome";

            nome.textContent =
                impressora.local || "Impressora";


            const modelo =
                document.createElement("div");

            modelo.className = "impressora-local";

            modelo.textContent =
                impressora.modelo || "Impressora";


            const situacao =
                SITUACOES[classeDoStatus(impressora)];


            const status =
                document.createElement("div");

            status.className = "impressora-status";

            status.innerHTML =
                '<span aria-hidden="true">' +
                situacao.icone +
                "</span> " +
                situacao.texto;


            card.appendChild(nome);

            card.appendChild(modelo);

            card.appendChild(status);


            const complemento =
                document.createElement("span");

            complemento.className = "apenas-leitor";

            complemento.textContent =
                "Rede " +
                (impressora.status_rede || "desconhecida") +
                ". Ver detalhes";

            card.appendChild(complemento);

            grid.appendChild(card);
        }
    );
}


/* =========================================================
   CONTADORES E CABEÇALHO
========================================================== */

function escreverTexto(id, texto) {

    const elemento =
        document.getElementById(id);


    if (elemento) {
        elemento.textContent = texto;
    }
}


function atualizarContadores(resumo) {

    if (!resumo) {
        return;
    }

    escreverTexto("contadorTotal", resumo.total);
    escreverTexto("contadorOnline", resumo.online);
    escreverTexto("contadorOffline", resumo.offline);
    escreverTexto("contadorAtencao", resumo.atencao);
    escreverTexto("contadorCritico", resumo.criticas);
}


function aplicarDados(dados) {

    impressoras = dados.impressoras || [];

    montarCards();

    atualizarContadores(dados.resumo);

    escreverTexto(
        "ultimaMedicao",
        dados.atualizado_em || "Aguardando"
    );

    // mantém o filtro que o usuário tinha escolhido
    filtrarImpressoras(filtroAtual);

    atualizarStatusSistema();
}


/* =========================================================
   INDICADORES DA ABA ANÁLISE
========================================================== */

function atualizarAnalise(analise) {

    if (!analise) {
        return;
    }


    escreverTexto(
        "analiseRegistros",
        analise.total_registros
    );

    escreverTexto(
        "analiseConsumo",
        Number(analise.consumo_medio || 0).toFixed(2) + "%"
    );

    escreverTexto(
        "analiseCriticas",
        analise.total_criticas
    );

    escreverTexto(
        "analiseAtencoes",
        analise.total_atencoes
    );


    const medicoes =
        (analise.total_online || 0) +
        (analise.total_offline || 0);

    const disponibilidade =
        medicoes > 0
            ? ((analise.total_online / medicoes) * 100).toFixed(1) + "%"
            : "0%";

    escreverTexto(
        "analiseDisponibilidade",
        disponibilidade
    );
}


async function carregarAnalise() {

    try {

        const analise =
            await buscarNaApi(
                configuracao.api_analise
            );

        atualizarAnalise(analise);

        return analise;

    } catch (erro) {

        console.error(
            "Não foi possível buscar a análise:",
            erro
        );

        return null;
    }
}


/* =========================================================
   ATUALIZAÇÃO PERIÓDICA

   Busca as duas rotas da API e atualiza apenas os pedaços
   da página que mudaram.
========================================================== */

async function atualizarTudo() {

    await Promise.all([
        carregarImpressoras(),
        carregarAnalise()
    ]);
}


/* =========================================================
   RELÓGIO
========================================================== */

function atualizarRelogio() {

    const agora = new Date();

    const horas =
        String(
            agora.getHours()
        ).padStart(2, "0");

    const minutos =
        String(
            agora.getMinutes()
        ).padStart(2, "0");

    const segundos =
        String(
            agora.getSeconds()
        ).padStart(2, "0");


    document.getElementById(
        "relogio"
    ).textContent =
        `${horas}:${minutos}:${segundos}`;
}


setInterval(
    atualizarRelogio,
    1000
);

atualizarRelogio();


/* =========================================================
   CONVERSÃO CORRETA DA DATA DO SQLITE
========================================================== */

function converterDataBanco(dataTexto) {

    if (!dataTexto) {
        return null;
    }


    const texto =
        String(
            dataTexto
        ).trim();


    let partes =
        texto.split(" ");


    if (partes.length < 2) {

        partes =
            texto.split("T");

    }


    const dataParte =
        partes[0];

    const horaParte =
        partes[1] || "00:00:00";


    let dia;
    let mes;
    let ano;


    if (dataParte.includes("/")) {

        const partesData =
            dataParte.split("/");


        if (partesData.length !== 3) {
            return null;
        }


        dia =
            parseInt(
                partesData[0],
                10
            );

        mes =
            parseInt(
                partesData[1],
                10
            ) - 1;

        ano =
            parseInt(
                partesData[2],
                10
            );

    }


    else if (dataParte.includes("-")) {

        const partesData =
            dataParte.split("-");


        if (partesData.length !== 3) {
            return null;
        }


        ano =
            parseInt(
                partesData[0],
                10
            );

        mes =
            parseInt(
                partesData[1],
                10
            ) - 1;

        dia =
            parseInt(
                partesData[2],
                10
            );

    }


    else {

        return null;

    }


    const partesHora =
        horaParte.split(":");


    const hora =
        parseInt(
            partesHora[0] || "0",
            10
        );

    const minuto =
        parseInt(
            partesHora[1] || "0",
            10
        );

    const segundo =
        parseInt(
            partesHora[2] || "0",
            10
        );


    const data =
        new Date(
            ano,
            mes,
            dia,
            hora,
            minuto,
            segundo
        );


    if (
        isNaN(
            data.getTime()
        )
    ) {

        return null;

    }


    return data;
}


/* =========================================================
   STATUS DO SISTEMA
========================================================== */

function atualizarStatusSistema() {

    const ponto =
        document.getElementById(
            "pontoSistema"
        );

    const texto =
        document.getElementById(
            "textoSistema"
        );


    let ultimaData = null;


    impressoras.forEach(
        function (impressora) {

            if (!impressora.data_hora) {
                return;
            }


            const data =
                converterDataBanco(
                    impressora.data_hora
                );


            if (!data) {
                return;
            }


            if (
                ultimaData === null ||
                data > ultimaData
            ) {

                ultimaData = data;

            }

        }
    );


    if (!ultimaData) {

        texto.textContent =
            "Aguardando dados";

        ponto.classList.add(
            "ponto-inativo"
        );

        return;

    }


    const agora =
        new Date();


    const diferencaMilissegundos =
        agora.getTime() -
        ultimaData.getTime();


    const diferencaMinutos =
        diferencaMilissegundos /
        60000;


    if (
        diferencaMinutos >= 0 &&
        diferencaMinutos <= 15
    ) {

        texto.textContent =
            "Sistema atualizado";

        ponto.classList.remove(
            "ponto-inativo"
        );

    }


    else {

        texto.textContent =
            "Sistema desatualizado";

        ponto.classList.add(
            "ponto-inativo"
        );

    }

}


carregarImpressoras();


/* =========================================================
   ABAS
========================================================== */

function mostrarAba(nome) {

    const monitoramento =
        document.getElementById(
            "aba-monitoramento"
        );

    const analise =
        document.getElementById(
            "aba-analise"
        );


    const btnMonitoramento =
        document.getElementById(
            "btnMonitoramento"
        );

    const btnAnalise =
        document.getElementById(
            "btnAnalise"
        );


    monitoramento.classList.remove(
        "ativa"
    );

    analise.classList.remove(
        "ativa"
    );

    btnMonitoramento.classList.remove(
        "ativo"
    );

    btnAnalise.classList.remove(
        "ativo"
    );


    const mostrandoAnalise =
        nome === "analise";


    if (mostrandoAnalise) {

        analise.classList.add(
            "ativa"
        );

        btnAnalise.classList.add(
            "ativo"
        );

    }

    else {

        monitoramento.classList.add(
            "ativa"
        );

        btnMonitoramento.classList.add(
            "ativo"
        );

    }


    // informa aos leitores de tela qual aba está aberta

    btnAnalise.setAttribute(
        "aria-selected",
        String(mostrandoAnalise)
    );

    btnMonitoramento.setAttribute(
        "aria-selected",
        String(!mostrandoAnalise)
    );

}


/* =========================================================
   FILTROS
========================================================== */

function marcarFiltroAtivo(filtro) {

    // deixa marcado qual contador está selecionado

    const contadores = {
        todos: "contador-total",
        online: "contador-online",
        offline: "contador-offline",
        atencao: "contador-atencao",
        critico: "contador-critico"
    };


    Object.keys(contadores).forEach(
        function (nome) {

            const elemento =
                document.querySelector(
                    "." + contadores[nome]
                );


            if (elemento) {

                elemento.setAttribute(
                    "aria-pressed",
                    String(nome === filtro)
                );
            }
        }
    );
}


function filtrarImpressoras(filtro) {

    filtroAtual = filtro;

    marcarFiltroAtivo(filtro);

    const cards =
        document.querySelectorAll(
            ".impressora"
        );


    let quantidade = 0;


    cards.forEach(
        function (card) {

            const rede =
                card.dataset.rede;

            const geral =
                card.dataset.geral;


            let mostrar = false;


            if (
                filtro === "todos"
            ) {

                mostrar = true;

            }


            else if (
                filtro === "online"
            ) {

                mostrar =
                    rede === "online";

            }


            else if (
                filtro === "offline"
            ) {

                mostrar =
                    rede === "offline";

            }


            else if (
                filtro === "atencao"
            ) {

                mostrar =
                    geral === "atencao";

            }


            else if (
                filtro === "critico"
            ) {

                mostrar =
                    geral === "critico";

            }


            if (mostrar) {

                card.style.display =
                    "flex";

                quantidade++;

            }


            else {

                card.style.display =
                    "none";

            }

        }
    );


    document.getElementById(
        "contadorGrid"
    ).textContent =
        `${quantidade} impressora${quantidade !== 1 ? "s" : ""}`;

}


/* =========================================================
   DETALHES DA IMPRESSORA
========================================================== */

function abrirDetalhes(indice) {

    // quem estava com o foco volta a tê-lo quando a janela fechar
    elementoQueAbriuModal = document.activeElement;

    const impressora =
        impressoras[indice];


    if (!impressora) {
        return;
    }


    document.getElementById(
        "modalTitulo"
    ).textContent =
        impressora.local ||
        "Impressora";


    let html = "";


    html += `

        <div class="detalhes-grid">

            <div class="detalhe">

                <span class="detalhe-label">
                    Local
                </span>

                <span class="detalhe-valor">
                    ${impressora.local || "-"}
                </span>

            </div>


            <div class="detalhe">

                <span class="detalhe-label">
                    Modelo
                </span>

                <span class="detalhe-valor">
                    ${impressora.modelo || "-"}
                </span>

            </div>


            <div class="detalhe">

                <span class="detalhe-label">
                    Tipo
                </span>

                <span class="detalhe-valor">
                    ${impressora.tipo || "-"}
                </span>

            </div>


            <div class="detalhe">

                <span class="detalhe-label">
                    IP
                </span>

                <span class="detalhe-valor">
                    ${impressora.ip || "-"}
                </span>

            </div>


            <div class="detalhe">

                <span class="detalhe-label">
                    Número de série
                </span>

                <span class="detalhe-valor">
                    ${impressora.serie || "-"}
                </span>

            </div>


            <div class="detalhe">

                <span class="detalhe-label">
                    Papel
                </span>

                <span class="detalhe-valor">
                    ${impressora.paper || "-"}
                </span>

            </div>


            <div class="detalhe">

                <span class="detalhe-label">
                    Status da rede
                </span>

                <span class="detalhe-valor">
                    ${impressora.status_rede || "-"}
                </span>

            </div>


            <div class="detalhe">

                <span class="detalhe-label">
                    Status geral
                </span>

                <span class="detalhe-valor">
                    ${impressora.status_geral || "-"}
                </span>

            </div>


            <div class="detalhe">

                <span class="detalhe-label">
                    Última medição
                </span>

                <span class="detalhe-valor">
                    ${impressora.data_hora || "-"}
                </span>

            </div>

        </div>

    `;


    html += `

        <div class="secao-modal">

            <h3>
                Suprimentos
            </h3>

    `;


    const suprimentos =
        impressora.suprimentos || {};


    const statusSuprimentos =
        impressora.status_suprimentos || {};


    const chaves =
        Object.keys(
            suprimentos
        );


    if (
        chaves.length === 0
    ) {

        html += `

            <div class="sem-suprimentos">
                Nenhuma informação de suprimentos disponível.
            </div>

        `;

    }


    else {

        html += `

            <div class="suprimentos">

        `;


        chaves.forEach(
            function (chave) {

                let valor =
                    Number(
                        suprimentos[chave]
                    );


                if (
                    Number.isNaN(
                        valor
                    )
                ) {

                    valor = 0;

                }


                valor =
                    Math.max(
                        0,
                        Math.min(
                            100,
                            valor
                        )
                    );


                const status =
                    statusSuprimentos[chave] ||
                    "normal";


                let classeBarra =
                    "barra-normal";


                if (
                    status === "atencao"
                ) {

                    classeBarra =
                        "barra-atencao";

                }


                else if (
                    status === "critico"
                ) {

                    classeBarra =
                        "barra-critico";

                }


                let nome =
                    chave
                    .replace(
                        "toner_",
                        "Toner "
                    )
                    .replace(
                        "unidade_imagem",
                        "Unidade de imagem"
                    );


                nome =
                    nome.charAt(0).toUpperCase() +
                    nome.slice(1);


                html += `

                    <div class="suprimento">

                        <div class="suprimento-topo">

                            <span>
                                ${nome}
                            </span>

                            <strong>
                                ${valor}%
                            </strong>

                        </div>


                        <div class="barra-suprimento">

                            <div
                                class="barra-preenchimento ${classeBarra}"
                                style="width: ${valor}%;">

                            </div>

                        </div>

                    </div>

                `;

            }
        );


        html += `

            </div>

        `;

    }


    html += `

        </div>

    `;


    if (impressora.ip) {

        html += `

            <a
                class="botao-acesso"
                href="http://${impressora.ip}"
                target="_blank">

                🌐 Acessar interface da impressora

            </a>

        `;

    }


    document.getElementById(
        "modalCorpo"
    ).innerHTML =
        html;


    document.getElementById(
        "modalDetalhes"
    ).classList.add(
        "ativo"
    );


    // o foco vai para dentro da janela

    const botaoFechar =
        document.getElementById(
            "botaoFecharModal"
        );


    if (botaoFechar && botaoFechar.focus) {
        botaoFechar.focus();
    }
}


/* =========================================================
   FOCO DENTRO DA JANELA

   Com a janela aberta, o Tab não pode sair para a página
   atrás dela: o foco circula entre os elementos da janela.
========================================================== */

function elementosFocaveisDoModal() {

    const modal =
        document.getElementById(
            "modalDetalhes"
        );


    if (!modal || !modal.querySelectorAll) {
        return [];
    }


    return Array.from(
        modal.querySelectorAll(
            "button, a[href], [tabindex]:not([tabindex=\"-1\"])"
        )
    );
}


function manterFocoNaJanela(evento) {

    if (
        evento.key !== "Tab" ||
        !modalEstaAberto()
    ) {
        return;
    }


    const focaveis =
        elementosFocaveisDoModal();


    if (focaveis.length === 0) {
        return;
    }


    const primeiro = focaveis[0];

    const ultimo =
        focaveis[focaveis.length - 1];


    if (
        evento.shiftKey &&
        document.activeElement === primeiro
    ) {

        evento.preventDefault();

        ultimo.focus();

    }

    else if (
        !evento.shiftKey &&
        document.activeElement === ultimo
    ) {

        evento.preventDefault();

        primeiro.focus();
    }
}


document.addEventListener(
    "keydown",
    manterFocoNaJanela
);


/* =========================================================
   TECLADO

   Cards e contadores são divs com papel de botão. O
   navegador não aciona esses elementos pelo teclado
   sozinho, então tratamos Enter e Espaço aqui.
========================================================== */

document.addEventListener(
    "keydown",
    function (evento) {

        if (
            evento.key !== "Enter" &&
            evento.key !== " "
        ) {
            return;
        }


        const alvo = evento.target;


        if (
            !alvo ||
            !alvo.getAttribute ||
            alvo.getAttribute("role") !== "button"
        ) {
            return;
        }


        // evita que o Espaço role a página
        evento.preventDefault();

        alvo.click();
    }
);


/* =========================================================
   FECHAR MODAL
========================================================== */

function modalEstaAberto() {

    const modal =
        document.getElementById(
            "modalDetalhes"
        );

    return Boolean(
        modal &&
        modal.classList &&
        modal.classList.contains("ativo")
    );
}


function fecharModal() {

    document.getElementById(
        "modalDetalhes"
    ).classList.remove(
        "ativo"
    );


    // devolve o foco para o card que abriu a janela

    if (
        elementoQueAbriuModal &&
        elementoQueAbriuModal.focus
    ) {
        elementoQueAbriuModal.focus();
    }

    elementoQueAbriuModal = null;
}


function fecharModalFora(evento) {

    if (
        evento.target.id ===
        "modalDetalhes"
    ) {

        fecharModal();

    }

}


document.addEventListener(
    "keydown",
    function (evento) {

        if (
            evento.key === "Escape"
        ) {

            fecharModal();

        }

    }
);


/* =========================================================
   ATUALIZAÇÃO AUTOMÁTICA
   
   A página será recarregada a cada 50 segundos.
========================================================== */

let segundosParaAtualizar = configuracao.intervalo_atualizacao;

let atualizacaoEmAndamento = false;


const contadorAtualizacao =
    document.getElementById(
        "contadorAtualizacao"
    );


function atualizarContador() {

    if (
        !contadorAtualizacao
    ) {
        return;
    }

    contadorAtualizacao.textContent =
        `Próxima atualização: ${segundosParaAtualizar}s`;
}


atualizarContador();


setInterval(
    function () {

        if (atualizacaoEmAndamento) {
            return;
        }


        segundosParaAtualizar--;


        if (
            segundosParaAtualizar > 0
        ) {

            atualizarContador();

            return;
        }


        // ------------------------------------------------
        // Chegou a hora: busca os dados novos na API.
        // A página não é recarregada, apenas os valores
        // da tela são trocados.
        // ------------------------------------------------

        atualizacaoEmAndamento = true;

        contadorAtualizacao.textContent =
            "Atualizando...";

        contadorAtualizacao.classList.add(
            "atualizando"
        );


        atualizarTudo().finally(
            function () {

                contadorAtualizacao.classList.remove(
                    "atualizando"
                );

                segundosParaAtualizar =
                    configuracao.intervalo_atualizacao;

                atualizarContador();

                atualizacaoEmAndamento = false;
            }
        );
    },
    1000
);
