"""
JobFlags module.

Provides the base JobFlags dataclass used across Lorenzetti for unified,
typed, and serializable configuration and steering flags.
"""

from dataclasses import dataclass, fields, field, is_dataclass
from typing import Dict, Any, Type, TypeVar
import json

__all__ = ["JobFlags"]

T = TypeVar("T", bound="JobFlags")


@dataclass
class JobFlags:
    """
    Base configuration dataclass for Lorenzetti steering flags.

    Features:
    - Supports class-level steering (e.g. via --pre-init "Flags.Param = value").
    - Supports explicit instance creation (e.g. flags = Flags(Param=value)).
    - Provides dictionary and JSON export/import for --job-file.
    - Provides reset() to restore default values between test/job runs.
    """

    def __init__(self, **kwargs):
        for f in fields(self):
            val = kwargs.get(f.name, getattr(self.__class__, f.name, f.default))
            setattr(self, f.name, val)

    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """Returns the current flag values as a dictionary."""
        return {f.name: getattr(cls, f.name) for f in fields(cls)}

    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """Instantiates a flags object from a dictionary, ignoring unknown keys."""
        valid_keys = {f.name for f in fields(cls)}
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)

    @classmethod
    def reset(cls) -> None:
        """Resets all class-level attributes to their declared dataclass defaults."""
        for f in fields(cls):
            if f.default is not field:
                setattr(cls, f.name, f.default)

    @classmethod
    def to_json(cls, indent: int = 2) -> str:
        """Serializes flags to a formatted JSON string."""
        return json.dumps(cls.to_dict(), indent=indent)

    @classmethod
    def from_json(cls, json_str: str) -> None:
        """Updates class-level attributes from a JSON string."""
        data = json.loads(json_str)
        for k, v in data.items():
            if hasattr(cls, k):
                setattr(cls, k, v)

    def __repr__(self) -> str:
        cls_name = self.__class__.__name__
        items = [f"{f.name}={getattr(self, f.name)!r}" for f in fields(self)]
        return f"{cls_name}({', '.join(items)})"
