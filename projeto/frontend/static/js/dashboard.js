document.addEventListener('DOMContentLoaded', () => {
    const dashboardTitle = document.getElementById('dashboard-title');
    const dashboardSubtitle = document.getElementById('dashboard-subtitle');
    const psychologistArea = document.getElementById('psychologist-area');
    const companyUsersTotal = document.getElementById('company-users-total');
    const companyCheckinsTotal = document.getElementById('company-checkins-total');
    const companyAverageStress = document.getElementById('company-average-stress');
    const companyGroupChart = document.getElementById('company-group-chart');
    const companyMoodChart = document.getElementById('company-mood-chart');
    const peopleTable = document.getElementById('people-table');
    const userSearchForm = document.getElementById('user-search-form');
    const targetUserId = document.getElementById('target-user-id');
    const teamSearchForm = document.getElementById('team-search-form');
    const targetTeam = document.getElementById('target-team');
    const individualSectionTitle = document.getElementById('individual-section-title');
    const individualSectionDescription = document.getElementById('individual-section-description');
    const periodButtons = document.querySelectorAll('.periodo-btn');
    const stressChartSvg = document.getElementById('stress-chart-svg');
    const stressChartSummary = document.getElementById('stress-chart-summary');
    const stressChartEmpty = document.getElementById('stress-chart-empty');
    const stressChartTooltip = document.getElementById('stress-chart-tooltip');
    const aiTrendCard = document.getElementById('ai-trend-card');
    const moodDistribution = document.getElementById('mood-distribution');
    const recentCheckinsChart = document.getElementById('recent-checkins-chart');

    let currentUser = null;
    let overviewUsers = [];
    let individualCheckins = [];
    let aiTrendOverride = null;
    let trendMetaLabel = 'Nivel atual';
    let activeChartMode = 'all';

    function getAuthHeaders() {
        const accessToken = localStorage.getItem('access_token');
        const tokenType = localStorage.getItem('token_type') || 'bearer';
        const headers = {};

        if (accessToken) {
            headers.Authorization = `${tokenType} ${accessToken}`;
        }

        return headers;
    }

    async function fetchJson(url) {
        const response = await fetch(url, {
            cache: 'no-store',
            headers: getAuthHeaders()
        });

        const data = await response.json().catch(() => null);

        if (!response.ok) {
            throw new Error(data?.detail || `Erro ${response.status}`);
        }

        return data;
    }

    function normalizeText(value) {
        return String(value || '')
            .normalize('NFD')
            .replace(/[\u0300-\u036f]/g, '')
            .toLowerCase()
            .trim();
    }

    function isPsychologistRole(role) {
        const normalizedRole = normalizeText(role);
        return normalizedRole.includes('psicolog')
            || normalizedRole.includes('pscolog')
            || normalizedRole.includes('psicoloc');
    }

    function escapeHtml(value) {
        return String(value ?? '')
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    function clamp(value, min, max) {
        return Math.min(Math.max(value, min), max);
    }

    function getCheckinDate(checkin) {
        const date = new Date(checkin.created_at);
        return Number.isNaN(date.getTime()) ? null : date;
    }

    function getStressValue(checkin) {
        const stress = Number(checkin.stress_level);
        return Number.isNaN(stress) ? null : clamp(stress, 0, 100);
    }

    function normalizeCheckins(checkins) {
        return checkins
            .map((checkin) => ({
                ...checkin,
                date: getCheckinDate(checkin),
                stress: getStressValue(checkin)
            }))
            .filter((checkin) => checkin.date && checkin.stress !== null)
            .sort((a, b) => a.date - b.date);
    }

    function getChartModeLabel(mode) {
        const labels = {
            month: 'media mensal',
            year: 'media anual',
            all: 'todos os check-ins'
        };

        return labels[mode] || labels.all;
    }

    function getGroupedStressCheckins(checkins, mode) {
        if (mode === 'all') {
            return checkins.map((checkin) => ({
                ...checkin,
                label: formatShortDate(checkin.date),
                sourceCount: 1
            }));
        }

        const groups = new Map();

        checkins.forEach((checkin) => {
            const year = checkin.date.getFullYear();
            const month = checkin.date.getMonth() + 1;
            const key = mode === 'month'
                ? `${year}-${String(month).padStart(2, '0')}`
                : String(year);
            const label = mode === 'month'
                ? `${String(month).padStart(2, '0')}/${year}`
                : String(year);
            const date = mode === 'month'
                ? new Date(year, month - 1, 1)
                : new Date(year, 0, 1);

            if (!groups.has(key)) {
                groups.set(key, {
                    date,
                    label,
                    stressTotal: 0,
                    sourceCount: 0
                });
            }

            const group = groups.get(key);
            group.stressTotal += checkin.stress;
            group.sourceCount += 1;
        });

        return Array.from(groups.values())
            .map((group) => ({
                date: group.date,
                label: group.label,
                stress: Math.round(group.stressTotal / group.sourceCount),
                sourceCount: group.sourceCount
            }))
            .sort((a, b) => a.date - b.date);
    }

    function getAverageStress(checkins) {
        if (checkins.length === 0) {
            return 0;
        }

        const total = checkins.reduce((sum, checkin) => sum + checkin.stress, 0);
        return Math.round(total / checkins.length);
    }

    function formatShortDate(date) {
        return new Intl.DateTimeFormat('pt-BR', {
            day: '2-digit',
            month: '2-digit'
        }).format(date);
    }

    function hideStressTooltip() {
        stressChartTooltip.hidden = true;
    }

    function positionStressTooltip(target, event = null) {
        const chartFrame = stressChartSvg.closest('.chart-frame');
        const frameRect = chartFrame.getBoundingClientRect();
        const tooltipRect = stressChartTooltip.getBoundingClientRect();
        const maxLeft = Math.max(8, frameRect.width - tooltipRect.width - 8);
        const maxTop = Math.max(8, frameRect.height - tooltipRect.height - 8);
        let left = 0;
        let top = 0;

        if (event && typeof event.clientX === 'number') {
            left = event.clientX - frameRect.left + 12;
            top = event.clientY - frameRect.top - tooltipRect.height - 12;

            if (top < 8) {
                top = event.clientY - frameRect.top + 14;
            }
        } else {
            const point = target.querySelector('.chart-point');
            const pointRect = point.getBoundingClientRect();

            left = pointRect.left + pointRect.width / 2 - frameRect.left - tooltipRect.width / 2;
            top = pointRect.top - frameRect.top - tooltipRect.height - 12;

            if (top < 8) {
                top = pointRect.bottom - frameRect.top + 12;
            }
        }

        stressChartTooltip.style.left = `${clamp(left, 8, maxLeft)}px`;
        stressChartTooltip.style.top = `${clamp(top, 8, maxTop)}px`;
    }

    function showStressTooltip(target, event = null) {
        stressChartTooltip.innerHTML = `
            <strong>${escapeHtml(target.dataset.tooltipTitle)}</strong>
            <span>${escapeHtml(target.dataset.tooltipValue)}</span>
            <small>${escapeHtml(target.dataset.tooltipSource)}</small>
        `;
        stressChartTooltip.hidden = false;
        stressChartTooltip.style.visibility = 'hidden';
        positionStressTooltip(target, event);
        stressChartTooltip.style.visibility = 'visible';
    }

    function bindStressChartTooltips() {
        stressChartSvg.querySelectorAll('.chart-point-group').forEach((point) => {
            point.addEventListener('mouseenter', (event) => showStressTooltip(point, event));
            point.addEventListener('mousemove', (event) => positionStressTooltip(point, event));
            point.addEventListener('mouseleave', hideStressTooltip);
            point.addEventListener('focus', () => showStressTooltip(point));
            point.addEventListener('blur', hideStressTooltip);
        });
    }

    function setIndividualUnavailable(message) {
        stressChartSvg.innerHTML = '';
        hideStressTooltip();
        stressChartSummary.textContent = message;
        stressChartEmpty.textContent = message;
        stressChartEmpty.hidden = false;
        aiTrendCard.className = 'trend-card';
        aiTrendCard.innerHTML = `<p>${escapeHtml(message)}</p>`;
        aiTrendOverride = null;
        moodDistribution.innerHTML = `<p class="bar-empty">${escapeHtml(message)}</p>`;
        recentCheckinsChart.innerHTML = `<p class="bar-empty">${escapeHtml(message)}</p>`;
    }

    function renderStressChart(checkins, sourceCheckins = checkins) {
        if (checkins.length === 0) {
            stressChartSvg.innerHTML = '';
            hideStressTooltip();
            stressChartSummary.textContent = 'Sem check-ins registrados.';
            stressChartEmpty.textContent = 'Nenhum check-in encontrado.';
            stressChartEmpty.hidden = false;
            return;
        }

        stressChartEmpty.hidden = true;
        hideStressTooltip();
        stressChartSvg.setAttribute(
            'aria-label',
            activeChartMode === 'all'
                ? 'Evolucao dos valores de stress por check-in'
                : `Evolucao da ${getChartModeLabel(activeChartMode)} de stress`
        );

        const width = 720;
        const height = 260;
        const paddingX = 52;
        const paddingY = 30;
        const chartWidth = width - paddingX * 2;
        const chartHeight = height - paddingY * 2;
        const baseY = height - paddingY;
        const points = checkins.map((checkin, index) => {
            const x = checkins.length === 1
                ? paddingX + chartWidth / 2
                : paddingX + (index / (checkins.length - 1)) * chartWidth;
            const y = paddingY + ((100 - checkin.stress) / 100) * chartHeight;

            return { x, y, checkin };
        });

        const linePath = points.map((point, index) => {
            const command = index === 0 ? 'M' : 'L';
            return `${command} ${point.x.toFixed(1)} ${point.y.toFixed(1)}`;
        }).join(' ');

        const areaPath = points.length > 1
            ? `${linePath} L ${points[points.length - 1].x.toFixed(1)} ${baseY} L ${points[0].x.toFixed(1)} ${baseY} Z`
            : '';

        const grid = [0, 25, 50, 75, 100].map((value) => {
            const y = paddingY + ((100 - value) / 100) * chartHeight;

            return `
                <line class="chart-grid-line" x1="${paddingX}" y1="${y}" x2="${width - paddingX}" y2="${y}"></line>
                <text class="chart-axis-label" x="12" y="${y + 4}">${value}</text>
            `;
        }).join('');

        const circles = points.map((point) => {
            const sourceText = point.checkin.sourceCount > 1
                ? `${point.checkin.sourceCount} check-ins`
                : '1 check-in';
            const valuePrefix = activeChartMode === 'all' ? 'Valor' : 'Média';
            const tooltipValue = `${valuePrefix}: ${point.checkin.stress}`;
            const ariaLabel = `${point.checkin.label}, ${valuePrefix.toLowerCase()} ${point.checkin.stress}, ${sourceText}`;

            return `
            <g
                class="chart-point-group"
                tabindex="0"
                aria-label="${escapeHtml(ariaLabel)}"
                data-tooltip-title="${escapeHtml(point.checkin.label)}"
                data-tooltip-value="${escapeHtml(tooltipValue)}"
                data-tooltip-source="${escapeHtml(sourceText)}"
            >
                <title>${escapeHtml(point.checkin.label)} | ${valuePrefix.toLowerCase()} ${point.checkin.stress} | ${sourceText}</title>
                <circle class="chart-point-hit" cx="${point.x}" cy="${point.y}" r="16"></circle>
                <circle class="chart-point" cx="${point.x}" cy="${point.y}" r="6"></circle>
            </g>
            `;
        }).join('');

        const dateLabels = points
            .filter((_, index) => activeChartMode !== 'all' || index === 0 || index === points.length - 1 || points.length <= 6)
            .map((point) => `
                <text class="chart-date-label" x="${point.x}" y="${height - 8}" text-anchor="middle">${escapeHtml(point.checkin.label)}</text>
            `).join('');

        stressChartSvg.innerHTML = `
            ${grid}
            ${areaPath ? `<path class="chart-area" d="${areaPath}"></path>` : ''}
            ${points.length > 1 ? `<path class="chart-line" d="${linePath}"></path>` : ''}
            ${dateLabels}
            ${circles}
        `;
        bindStressChartTooltips();

        if (activeChartMode === 'all') {
            stressChartSummary.textContent = `${checkins.length} check-ins registrados | media ${getAverageStress(checkins)}`;
            return;
        }

        const unitLabel = activeChartMode === 'month' ? 'meses' : 'anos';
        stressChartSummary.textContent = `${getChartModeLabel(activeChartMode)} | ${checkins.length} ${unitLabel} no grafico | ${sourceCheckins.length} check-ins considerados | media geral ${getAverageStress(sourceCheckins)}`;
    }

    function renderBarList(container, items, labelKey, valueKey, emptyMessage, valueFormatter = (value) => value) {
        if (!items || items.length === 0) {
            container.innerHTML = `<p class="bar-empty">${escapeHtml(emptyMessage)}</p>`;
            return;
        }

        const maxValue = Math.max(...items.map((item) => Number(item[valueKey]) || 0));

        container.innerHTML = items.map((item) => {
            const value = Number(item[valueKey]) || 0;
            const width = maxValue > 0 ? Math.max((value / maxValue) * 100, 8) : 8;

            return `
                <div class="bar-row">
                    <span class="bar-label">${escapeHtml(item[labelKey])}</span>
                    <span class="bar-track"><span class="bar-fill" style="--bar-width: ${width}%"></span></span>
                    <span class="bar-value">${escapeHtml(valueFormatter(value))}</span>
                </div>
            `;
        }).join('');
    }

    function renderAiTrend(checkins) {
        if (checkins.length === 0 && !aiTrendOverride) {
            aiTrendCard.className = 'trend-card';
            aiTrendCard.innerHTML = '<p class="bar-empty">Sem check-ins para gerar tendencia.</p>';
            return;
        }

        const latestCheckin = aiTrendOverride || checkins[checkins.length - 1];
        const insight = latestCheckin.ai_insights || 'Insight de IA ainda nao disponivel.';
        const normalizedInsight = normalizeText(insight);
        let trendClass = 'trend-card--stable';
        let trendLabel = 'Em estabilidade';

        if (normalizedInsight.includes('piora')) {
            trendClass = 'trend-card--worse';
            trendLabel = 'Em piora';
        } else if (normalizedInsight.includes('melhora')) {
            trendClass = 'trend-card--better';
            trendLabel = 'Em melhora';
        } else if (!normalizedInsight.includes('estabilidade')) {
            trendLabel = 'A definir';
        }

        aiTrendCard.className = `trend-card ${trendClass}`;
        aiTrendCard.innerHTML = `
            <strong>${escapeHtml(trendLabel)}</strong>
            <span class="trend-meta">${escapeHtml(trendMetaLabel)}: ${escapeHtml(latestCheckin.overall_mood || 'A definir')}</span>
            <p>${escapeHtml(insight)}</p>
        `;
    }

    function getMoodColor(index) {
        const colors = ['#761cee', '#147dac', '#44edf5', '#ef8f92', '#8a7a2c', '#b71c1c', '#4f46e5'];
        return colors[index % colors.length];
    }

    function getPiePoint(centerX, centerY, radius, angle) {
        const radians = (angle - 90) * Math.PI / 180;

        return {
            x: centerX + radius * Math.cos(radians),
            y: centerY + radius * Math.sin(radians)
        };
    }

    function getPieSlicePath(centerX, centerY, radius, startAngle, endAngle) {
        const start = getPiePoint(centerX, centerY, radius, startAngle);
        const end = getPiePoint(centerX, centerY, radius, endAngle);
        const largeArcFlag = endAngle - startAngle > 180 ? 1 : 0;

        return [
            `M ${centerX} ${centerY}`,
            `L ${start.x.toFixed(2)} ${start.y.toFixed(2)}`,
            `A ${radius} ${radius} 0 ${largeArcFlag} 1 ${end.x.toFixed(2)} ${end.y.toFixed(2)}`,
            'Z'
        ].join(' ');
    }

    function renderMoodDistribution(checkins) {
        if (checkins.length === 0) {
            moodDistribution.innerHTML = '<p class="bar-empty">Sem dados de humor neste periodo.</p>';
            return;
        }

        const counts = checkins.reduce((accumulator, checkin) => {
            const mood = checkin.overall_mood || 'A definir';
            accumulator[mood] = (accumulator[mood] || 0) + 1;
            return accumulator;
        }, {});

        const items = Object.entries(counts)
            .map(([mood, count]) => ({ mood, count }))
            .sort((a, b) => b.count - a.count);

        const total = items.reduce((sum, item) => sum + item.count, 0);
        let currentAngle = 0;

        const slices = items.map((item, index) => {
            const sliceAngle = (item.count / total) * 360;
            const startAngle = currentAngle;
            const endAngle = currentAngle + sliceAngle;
            const color = getMoodColor(index);
            currentAngle = endAngle;

            if (items.length === 1) {
                return `<circle class="pie-slice" cx="110" cy="110" r="82" style="--slice-color: ${color}"></circle>`;
            }

            return `
                <path
                    class="pie-slice"
                    d="${getPieSlicePath(110, 110, 82, startAngle, endAngle)}"
                    style="--slice-color: ${color}"
                ></path>
            `;
        }).join('');

        const legend = items.map((item, index) => {
            const percentage = Math.round((item.count / total) * 100);

            return `
                <div class="pie-legend-item">
                    <span class="pie-swatch" style="--slice-color: ${getMoodColor(index)}"></span>
                    <span class="pie-label">${escapeHtml(item.mood)}</span>
                    <strong class="pie-value">${item.count} (${percentage}%)</strong>
                </div>
            `;
        }).join('');

        moodDistribution.innerHTML = `
            <div class="pie-chart-layout">
                <svg class="pie-chart" viewBox="0 0 220 220" role="img" aria-label="Distribuicao de humor no periodo">
                    <title>Distribuicao de humor no periodo</title>
                    ${slices}
                </svg>
                <div class="pie-legend">${legend}</div>
            </div>
        `;
    }

    function renderRecentCheckins(checkins) {
        const recentCheckins = checkins.slice(-8);

        if (recentCheckins.length === 0) {
            recentCheckinsChart.innerHTML = '<p class="bar-empty">Sem check-ins recentes neste periodo.</p>';
            return;
        }

        recentCheckinsChart.innerHTML = recentCheckins.map((checkin) => {
            const height = Math.max(checkin.stress, 8);

            return `
                <div class="recent-bar">
                    <div class="recent-bar-track">
                        <div class="recent-bar-fill" style="--bar-height: ${height}%"></div>
                    </div>
                    <strong>${checkin.stress}</strong>
                    <span>${formatShortDate(checkin.date)}</span>
                </div>
            `;
        }).join('');
    }

    function renderIndividualCharts() {
        const checkins = normalizeCheckins(individualCheckins);
        const stressChartCheckins = getGroupedStressCheckins(checkins, activeChartMode);

        renderStressChart(stressChartCheckins, checkins);
        renderAiTrend(checkins);
        renderMoodDistribution(checkins);
        renderRecentCheckins(checkins);
    }

    function setupPeriodFilters() {
        periodButtons.forEach((button) => {
            button.addEventListener('click', () => {
                activeChartMode = button.dataset.period;

                periodButtons.forEach((item) => {
                    const active = item === button;
                    item.classList.toggle('active', active);
                    item.setAttribute('aria-pressed', active ? 'true' : 'false');
                });

                renderIndividualCharts();
            });
        });
    }

    function getUserLabel(userId) {
        const user = overviewUsers.find((item) => Number(item.id) === Number(userId));

        if (!user) {
            return `Pessoa #${userId}`;
        }

        return `${user.name} (#${user.id})`;
    }

    async function loadIndividualDashboard(userId, label = null) {
        individualSectionTitle.textContent = label || getUserLabel(userId);
        individualSectionDescription.textContent = Number(userId) === currentUser.id
            ? 'Dados da pessoa logada.'
            : 'Dados individuais carregados pela busca do psicologo.';
        aiTrendOverride = null;
        trendMetaLabel = 'Nivel atual';

        try {
            const checkins = await fetchJson(`/forms/history/${userId}`);

            if (!Array.isArray(checkins)) {
                individualCheckins = [];
                setIndividualUnavailable('Nao foi possivel carregar esta dashboard.');
                return;
            }

            individualCheckins = checkins;
            renderIndividualCharts();
        } catch (error) {
            console.error('Erro ao carregar dashboard individual:', error);
            individualCheckins = [];
            setIndividualUnavailable(error.message || 'Nao foi possivel carregar esta dashboard.');
        }
    }

    async function loadTeamDashboard(teamId, teamName) {
        individualSectionTitle.textContent = `Time: ${teamName}`;
        individualSectionDescription.textContent = 'Dados agregados do time selecionado.';
        trendMetaLabel = 'Media atual do time';

        try {
            const data = await fetchJson(`/analytics/team-history/${teamId}`);

            if (!Array.isArray(data.checkins)) {
                individualCheckins = [];
                aiTrendOverride = null;
                setIndividualUnavailable('Nao foi possivel carregar este time.');
                return;
            }

            individualSectionDescription.textContent = `${data.users_count} pessoa(s) | ${data.checkins_count} check-ins no time.`;
            individualCheckins = data.checkins;
            aiTrendOverride = data.trend || null;
            renderIndividualCharts();
        } catch (error) {
            console.error('Erro ao carregar dashboard do time:', error);
            individualCheckins = [];
            aiTrendOverride = null;
            trendMetaLabel = 'Nivel atual';
            setIndividualUnavailable(error.message || 'Nao foi possivel carregar este time.');
        }
    }

    function renderPeopleTable(users) {
        if (!users || users.length === 0) {
            peopleTable.innerHTML = '<p class="bar-empty">Nenhuma pessoa encontrada.</p>';
            return;
        }

        peopleTable.innerHTML = users.map((user) => `
            <div class="people-row">
                <span>#${user.id}</span>
                <strong>${escapeHtml(user.name)}</strong>
                <span>${escapeHtml(user.team || 'Sem time')}</span>
                <span>${user.checkins}</span>
                <span>${escapeHtml(user.last_mood || '-')}</span>
            </div>
        `).join('');
    }

    function renderTeamOptions(groups) {
        if (!targetTeam) {
            return;
        }

        const previousValue = targetTeam.value;
        const options = (groups || [])
            .filter((group) => group.team_id && group.group)
            .map((group) => `
                <option value="${escapeHtml(group.team_id)}" data-team-name="${escapeHtml(group.group)}">
                    ${escapeHtml(group.group)} (${group.users} pessoa(s), ${group.checkins} check-ins)
                </option>
            `)
            .join('');

        targetTeam.innerHTML = `<option value="">Selecione</option>${options}`;

        if (previousValue) {
            targetTeam.value = previousValue;
        }
    }

    function renderCompanyOverview(data) {
        overviewUsers = data.users || [];
        companyUsersTotal.textContent = data.total_users ?? '-';
        companyCheckinsTotal.textContent = data.total_checkins ?? '-';
        companyAverageStress.textContent = data.average_stress ?? '-';

        renderBarList(
            companyGroupChart,
            data.groups || [],
            'group',
            'average_stress',
            'Sem dados por grupo.',
            (value) => value.toFixed(0)
        );
        renderBarList(companyMoodChart, data.mood_distribution || [], 'mood', 'count', 'Sem dados de humor.');
        renderPeopleTable(overviewUsers);
        renderTeamOptions(data.groups || []);
    }

    async function loadCompanyOverview() {
        try {
            const data = await fetchJson('/analytics/company-overview');
            renderCompanyOverview(data);
        } catch (error) {
            console.error('Erro ao carregar visao geral:', error);
            companyGroupChart.innerHTML = `<p class="bar-empty">${escapeHtml(error.message)}</p>`;
            companyMoodChart.innerHTML = '<p class="bar-empty">Nao foi possivel carregar os dados gerais.</p>';
            peopleTable.innerHTML = '<p class="bar-empty">Nao foi possivel carregar a lista de pessoas.</p>';
        }
    }

    async function loadCurrentUser() {
        try {
            currentUser = await fetchJson('/usuarios/me');
            return currentUser;
        } catch (error) {
            console.error('Erro ao carregar usuario:', error);
            setIndividualUnavailable('Faca login para consultar os dashboards.');
            return null;
        }
    }

    function setupSearch() {
        userSearchForm.addEventListener('submit', (event) => {
            event.preventDefault();

            const userId = Number(targetUserId.value);

            if (!userId) {
                return;
            }

            loadIndividualDashboard(userId);
        });

        teamSearchForm.addEventListener('submit', (event) => {
            event.preventDefault();

            const teamId = targetTeam.value;
            const selectedOption = targetTeam.options[targetTeam.selectedIndex];
            const teamName = selectedOption?.dataset.teamName || selectedOption?.textContent || 'Time';

            if (!teamId) {
                return;
            }

            loadTeamDashboard(teamId, teamName);
        });
    }

    async function init() {
        setupPeriodFilters();
        setupSearch();

        const user = await loadCurrentUser();

        if (!user) {
            return;
        }

        const psychologist = isPsychologistRole(user.role);

        dashboardTitle.textContent = psychologist ? 'Dashboards da empresa' : 'Sua evolução';
        dashboardSubtitle.textContent = psychologist
            ? 'Acompanhe indicadores gerais e consulte dashboards individuais por ID.'
            : 'Acompanhe seus check-ins e identifique mudanças ao longo do tempo.';

        if (psychologist) {
            psychologistArea.hidden = false;
            await loadCompanyOverview();
        }

        await loadIndividualDashboard(user.id, 'Minha dashboard');
    }

    init();
});
