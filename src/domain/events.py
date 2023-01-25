import copy
import typing as tp

from src.domain.model import Event
from src.domain.model import InEvent
from src.domain.model import NodeType
from src.domain.model import OutEvent
from src.domain.model import Scenario


class EventProcessor:
    """
    Превращает входящие события в исходящие по сценарию
    По интентам - неинтентам:
    """

    def __init__(
        self,
        scenarios: tp.Dict[str, tp.Dict[str, tp.List[str]]],
        default_scenario_name: str,
    ) -> None:
        """
        Инициализация event processor'а
        :param scenarios: {имя_сценария: {"intents": ["реквизиты"], "phrases": []}, имя_сценария2: {...}, ...}
        :param default_scenario_name: имя сценария по умолчанию
        """
        self.scenarios = scenarios
        self.default_scenario_name = default_scenario_name
        if self.default_scenario_name not in self.scenarios:
            raise Exception("No scenario with default name in scenarios")

    def add_scenario(
        self, scenario: Scenario, intents: tp.List[str], phrases: tp.List[str]
    ) -> None:
        self.scenarios[scenario.name] = {"intents": intents, "phrases": phrases}

    async def check_scenario_start(
        self, scenario: Scenario, event: InEvent
    ) -> tp.List[str]:
        """
        Проверка запустится ли этот сценарий, то есть это проверка самого начала сценария
        Для четкой фразы допускается или одна фраза, или несколько соединенных ИЛИ
        Для интентов допускаются все логические операции
        :param scenario: сценарий
        :param event: событие
        :return: айдишники нод для последующего пути
        """
        match_phrases_nodes = None
        if event.text:
            match_phrases_nodes = scenario.get_nodes_by_type(NodeType.matchText)
        if event.intent:
            match_phrases_nodes = scenario.get_nodes_by_type(NodeType.inIntent)
        if match_phrases_nodes is None:
            raise Exception("InEvent must have text or intent")

        if len(match_phrases_nodes) == 1:
            _, _, filtered_text = await match_phrases_nodes[0].execute(
                event.user, {}, event.text
            )
            if filtered_text:
                if not match_phrases_nodes[0].next_ids:
                    raise Exception("matchText node need some child")
                res: tp.List[str] = match_phrases_nodes[0].next_ids
                return res
        elif len(match_phrases_nodes) > 1:
            if not match_phrases_nodes[0].next_ids:
                raise Exception("matchText node need some child")
            or_node = scenario.get_node_by_id(match_phrases_nodes[0].next_ids[0])
            if not or_node.next_ids:
                raise Exception("OR node must have any child")
            for n in match_phrases_nodes:
                if not n.next_ids:
                    raise Exception("matchText node need some child")
                if or_node.element_id not in n.next_ids:
                    raise Exception("Not only one child for matchText nodes")
                _, _, filtered_text = await n.execute(event.user, {}, event.text)
                if filtered_text:
                    return or_node.next_ids
        else:
            pass
        return []

    @staticmethod
    def is_button_in_events(events: tp.List[OutEvent]) -> str:
        buttons_node_id = ""
        for event in events:
            if event.buttons:
                buttons_node_id = event.linked_node_id
        return buttons_node_id

    async def process_event(
        self,
        event: InEvent,
        ctx: tp.Dict[str, str],
        scenario_getter: tp.Callable[[str], tp.Awaitable[Scenario]],
    ) -> tp.Tuple[tp.List[OutEvent], tp.Dict[str, str]]:
        """
        Ветвление исполнения только в логических блоках, иначе только один потомок
        То есть без учета логических блоков и изменения сообщений должен быть только один потомок
        :param event: входящее событие, текст или нажатая кнопка
        :param ctx: контекст юзера в данном сценарии
        :param scenario_getter: отдает сценарий по названию
        :return: список исходящих событий и словарь для обновления контекста
        """
        user = event.user
        current_scenario_name = user.current_scenario_name
        current_node_id = user.current_node_id
        if current_scenario_name and current_node_id:
            current_scenario = await scenario_getter(current_scenario_name)
            current_node = current_scenario.get_node_by_id(current_node_id)
            nodes_id = current_node.next_ids
        elif current_node_id and not current_scenario_name:
            raise Exception("Current node set, not current scenario")
        else:
            # никакой сценарий еще не начат
            if not event.text and not event.intent:
                raise Exception("Couldnt start scenario without text and intent")
            for name, start_dict in self.scenarios.items():
                if (
                    event.text in start_dict["phrases"]
                    or event.intent in start_dict["intents"]
                ):
                    scenario = await scenario_getter(name)
                    nodes_id = await self.check_scenario_start(
                        scenario=scenario, event=event
                    )
                    if nodes_id:
                        current_scenario = scenario
                        user.current_scenario_name = current_scenario.name
                        break
            else:
                current_scenario = await scenario_getter(self.default_scenario_name)
                user.current_scenario_name = current_scenario.name
                current_node = current_scenario.get_node_by_id(current_scenario.root_id)
                nodes_id = current_node.next_ids
        if event.button_pushed_next:
            nodes_id = [event.button_pushed_next]
        elif not nodes_id:
            raise Exception("Absense of next nodes with set scenario is not acceptable")

        # текущий сценарий и последующие айдишники нод мы нашли
        # current_scenario - текущий сценарий, nodes_id - айдишники следующих нод
        if len(nodes_id) != 1:
            raise Exception("Only one child must be from regular node")

        output: tp.List[OutEvent] = []

        pipeline_text = event.text
        current_node = current_scenario.get_node_by_id(nodes_id[0])
        if event.button_pushed_next:
            current_node = current_scenario.get_node_by_id(event.button_pushed_next)
            pipeline_text = event.button_pushed_next
        last_node = copy.deepcopy(
            current_node
        )  # нужно для определения последнего сработавшего блока для logicalUnit
        if pipeline_text is None:
            raise Exception("Pipeline text must be something")

        # идем по сценарию пока не встретим спец блоки
        for _ in range(15):
            if current_node.node_type in (
                NodeType.outMessage,
                NodeType.setVariable,
                NodeType.remoteRequest,
                NodeType.dataExtract,
            ):
                out_events, update_ctx, pipeline_text = await current_node.execute(
                    user, ctx, pipeline_text
                )
                output += out_events
                ctx.update(update_ctx)
            elif current_node.node_type == NodeType.inMessage:
                user.current_node_id = current_node.element_id
                return output, ctx
            elif current_node.node_type == NodeType.logicalUnit:
                # TODO: refactor
                parents = current_scenario.get_parents_of_node(
                    current_node.element_id
                )  # родители логического блока
                if len(parents) == 1:
                    _, _, next_node_id = await current_node.execute(
                        user, ctx, pipeline_text
                    )
                    current_node = current_scenario.get_node_by_id(next_node_id)
                    continue
                lu_in_res: tp.List[str] = []
                parents = [x for x in parents if x.element_id != last_node.element_id]
                lu_in_res.append(pipeline_text)
                # сделана глубина 2, надо отрефакторить
                for p in parents:
                    internal_parents = current_scenario.get_parents_of_node(
                        p.element_id
                    )
                    internal_res: tp.List[str] = []
                    for ip in internal_parents:
                        _, _, result_text = await ip.execute(user, ctx, "")
                        internal_res.append(result_text)
                    res_for_parent = "###$###".join(internal_res)
                    _, _, result_text = await p.execute(user, ctx, res_for_parent)
                    lu_in_res.append(result_text)
                resulted_text = "###$###".join(lu_in_res)
                _, _, next_node_id = await current_node.execute(
                    user, ctx, resulted_text
                )
                current_node = current_scenario.get_node_by_id(next_node_id)
                """
                Надо находить родителей логических блоков
                родителями могут быть только: dataExtract, logicalUnit, remoteRequest, getVariable
                у них у всех только один выход
                два типа родителей: 
                    - им самим нужны родители (dataExtract, logicalUnit) 
                    - или нет (remoteRequest, getVariable)
                В зависимости от количества родителей логическим блокам для исполнения надо разное кол-во аргументов
                в цикле идем к родителю, смотрим, если у того нет родителей то исполняем его и сохраняем рез-т в LU
                если родители есть то идем к ним, смотрим есть ли родители утех родителей, и т. д.
                пока не дойдем до верхушки логической пирамиды
                """
                continue
            elif current_node.node_type == NodeType.editMessage:
                out_events, update_ctx, pipeline_text = await current_node.execute(
                    user, ctx, pipeline_text
                )
                output += out_events
                ctx.update(update_ctx)
                if current_node.next_ids is None:
                    raise Exception("EditNode must have at least one child")
                elif len(current_node.next_ids) == 1:
                    last_buttons_node_id = self.is_button_in_events(output)
                    if last_buttons_node_id:
                        user.current_node_id = last_buttons_node_id
                    else:
                        user.current_node_id = None
                        user.current_scenario_name = None
                    return output, ctx
                elif len(current_node.next_ids) == 2:
                    last_node = copy.deepcopy(current_node)
                    current_node = current_scenario.get_node_by_id(
                        current_node.next_ids[1]
                    )
                    continue

            if current_node.next_ids is None:
                raise Exception("Only one child must be from regular node")
            if len(current_node.next_ids) > 1:
                raise Exception("Only one child must be from regular node")
            if len(current_node.next_ids) == 0:
                last_buttons_node_id = self.is_button_in_events(output)
                if last_buttons_node_id:
                    user.current_node_id = last_buttons_node_id
                else:
                    user.current_node_id = None
                    user.current_scenario_name = None
                return output, ctx
            last_node = copy.deepcopy(current_node)
            current_node = current_scenario.get_node_by_id(current_node.next_ids[0])

        return output, {}

    async def handle_message(
        self, event: Event, ctx: tp.Dict[str, str]
    ) -> tp.Tuple[tp.List[Event], tp.Dict[str, str]]:
        if isinstance(event, InEvent):
            return await self.process_event(event=event, ctx=ctx)  # type: ignore
        return [], ctx
