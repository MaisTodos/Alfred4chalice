import pytest
from marshmallow import ValidationError, fields

from alfred.marshmallow_utils.fields.string_length_field import StringLengthField


def test_string_field_is_subclass():
    assert issubclass(StringLengthField, fields.String)


def test_string_field_invalid_default_message():
    name = ""
    field = StringLengthField()

    with pytest.raises(ValidationError) as err:
        field._deserialize(name, "name", {"name": name})

    assert err.value.args[0] == "Shorter than minimum length 1"


def test_string_field_invalid_custom_message():
    err_msg = "Necessário no minimo 1 caracter"
    name = ""
    field = StringLengthField(error_msg=err_msg)

    with pytest.raises(ValidationError) as err:
        field._deserialize(name, "name", {"name": name})

    assert err.value.args[0] == err_msg


def test_string_field_valid():
    field = StringLengthField()
    name = "A"

    value = field._deserialize(name, "name", {"name": name})

    assert value == name
