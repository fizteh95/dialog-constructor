import typing as tp

import uvicorn
from fastapi import APIRouter
from fastapi import FastAPI

from src import settings
from src.settings import logger


class Web:
    def __init__(
        self,
        host: str,
        port: int,
        message_handler: tp.Callable[
            [tp.Dict[str, tp.Any]], tp.Awaitable[tp.List[tp.Dict[str, tp.Any]]]
        ],
    ) -> None:
        self.host = host
        self.port = port
        self.message_handler = message_handler
        self.app = FastAPI()
        self.router = APIRouter()
        self.router.add_api_route(
            path="/healthcheck", endpoint=self.healthcheck, methods=["GET", "POST"]
        )
        self.router.add_api_route(
            path="/message_text", endpoint=self.message_text, methods=["POST"]
        )
        self.app.include_router(self.router)

    @staticmethod
    async def healthcheck() -> tp.Dict[str, str]:
        return {"status": "ok"}

    async def message_text(
        self, body: tp.Dict[str, str]
    ) -> tp.List[tp.Dict[str, tp.Any]]:
        logger.info(f"incoming request: {body}")
        events = await self.message_handler(body)
        return events

    async def start(self) -> None:
        config = uvicorn.Config(
            self.app,
            host=self.host,
            port=self.port,
            log_level="debug",
            log_config=settings.LOGGING,
        )
        server = uvicorn.Server(config)
        await server.serve()
