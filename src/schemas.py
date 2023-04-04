from marshmallow import Schema, EXCLUDE, fields as _fields, validates, ValidationError

from src.models import User


class ExcludeSchema(Schema):
    class Meta:
        unknown = EXCLUDE


class CoreSchema(ExcludeSchema):
    _id = _fields.String(required=False, allow_none=True)
    code = _fields.String(required=False, allow_none=True)
    name = _fields.String(required=False, allow_none=True)
    description = _fields.String(required=False, allow_none=True)
    value = _fields.String(required=False, allow_none=True)


class AddressResponseSchema(ExcludeSchema):
    street = _fields.String(required=True, allow_none=False)
    street_line_2 = _fields.String(required=False, allow_none=True)
    state = _fields.String(required=True, allow_none=False)
    country = _fields.String(required=True, allow_none=False)


class UserResponseSchema(ExcludeSchema):
    pk = _fields.String(required=False, allow_none=True)
    date_created = _fields.DateTime(required=False, allow_none=True)
    first_name = _fields.String(required=True, allow_none=False)
    last_name = _fields.String(required=True, allow_none=False)
    email = _fields.String(required=True, allow_none=False)


class RegistrationSchema(UserResponseSchema):
    password = _fields.String(required=True, allow_none=False)


class LoginSchema(ExcludeSchema):
    password = _fields.String(required=True, allow_none=False)
    email = _fields.String(required=True, allow_none=False)

    @validates("email")
    def validate_email(self, email):
        if not User.objects.raw({"email": email}).count():
            raise ValidationError(message="Invalid email", field_name="email")


class LoginResponseSchema(UserResponseSchema):
    auth_token = _fields.String(required=True, allow_none=False)


class ProductResponseSchema(ExcludeSchema):
    """

    """


class ProductRequestSchema(ExcludeSchema):
    """

    """
