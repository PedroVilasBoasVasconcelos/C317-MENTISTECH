from playwright.sync_api import expect


USER = {
    "id": 7,
    "name": "Ana Silva",
    "email": "ana@example.com",
    "role": "Desenvolvedora",
    "team": "Produto",
}

CHECKINS = [
    {
        "id": 1,
        "created_at": "2026-04-10T12:00:00",
        "overall_mood": "Regular",
        "stress_level": 55,
        "ai_insights": "Tendencia de estabilidade detectada pela IA.",
        "answers": [],
    },
    {
        "id": 2,
        "created_at": "2026-05-10T12:00:00",
        "overall_mood": "Bem",
        "stress_level": 70,
        "ai_insights": "Tendencia de melhora detectada pela IA.",
        "answers": [],
    },
]


def test_dashboard_individual_renderiza_graficos_e_filtros(authenticated_page):
    page = authenticated_page
    page.route("**/usuarios/me", lambda route: route.fulfill(json=USER))
    page.route("**/forms/history/7", lambda route: route.fulfill(json=CHECKINS))

    page.goto("/dashboards")

    expect(page.locator("#dashboard-title")).to_have_text("Sua evolução")
    expect(page.locator("#individual-section-title")).to_have_text("Minha dashboard")
    expect(page.locator("#stress-chart-svg .chart-point-group")).to_have_count(2)
    expect(page.locator("#mood-distribution .pie-legend-item")).to_have_count(2)
    expect(page.locator("#ai-trend-card")).to_contain_text("Em melhora")

    page.locator('[data-period="month"]').click()
    expect(page.locator('[data-period="month"]')).to_have_attribute("aria-pressed", "true")
    expect(page.locator("#stress-chart-summary")).to_contain_text("media mensal")


def test_dashboard_de_psicologo_exibe_visao_geral_e_busca_time(authenticated_page):
    page = authenticated_page
    psychologist = {**USER, "role": "Psicóloga"}
    overview = {
        "total_users": 3,
        "total_checkins": 5,
        "average_stress": 67,
        "mood_distribution": [{"mood": "Bem", "count": 3}],
        "groups": [
            {
                "team_id": 9,
                "group": "Produto",
                "users": 2,
                "checkins": 4,
                "average_stress": 70,
            }
        ],
        "users": [
            {
                "id": 7,
                "name": "Ana Silva",
                "team": "Produto",
                "checkins": 2,
                "last_mood": "Bem",
            }
        ],
    }
    team_history = {
        "team_id": 9,
        "team": "Produto",
        "users_count": 2,
        "checkins_count": 2,
        "trend": {
            "overall_mood": "Bem",
            "stress_level": 70,
            "ai_insights": "Tendencia de melhora do time detectada pela IA.",
        },
        "checkins": CHECKINS,
    }

    page.route("**/usuarios/me", lambda route: route.fulfill(json=psychologist))
    page.route("**/analytics/company-overview", lambda route: route.fulfill(json=overview))
    page.route("**/forms/history/7", lambda route: route.fulfill(json=CHECKINS))
    page.route("**/analytics/team-history/9", lambda route: route.fulfill(json=team_history))

    page.goto("/dashboards")

    expect(page.locator("#psychologist-area")).to_be_visible()
    expect(page.locator("#company-users-total")).to_have_text("3")
    expect(page.locator("#company-checkins-total")).to_have_text("5")
    expect(page.locator("#target-team option")).to_have_count(2)

    page.locator("#target-team").select_option("9")
    page.get_by_role("button", name="Buscar time").click()

    expect(page.locator("#individual-section-title")).to_have_text("Time: Produto")
    expect(page.locator("#individual-section-description")).to_contain_text("2 pessoa(s)")
