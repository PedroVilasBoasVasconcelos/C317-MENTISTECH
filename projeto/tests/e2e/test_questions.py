from playwright.sync_api import expect


QUESTIONS = [
    {"id": 1, "question": "Como está sua carga de trabalho?", "type": "scale"},
    {"id": 2, "question": "Você recebeu apoio da equipe?", "type": "scale"},
    {"id": 3, "question": "Como está sua rotina pessoal?", "type": "scale"},
]


def test_questionario_valida_resposta_e_envia_fluxo_completo(authenticated_page):
    page = authenticated_page
    submitted = {}
    page.route("**/forms/questions", lambda route: route.fulfill(json=QUESTIONS))
    page.route(
        "**/usuarios/me",
        lambda route: route.fulfill(
            json={
                "id": 7,
                "name": "Ana Silva",
                "email": "ana@example.com",
                "role": "Desenvolvedora",
                "team": "Produto",
            }
        ),
    )

    def handle_submit(route):
        submitted.update(route.request.post_data_json)
        route.fulfill(status=201, json={"message": "Formulario enviado com sucesso"})

    page.route("**/forms/submit", handle_submit)
    page.goto("/questions")

    expect(page.locator("#passo-atual")).to_have_text("Pergunta 1 de 3")
    page.locator("#botao-proximo").click()
    expect(page.locator("#modal-titulo")).to_have_text("Selecione uma resposta")
    page.locator("#modal-confirmar").click()

    for index in range(3):
        page.locator("#opcoes .opcao-card").nth(2).click()
        page.locator("#botao-proximo").click()

    expect(page.locator("#modal-titulo")).to_have_text(
        "Deseja salvar e enviar suas respostas?"
    )
    page.locator("#modal-confirmar").click()
    expect(page.locator("#modal-titulo")).to_have_text("Respostas enviadas com sucesso")

    assert submitted["user_id"] == 7
    assert submitted["answers"] == [
        {"question_id": 1, "value": 3},
        {"question_id": 2, "value": 3},
        {"question_id": 3, "value": 3},
    ]

    page.locator("#modal-confirmar").click()
    expect(page).to_have_url("/initial")


def test_questionario_permite_voltar_para_pergunta_anterior(authenticated_page):
    page = authenticated_page
    page.route("**/forms/questions", lambda route: route.fulfill(json=QUESTIONS))
    page.route("**/usuarios/me", lambda route: route.fulfill(status=401, json={}))
    page.goto("/questions")

    page.locator("#opcoes .opcao-card").first.click()
    page.locator("#botao-proximo").click()
    expect(page.locator("#passo-atual")).to_have_text("Pergunta 2 de 3")

    page.locator("#botao-voltar").click()
    expect(page.locator("#passo-atual")).to_have_text("Pergunta 1 de 3")
    expect(page.locator('#opcoes input[name="resposta"]').first).to_be_checked()
