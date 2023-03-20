from marshmallow import ValidationError, fields
from datetime import date



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
            raise ValidationError(self.error_messages["birth_date_error_msg"])
        
        if verify_age > self.max_age:
            raise ValidationError(self.error_messages["birth_date_error_msg"])

    def __init__(
        self,
        min_age,
        max_age,
        birth_date_error_msg="Data de nascimento inválida",
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.min_age = min_age
        self.max_age = max_age
        self.error_messages["birth_date_error_msg"] = birth_date_error_msg
