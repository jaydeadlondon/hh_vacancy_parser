import json
from datetime import datetime
import aio_pika
from aio_pika import DeliveryMode, Message
from app.core.config import settings
from shared.utils.logger import get_logger

logger = get_logger(__name__)

QUEUE_VACANCIES_NEW = "vacancies.new"


class RabbitMQPublisher:
    """Публикуем сообщения в RabbitMQ"""

    def __init__(self) -> None:
        self._connection: aio_pika.RobustConnection | None = None
        self._channel: aio_pika.RobustChannel | None = None

    async def connect(self) -> None:
        self._connection = await aio_pika.connect_robust(settings.rabbitmq_url)
        self._channel = await self._connection.channel()

        await self._channel.declare_queue(
            QUEUE_VACANCIES_NEW,
            durable=True,
        )

        logger.info("✅ RabbitMQ подключён")

    async def disconnect(self) -> None:
        if self._connection:
            await self._connection.close()

    async def publish_vacancy(
        self,
        vacancy_id: int,
        user_id: int,
        filter_id: int,
    ) -> None:
        """
        Отправляем вакансию в очередь для AI анализа
        """
        if not self._channel:
            raise RuntimeError("RabbitMQ не подключён")

        payload = {
            "vacancy_id": vacancy_id,
            "user_id": user_id,
            "filter_id": filter_id,
            "published_at": datetime.utcnow().isoformat(),
        }

        message = Message(
            body=json.dumps(payload).encode(),
            delivery_mode=DeliveryMode.PERSISTENT,
            content_type="application/json",
        )

        await self._channel.default_exchange.publish(
            message,
            routing_key=QUEUE_VACANCIES_NEW,
        )

        logger.debug(
            f"📤 Отправлено в очередь: vacancy_id={vacancy_id} user_id={user_id}"
        )
