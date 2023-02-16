import sys
import threading
import urllib.parse

from lib.utils.file_utils import *
from thirdparty.colorama import init, Fore, Style

if sys.platform in ["win32", "msys"]:
    from thirdparty.colorama.win32 import *


class NoColor:
    RED = GREEN = YELLOW = BLUE = MAGENTA = CYAN = WHITE = BRIGHT = RESET_ALL = ''


class PrintOutput(object):
    def __init__(self, color):
        init()
        self.mutex = threading.Lock()
        self.blacklists = {}
        self.mutex_checked_paths = threading.Lock()
        self.base_path = None
        self.errors = 0
        if not color:
            self.disable_colors()

    def header(self, text):
        pass

    def in_line(self, string):
        self.erase()
        sys.stdout.write(string)
        sys.stdout.flush()

    def erase(self):
        if sys.platform in ["win32", "cygwin", "msys"]:
            csbi = GetConsoleScreenBufferInfo()
            line = "\b" * int(csbi.dwCursorPosition.X)
            sys.stdout.write(line)
            width = csbi.dwCursorPosition.X
            csbi.dwCursorPosition.X = 0
            FillConsoleOutputCharacter(STDOUT, " ", width, csbi.dwCursorPosition)
            sys.stdout.write(line)
            sys.stdout.flush()

        else:
            sys.stdout.write("\033[1K")
            sys.stdout.write("\033[0G")

    def new_line(self, string=''):
        sys.stdout.write(string + "\n")
        sys.stdout.flush()

    def status_report(self, path, response, full_url, added_to_queue):
        content_length = None
        status = response.status

        # Format message
        try:
            size = int(response.headers["content-length"])

        except (KeyError, ValueError):
            size = len(response.body)

        finally:
            content_length = FileUtils.size_human(size)

        show_path = "/" + self.base_path + path

        parsed = urllib.parse.urlparse(self.target)
        show_path = "{0}://{1}{2}".format(parsed.scheme, parsed.netloc, show_path)

        message = "{0} - {1} - {2}".format(
            status, content_length.rjust(6, " "), show_path
        )

        if status in [200, 201, 204]:
            message = Fore.GREEN + message + Style.RESET_ALL

        elif status == 401:
            message = Fore.YELLOW + message + Style.RESET_ALL

        elif status == 403:
            message = Fore.BLUE + message + Style.RESET_ALL

        elif status in range(500, 600):
            message = Fore.RED + message + Style.RESET_ALL

        elif status in range(300, 400):
            message = Fore.CYAN + message + Style.RESET_ALL
            if "location" in [h.lower() for h in response.headers]:
                message += "  ->  {0}".format(response.headers["location"])

        else:
            message = Fore.MAGENTA + message + Style.RESET_ALL

        if added_to_queue:
            message += "     (Added to queue)"

        with self.mutex:
            self.new_line(message)

    def last_path(self, path, index, length, current_job, all_jobs, rate):
        pass

    def add_connection_error(self):
        self.errors += 1

    def error(self, reason):
        pass

    def warning(self, reason):
        pass

    def config(
        self,
        extensions,
        prefixes,
        suffixes,
        threads,
        wordlist_size,
        method,
    ):
        pass

    def set_target(self, target, scheme):
        if not target.startswith("http://") and not target.startswith("https://") and "://" not in target:
            target = "{0}://{1}".format(scheme, target)

        self.target = target

    def output_file(self, target):
        pass

    def error_log_file(self, target):
        pass

    def debug(self, info):
        with self.mutex:
            self.new_line(info)

    def disable_colors(self):
        global Fore
        global Style
        global Back

        Fore = Style = Back = NoColor
