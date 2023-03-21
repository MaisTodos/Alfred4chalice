from datetime import date

from marshmallow import ValidationError, fields


class BirthDateField(fields.Date):
    def _deserialize(self, value, attr, data, **kwargs):
        value = super()._deserialize(value, attr, data, **kwargs)

        today = date.today()
        verify_age = (
            today.year
            - value.year
            - ((today.month, today.day) < (value.month, value.day))
        )

        if verify_age < self.min_age:
            raise ValidationError(self.error_messages["below_min_error_msg"])

        if verify_age > self.max_age:
            raise ValidationError(self.error_messages["above_max_error_msg"])

        return value

    def __init__(
        self,
        min_age,
        max_age,
        above_max_error_msg="Data de nascimento não permitida.",
        below_min_error_msg="Usuário não possui idade mínima.",
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.min_age = min_age
        self.max_age = max_age
        self.error_messages["above_max_error_msg"] = above_max_error_msg
        self.error_messages["below_min_error_msg"] = below_min_error_msg
