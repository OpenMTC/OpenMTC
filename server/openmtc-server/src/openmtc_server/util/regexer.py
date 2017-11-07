"""
Created to generate semantically closed regular expressions.
"""


def capturing_group(name):
    return _group(name)


def not_capturing_group(name, negated=False):
    if not negated:
        return _group("?:" + name)
    else:
        return _group("?!" + name)


def _group(name):
    return "(" + name + ")"


def zero_plus_elem(name):
    return name + "*"


def one_plus_elem(name):
    return name + "+"


def zero_or_one_elem(name):
    return name + "?"


def negate(name):
    return "!" + name


def slash(name):
    return "/" + name


def alternative(names):
    return "|".join(names)


"""
@deprecated:
"""


def test_route_regex(route):
    result = route.regex.match('/m2m/applications/myApp/test')
    print(result.groups())
    result = route.regex.match('/m2m/applications/myApp/')
    print(result.groups())
    result = route.regex.match('/m2m/applications/myApp')
    print(result.groups())
    exit()
