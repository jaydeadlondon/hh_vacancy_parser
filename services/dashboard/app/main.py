import streamlit as st
from app.api.client import DashboardAPIClient

st.set_page_config(
    page_title="HH Vacancy Parser",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Стили ────────────────────────────────────────────────────────────────────

st.markdown(
    """
<style>
    .metric-card {
        background: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
    }
    .score-high { color: #28a745; font-weight: bold; }
    .score-mid  { color: #ffc107; font-weight: bold; }
    .score-low  { color: #dc3545; font-weight: bold; }
    .vacancy-card {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
    }
</style>
""",
    unsafe_allow_html=True,
)


# ─── Инициализация session state ──────────────────────────────────────────────


def init_session() -> None:
    if "jwt_token" not in st.session_state:
        st.session_state.jwt_token = None
    if "user" not in st.session_state:
        st.session_state.user = None
    if "page" not in st.session_state:
        st.session_state.page = "vacancies"


# ─── Страница авторизации ─────────────────────────────────────────────────────


def show_login_page() -> None:
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.title("🔍 HH Vacancy Parser")
        st.subheader("Войди в аккаунт")

        with st.form("login_form"):
            username = st.text_input("Имя пользователя")
            password = st.text_input("Пароль", type="password")
            submitted = st.form_submit_button(
                "Войти",
                use_container_width=True,
                type="primary",
            )

        if submitted:
            if not username or not password:
                st.error("Заполни все поля")
                return

            client = DashboardAPIClient()
            result = client.login(username, password)

            if result["status"] == 200:
                st.session_state.jwt_token = result["data"]["access_token"]

                # Получаем данные пользователя
                me_result = client.get_me()
                if me_result["status"] == 200:
                    st.session_state.user = me_result["data"]

                st.success("✅ Вход выполнен!")
                st.rerun()
            else:
                error = result["data"].get("detail", "Ошибка входа")
                st.error(f"❌ {error}")


# ─── Сайдбар ──────────────────────────────────────────────────────────────────


def show_sidebar() -> None:
    user = st.session_state.user or {}

    with st.sidebar:
        st.title("🔍 HH Parser")
        st.divider()

        # Профиль
        st.markdown(f"👤 **{user.get('username', 'Пользователь')}**")
        st.markdown(f"📧 {user.get('email', '')}")

        telegram = user.get("telegram_username")
        if telegram:
            st.markdown(f"✅ Telegram: @{telegram}")
        else:
            st.warning("Telegram не привязан")

        st.divider()

        # Навигация
        st.markdown("**Навигация**")

        if st.button("📋 Вакансии", use_container_width=True):
            st.session_state.page = "vacancies"
            st.rerun()

        if st.button("📊 Аналитика", use_container_width=True):
            st.session_state.page = "analytics"
            st.rerun()

        if st.button("⚙️ Мои фильтры", use_container_width=True):
            st.session_state.page = "filters"
            st.rerun()

        st.divider()

        if st.button("🚪 Выйти", use_container_width=True):
            st.session_state.jwt_token = None
            st.session_state.user = None
            st.rerun()


# ─── Главная страница — Вакансии ──────────────────────────────────────────────


def show_vacancies_page() -> None:
    st.title("📋 Вакансии")

    client = DashboardAPIClient()

    # ─── Фильтры ──────────────────────────────────────────────────────────────
    with st.expander("🔧 Фильтры", expanded=True):
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            search = st.text_input(
                "🔎 Поиск по названию", placeholder="Python, React..."
            )

        with col2:
            min_score = st.slider(
                "⭐ Минимальный score",
                min_value=0,
                max_value=100,
                value=0,
                step=5,
            )

        with col3:
            level = st.selectbox(
                "📊 Уровень",
                options=["Все", "Junior", "Middle", "Senior", "Lead"],
            )

        with col4:
            limit = st.selectbox(
                "📄 Показать",
                options=[20, 50, 100],
                index=1,
            )

    # ─── Загрузка данных ──────────────────────────────────────────────────────
    with st.spinner("Загружаем вакансии..."):
        result = client.get_vacancies(
            limit=limit,
            min_score=min_score if min_score > 0 else None,
            level=level if level != "Все" else None,
            search=search if search else None,
        )

    if result["status"] != 200:
        st.error("❌ Ошибка загрузки вакансий. Проверь подключение к API.")
        return

    vacancies = result["data"]

    if not vacancies:
        st.info("😔 Вакансии не найдены. Создай фильтры в Telegram боте!")
        return

    # ─── Метрики ──────────────────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)

    scores = [v.get("attractiveness_score", 0) or 0 for v in vacancies]
    salaries_from = [v.get("salary_from") for v in vacancies if v.get("salary_from")]

    with col1:
        st.metric("📦 Всего вакансий", len(vacancies))

    with col2:
        avg_score = sum(scores) / len(scores) if scores else 0
        st.metric("⭐ Средний score", f"{avg_score:.1f}%")

    with col3:
        avg_salary = (
            int(sum(salaries_from) / len(salaries_from)) if salaries_from else 0
        )
        st.metric(
            "💰 Средняя зарплата от", f"{avg_salary:,} ₽" if avg_salary else "н/д"
        )

    with col4:
        remote_count = sum(1 for v in vacancies if v.get("is_remote"))
        st.metric("🏠 Удалённых", remote_count)

    st.divider()

    # ─── Карточки вакансий ────────────────────────────────────────────────────
    for vacancy in vacancies:
        score = vacancy.get("attractiveness_score", 0) or 0

        if score >= 80:
            score_color = "score-high"
            score_emoji = "🟢"
        elif score >= 60:
            score_color = "score-mid"
            score_emoji = "🟡"
        else:
            score_color = "score-low"
            score_emoji = "🔴"

        sal_from = vacancy.get("salary_from")
        sal_to = vacancy.get("salary_to")
        currency = vacancy.get("salary_currency", "RUR")

        if sal_from and sal_to:
            salary_str = f"{sal_from:,} – {sal_to:,} {currency}"
        elif sal_from:
            salary_str = f"от {sal_from:,} {currency}"
        elif sal_to:
            salary_str = f"до {sal_to:,} {currency}"
        else:
            salary_str = "не указана"

        stack = vacancy.get("detected_stack") or []
        stack_str = " • ".join(stack[:6]) if stack else "не определён"

        with st.container():
            col1, col2 = st.columns([4, 1])

            with col1:
                st.markdown(f"### [{vacancy['title']}]({vacancy['url']})")
                st.markdown(
                    f"🏢 **{vacancy.get('company', 'н/д')}** | "
                    f"💰 {salary_str} | "
                    f"📍 {vacancy.get('location', 'н/д')} "
                    f"{'🏠' if vacancy.get('is_remote') else ''}"
                )
                st.markdown(f"🛠 `{stack_str}`")

                summary = vacancy.get("ai_summary", "")
                if summary:
                    st.caption(f"💬 {summary}")

            with col2:
                st.markdown(
                    f"<div style='text-align:center'>"
                    f"<span class='{score_color}'>{score_emoji} {score:.0f}%</span>"
                    f"<br/><small>{vacancy.get('detected_level', '')}</small>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
                st.link_button(
                    "Открыть →",
                    vacancy["url"],
                    use_container_width=True,
                )

            st.divider()


# ─── Страница аналитики ───────────────────────────────────────────────────────


def show_analytics_page() -> None:
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go

    st.title("📊 Аналитика")

    client = DashboardAPIClient()

    with st.spinner("Загружаем данные..."):
        result = client.get_vacancies(limit=200)

    if result["status"] != 200:
        st.error("❌ Ошибка загрузки данных")
        return

    vacancies = result["data"]

    if not vacancies:
        st.info("😔 Нет данных для аналитики")
        return

    df = pd.DataFrame(vacancies)

    # ─── Метрики верхнего уровня ──────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("📦 Всего вакансий", len(df))

    with col2:
        avg_score = (
            df["attractiveness_score"].mean() if "attractiveness_score" in df else 0
        )
        st.metric("⭐ Средний AI score", f"{avg_score:.1f}%")

    with col3:
        remote_pct = (df["is_remote"].sum() / len(df) * 100) if "is_remote" in df else 0
        st.metric("🏠 Удалённых", f"{remote_pct:.1f}%")

    with col4:
        with_salary = df["salary_from"].notna().sum() if "salary_from" in df else 0
        st.metric("💰 Указали зарплату", with_salary)

    st.divider()

    # ─── Графики ──────────────────────────────────────────────────────────────
    col1, col2 = st.columns(2)

    # График 1 — Распределение по уровням
    with col1:
        st.subheader("📊 Распределение по уровням")
        if "detected_level" in df and df["detected_level"].notna().any():
            level_counts = df["detected_level"].value_counts()
            fig = px.pie(
                values=level_counts.values,
                names=level_counts.index,
                color_discrete_sequence=px.colors.qualitative.Set3,
                hole=0.4,
            )
            fig.update_layout(showlegend=True, height=350)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Нет данных об уровнях")

    # График 2 — Распределение AI score
    with col2:
        st.subheader("⭐ Распределение AI Score")
        if "attractiveness_score" in df and df["attractiveness_score"].notna().any():
            fig = px.histogram(
                df,
                x="attractiveness_score",
                nbins=20,
                color_discrete_sequence=["#4CAF50"],
                labels={"attractiveness_score": "AI Score"},
            )
            fig.update_layout(
                xaxis_title="Score (%)",
                yaxis_title="Количество",
                height=350,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Нет данных о score")

    # График 3 — Зарплаты по уровням
    st.subheader("💰 Зарплаты по уровням")
    salary_df = df[df["salary_from"].notna() & df["detected_level"].notna()].copy()

    if not salary_df.empty:
        fig = px.box(
            salary_df,
            x="detected_level",
            y="salary_from",
            color="detected_level",
            color_discrete_sequence=px.colors.qualitative.Set2,
            labels={
                "detected_level": "Уровень",
                "salary_from": "Зарплата от (₽)",
            },
            category_orders={"detected_level": ["Junior", "Middle", "Senior", "Lead"]},
        )
        fig.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Недостаточно данных о зарплатах")

    # График 4 — Популярные технологии
    st.subheader("🛠 Популярные технологии")
    if "detected_stack" in df:
        all_tech: list[str] = []
        for stack in df["detected_stack"].dropna():
            if isinstance(stack, list):
                all_tech.extend(stack)

        if all_tech:
            from collections import Counter

            tech_counts = Counter(all_tech).most_common(15)
            tech_df = pd.DataFrame(tech_counts, columns=["Технология", "Количество"])

            fig = px.bar(
                tech_df,
                x="Количество",
                y="Технология",
                orientation="h",
                color="Количество",
                color_continuous_scale="Viridis",
            )
            fig.update_layout(
                height=500,
                yaxis={"categoryorder": "total ascending"},
                showlegend=False,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Нет данных о технологиях")

    # График 5 — Score vs Зарплата
    st.subheader("📈 AI Score vs Зарплата")
    scatter_df = df[
        df["salary_from"].notna() & df["attractiveness_score"].notna()
    ].copy()

    if not scatter_df.empty:
        fig = px.scatter(
            scatter_df,
            x="salary_from",
            y="attractiveness_score",
            color="detected_level",
            hover_data=["title", "company"],
            labels={
                "salary_from": "Зарплата от (₽)",
                "attractiveness_score": "AI Score (%)",
                "detected_level": "Уровень",
            },
            color_discrete_sequence=px.colors.qualitative.Set1,
        )
        fig.update_layout(height=450)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Недостаточно данных")


# ─── Страница фильтров ────────────────────────────────────────────────────────


def show_filters_page() -> None:
    st.title("⚙️ Мои фильтры")

    client = DashboardAPIClient()
    result = client.get_filters()

    if result["status"] != 200:
        st.error("❌ Ошибка загрузки фильтров")
        return

    filters = result["data"]

    if not filters:
        st.info(
            "😔 Фильтры не найдены.\n\n"
            "Создай фильтры через Telegram бот командой /filters"
        )
        return

    for f in filters:
        with st.expander(
            f"{'✅' if f.get('is_active') else '❌'} {f['name']}",
            expanded=False,
        ):
            col1, col2 = st.columns(2)

            with col1:
                keywords = f.get("keywords") or []
                st.markdown(
                    f"**🔑 Ключевые слова:** {', '.join(keywords) or 'не указаны'}"
                )

                excluded = f.get("excluded_keywords") or []
                st.markdown(f"**🚫 Исключить:** {', '.join(excluded) or 'не указаны'}")

                salary = f.get("min_salary")
                st.markdown(
                    f"**💰 Мин. зарплата:** {f'{salary:,} ₽' if salary else 'не указана'}"
                )

            with col2:
                stack = f.get("tech_stack") or []
                st.markdown(f"**🛠 Стек:** {', '.join(stack) or 'не указан'}")

                st.markdown(f"**📍 Город:** {f.get('location') or 'любой'}")

                level_map = {
                    "noExperience": "Без опыта",
                    "between1And3": "Junior (1-3 года)",
                    "between3And6": "Middle (3-6 лет)",
                    "moreThan6": "Senior (6+ лет)",
                }
                level = level_map.get(f.get("experience_level", ""), "не указан")
                st.markdown(f"**📊 Уровень:** {level}")

                remote = "🏠 Только удалённо" if f.get("remote_ok") else "🏢 Любой"
                st.markdown(f"**💼 Формат:** {remote}")


# ─── Точка входа ──────────────────────────────────────────────────────────────


def main() -> None:
    init_session()

    if not st.session_state.jwt_token:
        show_login_page()
        return

    show_sidebar()

    page = st.session_state.get("page", "vacancies")

    if page == "vacancies":
        show_vacancies_page()
    elif page == "analytics":
        show_analytics_page()
    elif page == "filters":
        show_filters_page()


if __name__ == "__main__":
    main()
