// ─── Конфигурация ─────────────────────────────────────────────────────────────
const API_BASE = 'http://localhost:8000'

// ─── HTTP клиент ──────────────────────────────────────────────────────────────
const api = {

    _getHeaders() {
        const token = localStorage.getItem('jwt_token')
        const headers = { 'Content-Type': 'application/json' }
        if (token) headers['Authorization'] = `Bearer ${token}`
        return headers
    },

    async _request(method, path, body = null) {
        try {
            const options = {
                method,
                headers: this._getHeaders(),
            }
            if (body) options.body = JSON.stringify(body)

            const response = await fetch(`${API_BASE}${path}`, options)
            const data = response.status !== 204 ? await response.json() : {}

            return { status: response.status, data }
        } catch (error) {
            console.error('API Error:', error)
            return { status: 0, data: { detail: 'Ошибка соединения с сервером' } }
        }
    },

    // ─── Auth ──────────────────────────────────────────────────────────────────
    login: (username, password) =>
        api._request('POST', '/api/v1/auth/login', { username, password }),

    register: (username, email, password) =>
        api._request('POST', '/api/v1/auth/register', { username, email, password }),

    getMe: () =>
        api._request('GET', '/api/v1/auth/me'),

    linkTelegram: (telegram_chat_id, telegram_username) =>
        api._request('PATCH', '/api/v1/users/me/telegram', { telegram_chat_id, telegram_username }),

    // ─── Filters ──────────────────────────────────────────────────────────────
    getFilters: () =>
        api._request('GET', '/api/v1/filters'),

    createFilter: (data) =>
        api._request('POST', '/api/v1/filters', data),

    deleteFilter: (id) =>
        api._request('DELETE', `/api/v1/filters/${id}`),

    // ─── Vacancies ────────────────────────────────────────────────────────────
    getVacancies: (params = {}) => {
        const query = new URLSearchParams()
        if (params.limit)     query.set('limit', params.limit)
        if (params.min_score) query.set('min_score', params.min_score)
        if (params.level)     query.set('level', params.level)
        if (params.q)         query.set('q', params.q)
        return api._request('GET', `/api/v1/vacancies/list?${query}`)
    },

    getTopVacancies: (limit = 10) =>
        api._request('GET', `/api/v1/vacancies/top?limit=${limit}`),
}

// ─── Утилиты ──────────────────────────────────────────────────────────────────

function showToast(message, type = 'success') {
    const toast = document.createElement('div')
    toast.className = `toast toast-${type}`
    toast.textContent = message
    document.body.appendChild(toast)
    setTimeout(() => toast.remove(), 3500)
}

function logout() {
    localStorage.removeItem('jwt_token')
    localStorage.removeItem('user')
    window.location.href = 'index.html'
}

function formatSalary(from, to, currency = 'RUR') {
    const cur = currency === 'RUR' ? '₽' : currency
    if (from && to) return `${from.toLocaleString()} – ${to.toLocaleString()} ${cur}`
    if (from) return `от ${from.toLocaleString()} ${cur}`
    if (to)   return `до ${to.toLocaleString()} ${cur}`
    return 'Не указана'
}

function getScoreColor(score) {
    if (score >= 80) return { text: 'text-green-400',  bg: 'bg-green-400' }
    if (score >= 60) return { text: 'text-yellow-400', bg: 'bg-yellow-400' }
    return              { text: 'text-red-400',    bg: 'bg-red-400' }
}

function getLevelBadge(level) {
    const map = {
        'Junior': 'bg-green-500 bg-opacity-15 text-green-400 border-green-500',
        'Middle': 'bg-yellow-500 bg-opacity-15 text-yellow-400 border-yellow-500',
        'Senior': 'bg-red-500 bg-opacity-15 text-red-400 border-red-500',
        'Lead':   'bg-purple-500 bg-opacity-15 text-purple-400 border-purple-500',
    }
    return map[level] || 'bg-gray-500 bg-opacity-15 text-gray-400 border-gray-500'
}

// ─── Загрузка профиля в сайдбар ───────────────────────────────────────────────

async function loadUserProfile() {
    const token = localStorage.getItem('jwt_token')
    if (!token) {
        window.location.href = 'index.html'
        return
    }

    const result = await api.getMe()
    if (result.status === 200) {
        const user = result.data
        localStorage.setItem('user', JSON.stringify(user))

        const nameEl    = document.getElementById('user-name')
        const emailEl   = document.getElementById('user-email')
        const avatarEl  = document.getElementById('user-avatar')

        if (nameEl)   nameEl.textContent   = user.username
        if (emailEl)  emailEl.textContent  = user.email
        if (avatarEl) avatarEl.textContent = user.username[0].toUpperCase()
    } else {
        logout()
    }
}