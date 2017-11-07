from re import compile as re_compile


def _get_regex_path_component():
    # see http://tools.ietf.org/html/rfc3986#section-3.3
    # path-abempty  = *( "/" segment )
    # segment       = *pchar
    # pchar         = unreserved / pct-encoded / sub-delims / ":" / "@"
    # pct-encoded = "%" HEXDIG HEXDIG
    # unreserved  = ALPHA / DIGIT / "-" / "." / "_" / "~"
    # sub-delims  = "!" / "$" / "&" / """ / "(" / ")" / "*" / "+" / "," / ";" /
    #               "="

    unreserved = r"[\w\.\-~]"
    pct_encoded = "%[A-Fa-f0-9][A-Fa-f0-9]"
    sub_delims = r"[!$&'()\*\+,;=]"

    pchar = "(?:" + unreserved + "|" + pct_encoded + "|" + sub_delims + "|:|@)"
    segment = pchar + "+"

    return segment


_sp_id = r'(//%s)?' % _get_regex_path_component()
_cse_id = r'(/%s)?' % _get_regex_path_component()
_path_suffix = r'(?:/?(%s(?:/%s)*))?' % (_get_regex_path_component(), _get_regex_path_component())

_onem2m_address_splitter = re_compile(r'^%s%s%s' % (_sp_id, _cse_id, _path_suffix))


def split_onem2m_address(onem2m_address):
    """

    :param str onem2m_address:
    :return: sp_id, cse_id, cse-relative rest
    """
    return _onem2m_address_splitter.findall(onem2m_address).pop()
