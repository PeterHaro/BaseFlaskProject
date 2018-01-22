import codecs
import errno
import json
import os
import re
from pprint import pprint


def remove_prefix(text, prefix):
    if text.startswith(prefix):
        return text[len(prefix):]
    return text


class Expander(object):
    REGULAR_EXPRESSION_FOR_LOCATING_EXPANSION_ENTRY = re.compile("{{__\(\'(.*?)\'\)\}\}")
    REGULAR_EXPRESSION_FOR_EXPAND_STATEFUL_EXPRESSION = re.compile("{{ __\((.*?)\) __\}\}")

    def __init__(self, configuration_file, custom_configuration_file=None, root_directory="../public/templates",
                 output_directory="../public/", language_code="en"):

        self.language_code = language_code
        self.root_directory = root_directory
        self.output_directory = output_directory
        with open(configuration_file) as default_config:
            self.configuration_file = json.load(default_config)
        self.custom_configuration_file = None
        if custom_configuration_file is not None:
            with open(custom_configuration_file) as specialized_config:
                self.custom_configuration_file = json.load(specialized_config)

        self.registered_expansions_keywords = {
            "EXPAND_MENU": self.expand_menu,  # (EXPAND_FIELD_<FIELDNAME>) __
            "EXPAND_LANGUAGES": self.expand_languages,
            "EXPAND_FIELD": self.expand_field
        }

    def expand_menu(self, line):
        retval = ""
        pages = self.configuration_file["pages"]
        if pages is not None:
            for page in pages:
                retval += "<li><a href='" + page + ".html'>" + page + "</a></li>" + "\n"
        return retval

    def expand_field(self, line):
        keyword = line.replace("EXPAND_FIELD_", "")  # Strip away EXPAND_FIELD
        fields = self.fetch_expansion("fields", keyword)
        return self.process_line(fields)  # Expand subfields in fields

    def expand_languages(self):
        pass

    def dump_configurations(self):
        pprint(self.configuration_file)
        if self.custom_configuration_file is not None:
            pprint(self.custom_configuration_file)

    def walk_and_parse(self):
        for root, dirs, files in os.walk(self.root_directory):
            for filename in files:
                if remove_prefix(root, (self.root_directory + os.sep)) and remove_prefix(root, self.root_directory):
                    pass  # Not applicable for this project
                    # Load configuration file for the given sub-folder
                #                    with open((root + os.sep + "configuration.json")) as specialized_configuration:
                #                        self.custom_configuration_file = json.load(specialized_configuration)
                else:
                    self.custom_configuration_file = None
                if filename.endswith(".html"):
                    self.expand_file(os.path.join(root, filename), filename)

    def expand_file(self, path, filename):
        output_lines = []
        with open(path, "r") as templateFile:
            for line in templateFile:
                output_lines.append(self.process_line(line))

        #Not applicable for htis project
        #possible_folder = remove_prefix(path, (self.root_directory + os.sep))
#        output_folder_subtree = "" #
#        if os.path.dirname(possible_folder):
            # output_folder_subtree = possible_folder.split(filename)[0]

#        if not os.path.exists((self.output_directory + output_folder_subtree)):
#            try:
#                os.makedirs((self.output_directory + output_folder_subtree))
#            except OSError as ose:
#                if ose.errno != errno.EEXIST:
#                    raise

        print(
            "Output Directory: " + self.output_directory + "/" + filename)
        with codecs.open(self.output_directory + "/" + filename, "w+", "utf-8") as outputFile:
            outputFile.writelines(output_lines)

    # TODO: Refactor this method, especially the part with multiple expansions
    # noinspection PyTypeChecker
    def process_line(self, line):
        match = self.REGULAR_EXPRESSION_FOR_LOCATING_EXPANSION_ENTRY.search(line)
        if match:
            expansion = self.fetch_expansion(match.group(1))
            try:
                return line.replace(match.group(0), expansion[self.language_code])
            except TypeError:
                print("Cannot find field: " + match.group(1) + " in the configuration file. Going to default value")
                return "Missing value"
        else:
            match = self.REGULAR_EXPRESSION_FOR_EXPAND_STATEFUL_EXPRESSION.search(line)
            if match:
                keyword = match.group(1).rsplit("_", 1)[0]
                if keyword == "EXPAND":  # This means it is a simple expansions keyword and not a variable field
                    return self.registered_expansions_keywords[match.group(1)](line)
                else:
                    return self.registered_expansions_keywords[keyword](match.group(1))
            return line

    def fetch_expansion(self, index, extended_index=None):
        if self.custom_configuration_file is not None:
            if self.custom_configuration_file[index] is not None:
                if extended_index is not None:
                    return "" if self.custom_configuration_file[index][0][extended_index] is None else \
                        self.custom_configuration_file[index][0][extended_index]
                else:
                    return self.custom_configuration_file[index]
        try:
            return "" if self.configuration_file[index] is None else self.configuration_file[index]
        except KeyError:
            return ""


if __name__ == "__main__":
    Expander = Expander("configuration.json")
    Expander.walk_and_parse()
