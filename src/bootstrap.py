import asyncio
import importlib
import json
import os
import typing as tp

from aiogram import Bot

from src.adapters.ep_wrapper import AbstractEPWrapper
from src.adapters.poller_adapter import AbstractPollerAdapter
from src.adapters.repository import AbstractRepo
from src.adapters.sender_wrapper import AbstractSenderWrapper
from src.adapters.web_adapter import AbstractWebAdapter
from src.domain.events import EventProcessor
from src.domain.model import Scenario
from src.domain.scenario_loader import Parser
from src.domain.scenario_loader import XMLParser
from src.entrypoints.poller import Poller
from src.entrypoints.web import Web
from src.service_layer.message_bus import MessageBus
from src.service_layer.sender import Sender


async def upload_scenarios_to_repo(repo: AbstractRepo, parser: Parser) -> None:
    tree = os.walk("./src/scenarios")
    paths = []
    for item in tree:
        if "__pycache__" not in item[0]:
            paths.append(item)
    scenario_names = paths[0][1]
    scenario_names = [x for x in scenario_names if x != "__pycache__"]
    for i, name in enumerate(scenario_names):
        scenario_files = paths[i + 1][2]
        if "scenario.py" in scenario_files:
            make_scenario_file = importlib.import_module(
                f"src.scenarios.{name}.scenario"
            )
            scenario = make_scenario_file.make_scenario()
        elif "scenario.xml" in scenario_files:
            root_id, nodes = parser.parse(
                src_path=f"./src/scenarios/{name}/scenario.xml"
            )
            parsed_nodes = {x.element_id: x for x in nodes}
            scenario = Scenario(name=name, root_id=root_id, nodes=parsed_nodes)
        else:
            continue
        with open(f"./src/scenarios/{name}/text_templates.json", "r") as f:
            text_dict = json.load(f)
        await repo.add_scenario(scenario=scenario)
        await repo.add_scenario_texts(scenario_name=scenario.name, texts=text_dict)


async def download_scenarios_to_ep(
    wrapped_ep: AbstractEPWrapper, repo: AbstractRepo
) -> None:
    scenario_names = await repo.get_all_scenario_names()
    for name in scenario_names:
        await wrapped_ep.add_scenario(name)


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

    concrete_repo = repo()
    parser = XMLParser()
    await upload_scenarios_to_repo(repo=concrete_repo, parser=parser)

    mock_scenario = await concrete_repo.get_scenario_by_name("default")
    concrete_ep = ep(
        {mock_scenario.name: {"intents": [], "phrases": []}}, mock_scenario.name
    )
    wrapped_ep = ep_wrapper(event_processor=concrete_ep, repo=concrete_repo)
    await download_scenarios_to_ep(wrapped_ep=wrapped_ep, repo=concrete_repo)

    concrete_bus = bus()
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
