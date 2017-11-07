from openmtc_server.Event import ResourceTreeEvent, BasicEvent


class NetworkEvent(BasicEvent):
    def __init__(self, run_task):
        super(NetworkEvent, self).__init__()

        self._run_task = run_task

    def _execute_handler(self, data, *event_data):
        self._run_task(super(NetworkEvent, self)._execute_handler, data,
                       *event_data)


class ResourceFinishEvent(ResourceTreeEvent):
    def __init__(self, run_task):
        super(ResourceFinishEvent, self).__init__()

        self._run_task = run_task

    def _execute_handler(self, data, *event_data):
        self._run_task(super(ResourceFinishEvent, self)._execute_handler, data,
                       *event_data)

    def fire(self, resource, req):
        self._fired(type(resource), resource, req)
