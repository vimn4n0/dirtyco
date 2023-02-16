from lib.reports import *
from xml.dom import minidom

import xml.etree.cElementTree as ET
import time
import sys


class XMLReport(FileBaseReport):
    def generate(self):
        result = ET.Element("coconutscan", args=" ".join(sys.argv), time=time.ctime())

        for entry in self.entries:
            header_name = "{0}://{1}:{2}/{3}".format(
                entry.protocol, entry.host, entry.port, entry.base_path
            )
            target = ET.SubElement(result, "target", url=header_name)

            for e in entry.results:
                path = ET.SubElement(target, "info", path="/" + e.path)
                ET.SubElement(path, "status").text = str(e.status)
                ET.SubElement(path, "contentlength").text = str(e.get_content_length())
                ET.SubElement(path, "redirect").text = e.response.redirect if e.response.redirect else ""

        result = ET.tostring(result, encoding="utf-8", method="xml")
        return minidom.parseString(result).toprettyxml()

    def save(self):
        self.file.seek(0)
        self.file.truncate(0)
        self.file.flush()
        self.file.writelines(self.generate())
        self.file.flush()
