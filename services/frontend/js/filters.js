document.addEventListener('DOMContentLoaded', async () => {
    await loadUserProfile()
    await loadFilters()
})

// ─── Загрузка фильтров ────────────────────────────────────────────────────────

async function loadFilters() {
    const result = await api.getFilters()

    if (result.status !== 200) {
        showToast('Ошибка загрузки фильтров', 'error')
        return
    }

    const filters = result.data
    const list    = document.getElementById('filters-list')
    const empty   = document.getElementById('filters-empty')

    if (!filters.length) {
        list.innerHTML = ''
        empty.classList.remove('hidden')
        return
    }

    empty.classList.add('hidden')
    list.innerHTML = filters.map(renderFilterCard).join('')
}

// ─── Карточка фильтра ─────────────────────────────────────────────────────────

function renderFilterCard(f) {
    const keywords = (f.keywords || []).join(', ') || '—'
    const excluded = (f.excluded_keywords || []).join(', ') || '—'
    const stack    = (f.tech_stack || []).join(', ') || '—'

    const levelMap = {
        noExperience: 'Без опыта',
        between1And3: 'Junior (1-3 года)',
        between3And6: 'Middle (3-6 лет)',
        moreThan6:    'Senior (6+ лет)',
    }

    return `
    <div class="bg-dark-800 rounded-2xl p-6 border border-white border-opacity-5 fade-in">
        <div class="flex items-start justify-between mb-4">
            <div class="flex items-center gap-3">
                <div class="w-10 h-10 bg-accent-500 bg-opacity-20 rounded-xl flex items-center justify-center border border-accent-500 border-opacity-20">
                    <svg class="w-5 h-5 text-accent-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z"/>
                    </svg>
                </div>
                <div>
                    <h3 class="font-semibold text-white">${f.name}</h3>
                    <span class="text-xs ${f.is_active ? 'text-green-400' : 'text-gray-500'}">
                        ${f.is_active ? '● Активен' : '○ Отключён'}
                    </span>
                </div>
            </div>
            <button onclick="deleteFilter(${f.id})"
                class="text-gray-600 hover:text-red-400 transition-colors p-1.5 hover:bg-red-500 hover:bg-opacity-10 rounded-lg">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                </svg>
            </button>
        </div>

        <div class="space-y-2.5">
            <div class="flex justify-between text-sm">
                <span class="text-gray-500">Ключевые слова</span>
                <span class="text-gray-300 text-right max-w-[60%] truncate">${keywords}</span>
            </div>
            <div class="flex justify-between text-sm">
                <span class="text-gray-500">Исключить</span>
                <span class="text-gray-300 text-right max-w-[60%] truncate">${excluded}</span>
            </div>
            <div class="flex justify-between text-sm">
                <span class="text-gray-500">Мин. зарплата</span>
                <span class="text-green-400 font-medium">${f.min_salary ? f.min_salary.toLocaleString() + ' ₽' : '—'}</span>
            </div>
            <div class="flex justify-between text-sm">
                <span class="text-gray-500">Уровень</span>
                <span class="text-gray-300">${levelMap[f.experience_level] || '—'}</span>
            </div>
            <div class="flex justify-between text-sm">
                <span class="text-gray-500">Город</span>
                <span class="text-gray-300">${f.location || 'Любой'}</span>
            </div>
            <div class="flex justify-between text-sm">
                <span class="text-gray-500">Формат</span>
                <span class="text-gray-300">${f.remote_ok ? '🏠 Удалённо' : '🏢 Любой'}</span>
            </div>
            <div class="flex justify-between text-sm">
                <span class="text-gray-500">Стек (AI)</span>
                <span class="text-accent-400 text-right max-w-[60%] truncate">${stack}</span>
            </div>
        </div>
    </div>`
}

// ─── Удаление фильтра ─────────────────────────────────────────────────────────

async function deleteFilter(id) {
    if (!confirm('Удалить этот фильтр?')) return

    const result = await api.deleteFilter(id)

    if (result.status === 204 || result.status === 200) {
        showToast('Фильтр удалён', 'success')
        await loadFilters()
    } else {
        showToast('Ошибка удаления', 'error')
    }
}

// ─── Модальное окно ───────────────────────────────────────────────────────────

function openCreateModal() {
    document.getElementById('modal-create').classList.remove('hidden')
    document.getElementById('f-name').focus()
}

function closeCreateModal() {
    document.getElementById('modal-create').classList.add('hidden')
    clearModalForm()
}

function clearModalForm() {
    ['f-name', 'f-keywords', 'f-excluded', 'f-salary', 'f-location', 'f-stack']
        .forEach(id => { document.getElementById(id).value = '' })
    document.getElementById('f-experience').value = ''
    document.getElementById('f-remote').value = 'false'
    document.getElementById('modal-error').classList.add('hidden')
}

// ─── Создание фильтра ─────────────────────────────────────────────────────────

async function createFilter() {
    const name      = document.getElementById('f-name').value.trim()
    const keywords  = document.getElementById('f-keywords').value.trim()
    const excluded  = document.getElementById('f-excluded').value.trim()
    const salary    = document.getElementById('f-salary').value.trim()
    const exp       = document.getElementById('f-experience').value
    const location  = document.getElementById('f-location').value.trim()
    const remote    = document.getElementById('f-remote').value
    const stack     = document.getElementById('f-stack').value.trim()
    const errorEl   = document.getElementById('modal-error')
    const spinner   = document.getElementById('create-spinner')
    const btnText   = document.getElementById('create-btn-text')

    errorEl.classList.add('hidden')

    if (!name) {
        errorEl.textContent = 'Введи название фильтра'
        errorEl.classList.remove('hidden')
        return
    }

    const data = {
        name,
        remote_ok: remote === 'true',
    }

    if (keywords)  data.keywords          = keywords.split(',').map(s => s.trim()).filter(Boolean)
    if (excluded)  data.excluded_keywords = excluded.split(',').map(s => s.trim()).filter(Boolean)
    if (salary)    data.min_salary        = parseInt(salary)
    if (exp)       data.experience_level  = exp
    if (location)  data.location          = location
    if (stack)     data.tech_stack        = stack.split(',').map(s => s.trim()).filter(Boolean)

    spinner.classList.remove('hidden')
    btnText.textContent = 'Создаём...'

    const result = await api.createFilter(data)

    spinner.classList.add('hidden')
    btnText.textContent = 'Создать фильтр'

    if (result.status === 201) {
        closeCreateModal()
        showToast('Фильтр создан! Парсер запустится в ближайший час 🚀', 'success')
        await loadFilters()
    } else {
        const msg = result.data?.detail || 'Ошибка создания фильтра'
        errorEl.textContent = msg
        errorEl.classList.remove('hidden')
    }
}

// ─── Enter в модалке ──────────────────────────────────────────────────────────

document.addEventListener('keydown', e => {
    if (e.key === 'Escape') closeCreateModal()
})