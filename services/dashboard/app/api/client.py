from typing import Any
import httpx
import streamlit as st

API_URL = "http://localhost:8000"


class DashboardAPIClient:
    """
    HTTP клиент к API Gateway для дашборда
    Токен берём из streamlit session_state
    """

    def __init__(self) -> None:
        self._base_url = API_URL
        self._token: str | None = st.session_state.get("jwt_token")

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    def login(
        self, username: str, password: str
    ) -> dict[str, Any]:  # sync запрос тк streamlit без async
        try:
            response = httpx.post(
                f"{self._base_url}/api/v1/auth/login",
                json={"username": username, "password": password},
                timeout=15.0,
            )
            return {"status": response.status_code, "data": response.json()}
        except httpx.RequestError as e:
            return {"status": 0, "data": {"detail": str(e)}}

    def get_me(self) -> dict[str, Any]:
        try:
            response = httpx.get(
                f"{self._base_url}/api/v1/auth/me",
                headers=self._headers(),
                timeout=15.0,
            )
            return {"status": response.status_code, "data": response.json()}
        except httpx.RequestError as e:
            return {"status": 0, "data": {"detail": str(e)}}

    def get_vacancies(
        self,
        limit: int = 50,
        min_score: float | None = None,
        level: str | None = None,
        search: str | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"limit": limit}
        if min_score is not None:
            params["min_score"] = min_score
        if level:
            params["level"] = level
        if search:
            params["q"] = search

        try:
            response = httpx.get(
                f"{self._base_url}/api/v1/vacancies/list",
                headers=self._headers(),
                params=params,
                timeout=15.0,
            )
            return {"status": response.status_code, "data": response.json()}
        except httpx.RequestError as e:
            return {"status": 0, "data": {"detail": str(e)}}

    def get_top_vacancies(self, limit: int = 10) -> dict[str, Any]:
        try:
            response = httpx.get(
                f"{self._base_url}/api/v1/vacancies/top",
                headers=self._headers(),
                params={"limit": limit},
                timeout=15.0,
            )
            return {"status": response.status_code, "data": response.json()}
        except httpx.RequestError as e:
            return {"status": 0, "data": {"detail": str(e)}}

    def get_filters(self) -> dict[str, Any]:
        try:
            response = httpx.get(
                f"{self._base_url}/api/v1/filters",
                headers=self._headers(),
                timeout=15.0,
            )
            return {"status": response.status_code, "data": response.json()}
        except httpx.RequestError as e:
            return {"status": 0, "data": {"detail": str(e)}}
