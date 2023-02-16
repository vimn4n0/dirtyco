from lib.reports import *
import time
import sys


class MarkdownReport(FileBaseReport):
    def __init__(self, output_file_name, entries=[]):
        self.output = output_file_name
        self.entries = entries
        self.header_written = False
        self.written_entries = []
        self.printed_target_header_list = []
        self.completed_hosts = []

        self.open()

    def generate_header(self):
        if self.header_written is False:
            self.header_written = True
            result = "### Info\n"
            result += "Args: {0}\n".format(' '.join(sys.argv))
            result += "Time: {0}\n".format(time.ctime())
            result += "\n"
            return result
        else:
            return ""

    def generate(self):
        result = self.generate_header()

        for entry in self.entries:
            header_name = "{0}://{1}:{2}/{3}".format(
                entry.protocol, entry.host, entry.port, entry.base_path
            )
            if (entry.protocol, entry.host, entry.port, entry.base_path) not in self.printed_target_header_list:
                result += "### Target: {0}\n\n".format(header_name)
                result += "Path | Status | Size | Redirection\n"
                result += "-----|--------|------|------------\n"
                self.printed_target_header_list.append((entry.protocol, entry.host, entry.port, entry.base_path))

            for e in entry.results:
                if (entry.protocol, entry.host, entry.port, entry.base_path, e.path) not in self.written_entries:
                    result += "[/{0}]({1}) | ".format(e.path, header_name + e.path)
                    result += "{0} | ".format(e.status)
                    result += "{0} | ".format(e.get_content_length())
                    result += "{0}\n".format(e.response.redirect)

                    self.written_entries.append((entry.protocol, entry.host, entry.port, entry.base_path, e.path))

            if entry.completed and entry not in self.completed_hosts:
                result += "\n"
                self.completed_hosts.append(entry)

        return result
