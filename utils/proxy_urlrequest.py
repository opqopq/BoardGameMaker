__author__ = 'Olivier POYEN'
''''
Url Request with proxy support.
So far, prxy is hard coded at the beginning of the module
'''

PROXY_NAME = '10.120.1.1' #as string like '10.120.50.60'
PROXY_PORT = 8080

from kivy.network.urlrequest import UrlRequest, urlparse

class UrlRequest(UrlRequest):

    def __init__(self, url, on_success=None, on_redirect=None,
                 on_failure=None, on_error=None, on_progress=None,
                 req_body=None, req_headers=None, chunk_size=8192,
                 timeout=None, method=None, decode=True, debug=False,
                 file_path=None, use_proxy= False):
        self._useproxy = use_proxy
        super(UrlRequest, self).__init__( url, on_success, on_redirect,on_failure, on_error, on_progress,req_body, req_headers, chunk_size,timeout, method, decode, debug, file_path)

    def _fetch_url(self, url, body, headers, q):
        # Parse and fetch the current url
        trigger = self._trigger_result
        chunk_size = self._chunk_size
        report_progress = self.on_progress is not None
        timeout = self._timeout
        file_path = self.file_path
        # parse url
        parse = urlparse(url)

        # translate scheme to connection class
        cls = self.get_connection_for_scheme(parse.scheme)

        # correctly determine host/port
        port = None
        host = parse.netloc.split(':')
        if len(host) > 1:
            port = int(host[1])
        host = host[0]

        # create connection instance
        args = {}
        if timeout is not None:
            args['timeout'] = timeout

        if self._useproxy:
            req = cls(PROXY_NAME,PROXY_PORT)
        else:
            req = cls(host, port, **args)

        # reconstruct path to pass on the request
        path = parse.path
        if parse.params:
            path += ';' + parse.params
        if parse.query:
            path += '?' + parse.query
        if parse.fragment:
            path += '#' + parse.fragment

        # send request
        method = self._method
        if method is None:
            method = 'GET' if body is None else 'POST'

        #OPO Magic - insert a proxy
        if self._useproxy:
            from kivy.logger import Logger
            Logger.info('Url Request made using proxy to %s/%s'%(host,path))
            req.request(method, '%s://%s/%s'%(parse.scheme,host,path), body, headers or {})
        else:
            req.request(method, path, body, headers or {})
        # read header
        resp = req.getresponse()

        # read content
        if report_progress or file_path is not None:
            try:
                total_size = int(resp.getheader('content-length'))
            except:
                total_size = -1

            # before starting the download, send a fake progress to permit the
            # user to initialize his ui
            if report_progress:
                q(('progress', resp, (0, total_size)))

            def get_chunks(fd=None):
                bytes_so_far = 0
                result = b''
                while 1:
                    chunk = resp.read(chunk_size)
                    if not chunk:
                        break

                    if fd:
                        fd.write(chunk)
                    else:
                        result += chunk

                    bytes_so_far += len(chunk)
                    # report progress to user
                    if report_progress:
                        q(('progress', resp, (bytes_so_far, total_size)))
                        trigger()
                return bytes_so_far, result

            if file_path is not None:
                with open(file_path, 'wb') as fd:
                    bytes_so_far, result = get_chunks(fd)
            else:
                bytes_so_far, result = get_chunks()

            # ensure that restults are dispatched for the last chunk,
            # avoid trigger
            if report_progress:
                q(('progress', resp, (bytes_so_far, total_size)))
                trigger()
        else:
            result = resp.read()
            try:
                if isinstance(result, bytes):
                    result = result.decode('utf-8')
            except UnicodeDecodeError:
                # if it's an image? decoding would not work
                pass
        req.close()

        # return everything
        return result, resp
