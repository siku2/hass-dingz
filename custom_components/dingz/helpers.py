import abc
from typing import Any, cast

from homeassistant.helpers.entity import Entity


def compile_json_path(raw: str) -> list[str | int]:
    path = cast(list[str | int], raw.split("."))
    for i, seg in enumerate(path):
        if isinstance(seg, str) and seg.isdigit():
            path[i] = int(seg)
    return path


def json_path_lookup(value: Any, path: list[str | int]) -> Any | None:
    try:
        for key in path:
            value = value[key]
    except LookupError:
        return None
    return value


class UserAssignedNameMixin(Entity, abc.ABC):
    @property
    @abc.abstractmethod
    def comp_index(self) -> int:
        ...

    @property
    @abc.abstractmethod
    def user_given_name(self) -> str | None:
        ...

    @property
    def name(self) -> str | None:
        tr_key = self._name_translation_key
        if tr_key is None:
            return None

        name = self.user_given_name
        if not name:
            tr_key += "_fallback"

        tr_fmt: str | None = self.platform.platform_translations.get(tr_key)
        if tr_fmt is None:
            return None
        return tr_fmt.format(name=name, position=self.comp_index + 1)
