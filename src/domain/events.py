import copy
import typing as tp

from src.domain.model import Event
from src.domain.model import ExecuteNode
from src.domain.model import InEvent
from src.domain.model import NodeType
from src.domain.model import Scenario


class EventProcessor:
    """
    Превращает входящие события в исходящие по сценарию
    """

    def __init__(
        self, scenarios: tp.List[Scenario], default_scenario_name: str
    ) -> None:
        self.scenarios = {s.name: s for s in scenarios}
        self.default_scenario_name = default_scenario_name
        if self.default_scenario_name not in self.scenarios:
            raise Exception("No scenario with default name in scenarios")

    @staticmethod
    def get_next(
        scenario: Scenario,
        current_node: ExecuteNode | None = None,
        event: InEvent | None = None,
    ) -> tp.List[ExecuteNode]:
        if current_node is not None and event is not None:
            raise Exception("Not acceptable node and event both in finding next node")
        # два случая - если из кнопки ищем потомков, или из обычного блока
        if event is not None and event.button_pushed_next:
            res_from_button = []
            for n in event.button_pushed_next.split(","):
                res_from_button.append(scenario.get_node_by_id(n))
            return res_from_button
        else:
            if current_node is not None and current_node.next_ids is not None:
                res_from_node = []
                for n in current_node.next_ids:
                    res_from_node.append(scenario.get_node_by_id(n))
                return res_from_node
        return []

    async def process_event(
        self, event: InEvent, ctx: tp.Dict[str, str]
    ) -> tp.Tuple[tp.List[Event], tp.Dict[str, str]]:
        """
        Ограничения блок-схемы сценария:
        - должен начинаться с inMessage
        - во входящем событии должна быть нажатая кнопка или текст
        - одновременно во входящем событии не должно быть и нажатой кнопки и текста
        - нода inMessage должна быть единственным потомком для родителя
        - выполняется только один потомок ноды из всех сиблингов, у которого у первого появился ответ (для текущих
        блок-схем исполнение идет по порядку добавления блока на схему)
        - после inMessage должна быть хотя бы одна нода для выполнения
        :param event: входящее событие, текст или нажатая кнопка
        :param ctx: контекст юзера в данном сценарии
        :return: список исходящих событий и словарь для обновления контекста
        """
        user = event.user
        current_scenario_name = user.current_scenario_name
        if current_scenario_name is None:
            current_scenario = self.scenarios[self.default_scenario_name]
            await user.update_current_scenario_name(self.default_scenario_name)
        else:
            current_scenario = self.scenarios.get(
                current_scenario_name, self.scenarios[self.default_scenario_name]
            )
        current_node_id = user.current_node_id
        if current_node_id is None:
            current_node = current_scenario.get_node_by_id(current_scenario.root_id)
        else:
            current_node = current_scenario.get_node_by_id(current_node_id)
        if current_node.node_type != NodeType.inMessage and not current_node.buttons:
            raise Exception("Start executing not from input event")
        if event.button_pushed_next and event.text:
            raise Exception("Not acceptable text and buttons at same time in InEvent")

        out_events: tp.List[Event] = []

        if (current_node.node_type == NodeType.inMessage and not event.text) or (
            current_node.node_type != NodeType.inMessage and event.text
        ):
            raise Exception("Dont match input text and current node type")
        elif current_node.node_type == NodeType.inMessage and event.text:
            # исполнение стартовой ноды и ее потомков
            _, _, res = await current_node.execute(user, ctx, event.text)
            next_nodes = self.get_next(current_scenario, current_node=current_node)
            for n_n in next_nodes:
                output, to_update_ctx, text_for_pipeline = await n_n.execute(
                    user, ctx, res
                )
                if text_for_pipeline or to_update_ctx or output:
                    ctx.update(to_update_ctx)
                    out_events += output
                    executed_node = copy.deepcopy(n_n)
                    text_to_next = copy.deepcopy(text_for_pipeline)
                    break
            else:
                raise Exception("No block executed after inMessage")

            last_input_node: None | ExecuteNode = None
            # если после сообщения с кнопками будет еще сообщение исходящее
            if executed_node.buttons:
                last_input_node = copy.deepcopy(executed_node)

            for _ in range(15):
                # поиск и исполнение третьей и последующих очередей блоков
                next_nodes = self.get_next(current_scenario, current_node=executed_node)
                for n_n in next_nodes:
                    if n_n.node_type == NodeType.inMessage:
                        await user.update_current_node_id(n_n.element_id)
                        return out_events, ctx
                for n_n in next_nodes:
                    output, to_update_ctx, text_for_pipeline = await n_n.execute(
                        user, ctx, text_to_next
                    )
                    if text_for_pipeline or to_update_ctx or output:
                        ctx.update(to_update_ctx)
                        out_events += output
                        executed_node = copy.deepcopy(n_n)
                        text_to_next = copy.deepcopy(text_for_pipeline)
                        break
                else:
                    # если не было следующих нод или ничего не вернулось
                    if last_input_node is not None:
                        await user.update_current_node_id(last_input_node.element_id)
                        return out_events, ctx
                    else:
                        await user.update_current_node_id(None)
                        await user.update_current_scenario_name(None)
                        return out_events, ctx
            ...
        elif event.button_pushed_next:
            next_nodes = self.get_next(current_scenario, event=event)
            for n_n in next_nodes:
                output, to_update_ctx, text_for_pipeline = await n_n.execute(
                    user, ctx, ""
                )
                if text_for_pipeline or to_update_ctx or output:
                    ctx.update(to_update_ctx)
                    out_events += output
                    executed_node = copy.deepcopy(n_n)
                    text_to_next = copy.deepcopy(text_for_pipeline)
                    break
            else:
                raise Exception("No block executed after inMessage")

            last_input_node_from_button: None | ExecuteNode = None
            # если после сообщения с кнопками будет еще сообщение исходящее
            if executed_node.buttons:
                last_input_node_from_button = copy.deepcopy(executed_node)

            for _ in range(15):
                # поиск и исполнение третьей и последующих очередей блоков
                next_nodes = self.get_next(current_scenario, current_node=executed_node)

                for n_n in next_nodes:
                    if n_n.node_type == NodeType.inMessage:
                        await user.update_current_node_id(n_n.element_id)
                        return out_events, ctx
                for n_n in next_nodes:
                    output, to_update_ctx, text_for_pipeline = await n_n.execute(
                        user, ctx, text_to_next
                    )
                    if text_for_pipeline or to_update_ctx or output:
                        ctx.update(to_update_ctx)
                        out_events += output
                        executed_node = copy.deepcopy(n_n)
                        text_to_next = copy.deepcopy(text_for_pipeline)
                        break
                else:
                    # если не было следующих нод или ничего не вернулось
                    if last_input_node_from_button is not None:
                        await user.update_current_node_id(
                            last_input_node_from_button.element_id
                        )
                        return out_events, ctx
                    else:
                        await user.update_current_node_id(None)
                        await user.update_current_scenario_name(None)
                        return out_events, ctx
            ...
        ...
        return [], ctx
