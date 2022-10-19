import datetime
from datetime import date, timedelta

from marshmallow import fields

from alfred.auth.models import BasicAuthUser
from alfred.sqlalchemy_utils.filters.fields import (
    BooleanFilterField,
    DateFilterField,
    DateTimeFilterField,
    FilterFieldMixin,
    ListFilterField,
    LogicalFilterField,
    StringFilterField,
    TimePeriodFilterField,
)


def test_stringfilter_is_subclass():
    assert issubclass(StringFilterField, fields.String)
    assert issubclass(StringFilterField, FilterFieldMixin)


def test_stringfilter_success():
    field = StringFilterField(model=BasicAuthUser, op="==")
    document = "12309845687"

    value = field._deserialize(document, "document", {"document": document})

    assert value == {
        "model": BasicAuthUser,
        "field_name": "document",
        "filter_type": "sqlalchemy.and_",
        "op": "==",
        "value": "12309845687",
    }


def test_datefilter_is_subclass():
    assert issubclass(DateFilterField, fields.Date)
    assert issubclass(DateFilterField, FilterFieldMixin)


def test_datefilter_success():
    field = DateFilterField(
        model=BasicAuthUser,
        field_name="created_at",
        op=">=",
    )
    created_at_start = "2022-05-10"

    value = field._deserialize(
        created_at_start, "created_at_start", {"created_at_start": created_at_start}
    )

    assert value == {
        "model": BasicAuthUser,
        "field_name": "created_at",
        "filter_type": "sqlalchemy.and_",
        "op": ">=",
        "value": datetime.date(2022, 5, 10),
    }


def test_datetimefilter_is_subclass():
    assert issubclass(DateTimeFilterField, fields.DateTime)
    assert issubclass(DateTimeFilterField, FilterFieldMixin)


def test_datetimefilter_success():
    field = DateTimeFilterField(
        model=BasicAuthUser,
        field_name="created_at",
        op=">=",
    )
    created_at_start = "2022-05-10 00:00:01"

    value = field._deserialize(
        created_at_start, "created_at_start", {"created_at_start": created_at_start}
    )

    assert value == {
        "model": BasicAuthUser,
        "field_name": "created_at",
        "filter_type": "sqlalchemy.and_",
        "op": ">=",
        "value": datetime.datetime(2022, 5, 10, 00, 00, 1),
    }


def test_listfilter_is_subclass():
    assert issubclass(ListFilterField, fields.List)
    assert issubclass(ListFilterField, FilterFieldMixin)


def test_listfilter_sucess_empty():
    field = ListFilterField(model=BasicAuthUser, op="in", cls_or_instance=fields.Str())
    document = "12309845687"
    value = field._deserialize([], "document", {"document": document})

    assert value is None


def test_listfilter_sucess_not_empty():
    field = ListFilterField(model=BasicAuthUser, op="in", cls_or_instance=fields.Str())
    document = "12309845687"
    value = field._deserialize([document], "document", {"document": document})

    assert value == {
        "model": BasicAuthUser,
        "field_name": "document",
        "op": "in",
        "value": ["12309845687"],
        "filter_type": "sqlalchemy.and_",
    }


def test_logicalfilter_is_subclass():
    assert issubclass(LogicalFilterField, ListFilterField)


def test_logicalfilter_type():
    field = LogicalFilterField(
        model=BasicAuthUser, op="in", cls_or_instance=fields.Str()
    )
    document = "12309845687"
    value = field._deserialize([document], "document", {"document": document})

    assert value == {
        "model": BasicAuthUser,
        "field_name": "document",
        "op": "in",
        "value": ["12309845687"],
        "filter_type": "sqlalchemy.or_",
    }


def test_boolean_filter_field_is_subclass():
    assert issubclass(BooleanFilterField, FilterFieldMixin)
    assert issubclass(BooleanFilterField, fields.Boolean)


def test_boolean_filter_field_type():
    field = BooleanFilterField(
        model=BasicAuthUser,
        op="==",
    )
    is_active = True
    value = field._deserialize(is_active, "is_active", {"field_value": True})

    assert value == {
        "model": BasicAuthUser,
        "field_name": "is_active",
        "op": "==",
        "value": True,
        "filter_type": "sqlalchemy.and_",
    }


def test_time_period_filter_field_is_subclass():
    assert issubclass(TimePeriodFilterField, FilterFieldMixin)
    assert issubclass(TimePeriodFilterField, fields.Integer)


def test_time_period_filter_field_type():
    field = TimePeriodFilterField(model=BasicAuthUser)
    time_period = 7
    value = field._deserialize(time_period, "time_period", {"time_period": time_period})

    assert value == {
        "model": BasicAuthUser,
        "field_name": "time_period",
        "op": ">=",
        "value": date.today() - timedelta(days=time_period),
        "filter_type": "sqlalchemy.and_",
    }
