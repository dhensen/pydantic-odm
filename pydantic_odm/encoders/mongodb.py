"""Encoders for MongoDB"""
from __future__ import annotations

import abc
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, List, Union, cast
from decimal import Decimal
from bson.decimal128 import Decimal128

if TYPE_CHECKING:
    from pydantic.typing import DictStrAny


class AbstractMongoDBEncoder(abc.ABC):
    """Abstract MongoDB encoder"""

    @abc.abstractmethod
    def __call__(self, data: "DictStrAny") -> "DictStrAny":
        """Convert data from pydantic model or dict to dict supported MongoDB"""
        raise NotImplementedError()


def _recursive_iterator(
    data: Union["DictStrAny", List[Any]], transform_func
) -> Union["DictStrAny", List[Any]]:
    # Cast append func type
    append: Callable[[Union[str, int], Any], None]
    # Convert in list
    data = cast(List[Any], data)  # noqa
    _data = []
    iterator = enumerate(data)
    append = lambda k, v: _data.append(v)  # noqa: E731
    # Convert in dict
    if isinstance(data, dict):
        data = cast("DictStrAny", data)
        iterator = data.items()
        _data = {}
        append = lambda k, v: _data.update({k: v})  # noqa: E731
    # Iterate passed data
    for key, value in iterator:
        # Replace enum object to enum value
        value = transform_func(value)
        # Recursive call if find sequence
        if isinstance(value, (list, dict)):
            value = _recursive_iterator(value, transform_func)
        # Update new data with update method (append for list and update for dict)
        append(key, value)
    # Return new data
    return _data


def _convert_enums(
    data: Union["DictStrAny", List[Any]]
) -> Union["DictStrAny", List[Any]]:
    """
    Convert Enum to Enum.value for mongo query

    Note: May be this solution not good
    """

    def transform(value):
        if isinstance(value, Enum):
            value = value.value
        return value

    return _recursive_iterator(data, transform)


def _convert_decimals(
    data: Union["DictStrAny", List[Any]]
) -> Union["DictStrAny", List[Any]]:
    """
    Convert decimal.Decimal to bson.decimal128.Decimal128
    """

    def transform(value):
        if isinstance(value, Decimal):
            value = Decimal128(value)
        return value

    return _recursive_iterator(data, transform)


class BaseMongoDBEncoder(AbstractMongoDBEncoder):
    """Base MongoDB encoder"""

    def __call__(self, data: "DictStrAny") -> "DictStrAny":
        data = cast("DictStrAny", _convert_enums(data))
        return data
