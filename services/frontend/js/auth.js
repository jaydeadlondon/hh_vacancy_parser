// ─── Табы ─────────────────────────────────────────────────────────────────────

function switchTab(tab) {
    const loginForm    = document.getElementById('form-login')
    const registerForm = document.getElementById('form-register')
    const loginTab     = document.getElementById('tab-login')
    const registerTab  = document.getElementById('tab-register')

    if (tab === 'login') {
        loginForm.classList.remove('hidden')
        registerForm.classList.add('hidden')
        loginTab.classList.add('bg-accent-500', 'text-white')
        loginTab.classList.remove('text-gray-400')
        registerTab.classList.remove('bg-accent-500', 'text-white')
        registerTab.classList.add('text-gray-400')
    } else {
        registerForm.classList.remove('hidden')
        loginForm.classList.add('hidden')
        registerTab.classList.add('bg-accent-500', 'text-white')
        registerTab.classList.remove('text-gray-400')
        loginTab.classList.remove('bg-accent-500', 'text-white')
        loginTab.classList.add('text-gray-400')
    }
}

// ─── Показать/скрыть пароль ───────────────────────────────────────────────────

function togglePassword(inputId) {
    const input = document.getElementById(inputId)
    input.type = input.type === 'password' ? 'text' : 'password'
}

// ─── Авторизация ──────────────────────────────────────────────────────────────

async function handleLogin() {
    const username = document.getElementById('login-username').value.trim()
    const password = document.getElementById('login-password').value
    const errorEl  = document.getElementById('login-error')
    const spinner  = document.getElementById('login-spinner')
    const btnText  = document.getElementById('login-btn-text')

    errorEl.classList.add('hidden')

    if (!username || !password) {
        errorEl.textContent = 'Заполни все поля'
        errorEl.classList.remove('hidden')
        return
    }

    // Показываем спиннер
    spinner.classList.remove('hidden')
    btnText.textContent = 'Входим...'

    const result = await api.login(username, password)

    spinner.classList.add('hidden')
    btnText.textContent = 'Войти'

    if (result.status === 200) {
        localStorage.setItem('jwt_token', result.data.access_token)
        window.location.href = 'dashboard.html'
    } else {
        const msg = result.data?.detail || 'Неверный логин или пароль'
        errorEl.textContent = msg
        errorEl.classList.remove('hidden')
    }
}

// ─── Регистрация ──────────────────────────────────────────────────────────────

async function handleRegister() {
    const username  = document.getElementById('reg-username').value.trim()
    const email     = document.getElementById('reg-email').value.trim()
    const password  = document.getElementById('reg-password').value
    const errorEl   = document.getElementById('register-error')
    const successEl = document.getElementById('register-success')
    const spinner   = document.getElementById('register-spinner')
    const btnText   = document.getElementById('register-btn-text')

    errorEl.classList.add('hidden')
    successEl.classList.add('hidden')

    if (!username || !email || !password) {
        errorEl.textContent = 'Заполни все поля'
        errorEl.classList.remove('hidden')
        return
    }
    if (password.length < 8) {
        errorEl.textContent = 'Пароль минимум 8 символов'
        errorEl.classList.remove('hidden')
        return
    }

    spinner.classList.remove('hidden')
    btnText.textContent = 'Создаём...'

    const result = await api.register(username, email, password)

    spinner.classList.add('hidden')
    btnText.textContent = 'Создать аккаунт'

    if (result.status === 201) {
        // Сразу логиним
        const loginResult = await api.login(username, password)
        if (loginResult.status === 200) {
            localStorage.setItem('jwt_token', loginResult.data.access_token)
            window.location.href = 'dashboard.html'
        } else {
            successEl.textContent = '✅ Аккаунт создан! Войди в систему.'
            successEl.classList.remove('hidden')
            switchTab('login')
        }
    } else {
        const msg = result.data?.detail || 'Ошибка регистрации'
        errorEl.textContent = msg
        errorEl.classList.remove('hidden')
    }
}

// ─── Enter для форм ───────────────────────────────────────────────────────────

document.addEventListener('keydown', (e) => {
    if (e.key !== 'Enter') return
    const loginForm = document.getElementById('form-login')
    if (!loginForm.classList.contains('hidden')) {
        handleLogin()
    } else {
        handleRegister()
    }
})

// ─── Редирект если уже залогинен ──────────────────────────────────────────────

if (localStorage.getItem('jwt_token')) {
    window.location.href = 'dashboard.html'
}