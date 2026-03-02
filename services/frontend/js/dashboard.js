let filterTimeout = null
let allVacancies  = []

// ─── Инициализация ────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', async () => {
    await loadUserProfile()
    await loadVacancies()
})

// ─── Загрузка вакансий ────────────────────────────────────────────────────────

async function loadVacancies() {
    const search   = document.getElementById('filter-search')?.value?.trim()
    const minScore = document.getElementById('filter-score')?.value
    const level    = document.getElementById('filter-level')?.value
    const limit    = document.getElementById('filter-limit')?.value || 50

    const params = { limit }
    if (search)              params.q         = search
    if (minScore && minScore > 0) params.min_score = minScore
    if (level)               params.level     = level

    showSkeletons()

    const result = await api.getVacancies(params)

    if (result.status === 200) {
        allVacancies = result.data
        renderVacancies(allVacancies)
        updateMetrics(allVacancies)
    } else if (result.status === 401 || result.status === 403) {
        logout()
    } else {
        showToast('Ошибка загрузки вакансий', 'error')
    }
}

// ─── Рендер карточек ─────────────────────────────────────────────────────────

function renderVacancies(vacancies) {
    const list     = document.getElementById('vacancies-list')
    const empty    = document.getElementById('empty-state')
    const countEl  = document.getElementById('vacancy-count')

    countEl.textContent = `${vacancies.length} вакансий`

    if (!vacancies.length) {
        list.innerHTML = ''
        empty.classList.remove('hidden')
        return
    }

    empty.classList.add('hidden')
    list.innerHTML = vacancies.map((v, i) => renderCard(v, i)).join('')
}

function renderCard(v, index) {
    const score    = v.attractiveness_score || 0
    const colors   = getScoreColor(score)
    const level    = v.detected_level || ''
    const badge    = getLevelBadge(level)
    const salary   = formatSalary(v.salary_from, v.salary_to, v.salary_currency)
    const stack    = (v.detected_stack || []).slice(0, 5)

    const stackHtml = stack.map(t =>
        `<span class="tech-tag">${t}</span>`
    ).join('')

    const delay = index * 30

    return `
    <div class="vacancy-card bg-dark-800 rounded-2xl p-5 border border-white border-opacity-5 fade-in cursor-pointer"
         style="animation-delay: ${delay}ms"
         onclick="window.open('${v.url}', '_blank')">
        <div class="flex items-start justify-between gap-4">

            <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 mb-1 flex-wrap">
                    ${level ? `<span class="text-xs px-2 py-0.5 rounded-md border ${badge} font-medium">${level}</span>` : ''}
                    ${v.is_remote ? '<span class="text-xs px-2 py-0.5 rounded-md bg-blue-500 bg-opacity-15 text-blue-400 border border-blue-500 border-opacity-30 font-medium">Remote</span>' : ''}
                </div>

                <h3 class="text-base font-semibold text-white mb-1 truncate hover:text-accent-400 transition-colors">
                    ${v.title}
                </h3>

                <div class="flex items-center gap-3 text-sm text-gray-400 mb-3">
                    <span class="flex items-center gap-1">
                        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/>
                        </svg>
                        ${v.company || 'Компания не указана'}
                    </span>
                    ${v.location ? `
                    <span class="flex items-center gap-1">
                        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/>
                        </svg>
                        ${v.location}
                    </span>` : ''}
                    <span class="text-green-400 font-medium">${salary}</span>
                </div>

                ${stackHtml ? `<div class="flex flex-wrap gap-1.5 mb-3">${stackHtml}</div>` : ''}

                ${v.ai_summary ? `
                <p class="text-xs text-gray-500 line-clamp-2">${v.ai_summary}</p>
                ` : ''}
            </div>

            <!-- Score -->
            <div class="flex-shrink-0 flex flex-col items-center">
                <div class="relative w-16 h-16">
                    <svg class="w-16 h-16 -rotate-90" viewBox="0 0 36 36">
                        <circle cx="18" cy="18" r="15.9" fill="none" stroke="#21263a" stroke-width="2.5"/>
                        <circle cx="18" cy="18" r="15.9" fill="none"
                            stroke="${score >= 80 ? '#4ade80' : score >= 60 ? '#facc15' : '#f87171'}"
                            stroke-width="2.5"
                            stroke-dasharray="${score} ${100 - score}"
                            stroke-dashoffset="0"
                            stroke-linecap="round"/>
                    </svg>
                    <div class="absolute inset-0 flex items-center justify-center">
                        <span class="text-sm font-bold ${colors.text}">${Math.round(score)}</span>
                    </div>
                </div>
                <span class="text-xs text-gray-500 mt-1">AI Score</span>
            </div>

        </div>
    </div>`
}

// ─── Метрики ──────────────────────────────────────────────────────────────────

function updateMetrics(vacancies) {
    const total    = vacancies.length
    const scores   = vacancies.map(v => v.attractiveness_score || 0)
    const salaries = vacancies.filter(v => v.salary_from).map(v => v.salary_from)
    const remotes  = vacancies.filter(v => v.is_remote).length

    document.getElementById('metric-total').textContent  = total
    document.getElementById('metric-score').textContent  =
        scores.length ? (scores.reduce((a, b) => a + b, 0) / scores.length).toFixed(1) + '%' : '—'
    document.getElementById('metric-salary').textContent =
        salaries.length ? Math.round(salaries.reduce((a, b) => a + b, 0) / salaries.length).toLocaleString() + ' ₽' : '—'
    document.getElementById('metric-remote').textContent = remotes
}

// ─── Скелетон ─────────────────────────────────────────────────────────────────

function showSkeletons() {
    const list = document.getElementById('vacancies-list')
    list.innerHTML = Array(4).fill(`
        <div class="bg-dark-800 rounded-2xl p-5 border border-white border-opacity-5 animate-pulse">
            <div class="flex items-start gap-4">
                <div class="flex-1">
                    <div class="h-4 bg-dark-700 rounded w-1/4 mb-3"></div>
                    <div class="h-5 bg-dark-700 rounded w-3/4 mb-2"></div>
                    <div class="h-4 bg-dark-700 rounded w-1/2 mb-3"></div>
                    <div class="flex gap-2">
                        <div class="h-5 w-16 bg-dark-700 rounded-md"></div>
                        <div class="h-5 w-20 bg-dark-700 rounded-md"></div>
                        <div class="h-5 w-14 bg-dark-700 rounded-md"></div>
                    </div>
                </div>
                <div class="w-16 h-16 bg-dark-700 rounded-full"></div>
            </div>
        </div>
    `).join('')
}

// ─── Debounce фильтрации ──────────────────────────────────────────────────────

function debounceFilter() {
    clearTimeout(filterTimeout)
    filterTimeout = setTimeout(loadVacancies, 400)
}

function updateScoreLabel() {
    const val = document.getElementById('filter-score').value
    document.getElementById('score-label').textContent = val + '%'
}