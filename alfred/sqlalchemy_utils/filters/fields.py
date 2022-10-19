from datetime import date, timedelta

from marshmallow import fields


class FilterFieldMixin:
    filter_type = "sqlalchemy.and_"

    def _deserialize(self, value, attr, data, **kwargs):
        value = super()._deserialize(value, attr, data, **kwargs)
        field_name = self.field_name or attr

        return {
            "model": self.model,
            "field_name": field_name,
            "op": self.op,
            "value": value,
            "filter_type": self.filter_type,
        }

    def __init__(self, model, op, field_name=None, *args, **kwargs):
        self.model = model
        self.op = op
        self.field_name = field_name
        super().__init__(*args, **kwargs)


class StringFilterField(FilterFieldMixin, fields.String):
    pass


class DateFilterField(FilterFieldMixin, fields.Date):
    pass


class DateTimeFilterField(FilterFieldMixin, fields.DateTime):
    pass


class ListFilterField(FilterFieldMixin, fields.List):
    def _deserialize(self, value, attr, data, **kwargs):
        if value == []:
            return None
        return super()._deserialize(value, attr, data, **kwargs)


class LogicalFilterField(ListFilterField):
    filter_type = "sqlalchemy.or_"


class BooleanFilterField(FilterFieldMixin, fields.Boolean):
    pass


class TimePeriodFilterField(FilterFieldMixin, fields.Integer):
    def _deserialize(self, value, attr, data, **kwargs):
        data = super()._deserialize(value, attr, data, **kwargs)

        today = date.today()
        time_period_start = today - timedelta(days=data["value"])

        data["value"] = time_period_start

        return data

    def __init__(self, model, field_name=None, *args, **kwargs):
        super().__init__(model, ">=", field_name, *args, **kwargs)
