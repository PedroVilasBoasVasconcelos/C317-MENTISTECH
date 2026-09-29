# Testes E2E

Os testes usam Playwright com Chromium e iniciam o FastAPI automaticamente em
`http://127.0.0.1:8765`.

## Instalação

```powershell
venv\Scripts\python.exe -m pip install -r requirements-test.txt
venv\Scripts\python.exe -m playwright install chromium
```

## Execução

```powershell
venv\Scripts\python.exe -m pytest -q
```

Para executar apenas um fluxo:

```powershell
venv\Scripts\python.exe -m pytest -q tests/e2e/test_questions.py
```

As páginas e arquivos estáticos são servidos pela aplicação real. As APIs são
interceptadas nos cenários que precisam de dados controlados, evitando alterações
no banco local e tornando a suíte determinística.
