from openmtc_app.onem2m import XAE


class SimpleDecision2(XAE):
    remove_registration = True
    sensor = "onem2m/zigbeeipe-0/devices/ZBS122009491/sensor_data/brightness"
    actuator = "onem2m/cul868ipe-0/FS20_ST3_16108_1/Switch"

    def _on_register(self):

        def handle_brightness(container, content):
            command = "ON" if content[0]['v'] < 100.0 else "OFF"
            self.push_content(self.actuator, command)

        self.add_container_subscription(self.sensor, handle_brightness)


if __name__ == "__main__":
    from openmtc_app.flask_runner import SimpleFlaskRunner as Runner

    ep = "http://localhost:8000"
    Runner(SimpleDecision2(poas=['http://localhost:21387'])).run(ep)
