from lib.reports import *
from lib.utils.file_utils import FileUtils

import time
import sys


class PlainTextReport(FileBaseReport):
    def generate_header(self):
        if self.header_written is False:
            self.header_written = True
            return "# Coconut started {0} as: {1}\n\n".format(time.ctime(), ' '.join(sys.argv))
        else:
            return ""

    def generate(self):
        result = self.generate_header()

        for entry in self.entries:
            for e in entry.results:
                if (entry.protocol, entry.host, entry.port, entry.base_path, e.path) not in self.written_entries:
                    result += "{0}  ".format(e.status)
                    result += "{0}  ".format(FileUtils.size_human(e.get_content_length()).rjust(6, " "))
                    result += "{0}://{1}:{2}/".format(entry.protocol, entry.host, entry.port)
                    result += (
                        "{0}".format(e.path)
                        if entry.base_path == ""
                        else "{0}/{1}".format(entry.base_path, e.path)
                    )
                    location = e.response.redirect
                    if location:
                        result += "    -> REDIRECTS TO: {0}".format(location)

                    result += "\n"
                    self.written_entries.append((entry.protocol, entry.host, entry.port, entry.base_path, e.path))

        return result
