// ./assets/js/admin-login.js

// ⚠️ ATENÇÃO: Defina a URL base da sua API
const API_BASE_URL = 'http://127.0.0.1:5000/api'; 
// Substitua por 'https://[SEU-DOMINIO-VERCEL]/api' após o deploy.

document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('login-form');
    const loginBtn = document.getElementById('login-btn');
    const loginMessage = document.getElementById('login-message');

    // Verifica se o usuário já tem um token e redireciona (Melhoria de UX)
    if (localStorage.getItem('jwt_token')) {
        // Redireciona para o painel principal (que será o admin-panel.html)
        window.location.href = './admin-panel.html'; 
    }

    loginForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        
        loginBtn.disabled = true;
        loginBtn.textContent = 'Acessando...';
        loginMessage.style.display = 'none';

        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;

        const loginData = {
            username: username,
            password: password
        };
        
        try {
            const response = await fetch(`${API_BASE_URL}/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(loginData)
            });

            const result = await response.json();

            if (response.ok && result.token) {
                // 1. Login bem-sucedido
                localStorage.setItem('jwt_token', result.token);
                localStorage.setItem('admin_username', username);
                
                // 2. Redireciona para o painel principal
                loginMessage.className = 'alert success';
                loginMessage.textContent = 'Login realizado com sucesso! Redirecionando...';
                loginMessage.style.display = 'block';
                
                setTimeout(() => {
                    window.location.href = './admin-panel.html';
                }, 1000);

            } else {
                // 3. Falha no login (ex: 401 Unauthorized)
                loginMessage.className = 'alert error';
                loginMessage.textContent = result.erro || 'Usuário ou senha incorretos.';
                loginMessage.style.display = 'block';
                loginBtn.disabled = false;
                loginBtn.innerHTML = '<i class="fa-solid fa-right-to-bracket"></i> Acessar';
            }

        } catch (error) {
            console.error('Erro de rede/conexão:', error);
            loginMessage.className = 'alert error';
            loginMessage.textContent = 'Erro ao conectar com o servidor. Verifique sua conexão.';
            loginMessage.style.display = 'block';
            loginBtn.disabled = false;
            loginBtn.innerHTML = '<i class="fa-solid fa-right-to-bracket"></i> Acessar';
        }
    });
});