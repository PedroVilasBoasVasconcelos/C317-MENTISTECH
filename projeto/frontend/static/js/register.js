document.addEventListener('DOMContentLoaded', () => {
    const switchButtons = document.querySelectorAll('.switch-btn');
    const registerPanel = document.getElementById('register-panel');
    const loginPanel = document.getElementById('login-panel');
    const registerForm = document.getElementById('register-form');
    const loginForm = document.getElementById('login-form');
    const registerMessage = document.getElementById('register-message');
    const loginMessage = document.getElementById('login-message');

    const messages = {
        'Email already registered': 'Este email ja esta cadastrado.',
        'Invalid credentials': 'Email ou senha invalidos.',
        'password and confirm_password must match': 'As senhas precisam ser iguais.'
    };

    function setMode(mode) {
        switchButtons.forEach((btn) => {
            const active = btn.dataset.mode === mode;
            btn.classList.toggle('active', active);
            btn.setAttribute('aria-selected', active ? 'true' : 'false');
        });

        if (mode === 'login') {
            loginPanel.hidden = false;
            registerPanel.hidden = true;
        } else {
            loginPanel.hidden = true;
            registerPanel.hidden = false;
        }
    }

    function setMessage(element, text, type = 'error') {
        element.textContent = text;
        element.dataset.type = type;
    }

    function getErrorMessage(error) {
        if (!error) {
            return 'Nao foi possivel concluir a operacao.';
        }

        if (typeof error.detail === 'string') {
            return messages[error.detail] || error.detail;
        }

        if (Array.isArray(error.detail) && error.detail.length > 0) {
            const firstError = error.detail[0];
            const message = firstError.msg || firstError.message;
            return messages[message] || message || 'Verifique os dados preenchidos.';
        }

        return 'Verifique os dados preenchidos.';
    }

    async function requestJson(url, data) {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        const result = await response.json().catch(() => null);

        if (!response.ok) {
            throw result;
        }

        return result;
    }

    function saveSession(tokenData, userEmail) {
        localStorage.setItem('access_token', tokenData.access_token);
        localStorage.setItem('token_type', tokenData.token_type || 'bearer');
        localStorage.setItem('user_email', userEmail);
    }

    async function login(email, password) {
        const tokenData = await requestJson('/auth/login', {
            email,
            password
        });
        saveSession(tokenData, email);
        window.location.href = '/initial';
    }

    switchButtons.forEach((button) => {
        button.addEventListener('click', () => {
            setMode(button.dataset.mode);
        });
    });

    registerForm.addEventListener('submit', async (event) => {
        event.preventDefault();

        const submitButton = registerForm.querySelector('button[type="submit"]');
        const name = document.getElementById('nome').value.trim();
        const role = document.getElementById('cargo').value.trim();
        const team = document.getElementById('time').value.trim();
        const email = document.getElementById('cadastro-email').value.trim();
        const password = document.getElementById('cadastro-senha').value;
        const confirmPassword = document.getElementById('confirmar-senha').value;

        if (password !== confirmPassword) {
            setMessage(registerMessage, 'As senhas precisam ser iguais.');
            return;
        }

        submitButton.disabled = true;
        setMessage(registerMessage, 'Criando sua conta...', 'info');

        try {
            await requestJson('/auth/register', {
                name,
                email,
                password,
                confirm_password: confirmPassword,
                role,
                team
            });
            setMessage(registerMessage, 'Conta criada. Entrando...', 'success');
            await login(email, password);
        } catch (error) {
            setMessage(registerMessage, getErrorMessage(error));
            submitButton.disabled = false;
        }
    });

    loginForm.addEventListener('submit', async (event) => {
        event.preventDefault();

        const submitButton = loginForm.querySelector('button[type="submit"]');
        const email = document.getElementById('login-email').value.trim();
        const password = document.getElementById('login-senha').value;

        submitButton.disabled = true;
        setMessage(loginMessage, 'Entrando...', 'info');

        try {
            await login(email, password);
        } catch (error) {
            setMessage(loginMessage, getErrorMessage(error));
            submitButton.disabled = false;
        }
    });
});
