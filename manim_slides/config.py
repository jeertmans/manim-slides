from typing import Optional, Set

from pydantic import BaseModel, root_validator, validator

from .defaults import LEFT_ARROW_KEY_CODE, RIGHT_ARROW_KEY_CODE


class Key(BaseModel):
    ids: Set[int]
    name: Optional[str] = None

    @validator("ids", each_item=True)
    def id_is_posint(cls, v: int):
        if v < 0:
            raise ValueError("Key ids cannot be negative integers")
        return v

    def match(self, key_id: int):
        return key_id in self.ids


class Config(BaseModel):
    QUIT: Key = Key(ids=[ord("q")], name="QUIT")
    CONTINUE: Key = Key(ids=[RIGHT_ARROW_KEY_CODE], name="CONTINUE / NEXT")
    BACK: Key = Key(ids=[LEFT_ARROW_KEY_CODE], name="BACK")
    REVERSE: Key = Key(ids=[ord("v")], name="REVERSE")
    REWIND: Key = Key(ids=[ord("r")], name="REWIND")
    PLAY_PAUSE: Key = Key(ids=[32], name="PLAY / PAUSE")

    @root_validator
    def ids_are_unique_across_keys(cls, values):
        ids = set()

        for key in values.values():
            if len(ids.intersection(key.ids)) != 0:
                raise ValueError(
                    "Two or more keys share a common key code: please make sure each key has distinc key codes"
                )
            ids.update(key.ids)

        return values

    def merge_with(self, other: "Config") -> "Config":
        for key_name, key in self:
            other_key = getattr(other, key_name)
            key.ids.update(other_key.ids)
            key.name = other_key.name or key.name

        return self
