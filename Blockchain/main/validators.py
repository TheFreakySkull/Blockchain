from django.core.exceptions import ValidationError

def validate_positive(value):
    if value <= 0:
        raise ValidationError('%(value)s is not positive',
                              params={'value': value})
