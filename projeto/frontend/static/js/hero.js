document.addEventListener('DOMContentLoaded', () => {
    const contatoForm = document.getElementById('contato-form');
    const feedback = document.getElementById('contato-feedback');
    const primeiroNome = document.getElementById('primeiro-nome');
    const nivelAtualValor = document.getElementById('nivel-atual-valor');
    const nivelAtualTexto = document.getElementById('nivel-atual-texto');
    const totalCheckinsValor = document.getElementById('total-checkins-valor');
    const totalCheckinsTexto = document.getElementById('total-checkins-texto');
    const tendenciaValor = document.getElementById('tendencia-valor');
    const tendenciaTexto = document.getElementById('tendencia-texto');
    const proximoCheckinValor = document.getElementById('proximo-checkin-valor');
    const proximoCheckinTexto = document.getElementById('proximo-checkin-texto');
    const infoCards = document.querySelectorAll('.info-card');
    let currentUser = null;

    function setupTiltCards() {
        const maxTilt = 15;

        infoCards.forEach((card) => {
            let animationFrame = null;

            card.addEventListener('mousemove', (event) => {
                const rect = card.getBoundingClientRect();
                const x = (event.clientX - rect.left) / rect.width;
                const y = (event.clientY - rect.top) / rect.height;
                const tiltX = (y - 0.5) * maxTilt;
                const tiltY = (0.5 - x) * maxTilt;

                if (animationFrame) {
                    cancelAnimationFrame(animationFrame);
                }

                animationFrame = requestAnimationFrame(() => {
                    card.classList.add('is-tilting');
                    card.style.setProperty('--tilt-x', `${tiltX}deg`);
                    card.style.setProperty('--tilt-y', `${tiltY}deg`);
                    card.style.setProperty('--tilt-scale', '1.05');
                });
            });

            card.addEventListener('mouseleave', () => {
                if (animationFrame) {
                    cancelAnimationFrame(animationFrame);
                }

                card.classList.remove('is-tilting');
                card.style.setProperty('--tilt-x', '0deg');
                card.style.setProperty('--tilt-y', '0deg');
                card.style.setProperty('--tilt-scale', '1');
            });
        });
    }

    function getFirstName(fullName) {
        return fullName.trim().split(/\s+/)[0] || '[seu nome]';
    }

    function setCurrentLevelInfo(valor, texto) {
        nivelAtualValor.textContent = valor;
        nivelAtualTexto.textContent = texto;
    }

    function setTotalCheckinsInfo(valor, texto) {
        totalCheckinsValor.textContent = valor;
        totalCheckinsTexto.textContent = texto;
    }

    function setTrendInfo(valor, texto) {
        tendenciaValor.textContent = valor;
        tendenciaTexto.textContent = texto;
    }

    function setNextCheckinInfo(valor, texto) {
        proximoCheckinValor.textContent = valor;
        proximoCheckinTexto.textContent = texto;
    }

    function normalizeText(value) {
        return String(value || '')
            .normalize('NFD')
            .replace(/[\u0300-\u036f]/g, '')
            .toLowerCase()
            .trim();
    }

    function getAiTrendLabel(aiInsight) {
        const normalizedInsight = normalizeText(aiInsight);

        if (normalizedInsight.includes('melhora')) {
            return 'Em melhora';
        }

        if (normalizedInsight.includes('piora')) {
            return 'Em piora';
        }

        if (normalizedInsight.includes('estabilidade')) {
            return 'Em estabilidade';
        }

        return 'A definir';
    }

    function getAiTrendExplanation(latestCheckin, previousCheckin) {
        const insight = latestCheckin?.ai_insights || '';
        const variationMatch = insight.match(/Variacao em relacao ao ultimo check-in: ([^.]+)\./i);
        const confidenceMatch = insight.match(/confianca (\d+)%/i);

        if (variationMatch && confidenceMatch) {
            return `IA ${confidenceMatch[1]}% | ${variationMatch[1]}`;
        }

        if (variationMatch) {
            return variationMatch[1];
        }

        if (confidenceMatch) {
            return `IA com confianca ${confidenceMatch[1]}%`;
        }

        if (!previousCheckin) {
            return 'IA aguardando mais historico';
        }

        return 'analise da IA no ultimo check-in';
    }

    function getTrendInfo(checkins) {
        if (checkins.length === 0) {
            return {
                valor: 'Sem dados',
                texto: 'faca seu primeiro check-in'
            };
        }

        const latestCheckin = checkins[0];
        const previousCheckin = checkins[1] || null;
        const trendLabel = getAiTrendLabel(latestCheckin.ai_insights);

        if (trendLabel !== 'A definir') {
            return {
                valor: trendLabel,
                texto: getAiTrendExplanation(latestCheckin, previousCheckin)
            };
        }

        if (!previousCheckin) {
            return {
                valor: 'Sem hist\u00f3rico',
                texto: 'aguardando comparativo'
            };
        }

        const latestScore = Number(latestCheckin.stress_level);
        const previousScore = Number(previousCheckin.stress_level);

        if (Number.isNaN(latestScore) || Number.isNaN(previousScore)) {
            return {
                valor: 'A definir',
                texto: 'dados insuficientes'
            };
        }

        const difference = latestScore - previousScore;
        const absoluteDifference = Math.abs(difference);

        if (absoluteDifference <= 2) {
            return {
                valor: 'Em estabilidade',
                texto: 'sem mudancas relevantes'
            };
        }

        return difference > 0
            ? {
                valor: 'Em melhora',
                texto: `alta de ${absoluteDifference} pontos`
            }
            : {
                valor: 'Em piora',
                texto: `queda de ${absoluteDifference} pontos`
            };
    }

    function formatCheckinDate(dateValue) {
        if (!dateValue) {
            return '';
        }

        const date = new Date(dateValue);

        if (Number.isNaN(date.getTime())) {
            return '';
        }

        return new Intl.DateTimeFormat('pt-BR', {
            day: '2-digit',
            month: 'short'
        }).format(date);
    }

    function getNextCheckinValue(data) {
        if (data.available === true) {
            return 'Dispon\u00edvel';
        }

        const daysRemaining = Number(data.days_remaining);

        if (Number.isNaN(daysRemaining)) {
            return formatCheckinDate(data.next_checkin) || 'A definir';
        }

        if (daysRemaining <= 0) {
            return 'Hoje';
        }

        if (daysRemaining === 1) {
            return 'Amanh\u00e3';
        }

        return `Em ${daysRemaining} dias`;
    }

    function getNextCheckinText(data) {
        if (data.available === true) {
            return 'primeiro check-in liberado';
        }

        const formattedDate = formatCheckinDate(data.next_checkin);

        if (!formattedDate) {
            return 'pr\u00f3ximo check-in';
        }

        return `pr\u00f3ximo check-in em ${formattedDate}`;
    }

    async function loadCurrentUser() {
        const accessToken = localStorage.getItem('access_token');
        const tokenType = localStorage.getItem('token_type') || 'bearer';

        if (!accessToken) {
            return null;
        }

        try {
            const response = await fetch('/usuarios/me', {
                cache: 'no-store',
                headers: {
                    Authorization: `${tokenType} ${accessToken}`
                }
            });

            if (!response.ok) {
                return null;
            }

            const user = await response.json();
            currentUser = user;
            primeiroNome.textContent = getFirstName(user.name);
            return user;
        } catch (error) {
            console.error('Erro ao carregar usuario:', error);
            return null;
        }
    }

    async function loadCheckinsSummary(userId) {
        const accessToken = localStorage.getItem('access_token');
        const tokenType = localStorage.getItem('token_type') || 'bearer';
        const headers = {};

        if (accessToken) {
            headers.Authorization = `${tokenType} ${accessToken}`;
        }

        try {
            const response = await fetch(`/forms/history/${userId}`, {
                cache: 'no-store',
                headers
            });

            if (!response.ok) {
                setCurrentLevelInfo('A definir', 'n\u00e3o foi poss\u00edvel carregar');
                setTotalCheckinsInfo('A definir', 'n\u00e3o foi poss\u00edvel carregar');
                setTrendInfo('A definir', 'n\u00e3o foi poss\u00edvel carregar');
                return;
            }

            const checkins = await response.json();

            if (!Array.isArray(checkins)) {
                setCurrentLevelInfo('A definir', 'n\u00e3o foi poss\u00edvel carregar');
                setTotalCheckinsInfo('A definir', 'n\u00e3o foi poss\u00edvel carregar');
                setTrendInfo('A definir', 'n\u00e3o foi poss\u00edvel carregar');
                return;
            }

            setTotalCheckinsInfo(String(checkins.length), 'total realizado');
            const trendInfo = getTrendInfo(checkins);
            setTrendInfo(trendInfo.valor, trendInfo.texto);

            if (checkins.length === 0) {
                setCurrentLevelInfo('Sem dados', 'fa\u00e7a seu primeiro check-in');
                return;
            }

            const latestCheckin = checkins[0];
            setCurrentLevelInfo(latestCheckin.overall_mood || 'A definir', 'ultimo check-in');
        } catch (error) {
            console.error('Erro ao carregar resumo de check-ins:', error);
            setCurrentLevelInfo('A definir', 'n\u00e3o foi poss\u00edvel carregar');
            setTotalCheckinsInfo('A definir', 'n\u00e3o foi poss\u00edvel carregar');
            setTrendInfo('A definir', 'n\u00e3o foi poss\u00edvel carregar');
        }
    }

    async function loadNextCheckin(userId) {
        const accessToken = localStorage.getItem('access_token');
        const tokenType = localStorage.getItem('token_type') || 'bearer';
        const headers = {};

        if (accessToken) {
            headers.Authorization = `${tokenType} ${accessToken}`;
        }

        try {
            const response = await fetch(`/forms/next-checkin/${userId}`, {
                cache: 'no-store',
                headers
            });

            if (!response.ok) {
                setNextCheckinInfo('A definir', 'n\u00e3o foi poss\u00edvel carregar');
                return;
            }

            const data = await response.json();
            setNextCheckinInfo(getNextCheckinValue(data), getNextCheckinText(data));
        } catch (error) {
            console.error('Erro ao carregar proximo check-in:', error);
            setNextCheckinInfo('A definir', 'n\u00e3o foi poss\u00edvel carregar');
        }
    }

    async function loadDashboard() {
        const user = await loadCurrentUser();

        if (!user) {
            setCurrentLevelInfo('A definir', 'fa\u00e7a login para consultar');
            setTotalCheckinsInfo('A definir', 'fa\u00e7a login para consultar');
            setTrendInfo('A definir', 'fa\u00e7a login para consultar');
            setNextCheckinInfo('A definir', 'fa\u00e7a login para consultar');
            return;
        }

        await Promise.all([
            loadCheckinsSummary(user.id),
            loadNextCheckin(user.id)
        ]);
    }

    loadDashboard();
    setupTiltCards();

    contatoForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        feedback.textContent = 'Enviando mensagem...';
        feedback.style.color = 'var(--text-main)';

        const duvida = document.getElementById('duvida').value.trim();

        if (!currentUser) {
            feedback.textContent = 'Nao foi possivel identificar seu usuario. Faca login novamente.';
            feedback.style.color = '#b71c1c';
            return;
        }

        const payload = {
            subject: 'Contato pelo painel',
            user_id: currentUser.id,
            user_name: currentUser.name,
            user_email: currentUser.email,
            email_to: 'inatelc317.mentistech.test@gmail.com',
            message: duvida
        };

        try {
            const response = await fetch('/email/send', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                const data = await response.json();
                feedback.textContent = data.detail ? `Erro: ${data.detail}` : 'Erro ao enviar mensagem.';
                feedback.style.color = '#b71c1c';
                return;
            }

            feedback.textContent = 'Mensagem enviada com sucesso!';
            feedback.style.color = '#166534';
            contatoForm.reset();
        } catch (error) {
            console.error('Erro enviar email:', error);
            feedback.textContent = 'Erro ao enviar mensagem. Tente novamente.';
            feedback.style.color = '#b71c1c';
        }
    });
});
