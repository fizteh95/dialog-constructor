import asyncio

from aiogram import Bot

from src.adapters.ep_wrapper import EPWrapper
from src.adapters.poller_adapter import PollerAdapter
from src.adapters.repository import InMemoryRepo
from src.adapters.sender_wrapper import SenderWrapper
from src.domain.events import EventProcessor
from src.domain.model import InIntent
from src.domain.model import NodeType
from src.domain.model import OutMessage
from src.domain.model import Scenario
from src.domain.scenario_loader import XMLParser
from src.entrypoints.poller import TgPoller
from src.service_layer.message_bus import ConcreteMessageBus
from src.service_layer.sender import TgSender


def mock_scenario() -> Scenario:
    mock_node = InIntent(
        element_id="id_1",
        value="mock_start",
        next_ids=["id_2"],
        node_type=NodeType.inIntent,
    )
    mock_out_node = OutMessage(
        element_id="id_2",
        value="Подключаем оператора",
        next_ids=[],
        node_type=NodeType.outMessage,
    )
    default_scenario = Scenario(
        "default", "id_1", {"id_1": mock_node, "id_2": mock_out_node}
    )
    return default_scenario


async def main() -> None:
    xml_src_path = "./src/resources/weather-demo.xml"
    parser = XMLParser()
    root_id, nodes = parser.parse(src_path=xml_src_path)
    parsed_nodes = {x.element_id: x for x in nodes}
    scenario = Scenario(name="weather-demo", root_id=root_id, nodes=parsed_nodes)
    scenario_texts = {
        "TEXT1": "Введите широту",
        "TEXT2": "Неправильная широта, попробуйте еще раз",
        "TEXT3": "Введите долготу",
        "TEXT4": "Неправильная долгота, попробуйте еще раз",
        "TEXT5": "Температура в заданном месте: $temperature$ градусов Цельсия",
        "TEXT6": "Что-то пошло не так",
        "TEXT7": "Хотите посмотреть фичу изменения сообщения?",
        "TEXT8": "Да",
        "TEXT9": "Нет",
        "TEXT10": "Сообщение изменено ;)",
        "TEXT11": "Сценарий окончен.",
    }

    mock_scenario_ = mock_scenario()

    repo = InMemoryRepo()
    await repo.add_scenario(mock_scenario_)
    await repo.add_scenario(scenario)
    await repo.add_scenario_texts(scenario.name, scenario_texts)

    ep = EventProcessor(
        {mock_scenario_.name: {"intents": [], "phrases": []}}, mock_scenario_.name
    )
    wrapped_ep = EPWrapper(event_processor=ep, repo=repo)
    await wrapped_ep.add_scenario(scenario.name)

    bot = Bot(token="5023614422:AAEIwysH_RgMug_GpVV8b3ZpEw4kVnRL3IU")

    sender = TgSender(bot=bot)
    wrapped_sender = SenderWrapper(sender=sender, repo=repo)

    bus = ConcreteMessageBus()
    bus.register(wrapped_ep)
    bus.register(wrapped_sender)

    poller_adapter = PollerAdapter(bus=bus, repo=repo)
    poller = TgPoller(
        message_handler=poller_adapter.message_handler,
        user_finder=poller_adapter.user_finder,
        bot=bot,
    )

    await poller.poll()


if __name__ == "__main__":
    asyncio.run(main())
