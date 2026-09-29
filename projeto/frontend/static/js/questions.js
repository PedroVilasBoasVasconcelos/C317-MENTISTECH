document.addEventListener("DOMContentLoaded", async () => {
    let perguntas = [];

    try {
        const response = await fetch('/forms/questions');
        perguntas = await response.json();
    } catch (error) {
        console.error('Erro ao carregar perguntas:', error);
        // Fallback or error handling
        perguntas = [];
    }

    let perguntaAtual = 0;
    const respostas = {};

    const pagina = document.getElementById("questionario-page");
    const heroUrl = pagina.dataset.heroUrl;
    let currentUser = null;

    const passoAtual = document.getElementById("passo-atual");
    const perguntaTitulo = document.getElementById("pergunta-titulo");
    const opcoesContainer = document.getElementById("opcoes");
    const botaoVoltar = document.getElementById("botao-voltar");
    const botaoProximo = document.getElementById("botao-proximo");
    const formulario = document.getElementById("questionario-form");
    const progressoContainer = document.getElementById("progresso");

    // Generate progress bars dynamically
    progressoContainer.innerHTML = '';
    for (let i = 0; i < perguntas.length; i++) {
        const span = document.createElement('span');
        progressoContainer.appendChild(span);
    }
    const barrasProgresso = Array.from(progressoContainer.querySelectorAll('span'));

    const modalOverlay = document.getElementById("modal-overlay");
    const modalLabel = document.getElementById("modal-label");
    const modalTitulo = document.getElementById("modal-titulo");
    const modalTexto = document.getElementById("modal-texto");
    const modalCancelar = document.getElementById("modal-cancelar");
    const modalConfirmar = document.getElementById("modal-confirmar");

    let acaoConfirmarModal = null;
    let acaoCancelarModal = null;

    const defaultScaleOptions = [
        { face: "😣", label: "Muito ruim" },
        { face: "😕", label: "Ruim" },
        { face: "😐", label: "Neutro" },
        { face: "🙂", label: "Bom" },
        { face: "😄", label: "Excelente" }
    ];

    const scaleOptionsByQuestionId = {
        1: [
            { face: "😣", label: "Muito alta", value: 5 },
            { face: "😕", label: "Alta", value: 4 },
            { face: "😐", label: "Moderada", value: 3 },
            { face: "🙂", label: "Baixa", value: 2 },
            { face: "😄", label: "Nenhuma", value: 1 }
        ],
        2: [
            { face: "😣", label: "Nenhum apoio" },
            { face: "😕", label: "Pouco apoio" },
            { face: "😐", label: "Moderado" },
            { face: "🙂", label: "Bom apoio" },
            { face: "😄", label: "Muito apoio" }
        ],
        3: [
            { face: "😣", label: "Interferiu muito", value: 5 },
            { face: "😕", label: "Interferiu bastante", value: 4 },
            { face: "😐", label: "Moderado", value: 3 },
            { face: "🙂", label: "Interferiu pouco", value: 2 },
            { face: "😄", label: "N\u00e3o interferiu", value: 1 }
        ],
        4: [
            { face: "😣", label: "Nada acolhedora" },
            { face: "😕", label: "Pouco acolhedora" },
            { face: "😐", label: "Neutra" },
            { face: "🙂", label: "Acolhedora" },
            { face: "😄", label: "Muito acolhedora" }
        ],
        5: defaultScaleOptions,
        6: defaultScaleOptions,
        7: defaultScaleOptions,
        8: [
            { face: "😣", label: "Nada reconhecido(a)" },
            { face: "😕", label: "Pouco" },
            { face: "😐", label: "Moderado" },
            { face: "🙂", label: "Bem reconhecido(a)" },
            { face: "😄", label: "Muito reconhecido(a)" }
        ],
        9: [
            { face: "😣", label: "Nenhuma" },
            { face: "😕", label: "Poucas" },
            { face: "😐", label: "Moderadas" },
            { face: "🙂", label: "Boas" },
            { face: "😄", label: "Excelentes" }
        ],
        10: [
            { face: "😣", label: "Muito negativo" },
            { face: "😕", label: "Negativo" },
            { face: "😐", label: "Neutro" },
            { face: "🙂", label: "Positivo" },
            { face: "😄", label: "Muito positivo" }
        ]
    };

    function getAuthHeaders() {
        const accessToken = localStorage.getItem("access_token");
        const tokenType = localStorage.getItem("token_type") || "bearer";
        const headers = {};

        if (accessToken) {
            headers.Authorization = `${tokenType} ${accessToken}`;
        }

        return headers;
    }

    async function loadCurrentUser() {
        try {
            const response = await fetch("/usuarios/me", {
                cache: "no-store",
                headers: getAuthHeaders()
            });

            if (!response.ok) {
                return null;
            }

            return await response.json();
        } catch (error) {
            console.error("Erro ao carregar usuario:", error);
            return null;
        }
    }

    function abrirModal({
        label = "AVISO",
        titulo = "",
        texto = "",
        textoConfirmar = "OK",
        textoCancelar = "Cancelar",
        mostrarCancelar = true,
        onConfirm = null,
        onCancel = null
    }) {
        modalLabel.textContent = label;
        modalTitulo.textContent = titulo;
        modalTexto.textContent = texto;
        modalConfirmar.textContent = textoConfirmar;
        modalCancelar.textContent = textoCancelar;

        acaoConfirmarModal = onConfirm;
        acaoCancelarModal = onCancel;

        modalCancelar.style.display = mostrarCancelar ? "inline-flex" : "none";
        modalOverlay.classList.add("ativo");
    }

    function fecharModal() {
        modalOverlay.classList.remove("ativo");
        acaoConfirmarModal = null;
        acaoCancelarModal = null;
    }

    modalConfirmar.addEventListener("click", () => {
        if (acaoConfirmarModal) {
            acaoConfirmarModal();
        } else {
            fecharModal();
        }
    });

    modalCancelar.addEventListener("click", () => {
        if (acaoCancelarModal) {
            acaoCancelarModal();
        }
        fecharModal();
    });

    modalOverlay.addEventListener("click", (event) => {
        if (event.target === modalOverlay) {
            fecharModal();
        }
    });

    function renderizarPergunta() {
        if (perguntas.length === 0) {
            perguntaTitulo.textContent = "Erro ao carregar perguntas.";
            return;
        }

        const pergunta = perguntas[perguntaAtual];
        const respostaAtual = respostas[pergunta.id];

        passoAtual.textContent = `Pergunta ${perguntaAtual + 1} de ${perguntas.length}`;
        perguntaTitulo.textContent = pergunta.question;

        if (pergunta.type === "scale") {
            const options = scaleOptionsByQuestionId[pergunta.id] || defaultScaleOptions;
            opcoesContainer.innerHTML = options.map((option, index) => {
                const value = option.value || index + 1;
                return `
                    <label class="opcao">
                        <input type="radio" name="resposta" value="${value}" ${respostaAtual == value ? "checked" : ""}>
                        <span class="opcao-card">
                            <span class="resposta-emoji" aria-hidden="true">${option.face}</span>
                            <strong>${option.label}</strong>
                        </span>
                    </label>
                `;
            }).join("");
        } else {
            // Fallback for other types
            opcoesContainer.innerHTML = "<p>Tipo de pergunta não suportado.</p>";
        }

        barrasProgresso.forEach((barra, indice) => {
            barra.className = "";

            if (indice < perguntaAtual) {
                barra.classList.add("feito");
            } else if (indice === perguntaAtual) {
                barra.classList.add("atual");
            }
        });

        botaoVoltar.textContent = perguntaAtual === 0 ? "SAIR" : "VOLTAR";
        botaoProximo.textContent = perguntaAtual === perguntas.length - 1 ? "SALVAR E ENVIAR" : "PRÓXIMO";
    }

    opcoesContainer.addEventListener("change", (event) => {
        if (event.target.name === "resposta") {
            const pergunta = perguntas[perguntaAtual];
            respostas[pergunta.id] = parseInt(event.target.value);
        }
    });

    botaoVoltar.addEventListener("click", () => {
        if (perguntaAtual === 0) {
            window.location.href = heroUrl;
            return;
        }

        perguntaAtual -= 1;
        renderizarPergunta();
    });

    formulario.addEventListener("submit", (event) => {
        event.preventDefault();

        const selecionada = formulario.querySelector('input[name="resposta"]:checked');

        if (!selecionada) {
            abrirModal({
                label: "ATENÇÃO",
                titulo: "Selecione uma resposta",
                texto: "Você precisa escolher uma opção antes de continuar.",
                textoConfirmar: "Entendi",
                mostrarCancelar: false,
                onConfirm: fecharModal
            });
            return;
        }

        const pergunta = perguntas[perguntaAtual];
        respostas[pergunta.id] = parseInt(selecionada.value);

        if (perguntaAtual === perguntas.length - 1) {
            abrirModal({
                label: "FINALIZAR QUESTIONÁRIO",
                titulo: "Deseja salvar e enviar suas respostas?",
                texto: "Se confirmar, os dados serão salvos e enviados para as psicólogas da empresa.",
                textoConfirmar: "Salvar e enviar",
                textoCancelar: "Revisar",
                mostrarCancelar: true,
                onConfirm: async () => {
                    try {
                        const answers = perguntas.map(pergunta => ({
                            question_id: pergunta.id,
                            value: respostas[pergunta.id] || 0
                        }));

                        if (!currentUser) {
                            throw new Error("Nao foi possivel identificar seu usuario. Faca login novamente.");
                        }

                        const payload = {
                            user_id: currentUser.id,
                            answers: answers,
                            created_at: new Date().toISOString()
                        };

                        const response = await fetch('/forms/submit', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                ...getAuthHeaders()
                            },
                            body: JSON.stringify(payload)
                        });

                        let data = null;

                        try {
                            data = await response.json();
                        } catch {
                            data = null;
                        }

                        if (!response.ok) {
                            throw new Error(
                                data?.detail ||
                                data?.message ||
                                `Erro ${response.status}`
                            );
                        }

                        abrirModal({
                            label: "DADOS ENVIADOS",
                            titulo: "Respostas enviadas com sucesso",
                            texto: "Os dados foram salvos com sucesso.",
                            textoConfirmar: "Voltar ao painel",
                            mostrarCancelar: false,
                            onConfirm: () => {
                                window.location.href = heroUrl;
                            }
                        });

                    } catch (error) {

                        console.error("Erro completo:", error);

                        abrirModal({
                            label: "ERRO",
                            titulo: "Erro ao enviar respostas",
                            texto: error.message,
                            textoConfirmar: "OK",
                            mostrarCancelar: false,
                            onConfirm: fecharModal
                        });
                    }
                }
            });
            return;
        }

        perguntaAtual += 1;
        renderizarPergunta();
    });

    currentUser = await loadCurrentUser();
    renderizarPergunta();
});
