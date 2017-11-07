# notes:
# - added base structure


from openmtc_app.onem2m import XAE


class TestIPE(XAE):
    remove_registration = True

    def _on_register(self):
        # log message
        self.logger.debug('registered')


if __name__ == '__main__':
    from openmtc_app.runner import AppRunner as Runner

    host = 'http://localhost:8000'
    app = TestIPE()
    Runner(app).run(host)
