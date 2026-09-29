from playwright.sync_api import expect


def test_alterna_entre_cadastro_e_login(page):
    page.goto("/autheticate")

    expect(page.locator("#register-panel")).to_be_visible()
    expect(page.locator("#login-panel")).to_be_hidden()

    page.get_by_role("button", name="Entrar").click()

    expect(page.locator("#register-panel")).to_be_hidden()
    expect(page.locator("#login-panel")).to_be_visible()


def test_cadastro_valida_confirmacao_de_senha_sem_chamar_api(page):
    requests = []
    page.on("request", lambda request: requests.append(request.url))
    page.goto("/autheticate")

    page.locator("#nome").fill("Ana Teste")
    page.locator("#cargo").fill("Desenvolvedora")
    page.locator("#time").fill("Produto")
    page.locator("#cadastro-email").fill("ana@example.com")
    page.locator("#cadastro-senha").fill("segredo")
    page.locator("#confirmar-senha").fill("diferente")
    page.get_by_role("button", name="Cadastrar").click()

    expect(page.locator("#register-message")).to_have_text("As senhas precisam ser iguais.")
    assert not any("/auth/register" in url for url in requests)


def test_cadastro_cria_sessao_e_abre_painel(page):
    payloads = {}

    def handle_register(route):
        payloads["register"] = route.request.post_data_json
        route.fulfill(
            status=201,
            json={
                "id": 42,
                "name": "Ana Teste",
                "email": "ana@example.com",
                "role": "Desenvolvedora",
                "team": "Produto",
            },
        )

    def handle_login(route):
        payloads["login"] = route.request.post_data_json
        route.fulfill(
            json={"access_token": "token-cadastro", "token_type": "bearer", "expires_in": 3600}
        )

    page.route("**/auth/register", handle_register)
    page.route("**/auth/login", handle_login)
    page.goto("/autheticate")

    page.locator("#nome").fill("Ana Teste")
    page.locator("#cargo").fill("Desenvolvedora")
    page.locator("#time").fill("Produto")
    page.locator("#cadastro-email").fill("ana@example.com")
    page.locator("#cadastro-senha").fill("segredo")
    page.locator("#confirmar-senha").fill("segredo")
    page.get_by_role("button", name="Cadastrar").click()

    expect(page).to_have_url("/initial")
    assert payloads["register"]["team"] == "Produto"
    assert payloads["login"] == {"email": "ana@example.com", "password": "segredo"}
    assert page.evaluate("localStorage.getItem('access_token')") == "token-cadastro"


def test_login_invalido_exibe_mensagem_traduzida(page):
    page.route(
        "**/auth/login",
        lambda route: route.fulfill(status=401, json={"detail": "Invalid credentials"}),
    )
    page.goto("/autheticate")
    page.get_by_role("button", name="Entrar").click()
    page.locator("#login-email").fill("ana@example.com")
    page.locator("#login-senha").fill("errada")
    page.locator("#login-form").get_by_role("button", name="Entrar").click()

    expect(page.locator("#login-message")).to_have_text("Email ou senha invalidos.")
    expect(page.locator("#login-form button[type=submit]")).to_be_enabled()
