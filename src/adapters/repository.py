import typing as tp
from abc import ABC
from abc import abstractmethod
from collections import defaultdict

from src.domain.model import Scenario
from src.domain.model import User


class AbstractRepo(ABC):
    # TODO: split repo for every model

    @abstractmethod
    async def prepare_db(self) -> None:
        """Migrations, etc"""

    # User
    @abstractmethod
    async def get_or_create_user(self, **kwargs: tp.Any) -> User:
        """Get by outer_id or create user"""

    @abstractmethod
    async def update_user(self, user: User) -> User:
        """Update user fields"""

    # Context
    @abstractmethod
    async def update_user_context(
        self, user: User, ctx_to_update: tp.Dict[str, str]
    ) -> None:
        """Update user context"""

    @abstractmethod
    async def get_user_context(self, user: User) -> tp.Dict[str, str]:
        """Get user context"""

    @abstractmethod
    async def get_user_history(self, user: User) -> tp.List[tp.Dict[str, str]]:
        """Get user history of out messages"""

    @abstractmethod
    async def add_to_user_history(
        self, user: User, ids_pair: tp.Dict[str, str]
    ) -> None:
        """Get user history of out messages"""

    @abstractmethod
    async def get_scenario_by_name(self, name: str, project_name: str) -> Scenario:
        """Get scenario by its name"""

    @abstractmethod
    async def add_scenario(self, scenario: Scenario, project_name: str) -> None:
        """Add scenario in repository"""

    @abstractmethod
    async def add_scenario_texts(
        self, scenario_name: str, project_name: str, texts: tp.Dict[str, str]
    ) -> None:
        """Add texts for templating scenario"""

    @abstractmethod
    async def get_scenario_text(
        self, scenario_name: str, project_name: str, template_name: str
    ) -> str:
        """Return template value"""

    @abstractmethod
    async def create_project(self, name: str) -> None:
        """Create project in db"""

    @abstractmethod
    async def get_all_scenarios_metadata(self) -> tp.List[tp.Tuple[str, str]]:
        """Get all scenarios names and projects"""


class InMemoryRepo(AbstractRepo):
    def __init__(self) -> None:
        self.users: tp.Dict[str, User] = {}
        self.users_ctx: tp.Dict[str, tp.Dict[str, str]] = defaultdict(dict)
        self.out_messages: tp.Dict[str, tp.List[tp.Dict[str, str]]] = defaultdict(list)
        self.projects: tp.Dict[
            str,
            tp.List[
                tp.Dict[str, tp.Union[tp.Dict[str, tp.Any], tp.Dict[str, str], str]]
            ],
        ] = {}
        """
        {
            "project_name1": 
            [
                {
                    "name": "First scenario"
                    "scenario": {Scenario json},
                    "texts": {"TEXT1": "some phrase", "TEXT2": "another phrase"}
                },
                {
                    "name": "Second scenario"
                    "scenario": {Scenario json},
                    "texts": {"TEXT1": "more some phrase", "TEXT2": "more another phrase"}
                },
                ...
            ],
            "project_name2": 
            [...]
        }
        """

    async def prepare_db(self) -> None:
        pass

    async def get_or_create_user(self, **kwargs: tp.Any) -> User:
        """Get by outer_id or create user"""
        if "outer_id" not in kwargs:
            raise Exception("User without outer_id is illegal")
        outer_id = kwargs["outer_id"]
        if outer_id in self.users:
            return self.users[outer_id]
        else:
            user = User(
                outer_id=outer_id,
                nickname=kwargs.get("nickname"),
                name=kwargs.get("name"),
                surname=kwargs.get("surname"),
                patronymic=kwargs.get("patronymic"),
                current_scenario_name=kwargs.get("current_scenario_name"),
                current_node_id=kwargs.get("current_node_id"),
            )
            self.users[outer_id] = user
            return user

    async def update_user(self, user: User) -> User:
        """Update user context"""
        self.users[user.outer_id] = user
        return self.users[user.outer_id]

    async def update_user_context(
        self, user: User, ctx_to_update: tp.Dict[str, str]
    ) -> None:
        """Update user fields"""
        self.users_ctx[user.outer_id].update(ctx_to_update)

    async def get_user_context(self, user: User) -> tp.Dict[str, str]:
        """Get user context"""
        return self.users_ctx[user.outer_id]

    async def get_user_history(self, user: User) -> tp.List[tp.Dict[str, str]]:
        """Get user history of out messages"""
        return self.out_messages[user.outer_id]

    async def add_to_user_history(
        self, user: User, ids_pair: tp.Dict[str, str]
    ) -> None:
        """Get user history of out messages"""
        self.out_messages[user.outer_id].append(ids_pair)

    async def get_scenario_by_name(self, name: str, project_name: str) -> Scenario:
        """Get scenario by its name"""
        scenarios_for_project = self.projects[project_name]
        for sc in scenarios_for_project:
            if sc["name"] == name:
                need_scenario_json: tp.Dict[str, tp.Any] = sc["scenario"]  # type: ignore
                need_scenario: Scenario = Scenario.from_dict(need_scenario_json)
                return need_scenario
        raise Exception("Scenario was not found")

    async def add_scenario(self, scenario: Scenario, project_name: str) -> None:
        """Add scenario in repository"""
        self.projects[project_name].append({"name": scenario.name, "scenario": scenario.to_dict(), "texts": {}})  # type: ignore

    async def add_scenario_texts(
        self, scenario_name: str, project_name: str, texts: tp.Dict[str, str]
    ) -> None:
        """Add texts for templating scenario"""
        for scenario_dict in self.projects[project_name]:
            if scenario_dict["name"] == scenario_name:
                scenario_dict["texts"] = texts

    async def get_scenario_text(
        self, scenario_name: str, project_name: str, template_name: str
    ) -> str:
        """Return template value"""
        try:
            for scenario_dict in self.projects[project_name]:
                if scenario_dict["name"] == scenario_name:
                    return scenario_dict["texts"][template_name]  # type: ignore
        except KeyError:
            print(f"Error, template {template_name} not found")
            return template_name
        raise Exception("Scenario was not found")

    async def create_project(self, name: str) -> None:
        """Create project in db"""
        if name not in self.projects:
            self.projects[name] = []

    async def get_all_scenarios_metadata(self) -> tp.List[tp.Tuple[str, str]]:
        """Get all scenarios names and projects"""
        res = []
        for project, scenarios in self.projects.items():
            for scenario in scenarios:
                res.append(
                    (
                        project,
                        scenario["name"],
                    )
                )
        return res
