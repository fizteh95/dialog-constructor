import asyncio
import importlib
import os
import typing as tp

from aiogram import Bot

from src.adapters.ep_wrapper import AbstractEPWrapper
from src.adapters.poller_adapter import AbstractPollerAdapter
from src.adapters.repository import AbstractRepo
from src.adapters.sender_wrapper import AbstractSenderWrapper
from src.adapters.web_adapter import AbstractWebAdapter
from src.domain.events import EventProcessor
from src.domain.model import InIntent
from src.domain.model import NodeType
from src.domain.model import OutMessage
from src.domain.model import Scenario
from src.domain.scenario_loader import XMLParser
from src.entrypoints.poller import Poller
from src.entrypoints.web import Web
from src.service_layer.message_bus import MessageBus
from src.service_layer.sender import Sender


def upload_scenarios_to_repo() -> None:
    tree = os.walk("./src/scenarios")
    paths = []
    scenarios: tp.Dict[str, Scenario] = {}
    for item in tree:
        paths.append(item)
    """
    ('./src/scenarios', ['quiz', 'mock', 'weather_demo'], [])
    ('./src/scenarios/quiz', [], ['text_templates.json', 'scenario.xml'])
    ('./src/scenarios/mock', [], ['text_templates.json', 'scenario.py'])
    ('./src/scenarios/weather_demo', [], ['text_templates.json', 'scenario.xml'])
    """
    scenario_names = paths[0][1]
    for i, name in enumerate(scenario_names):
        scenario_files = paths[i + 1][2]
        if "scenario.py" in scenario_files:
            make_scenario = __import__(f"src.scenarios.{name}.scenario.make_scenario")


def download_scenarios_to_ep() -> None:
    ...


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


async def bootstrap(
    repo: tp.Type[AbstractRepo],
    ep: tp.Type[EventProcessor],
    ep_wrapper: tp.Type[AbstractEPWrapper],
    bus: tp.Type[MessageBus],
    web: tp.Type[Web],
    web_adapter: tp.Type[AbstractWebAdapter],
    poller: tp.Type[Poller] | None = None,
    poller_adapter: tp.Type[AbstractPollerAdapter] | None = None,
    sender: tp.Type[Sender] | None = None,
    sender_wrapper: tp.Type[AbstractSenderWrapper] | None = None,
) -> tp.Any:
    upload_scenarios_to_repo()
    xml_src_path = "./src/scenarios/weather_demo/scenario.xml"
    parser = XMLParser()
    root_id, nodes = parser.parse(src_path=xml_src_path)
    parsed_nodes = {x.element_id: x for x in nodes}
    scenario = Scenario(name="weather-demo", root_id=root_id, nodes=parsed_nodes)
    scenario_texts = {
        "TEXT1": "Введите широту",
        "TEXT2": "Неправильная широта, попробуйте еще раз",
        "TEXT3": "Введите долготу",
        "TEXT4": "Неправильная долгота, попробуйте еще раз",
        "TEXT5": "Температура в заданном месте: {{temperature}} градусов Цельсия",
        "TEXT6": "Что-то пошло не так",
        "TEXT7": "Хотите посмотреть фичу изменения сообщения?",
        "TEXT8": "Да",
        "TEXT9": "Нет",
        "TEXT10": "Сообщение изменено ;)",
        "TEXT11": "Сценарий окончен.",
    }

    mock_scenario_ = mock_scenario()

    concrete_repo = repo()
    await concrete_repo.add_scenario(mock_scenario_)
    await concrete_repo.add_scenario(scenario)
    await concrete_repo.add_scenario_texts(scenario.name, scenario_texts)

    concrete_bus = bus()

    concrete_ep = ep(
        {mock_scenario_.name: {"intents": [], "phrases": []}}, mock_scenario_.name
    )
    wrapped_ep = ep_wrapper(event_processor=concrete_ep, repo=concrete_repo)
    await wrapped_ep.add_scenario(scenario.name)
    concrete_bus.register(wrapped_ep)

    concrete_web_adapter = web_adapter(
        repo=concrete_repo, bus=concrete_bus, ep_wrapped=wrapped_ep
    )
    concrete_web = web(
        host="localhost",
        port=8080,
        message_handler=concrete_web_adapter.message_handler,
    )

    if sender is not None or poller is not None:
        bot = Bot(token="5023614422:AAEIwysH_RgMug_GpVV8b3ZpEw4kVnRL3IU")

    if sender is not None and sender_wrapper is not None:
        concrete_sender = sender(bot=bot)
        wrapped_sender = sender_wrapper(sender=concrete_sender, repo=concrete_repo)
        concrete_bus.register(wrapped_sender)

    if poller is not None and poller_adapter is not None:
        concrete_poller_adapter = poller_adapter(bus=concrete_bus, repo=concrete_repo)
        concrete_poller = poller(
            message_handler=concrete_poller_adapter.message_handler,
            user_finder=concrete_poller_adapter.user_finder,
            bot=bot,
        )

    if poller is not None and poller_adapter is not None:
        return asyncio.gather(concrete_poller.poll(), concrete_web.start())
    else:
        return asyncio.gather(concrete_web.start())
