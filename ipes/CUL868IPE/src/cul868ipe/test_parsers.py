from .parsers import S300THParser, EM1000EMParser, FS20Parser


def test_parsers():
    # ('1', S300THData(temperature=22.5, humidity=31.3))
    sensor_id, data = (S300THParser()("K01253231"))
    assert sensor_id == '1'
    assert data.temperature == 22.5
    assert data.humidity == 31.3

    # ('1', S300THData(temperature=29.7, humidity=38.6))
    sensor_id, data = (S300THParser()("K01976238"))
    assert sensor_id == '1'
    assert data.temperature == 29.7
    assert data.humidity == 38.6

    # ('5', S300THData(temperature=27.1, humidity=38.4))
    sensor_id, data = (S300THParser()("K41714238"))
    assert sensor_id == '5'
    assert data.temperature == 27.1
    assert data.humidity == 38.4

    # ('6', EM1000EMData(counter=95, cumulated=0.257, last=30, top=60))
    sensor_id, data = (EM1000EMParser()("E02065F010103000600"))
    assert sensor_id == '6'
    assert data.counter == 95
    assert data.cumulated == 0.257
    assert data.last == 30
    assert data.top == 60

    # ('6', EM1000EMData(counter=96, cumulated=0.26, last=30, top=60))
    sensor_id, data = (EM1000EMParser()("E020660040103000600"))
    assert sensor_id == '6'
    assert data.counter == 96
    assert data.cumulated == 0.26
    assert data.last == 30
    assert data.top == 60

    # ('6', EM1000EMData(counter=97, cumulated=0.263, last=30, top=60))
    sensor_id, data = (EM1000EMParser()("E020661070103000600"))
    assert sensor_id == '6'
    assert data.counter == 97
    assert data.cumulated == 0.263
    assert data.last == 30
    assert data.top == 60

    # ('6', EM1000EMData(counter=98, cumulated=0.266, last=30, top=50))
    sensor_id, data = (EM1000EMParser()("E0206620A0103000500"))
    assert sensor_id == '6'
    assert data.counter == 98
    assert data.cumulated == 0.266
    assert data.last == 30
    assert data.top == 50

    # ('11111112-1414', FS20Data(command='14', duration='3321'))
    sensor_id, data = (FS20Parser()("F0001333A4F"))
    assert sensor_id == '11111112-1414'
    assert data.command == '14'
    assert data.duration == '3321'

    # ('11111112-1111', FS20Data(command='11', duration=''))
    sensor_id, data = (FS20Parser()("F00010000"))
    assert sensor_id == '11111112-1111'
    assert data.command == '11'
    assert data.duration == ''

    # ('22222222-1211', FS20Data(command='14', duration='3321'))
    sensor_id, data = (FS20Parser()("F5555103A4F"))
    assert sensor_id == '22222222-1211'
    assert data.command == '14'
    assert data.duration == '3321'

    # ('11111112-1212', FS20Data(command='14', duration='3321'))
    sensor_id, data = (FS20Parser()("F0001113A4F"))
    assert sensor_id == '11111112-1212'
    assert data.command == '14'
    assert data.duration == '3321'

    # ('11111112-4343', FS20Data(command='14', duration='3321'))
    sensor_id, data = (FS20Parser()("F0001EE3A4F"))
    assert sensor_id == '11111112-4343'
    assert data.command == '14'
    assert data.duration == '3321'

    # ('11111112-4444', FS20Data(command='14', duration='3321'))
    sensor_id, data = (FS20Parser()("F0001FF3A4F"))
    assert sensor_id == '11111112-4444'
    assert data.command == '14'
    assert data.duration == '3321'
