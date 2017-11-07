import string

letters_digits_underscore = string.letters + string.digits + "_"


class InvalidIdentifier(ValueError):
    pass


def is_identifier(s):
    if not s or s[0] not in string.letters:
        return False

    for c in s:
        if c not in letters_digits_underscore:
            return False

    return True


def check_identifier(s):
    if not is_identifier(s):
        raise InvalidIdentifier(s)
