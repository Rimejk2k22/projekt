from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class PasswordEqualValidator:
    """Validate whether both password are identical."""

    @classmethod
    def validate(cls, password, password2, user=None):
        if password != password2:
            raise ValidationError(
                _("Hasla sie roznia."),
                code="passwords_vary"
            )

    def get_help_text(self):
        return _("Either password and confirmation has to be the same.")