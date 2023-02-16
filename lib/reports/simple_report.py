from lib.reports import *


class SimpleReport(FileBaseReport):
    def generate(self):
        result = ""

        for entry in self.entries:
            for e in entry.results:
                if (entry.protocol, entry.host, entry.port, entry.base_path, e.path) not in self.written_entries:
                    result += "{0}://{1}:{2}/".format(entry.protocol, entry.host, entry.port)
                    result += (
                        "{0}\n".format(e.path)
                        if entry.base_path == ""
                        else "{0}/{1}\n".format(entry.base_path, e.path)
                    )
                    self.written_entries.append((entry.protocol, entry.host, entry.port, entry.base_path, e.path))

        return result
