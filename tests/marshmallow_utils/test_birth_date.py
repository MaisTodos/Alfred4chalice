import pytest
from marshmallow import ValidationError, fields

from alfred.marshmallow_utils.fields.birth_date import BirthDateField


def test_birth_date_is_subclass():
    assert issubclass(BirthDateField, fields.Date)


def test_birth_date_invalid_min_age_default_message():
    field = BirthDateField(min_age=16, max_age=80)
    birth_date = "2022-08-03"
    with pytest.raises(ValidationError) as err:
        field._deserialize(birth_date, "birth_date", {"birth_date": birth_date})

    assert err.value.args[0] == "Data de nascimento inválida"


def test_birth_date_invalid_max_age_default_message():
    field = BirthDateField(min_age=16, max_age=80)
    birth_date = "1900-08-03"
    with pytest.raises(ValidationError) as err:
        field._deserialize(birth_date, "birth_date", {"birth_date": birth_date})

    assert err.value.args[0] == "Data de nascimento inválida"

