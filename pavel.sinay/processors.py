# File implements high-level processors for transmitting files and executing code

import log

EXEC_PAGE_1 = """
<HTML>
     <HEAD>
     </HEAD>
     <BODY>
        Code to execute:
        <BR/>
        <FORM METHOD=POST ACTION = "/exec" ENCTYPE="text/plain">
            <TEXTAREA NAME="code" ROWS=4 COLS=30>"""

EXEC_PAGE_2 = """</TEXTAREA>
            <BR/>
            <INPUT TYPE=SUBMIT VALUE="Execute">
        </FROM>
     </BODY>
</HTML>
            """

EXEC_PAGE_3 = """for i in range (1, 10):
 print 'Hello World' + i*'!' """

class FileProcessor:
    def __init__(self, http_proc):
        self.file_exts = {"html": "text/html", "jpg": "image/jpg", "jpeg": "image/jpg", "mp3": "audio/mpeg",
                          "txt": "text/plain", "xml": "text/xml", "png": "image/png", "gif": "image/gif",
                          "zip": "application/zip", "pdf": "application/pdf", "gz": "application/x-gzip",
                          "mpg": "video/mpeg", "mpeg": "video/mpeg", "mpv": "video/mpeg"}
        self.file_ext = http_proc.path.rpartition(".")
        if self.file_ext[2] in self.file_exts and len(self.file_ext) == 3:
            http_proc.params["Content-Type"] = self.file_exts[self.file_ext[2]]
            try:
                f = open(http_proc.path[1:], 'r')
                http_proc.body = f.read()
            except:
                http_proc.code = 404
            http_proc.send()
        else:
            http_proc.code = 404
            http_proc.send()


class ExecProcessor:
    def __init__(self, http_proc):
        if http_proc.method != "GET":
            code = http_proc.body.split('=')[1][:-2]
            print code
            try :
                exec code
            except :
                http_proc.code = 500
                log.logger.error("Code is invalid")
            http_proc.body = EXEC_PAGE_1 + code + EXEC_PAGE_2
            http_proc.send()
        else:
            log.logger.info("Sending exec page")
            http_proc.params["Content-Type"] = "text/html"
            http_proc.body = EXEC_PAGE_1 + EXEC_PAGE_3 + EXEC_PAGE_2
            http_proc.send()


class RequestProcessor:
    def __init__(self, http_processor):
        self.http_proc = http_processor
        if self.http_proc.path == "/exec":
            log.logger.info("Executing code")
            ExecProcessor(http_processor)
        else:
            log.logger.info("Transmitting file " + self.http_proc.path)
            FileProcessor(http_processor)
