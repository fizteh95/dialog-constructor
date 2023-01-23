import copy
import typing as tp

from src.domain.model import Event
from src.domain.model import ExecuteNode
from src.domain.model import InEvent
from src.domain.model import NodeType
from src.domain.model import OutEvent
from src.domain.model import Scenario
from src.domain.model import User


class EventProcessor:
    """
    Превращает входящие события в исходящие по сценарию
    По интентам - неинтентам:
    """

    def __init__(
        self,
        scenarios: tp.Dict[str, tp.Dict[str, tp.List[str]]],
        scenario_getter: tp.Callable[[str], tp.Awaitable[Scenario]],
        default_scenario_name: str,
    ) -> None:
        """
        Инициализация event processor'а
        :param scenarios: {имя_сценария: {"intents": ["реквизиты"], "phrases": []}, имя_сценария2: {...}, ...}
        :param scenario_getter: геттер для получения объекта сценария извне по его имени
        :param default_scenario_name: имя сценария по умолчанию
        """
        self.scenarios = scenarios
        self.default_scenario_name = default_scenario_name
        self.scenario_getter = scenario_getter
        if self.default_scenario_name not in self.scenarios:
            raise Exception("No scenario with default name in scenarios")

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
        self, event: InEvent, ctx: tp.Dict[str, str]
    ) -> tp.Tuple[tp.List[OutEvent], tp.Dict[str, str]]:
        """
        Ветвление исполнения только в логических блоках, иначе только один потомок
        То есть без учета логических блоков и изменения сообщений должен быть только один потомок
        :param event: входящее событие, текст или нажатая кнопка
        :param ctx: контекст юзера в данном сценарии
        :return: список исходящих событий и словарь для обновления контекста
        """
        user = event.user
        current_scenario_name = user.current_scenario_name
        current_node_id = user.current_node_id
        if current_scenario_name and current_node_id:
            current_scenario = await self.scenario_getter(current_scenario_name)
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
                    scenario = await self.scenario_getter(name)
                    nodes_id = await self.check_scenario_start(
                        scenario=scenario, event=event
                    )
                    if nodes_id:
                        current_scenario = scenario
                        user.current_scenario_name = current_scenario.name
                        break
            else:
                current_scenario = await self.scenario_getter(
                    self.default_scenario_name
                )
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

        current_node = current_scenario.get_node_by_id(nodes_id[0])
        if event.button_pushed_next:
            current_node = current_scenario.get_node_by_id(event.button_pushed_next)

        # идем по сценарию пока не встретим спец блоки
        for _ in range(15):
            if current_node.node_type in (
                NodeType.outMessage,
                NodeType.setVariable,
                NodeType.remoteRequest,
                NodeType.dataExtract,
            ):
                out_events, update_ctx, out_text = await current_node.execute(
                    user, ctx, event.text
                )
                output += out_events
                ctx.update(update_ctx)
            elif current_node.node_type == NodeType.inMessage:
                user.current_node_id = current_node.element_id
                return output, ctx
            elif current_node.node_type == NodeType.logicalUnit:
                parents = current_scenario.get_parents_of_node(current_node.element_id)
                """
                Надо находить родителей логических блоков
                """
                raise

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
            current_node = current_scenario.get_node_by_id(current_node.next_ids[0])

        return output, {}

    async def handle_message(
        self, event: Event, ctx: tp.Dict[str, str]
    ) -> tp.Tuple[tp.List[Event], tp.Dict[str, str]]:
        if isinstance(event, InEvent):
            return await self.process_event(event=event, ctx=ctx)  # type: ignore
        return [], ctx

    # @staticmethod
    # def get_next(
    #     scenario: Scenario,
    #     current_node: ExecuteNode | None = None,
    #     event: InEvent | None = None,
    # ) -> tp.List[ExecuteNode]:
    #     if current_node is not None and event is not None:
    #         raise Exception("Not acceptable node and event both in finding next node")
    #     # два случая - если из кнопки ищем потомков, или из обычного блока
    #     if event is not None and event.button_pushed_next:
    #         res_from_button = []
    #         for n in event.button_pushed_next.split(","):
    #             res_from_button.append(scenario.get_node_by_id(n))
    #         return res_from_button
    #     else:
    #         if current_node is not None and current_node.next_ids is not None:
    #             res_from_node = []
    #             for n in current_node.next_ids:
    #                 res_from_node.append(scenario.get_node_by_id(n))
    #             return res_from_node
    #     return []
    #
    # async def _search_pathway(
    #     self,
    #     current_scenario: Scenario,
    #     start_node: ExecuteNode | None,
    #     start_event: InEvent | None,
    #     user: User,
    #     ctx: tp.Dict[str, str],
    #     input_str: str,
    # ) -> tp.Tuple[tp.List[Event], tp.Dict[str, str]]:
    #     out_events: tp.List[Event] = []
    #     last_input_node: None | ExecuteNode = None
    #
    #     next_nodes = self.get_next(
    #         current_scenario, current_node=start_node, event=start_event
    #     )
    #     # DEBUG
    #     if start_event and start_event.button_pushed_next:
    #         print("tp-0")
    #         print(next_nodes)
    #         print("tp-1")
    #     # ENDDEBUG
    #     for n_n in next_nodes:
    #         output, to_update_ctx, text_for_pipeline = await n_n.execute(
    #             user, ctx, input_str
    #         )
    #         if text_for_pipeline or to_update_ctx or output:
    #             ctx.update(to_update_ctx)
    #             out_events += output
    #             executed_node = copy.deepcopy(n_n)
    #             text_to_next = copy.deepcopy(text_for_pipeline)
    #             break
    #     else:
    #         executed_node = next_nodes[-1]
    #         text_to_next = ""
    #     #     await user.update_current_node_id(None)
    #     #     await user.update_current_scenario_name(None)
    #     #     raise Exception("No block executed after inMessage")
    #
    #     # если после сообщения с кнопками будет еще сообщение исходящее
    #     if executed_node.buttons:
    #         last_input_node = copy.deepcopy(executed_node)
    #
    #     outer_continuer = False
    #     node_from_last_iteration = copy.deepcopy(executed_node)
    #     for _ in range(15):
    #         # поиск и исполнение третьей и последующих очередей блоков
    #         if outer_continuer:
    #             next_nodes = [node_from_last_iteration]
    #         else:
    #             if executed_node.node_type == NodeType.editMessage:
    #                 next_nodes = [
    #                     current_scenario.get_node_by_id(executed_node.next_ids[1])
    #                 ]
    #             else:
    #                 next_nodes = self.get_next(
    #                     current_scenario, current_node=executed_node
    #                 )
    #             # DEBUG
    #             if start_event and start_event.button_pushed_next:
    #                 print("tp0")
    #                 print(next_nodes)
    #                 print("tp1")
    #             # ENDDEBUG
    #         outer_continuer = False
    #         for n_n in next_nodes:
    #             if n_n.node_type == NodeType.inMessage:
    #                 await user.update_current_node_id(n_n.element_id)
    #                 return out_events, ctx
    #             elif n_n.node_type == NodeType.editMessage:
    #                 output, _, text_for_pipeline = await n_n.execute(
    #                     user, ctx, text_to_next
    #                 )
    #                 out_events += output
    #                 if n_n.next_ids is None:
    #                     raise Exception("Logical unit has no child")
    #                 node_from_last_iteration = current_scenario.get_node_by_id(
    #                     n_n.next_ids[1]
    #                 )
    #                 # if not node_from_last_iteration.node_type == NodeType.inMessage:
    #                 #     await user.update_current_node_id(None)
    #                 #     await user.update_current_scenario_name(None)
    #                 #     return out_events, ctx
    #                 outer_continuer = True
    #                 break
    #             elif n_n.node_type == NodeType.logicalUnit:
    #                 _, _, text_for_pipeline = await n_n.execute(user, ctx, text_to_next)
    #                 if n_n.next_ids is None:
    #                     raise Exception("Logical unit has no child")
    #                 if text_for_pipeline:
    #                     node_from_last_iteration = current_scenario.get_node_by_id(
    #                         n_n.next_ids[0]
    #                     )
    #                 else:
    #                     node_from_last_iteration = current_scenario.get_node_by_id(
    #                         n_n.next_ids[-1]
    #                     )
    #                 outer_continuer = True
    #                 break
    #         if outer_continuer:
    #             continue
    #         for n_n in next_nodes:
    #             output, to_update_ctx, text_for_pipeline = await n_n.execute(
    #                 user, ctx, text_to_next
    #             )
    #             if text_for_pipeline or to_update_ctx or output:
    #                 ctx.update(to_update_ctx)
    #                 out_events += output
    #                 executed_node = copy.deepcopy(n_n)
    #                 text_to_next = copy.deepcopy(text_for_pipeline)
    #                 break
    #         else:
    #             # если не было следующих нод или ничего не вернулось
    #             if last_input_node is not None:
    #                 await user.update_current_node_id(last_input_node.element_id)
    #                 return out_events, ctx
    #             else:
    #                 await user.update_current_node_id(None)
    #                 await user.update_current_scenario_name(None)
    #                 return out_events, ctx
    #     return [], ctx
    #
    # async def process_event(
    #     self, event: InEvent, ctx: tp.Dict[str, str]
    # ) -> tp.Tuple[tp.List[Event], tp.Dict[str, str]]:
    #     """
    #     Ограничения блок-схемы сценария:
    #     - должен начинаться с inMessage
    #     - во входящем событии должна быть нажатая кнопка или текст
    #     - одновременно во входящем событии не должно быть и нажатой кнопки и текста
    #     - нода inMessage должна быть единственным потомком для родителя
    #     - выполняется только один потомок ноды из всех сиблингов, у которого у первого появился ответ (для текущих
    #     блок-схем исполнение идет по порядку добавления блока на схему)
    #     - после inMessage должна быть хотя бы одна нода для выполнения
    #     - у блока logicUnit должно быть два потомка, первый установленный на схему потомок исполняется если logicUnit
    #     вернул True, последний установленный выполняется если вернулось False
    #     :param event: входящее событие, текст или нажатая кнопка
    #     :param ctx: контекст юзера в данном сценарии
    #     :return: список исходящих событий и словарь для обновления контекста
    #     """
    #     user = event.user
    #     current_scenario_name = user.current_scenario_name
    #     if current_scenario_name is None:
    #         current_scenario = self.scenarios[self.default_scenario_name]
    #         await user.update_current_scenario_name(self.default_scenario_name)
    #     else:
    #         current_scenario = self.scenarios.get(
    #             current_scenario_name, self.scenarios[self.default_scenario_name]
    #         )
    #     current_node_id = user.current_node_id
    #     if current_node_id is None:
    #         current_node = current_scenario.get_node_by_id(current_scenario.root_id)
    #     else:
    #         current_node = current_scenario.get_node_by_id(current_node_id)
    #     if current_node.node_type != NodeType.inMessage and not current_node.buttons:
    #         raise Exception("Start executing not from input event")
    #     if event.button_pushed_next and event.text:
    #         raise Exception("Not acceptable text and buttons at same time in InEvent")
    #
    #     # исполнение потомков стартовой ноды
    #     # if (current_node.node_type == NodeType.inMessage and not event.text) or (
    #     #     current_node.node_type != NodeType.inMessage and event.text
    #     # ):
    #     #     raise Exception("Dont match input text and current node type")
    #     # el
    #     if current_node.node_type == NodeType.inMessage and event.text:
    #         return await self._search_pathway(
    #             current_scenario=current_scenario,
    #             start_node=current_node,
    #             start_event=None,
    #             user=user,
    #             ctx=ctx,
    #             input_str=event.text,
    #         )
    #     elif event.button_pushed_next:
    #         return await self._search_pathway(
    #             current_scenario=current_scenario,
    #             start_node=None,
    #             start_event=event,
    #             user=user,
    #             ctx=ctx,
    #             input_str="",
    #         )
    #     return [], ctx
    #
    # async def handle_message(
    #     self, event: Event, ctx: tp.Dict[str, str]
    # ) -> tp.Tuple[tp.List[Event], tp.Dict[str, str]]:
    #     if isinstance(event, InEvent):
    #         return await self.process_event(event=event, ctx=ctx)
    #     return [], ctx
