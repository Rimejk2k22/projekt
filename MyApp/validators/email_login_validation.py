from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.utils.module_loading import import_string
from django.utils.translation import gettext as _
from MyApp import models as m


def get_login_email_validators(validator_config):
    validators = []
    for validator in validator_config:
        try:
            klass = import_string(validator["NAME"])
        except ImportError:
            msg = (
                "The module in NAME could not be imported: %s. Check your "
                "LOGIN_EMAIL_VALIDATORS setting."
            )
            raise ImproperlyConfigured(msg % validator["NAME"])
        validators.append(klass(**validator.get("OPTIONS", {})))

    return validators


def validate_login_email(username=None, email=None, user=None, login_email_validators=None):
    """
    Validate whether login or email meets all validator requirements.

    If the login or email in not in database, return "None".
    Otherwise, raise ValidationError with all error messages.
    """
    errors = []

    for validator in login_email_validators:
        try:
            validator.validate(username, email, user)
        except ValidationError as error:
            errors.append(error)
    if errors:
        raise ValidationError(errors)


class LoginExistsValidator:
    def validate(self, username=None, email=None, user=None):
        user = m.User.objects.all().filter(username=username)
        if user:
            raise ValidationError(
                _("Uzytkownik o podanej nazwie istnieje."),
                code="user_exists",
                params={'username': username}
            )


class LoginLengthValidator:
    def validate(self, username=None, email=None, user=None):
        if len(username) <= 2:
            raise ValidationError(
                _("Nazwa uzytkownika musi zawierac wiecej niz 2 znaki."),
                code="username_too_short",
                params={'username': username}
            )


class EmailExistsValidator:
    def validate(self, username=None, email=None, user=None):
        user = m.User.objects.all().filter(email=email)
        if user:
            raise ValidationError(
                _("Podany adres e-mail zostal juz uzyty w procesie rejestracji."),
                code="email_exists",
                params={'email': email}
            )