import json
from datetime import datetime
import aio_pika
from aio_pika import DeliveryMode, Message
from app.core.config import settings
from shared.utils.logger import get_logger

logger = get_logger(__name__)

QUEUE_VACANCIES_ANALYZED = "vacancies.analyzed"


class RabbitMQPublisher:
    """Публикуем проанализированные вакансии"""

    def __init__(self) -> None:
        self._connection: aio_pika.RobustConnection | None = None
        self._channel: aio_pika.RobustChannel | None = None

    async def connect(self) -> None:
        self._connection = await aio_pika.connect_robust(settings.rabbitmq_url)
        self._channel = await self._connection.channel()

        await self._channel.declare_queue(
            QUEUE_VACANCIES_ANALYZED,
            durable=True,
        )
        logger.info("✅ RabbitMQ Publisher подключён")

    async def publish_analyzed(
        self,
        vacancy_id: int,
        user_id: int,
        attractiveness_score: float,
        analysis_id: int,
    ) -> None:
        """
        Отправляем результат анализа в очередь для Notifier
        """
        if not self._channel:
            raise RuntimeError("RabbitMQ не подключён")

        payload = {
            "vacancy_id": vacancy_id,
            "user_id": user_id,
            "attractiveness_score": attractiveness_score,
            "analysis_id": analysis_id,
            "analyzed_at": datetime.utcnow().isoformat(),
        }

        message = Message(
            body=json.dumps(payload).encode(),
            delivery_mode=DeliveryMode.PERSISTENT,
            content_type="application/json",
        )

        await self._channel.default_exchange.publish(
            message,
            routing_key=QUEUE_VACANCIES_ANALYZED,
        )

        logger.debug(
            f"📤 Отправлено в vacancies.analyzed: "
            f"vacancy_id={vacancy_id} score={attractiveness_score}"
        )
