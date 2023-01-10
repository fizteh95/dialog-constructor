import typing as tp

from src.executor.domain import Event


class User:
    def __init__(
        self,
        outer_id: int,
        nickname: None | str = None,
        name: None | str = None,
        surname: None | str = None,
        patronim: None | str = None,
    ) -> None:
        self.outer_id = outer_id
        self.nickname = nickname
        self.name = name
        self.surname = surname
        self.patronim = patronim
        self.event_history: tp.List[Event] = []
        self.current_scenario_id: None | str = None
        self.current_node_id: None | str = None

    def get_user_var(self, var: str) -> tp.Any:
        raise
