import re

from playwright.sync_api import expect


def test_home_exibe_conteudo_e_navega_pelas_secoes(page):
    page.goto("/")

    expect(page).to_have_title("Home")
    expect(page.locator("#hero h1")).to_have_text("MentisTech")
    expect(page.locator("#sobre")).to_be_visible()
    expect(page.locator("#como-funciona .card")).to_have_count(3)
    expect(page.locator("#beneficios .card")).to_have_count(2)

    page.get_by_role("link", name="Como funciona").click()
    expect(page).to_have_url(re.compile(r"/#como-funciona$"))

    page.get_by_role("link", name="Começar acompanhamento").click()
    expect(page.locator("#entrar-home")).to_be_in_viewport()


def test_botao_entrar_abre_autenticacao(page):
    page.goto("/")

    page.locator("#entrar-home").click()

    expect(page).to_have_url("/autheticate")
    expect(page.locator("#auth-card")).to_be_visible()
