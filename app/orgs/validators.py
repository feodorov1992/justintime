from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible


@deconstructible
class NumericStringValidator:

    def __init__(self, field_label: str, allowed_lengths: list):
        self.field_label = field_label
        self.allowed_lengths = sorted(allowed_lengths)

    def allowed_lengths_as_string(self):
        if not self.allowed_lengths:
            raise AttributeError(
                f'allowed_lengths must not be empty!'
            )
        result = list()
        if len(self.allowed_lengths) > 1:
            result.append(', '.join([str(i) for i in self.allowed_lengths[:-1]]))
        result.append(str(self.allowed_lengths[-1]))
        return ' или '.join(result)

    def __call__(self, value):
        if not value.isnumeric() or len(value) not in self.allowed_lengths:
            raise ValidationError(
                f'{self.field_label} должен состоять из {self.allowed_lengths_as_string()} цифр!',
                params={'value': value},
            )

    def __eq__(self, other):
        return (
            isinstance(other, NumericStringValidator)
            and self.field_label == other.field_label
            and self.allowed_lengths == other.allowed_lengths
        )
