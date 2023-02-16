import re
import threading
import urllib.parse

from lib.utils.file_utils import File


class Dictionary(object):

    def __init__(
        self,
        paths,
        extensions,
        suffixes=None,
        prefixes=None,
        lowercase=False,
        uppercase=False,
        capitalization=False,
        forced_extensions=False,
        exclude_extensions=[],
        no_extension=False,
        only_selected=False,
    ):

        self.entries = []
        self.current_index = 0
        self.condition = threading.Lock()
        self._extensions = extensions
        self._exclude_extensions = exclude_extensions
        self._prefixes = prefixes
        self._suffixes = suffixes
        self._paths = paths
        self._forced_extensions = forced_extensions
        self._no_extension = no_extension
        self._only_selected = only_selected
        self.lowercase = lowercase
        self.uppercase = uppercase
        self.capitalization = capitalization
        self.dictionary_files = [File(path) for path in self.paths]
        self.generate()

    @property
    def extensions(self):
        return self._extensions

    @extensions.setter
    def extensions(self, value):
        self._extensions = value

    @property
    def paths(self):
        return self._paths

    @paths.setter
    def paths(self, paths):
        self._paths = paths

    @classmethod
    def quote(cls, string):
        return urllib.parse.quote(string, safe="!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~")

    """
    Dictionary.generate() behaviour

    Classic coconut wordlist:
      1. If %EXT% keyword is present, append one with each extension REPLACED.
      2. If the special word is no present, append line unmodified.

    Forced extensions wordlist (NEW):
      This type of wordlist processing is a mix between classic processing
      and DirBuster processing.
          1. If %EXT% keyword is present in the line, immediately process as "classic coconut" (1).
          2. If the line does not include the special word AND is NOT terminated by a slash,
            append one with each extension APPENDED (line.ext) and ONLYE ONE with a slash.
          3. If the line does not include the special word and IS ALREADY terminated by slash,
            append line unmodified.
    """

    def generate(self):
        reext = re.compile(r"\%ext\%", re.IGNORECASE).sub
        renoforce = re.compile(r"\%noforce\%", re.IGNORECASE).sub
        find = re.findall
        custom = []
        result = []

        # Enable to use multiple dictionaries at once
        for dict_file in self.dictionary_files:
            for line in list(filter(None, dict.fromkeys(dict_file.get_lines()))):
                # Skip comments
                if line.lstrip().startswith("#"):
                    continue

                if line.startswith("/"):
                    line = line[1:]

                if self._no_extension:
                    line = line[0] + line[1:].split(".")[0]
                    if line == ".":
                        continue

                # Check if the line has the %NOFORCE% keyword
                if "%noforce%" in line.lower():
                    noforce = True
                    line = renoforce("", line)
                else:
                    noforce = False

                # Skip if the path contains excluded extensions
                if self._exclude_extensions:
                    if any(
                        [find("." + extension, line) for extension in self._exclude_extensions]
                    ):
                        continue

                # Classic coconut wordlist processing (with %EXT% keyword)
                if "%ext%" in line.lower():
                    for extension in self._extensions:
                        newline = reext(extension, line)

                        quoted = self.quote(newline)
                        result.append(quoted)

                # If forced extensions is used and the path is not a directory ... (terminated by /)
                # process line like a forced extension.
                elif self._forced_extensions and not line.rstrip().endswith("/") and not noforce:
                    quoted = self.quote(line)

                    for extension in self._extensions:
                        
                        if not extension.strip():
                            result.append(quoted)
                        else:
                            result.append(quoted + "." + extension)

                    result.append(quoted)
                    result.append(quoted + "/")

                # Append line unmodified.
                else:
                    quoted = self.quote(line)

                    if self._only_selected and not line.rstrip().endswith("/") and "." in line:
                        for extension in self._extensions:
                            if line.endswith("." + extension):
                                result.append(quoted)
                                break

                    else:
                        result.append(quoted)

        # Adding prefixes for finding config files etc
        if self._prefixes:
            for res in list(dict.fromkeys(result)):
                for pref in self._prefixes:
                    if not res.startswith(pref):
                        custom.append(pref + res)

        # Adding suffixes for finding backups etc
        if self._suffixes:
            for res in list(dict.fromkeys(result)):
                if not res.rstrip().endswith("/"):
                    for suff in self._suffixes:
                        if not res.rstrip().endswith(suff):
                            custom.append(res + suff)

        result = custom if custom else result

        if self.lowercase:
            self.entries = list(dict.fromkeys(map(lambda l: l.lower(), result)))

        elif self.uppercase:
            self.entries = list(dict.fromkeys(map(lambda l: l.upper(), result)))

        elif self.capitalization:
            self.entries = list(dict.fromkeys(map(lambda l: l.capitalize(), result)))

        else:
            self.entries = list(dict.fromkeys(result))

        del custom
        del result

    def regenerate(self):
        self.generate()
        self.reset()

    def next_with_index(self, base_path=None):
        self.condition.acquire()

        try:
            result = self.entries[self.current_index]

        except IndexError:
            self.condition.release()
            raise StopIteration

        self.current_index = self.current_index + 1
        current_index = self.current_index
        self.condition.release()
        return current_index, result

    def __next__(self, base_path=None):
        _, path = self.next_with_index(base_path)
        return path

    def reset(self):
        self.condition.acquire()
        self.current_index = 0
        self.condition.release()

    def __len__(self):
        return len(self.entries)
