import json
import time
import sys

from lib.reports import *


class JSONReport(FileBaseReport):
    def generate(self):
        report = {"info": {"args": ' '.join(sys.argv), "time": time.ctime()}, "results": []}

        for entry in self.entries:
            result = {}
            header_name = "{0}://{1}:{2}/{3}".format(
                entry.protocol, entry.host, entry.port, entry.base_path
            )
            result[header_name] = []

            for e in entry.results:
                path_entry = {
                    "status": e.status,
                    "path": "/" + e.path,
                    "content-length": e.get_content_length(),
                    "redirect": e.response.redirect,
                }
                result[header_name].append(path_entry)

            report["results"].append(result)

        return json.dumps(report, sort_keys=True, indent=4)

    def save(self):
        self.file.seek(0)
        self.file.truncate(0)
        self.file.flush()
        self.file.writelines(self.generate())
        self.file.flush()
