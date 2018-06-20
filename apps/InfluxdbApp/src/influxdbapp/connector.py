# -*- coding: utf-8 -*-

from influxdb import InfluxDBClient


class InfluxDBConnector:

    def __init__(
            self,
            host='localhost',
            port=8086,
            user='root',
            password='root',
            dbname='example',
            dbuser='test',
            dbuser_pw='test'):

        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.dbname = dbname
        self.dbuser = dbuser
        self.dbuser_pw = dbuser_pw
        self.client = InfluxDBClient(host, port, user, password, dbname)
        self.client.create_database(dbname)

    def update(
            self,
            cnt_senml,
            application_name,
            device_name,
            device_labels,
            sensor_name,
            sensor_labels):

        cnt_senml = cnt_senml
        json_body = [
            {
                "measurement": cnt_senml["n"],
                "tags": {
                    "application_name": application_name,
                    "device_name": device_name,
                    "device_labels": ";".join(device_labels),
                    "sensor_name": sensor_name,
                    "sensor_labels": ";".join(sensor_labels)
                },
                "time": int(cnt_senml["t"]),
                "fields": {
                    "value": cnt_senml["v"],
                    "bn": cnt_senml["bn"],
                    "unit": cnt_senml["u"]
                }
            }
        ]

        self.client.write_points(json_body, time_precision="s")
