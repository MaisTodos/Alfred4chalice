from marshmallow import ValidationError, fields


class StringLengthField(fields.String):
    def _deserialize(self, value, attr, data, **kwargs):
        value = super()._deserialize(value, attr, data, **kwargs)
        min_length = 1

        if len(value) < min_length:
            raise ValidationError(self.error_messages["document_error_msg"])

        return value

    def __init__(self, error_msg="Shorter than minimum length 1", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.error_messages["document_error_msg"] = error_msg
