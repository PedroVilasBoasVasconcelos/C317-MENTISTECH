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
        "id": 2,
        "created_at": "2026-05-15T12:00:00",
        "overall_mood": "Bem",
        "stress_level": 72,
        "ai_insights": "Tendencia de melhora detectada pela IA (confianca 82%).",
        "answers": [],
    },
    {
        "id": 1,
        "created_at": "2026-04-15T12:00:00",
        "overall_mood": "Regular",
        "stress_level": 60,
        "ai_insights": "Em estabilidade.",
        "answers": [],
    },
]


def mock_panel_apis(page):
    page.route("**/usuarios/me", lambda route: route.fulfill(json=USER))
    page.route("**/forms/history/7", lambda route: route.fulfill(json=CHECKINS))
    page.route(
        "**/forms/next-checkin/7",
        lambda route: route.fulfill(
            json={
                "available": False,
                "next_checkin": "2026-06-15T12:00:00",
                "days_remaining": 9,
            }
        ),
    )


def test_painel_carrega_resumo_do_usuario(authenticated_page):
    page = authenticated_page
    mock_panel_apis(page)

    page.goto("/initial")

    expect(page.locator("#primeiro-nome")).to_have_text("Ana")
    expect(page.locator("#nivel-atual-valor")).to_have_text("Bem")
    expect(page.locator("#total-checkins-valor")).to_have_text("2")
    expect(page.locator("#tendencia-valor")).to_have_text("Em melhora")
    expect(page.locator("#proximo-checkin-valor")).to_have_text("Em 9 dias")


def test_painel_envia_mensagem_de_contato(authenticated_page):
    page = authenticated_page
    mock_panel_apis(page)
    sent_payload = {}

    def handle_email(route):
        sent_payload.update(route.request.post_data_json)
        route.fulfill(json={"message": "Email enviado"})

    page.route("**/email/send", handle_email)
    page.goto("/initial")
    page.locator("#duvida").fill("Preciso de apoio com meu resultado.")
    page.get_by_role("button", name="Enviar mensagem").click()

    expect(page.locator("#contato-feedback")).to_have_text("Mensagem enviada com sucesso!")
    assert sent_payload["user_id"] == 7
    assert sent_payload["message"] == "Preciso de apoio com meu resultado."


def test_logout_limpa_sessao(authenticated_page):
    page = authenticated_page
    mock_panel_apis(page)
    page.goto("/initial")

    page.locator("#dashboard-menu-toggle").click()
    page.get_by_role("menuitem", name="Sair").click()

    expect(page).to_have_url("/autheticate")
    assert page.evaluate("localStorage.getItem('access_token')") is None
