from marshmallow import ValidationError, fields


class RequiredLengthStringField(fields.String):
    def _deserialize(self, value, attr, data, **kwargs):
        value = super()._deserialize(value, attr, data, **kwargs)
        min_length = 1

        if len(value) < min_length:
            raise ValidationError(self.error_messages["length_error_msg"])

        return value

    def __init__(self, min_length=1, length_error_msg=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.min_length = min_length
        self.error_messages["length_error_msg"] = (
            length_error_msg or f"Shorter than minimum length {min_length}"
        )
