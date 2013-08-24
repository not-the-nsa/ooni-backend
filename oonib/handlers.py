import types

from cyclone import escape
from cyclone import web

class OONIBHandler(web.RequestHandler):
    def write(self, chunk):
        """
        This is a monkey patch to RequestHandler to allow us to serialize also
        json list objects.
        """
        if isinstance(chunk, types.ListType):
            chunk = escape.json_encode(chunk)
            web.RequestHandler.write(self, chunk)
            self.set_header("Content-Type", "application/json")
        else:
            web.RequestHandler.write(self, chunk)

    def write_error(self, status_code, **kwargs):
        #XXX: handle all custom error codes
        if status_code == 406:
            e = kwargs['exception']
            response = {
                'backend_version': e.backend_version,
                'report_status': e.report_status,
                'test_helper_address': e.test_helper_address
                }
            self.write(response)
        else:
            web.RequestHandler.write_error(self, status_code, **kwargs)
