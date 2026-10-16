const impressoras =
    JSON.parse(
        document.getElementById(
            "dados-impressoras"
        ).textContent
    );


const configuracao =
    JSON.parse(
        document.getElementById(
            "config-dashboard"
        ).textContent
    );


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


atualizarStatusSistema();


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


    if (
        nome === "analise"
    ) {

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

}


/* =========================================================
   FILTROS
========================================================== */

function filtrarImpressoras(filtro) {

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

}


/* =========================================================
   FECHAR MODAL
========================================================== */

function fecharModal() {

    document.getElementById(
        "modalDetalhes"
    ).classList.remove(
        "ativo"
    );

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
        `🔄 Próxima atualização: ${segundosParaAtualizar}s`;

}


atualizarContador();


const intervaloAtualizacao =
    setInterval(
        function () {

            segundosParaAtualizar--;


            if (
                segundosParaAtualizar <= 0
            ) {

                clearInterval(
                    intervaloAtualizacao
                );


                contadorAtualizacao.textContent =
                    "🔄 Atualizando...";


                contadorAtualizacao.classList.add(
                    "atualizando"
                );


                setTimeout(
                    function () {
                        location.reload();
                    },
                    300
                );


                return;
            }


            atualizarContador();

        },
        1000
    );
