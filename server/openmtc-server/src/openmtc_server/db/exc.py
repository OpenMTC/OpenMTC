from openmtc.exc import OpenMTCError


class DBError(OpenMTCError):
    status_code = 500

    @property
    def statusCode(self):
        return self.status_code


class DBConflict(DBError):
    status_code = 409


class DBNotFound(DBError):
    status_code = 404
