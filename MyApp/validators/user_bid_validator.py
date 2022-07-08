class UserBidValidator:
    """Validate User Bid."""

    @classmethod
    def validate(cls, bid):
        errors = []
        if bid:
            try:
                float(bid)
            except ValueError:
                errors.append('Podaj liczbę.')

            if '.' in str(bid):
                bid = str(bid)
                decimnal_place = bid.index('.')
                if len(bid[decimnal_place + 1:]) > 2:
                    errors.append(
                        'Podaj poprawny format oferty (Max 2 cyfry po przecinku).'
                    )
        else:
            errors.append('Podaj swoją ofertę.')

        return errors