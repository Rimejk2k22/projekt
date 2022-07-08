from django.utils.translation import gettext as _


class DeliveryOfferValidator:
    """Validate DeliveryOffer form."""

    @classmethod
    def validate(cls, required_fields):
        # del required_fields['csrfmiddlewaretoken']
        del required_fields['description']
        del required_fields['extras']

        errors = []
        blank_field = False
        for field, *value in required_fields.items():

            if value[0][0]:
                if field == 'wage':
                    try:
                        value = float(*value[0])
                    except ValueError:
                        errors.append('Podaj poprawną cenę.')

                    if '.' in str(value):
                        value = str(value)
                        decimnal_place = value.index('.')
                        if len(value[decimnal_place + 1:]) > 2:
                            errors.append(
                                'Podaj poprawny format ceny (Max 2 cyfry po przecinku).'
                            )

                if field == 'distance':
                    try:
                        value = float(*value[0])
                    except ValueError:
                        errors.append('Podaj poprawny dystans.')

                    if '.' in str(value):
                        value = str(value)
                        decimnal_place = value.index('.')
                        if len(value[decimnal_place + 1:]) > 3:
                            errors.append(
                                'Podaj poprawny format dystansu (Max 3 cyfry po przecinku).'
                            )

                if field == 'street_from_number' or field == 'street_to_number':
                    try:
                        int(*value[0])
                    except ValueError:
                        errors.append('Podaj poprawny numer budynku.')

            else:
                blank_field = True

        if blank_field:
            errors.append('Wypełnij wszystkie wymagane pola.')

        return errors

    def get_help_text(self):
        return _("Check if form is valid.")
