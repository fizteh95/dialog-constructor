from abc import ABC, abstractmethod
import typing as tp

from src.adapters.repository import AbstractRepo
from src.domain.model import Scenario


class AbstractScenarioGetter(ABC):
    def __init__(self, repo: AbstractRepo) -> None:
        self.repo = repo

    @abstractmethod
    async def find(self, name: str) -> Scenario:
        """return self.scenarios[name]"""


class ScenarioGetter(AbstractScenarioGetter):
    def __init__(self, repo: AbstractRepo) -> None:
        super().__init__(repo=repo)

    async def find(self, name: str) -> Scenario:
        scenario = await self.repo.get_scenario_by_name(name)
