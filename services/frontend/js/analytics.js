// Chart.js глобальные настройки
Chart.defaults.color = '#6b7280'
Chart.defaults.borderColor = 'rgba(255,255,255,0.05)'
Chart.defaults.font.family = 'system-ui, sans-serif'

document.addEventListener('DOMContentLoaded', async () => {
    await loadUserProfile()
    await loadAnalytics()
})

async function loadAnalytics() {
    const result = await api.getVacancies({ limit: 200 })

    if (result.status !== 200) {
        showToast('Ошибка загрузки данных', 'error')
        return
    }

    const vacancies = result.data
    if (!vacancies.length) return

    updateMetrics(vacancies)
    renderLevelsChart(vacancies)
    renderScoreChart(vacancies)
    renderTechChart(vacancies)
    renderSalaryChart(vacancies)
}

// ─── Метрики ──────────────────────────────────────────────────────────────────

function updateMetrics(vacancies) {
    const scores   = vacancies.map(v => v.attractiveness_score || 0)
    const salaries = vacancies.filter(v => v.salary_from)
    const remotes  = vacancies.filter(v => v.is_remote).length

    document.getElementById('a-total').textContent       = vacancies.length
    document.getElementById('a-score').textContent       =
        (scores.reduce((a, b) => a + b, 0) / scores.length).toFixed(1) + '%'
    document.getElementById('a-salary-count').textContent = salaries.length
    document.getElementById('a-remote').textContent      = remotes
}

// ─── График уровней (Doughnut) ────────────────────────────────────────────────

function renderLevelsChart(vacancies) {
    const counts = {}
    vacancies.forEach(v => {
        const l = v.detected_level || 'Не определён'
        counts[l] = (counts[l] || 0) + 1
    })

    const labels = Object.keys(counts)
    const data   = Object.values(counts)

    new Chart(document.getElementById('chart-levels'), {
        type: 'doughnut',
        data: {
            labels,
            datasets: [{
                data,
                backgroundColor: [
                    'rgba(74, 222, 128, 0.8)',
                    'rgba(250, 204, 21, 0.8)',
                    'rgba(248, 113, 113, 0.8)',
                    'rgba(167, 139, 250, 0.8)',
                    'rgba(156, 163, 175, 0.8)',
                ],
                borderWidth: 0,
                hoverOffset: 6,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { padding: 16, usePointStyle: true, pointStyleWidth: 8 }
                }
            },
            cutout: '65%',
        }
    })
}

// ─── График Score (Histogram) ─────────────────────────────────────────────────

function renderScoreChart(vacancies) {
    const buckets = Array(10).fill(0)
    vacancies.forEach(v => {
        const s = v.attractiveness_score || 0
        const i = Math.min(Math.floor(s / 10), 9)
        buckets[i]++
    })

    const labels = ['0-10', '10-20', '20-30', '30-40', '40-50', '50-60', '60-70', '70-80', '80-90', '90-100']

    new Chart(document.getElementById('chart-scores'), {
        type: 'bar',
        data: {
            labels,
            datasets: [{
                label: 'Вакансий',
                data: buckets,
                backgroundColor: labels.map((_, i) => {
                    const alpha = 0.4 + (i / 10) * 0.5
                    return `rgba(99, 102, 241, ${alpha})`
                }),
                borderRadius: 6,
                borderSkipped: false,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { grid: { display: false }, ticks: { font: { size: 10 } } },
                y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { stepSize: 1 } },
            }
        }
    })
}

// ─── Топ технологий (Bar) ─────────────────────────────────────────────────────

function renderTechChart(vacancies) {
    const counts = {}
    vacancies.forEach(v => {
        (v.detected_stack || []).forEach(t => {
            counts[t] = (counts[t] || 0) + 1
        })
    })

    const sorted  = Object.entries(counts).sort((a, b) => b[1] - a[1]).slice(0, 12)
    const labels  = sorted.map(([t]) => t)
    const data    = sorted.map(([, c]) => c)

    new Chart(document.getElementById('chart-tech'), {
        type: 'bar',
        data: {
            labels,
            datasets: [{
                label: 'Вакансий',
                data,
                backgroundColor: 'rgba(99, 102, 241, 0.7)',
                borderRadius: 5,
                borderSkipped: false,
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { grid: { color: 'rgba(255,255,255,0.05)' } },
                y: { grid: { display: false }, ticks: { font: { size: 11 } } },
            }
        }
    })
}

// ─── Зарплаты по уровням (Bar grouped) ───────────────────────────────────────

function renderSalaryChart(vacancies) {
    const levels  = ['Junior', 'Middle', 'Senior', 'Lead']
    const avgData = levels.map(level => {
        const group = vacancies.filter(v => v.detected_level === level && v.salary_from)
        if (!group.length) return 0
        return Math.round(group.reduce((s, v) => s + v.salary_from, 0) / group.length)
    })

    new Chart(document.getElementById('chart-salary'), {
        type: 'bar',
        data: {
            labels: levels,
            datasets: [{
                label: 'Средняя зарплата от (₽)',
                data: avgData,
                backgroundColor: [
                    'rgba(74, 222, 128, 0.7)',
                    'rgba(250, 204, 21, 0.7)',
                    'rgba(248, 113, 113, 0.7)',
                    'rgba(167, 139, 250, 0.7)',
                ],
                borderRadius: 8,
                borderSkipped: false,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { grid: { display: false } },
                y: {
                    grid: { color: 'rgba(255,255,255,0.05)' },
                    ticks: {
                        callback: v => v ? v.toLocaleString() + ' ₽' : '0'
                    }
                },
            }
        }
    })
}