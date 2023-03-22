import datetime

import pytest
from marshmallow import ValidationError, fields

from alfred.marshmallow_utils.fields.birth_date import BirthDateField


def test_birth_date_is_subclass():
    assert issubclass(BirthDateField, fields.Date)


@pytest.mark.parametrize(
    "birth_date, error_message",
    [
        ("2022-08-03", "Usuário não possui idade mínima."),
        ("1900-08-03", "Data de nascimento não permitida."),
    ],
)
def test_birth_date_invalid_default_message(birth_date, error_message):
    field = BirthDateField(min_age=16, max_age=80)

    with pytest.raises(ValidationError) as err:
        field._deserialize(birth_date, "birth_date", {"birth_date": birth_date})

    assert err.value.args[0] == error_message


def test_birth_date_success():
    field = BirthDateField(min_age=16, max_age=80)
    birth_date = "1998-08-03"

    value = field._deserialize(birth_date, "birth_date", {"birth_date": birth_date})

    assert value == datetime.date(1998, 8, 3)
