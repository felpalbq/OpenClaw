import os
import sys
from abc import ABC, abstractmethod
from datetime import datetime

ROOT = str(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from state import read_state, write_state, merge_state


class BaseModule(ABC):
    name: str = ""
    display_name: str = ""
    llm_tier: str = "production"
    cron_interval: int = 600
    skills: list = []

    @abstractmethod
    def condition(self, state: dict) -> bool:
        pass

    @abstractmethod
    def act(self, state: dict, context: dict = None) -> dict:
        pass

    def write_result(self, result: dict, state: dict = None):
        merge_state({
            "modules": {
                self.name: {
                    "last_result": result,
                    "last_act_at": datetime.now().isoformat()
                }
            }
        }, agent=self.name, reason="module_act")

    def couple(self, state: dict = None):
        merge_state({
            "modules": {
                self.name: {
                    "status": "active",
                    "display_name": self.display_name,
                    "llm_tier": self.llm_tier,
                    "cron_interval": self.cron_interval,
                    "skills": self.skills,
                    "coupled_at": datetime.now().isoformat(),
                    "last_act_at": "",
                    "last_result": {},
                }
            }
        }, agent="ahri", reason=f"couple_{self.name}")

    def decouple(self, state: dict = None):
        merge_state({
            "modules": {
                self.name: {
                    "status": "inactive",
                    "decoupled_at": datetime.now().isoformat()
                }
            }
        }, agent="ahri", reason=f"decouple_{self.name}")

    def is_active(self, state: dict = None) -> bool:
        if state is None:
            state = read_state()

        mod = state.get("modules", {}).get(self.name, {})
        return mod.get("status") == "active"

    def run_cycle(self, state: dict = None):
        if state is None:
            state = read_state()

        if not self.is_active(state):
            return None

        if self.condition(state):
            result = self.act(state)
            self.write_result(result, state)
            return result

        return None


def list_active_modules(state: dict = None) -> list:
    if state is None:
        state = read_state()

    modules = state.get("modules", {})
    active = []
    for name, info in modules.items():
        if isinstance(info, dict) and info.get("status") == "active":
            active.append({
                "name": name,
                "display_name": info.get("display_name", name),
                "coupled_at": info.get("coupled_at", ""),
            })
    return active


def couple_module(module: BaseModule, state: dict = None):
    module.couple(state)


def decouple_module(module: BaseModule, state: dict = None):
    module.decouple(state)