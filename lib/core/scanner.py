import re

from urllib.parse import unquote
from lib.utils import RandomUtils
from thirdparty.sqlmap import DynamicContentParser


class ScannerException(Exception):
    pass


class Scanner(object):
    def __init__(self, requester, calibration=None, suffix=None, prefix=None):
        self.calibration = calibration
        self.suffix = suffix if suffix else ""
        self.prefix = prefix if prefix else ""
        self.requester = requester
        self.tester = None
        self.redirect_reg_exp = None
        self.invalid_status = None
        self.dynamic_parser = None
        self.sign = None
        self.ratio = 0.98
        self.setup()

    def setup(self):
        first_path = self.prefix + (
            self.calibration if self.calibration else RandomUtils.rand_string()
        ) + self.suffix
        first_response = self.requester.request(first_path)
        self.invalid_status = first_response.status

        if self.invalid_status == 404:
            # Using the response status code is enough :-}
            return

        second_path = self.prefix + (
            self.calibration if self.calibration else RandomUtils.rand_string(omit=first_path)
        ) + self.suffix
        second_response = self.requester.request(second_path)

        # Look for redirects
        if first_response.redirect and second_response.redirect:
            self.redirect_reg_exp = self.generate_redirect_reg_exp(
                first_response.redirect, first_path,
                second_response.redirect, second_path,
            )

        # Analyze response bodies
        if first_response.body is not None and second_response.body is not None:
            self.dynamic_parser = DynamicContentParser(
                self.requester, first_path, first_response.body, second_response.body
            )
        else:
            self.dynamic_parser = None

        base_ratio = float(
            "{0:.2f}".format(self.dynamic_parser.comparisonRatio)
        )  # Rounding to 2 decimals

        # If response length is small, adjust ratio
        if len(first_response) < 2000:
            base_ratio -= 0.1

        if base_ratio < self.ratio:
            self.ratio = base_ratio

    def generate_redirect_reg_exp(self, first_loc, first_path, second_loc, second_path):
        # Use a unique sign to locate where the path gets reflected in the redirect
        self.sign = RandomUtils.rand_string(n=20)
        first_loc = first_loc.replace(first_path, self.sign)
        second_loc = second_loc.replace(second_path, self.sign)
        reg_exp_start = "^"
        reg_exp_end = "$"

        for f, s in zip(first_loc, second_loc):
            if f == s:
                reg_exp_start += re.escape(f)
            else:
                reg_exp_start += ".*"
                break

        if reg_exp_start.endswith(".*"):
            for f, s in zip(first_loc[::-1], second_loc[::-1]):
                if f == s:
                    reg_exp_end = re.escape(f) + reg_exp_end
                else:
                    break

        return unquote(reg_exp_start + reg_exp_end)

    def scan(self, path, response):
        if self.invalid_status == response.status == 404:
            return False

        if self.invalid_status != response.status:
            return True

        if self.redirect_reg_exp and response.redirect:
            path = re.escape(unquote(path))
            # A lot of times, '#' or '?' will be removed in the redirect, cause false positives
            for char in ["\\#", "\\?"]:
                if char in path:
                    path = path.replace(char, "(|" + char) + ")"

            redirect_reg_exp = self.redirect_reg_exp.replace(self.sign, path)

            # Redirect sometimes encodes/decodes characters in URL, which may confuse the
            # rule check and make noise in the output, so we need to unquote() everything
            redirect_to_invalid = re.match(redirect_reg_exp, unquote(response.redirect))

            # If redirection doesn't match the rule, mark as found
            if redirect_to_invalid is None:
                return True

        ratio = self.dynamic_parser.compareTo(response.body)

        if ratio >= self.ratio:
            return False

        elif "redirect_to_invalid" in locals() and ratio >= (self.ratio - 0.15):
            return False

        return True
