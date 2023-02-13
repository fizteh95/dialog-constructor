import asyncio
import typing as tp

import uvicorn
from fastapi import APIRouter
from fastapi import FastAPI


class Web:
    def __init__(
        self,
        host: str,
        port: int,
    ) -> None:
        self.host = host
        self.port = port
        self.app = FastAPI()
        self.router = APIRouter()
        self.router.add_api_route(
            path="/healthcheck", endpoint=self.healthcheck, methods=["GET", "POST"]
        )
        self.router.add_api_route(
            path="/user/get_info", endpoint=self.get_user, methods=["GET"]
        )
        self.app.include_router(self.router)

    @staticmethod
    async def healthcheck() -> tp.Dict[str, str]:
        return {"status": "ok"}

    @staticmethod
    async def get_user() -> tp.Dict[str, tp.Any]:
        res = {'name': 'Лариса', 'surname': 'Куткина', 'patronymic': 'Валерьевна', 'birthDate': '1971-05-12', 'birthPlace': 'Село Байкалово',
    'identityDocType': 'Паспорт гражданина РФ', 'identityDocCountryCode': None, 'identityDocSerial': '65 99',
    'identityDocNumber': '243621', 'idenityDocIssueDate': '2016-05-13', 'identityDocIssueDate': '2016-05-13',
    'idenityDocIssuedBy': 'ОВД БАЙКАЛОВСКОГО РАЙОНА СВЕРДЛОВСКОЙ ОБЛАСТИ',
    'identityDocIssuedBy': 'ОВД БАЙКАЛОВСКОГО РАЙОНА СВЕРДЛОВСКОЙ ОБЛАСТИ', 'idenityDocIssuedByCode': '662-015',
    'identityDocIssuedByCode': '662-015', 'regAddress': 'обл. Свердловская с. Байкалово ул. Свердлова дом 6 17',
    'regRegion': 'Свердловская область', 'regCity': 'Екатеринбург',
    'postAddress': 'обл. Свердловская г. Екатеринбург Самолетная дом 29 78',
    'factAddress': 'обл. Свердловская г. Екатеринбург Самолетная дом 29 78', 'factRegion': 'Свердловская область',
    'factCity': 'Екатеринбург', 'snils': '667-187-187-49', 'phones': '79533810238', 'mobilePhones': None,
    'email': 'kutkina@skbbank.ru', 'currentLogin': '08203', 'hasSecretAnswer': True,
    'secretQuestion': 'Кодовое слово', 'currentSignProvider': 'sms_otp', 'hasIssueScratchCard': False}
        return res

    def start(self) -> None:
        config = uvicorn.Config(
            self.app, host=self.host, port=self.port, log_level="debug"
        )
        server = uvicorn.Server(config)
        server.run()


web = Web(host="0.0.0.0", port=8081)
web.start()
