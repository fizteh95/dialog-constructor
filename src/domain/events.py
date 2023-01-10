import typing as tp
from dataclasses import dataclass

from src.domain.model import Event, Scenario
from src.domain.model import User


@dataclass
class InEvent(Event):
    user: User
    text: tp.Optional[str] = None
    button_pushed_next: tp.Optional[str] = None


@dataclass
class Button:
    text: str
    callback_data: tp.Optional[str]


@dataclass
class OutEvent(Event):
    user: User
    text: str
    buttons: tp.Optional[tp.List[Button]] = None
    edited_node: tp.Optional[str] = None
    ...


class EventProcessor:
    """
    Превращает входящие события в исходящие по сценарию
    """
    def __init__(self, scenarios: tp.List[Scenario], default_scenario_name: str) -> None:
        self.scenarios = {s.name: s for s in scenarios}
        self.default_scenario_name = default_scenario_name
        if self.default_scenario_name not in self.scenarios:
            raise Exception("No scenario with default name in scenarios")

    def process_event(self, event: InEvent) -> tp.List[OutEvent]:
        current_scenario_name = event.user.current_scenario_name
        if current_scenario_name is None:
            current_scenario = self.scenarios[self.default_scenario_name]
        else:
            current_scenario = self.scenarios.get(current_scenario_name, self.scenarios[self.default_scenario_name])
        current_node_id = event.user.current_node_id
        if current_node_id is None:
            current_node = current_scenario.get_node_by_id(current_scenario.root_id)
        else:
            current_node = current_scenario.get_node_by_id(current_node_id)
        ...
        return []
