from lib.reports import *


class CSVReport(FileBaseReport):
    def generate_header(self):
        if self.header_written is False:
            self.header_written = True
            return "URL,Status,Size,Redirection\n"
        else:
            return ""

    def generate(self):
        result = self.generate_header()
        insecure_chars = ("+", "-", "=", "@")

        for entry in self.entries:
            for e in entry.results:
                if (entry.protocol, entry.host, entry.port, entry.base_path, e.path) not in self.written_entries:
                    path = e.path
                    status = e.status
                    content_length = e.get_content_length()
                    redirect = e.response.redirect

                    result += "{0}://{1}:{2}/{3}{4},".format(entry.protocol, entry.host, entry.port, entry.base_path, path)
                    result += "{0},".format(status)
                    result += "{0},".format(content_length)
                    if redirect:
                        # Preventing CSV injection. More info: https://www.exploit-db.com/exploits/49370
                        if redirect.startswith(insecure_chars):
                            redirect = "'" + redirect

                        redirect = redirect.replace("\"", "\"\"")
                        result += "\"{0}\"".format(redirect)

                    result += "\n"
                    self.written_entries.append((entry.protocol, entry.host, entry.port, entry.base_path, e.path))

        return result
