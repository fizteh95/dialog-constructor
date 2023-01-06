from src.dialogues.domain import Dialogue
from src.dialogues.scenario_loader import XMLParser
from src.executor.domain import ConcreteExecutor, ConcreteMessageBus, InMemoryRepo, TgPoller, TgSender
from aiogram import Bot
import asyncio


async def main() -> None:
    xml_src_path = "/home/dmitriy/PycharmProjects/dialogue-constructor/src/resources/dialogue-schema-test.xml"
    parser = XMLParser()
    root_id, nodes = parser.parse(src_path=xml_src_path)
    dialogue = Dialogue(root_id=root_id, name="Test scenario", nodes=nodes)
    print(root_id)
    print(dialogue)

    cmb = ConcreteMessageBus()
    imr = InMemoryRepo()
    ce = ConcreteExecutor(repo=imr, bus=cmb)

    bot = Bot(token="5421768118:AAHyArmRTT2PeNZgSS3_S21ZpqRoKp3QVdY")
    tg_poller = TgPoller(bus=cmb, repo=imr, bot=bot)
    tg_sender = TgSender(bot=bot)

    cmb.register(tg_sender)
    cmb.register(ce)

    await imr.create_dialogue_scenario(dialogue)
    await tg_poller.poll()


if __name__ == "__main__":
    asyncio.run(main())
