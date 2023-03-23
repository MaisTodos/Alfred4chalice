import pytest
from marshmallow import ValidationError, fields

from alfred.marshmallow_utils.fields.required_length_string import (
    RequiredLengthStringField,
)


def test_required_length_string_is_subclass():
    assert issubclass(RequiredLengthStringField, fields.String)


def test_required_length_string_invalid_default_message():
    name = ""
    field = RequiredLengthStringField()

    with pytest.raises(ValidationError) as err:
        field._deserialize(name, "name", {"name": name})

    assert err.value.args[0] == "Shorter than minimum length 1"


def test_required_length_string_invalid_custom_message():
    err_msg = "Necessário no minimo 1 caracter"
    name = ""
    field = RequiredLengthStringField(length_error_msg=err_msg)

    with pytest.raises(ValidationError) as err:
        field._deserialize(name, "name", {"name": name})

    assert err.value.args[0] == err_msg


def test_required_length_string_invalid_min_value():
    name = ""
    field = RequiredLengthStringField(min_length=2)

    with pytest.raises(ValidationError) as err:
        field._deserialize(name, "name", {"name": name})

    assert err.value.args[0] == "Shorter than minimum length 2"


def test_required_length_string_valid():
    field = RequiredLengthStringField()
    name = "A"

    value = field._deserialize(name, "name", {"name": name})

    assert value == name
