import argparse
import errno
import json
import os
from distutils.dir_util import copy_tree
from pprint import pprint

from shutil import copyfile, copy

from css_generator import CSSGenerator
from expand import Expander

debug = True

# SUper hacky shit file

def build_argument_parser():
    _parser = argparse.ArgumentParser(
        description="Create Flask projects allows you to create a new Flask project. Write -help for available commands")
    _parser.add_argument("-p", "--path", help="The output path in which the final project will reside",
                         default=os.path.dirname(os.path.abspath(__file__)), required=False)

    required_parameters = _parser.add_argument_group("Required arguments")
    required_parameters.add_argument("-n", "--name", help="Application name", required=True)

    return _parser


def create_folder_if_not_exists(directory):
    try:
        os.makedirs(directory)
        if debug:
            print("Just created directory at path: %s", directory)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise


class ProjectBuilder(object):
    EXCLUDE = set([".git"])

    def __init__(self, configuration_file, output_directory, application_name, root_directory="."):
        self.root_directory = root_directory
        self.application_name = application_name
        self.output_directory = output_directory
        with open(configuration_file, encoding="utf-8") as config:
            self.configuration_file = json.load(config)
        if debug:
            print("============= Configuration File =============")
            pprint(self.configuration_file)
        self.expander = Expander(configuration_file, root_directory="./FlaskBase/templates/",
                                 output_directory=os.path.join(self.output_directory, self.application_name) + "/templates")

    def modify_configuration_parameters(self):
        for key in self.configuration_file:
            currentValue = self.configuration_file[key]
            if isinstance(currentValue, dict):
                for lang in currentValue:
                    self.configuration_file[key][lang] = self.configuration_file[key][lang].replace("FlaskBase",
                                                                                                    self.application_name)
            elif isinstance(currentValue, list):
                if isinstance(currentValue[0], dict):
                    continue
                currentValue = [word.replace("FlaskBase", self.application_name) for word in currentValue]
                self.configuration_file[key] = currentValue
            else:
                self.configuration_file[key] = self.configuration_file[key].replace("FlaskBase", self.application_name)

    def create_scss_file(self, path):
        with open(path, "w", encoding="utf-8") as outfile:
            outfile.write("@import \"" + self.application_name + "/material-announcement\";")

    def create_output_file_structure(self):
        create_folder_if_not_exists(self.output_directory)
        create_folder_if_not_exists(self.output_directory + "/docs")
        create_folder_if_not_exists(self.output_directory + "/tests")
        create_folder_if_not_exists(self.output_directory + "/" + self.application_name)
        copy_tree("./FlaskBase", self.output_directory + "/" + self.application_name)
        create_folder_if_not_exists(self.output_directory + "/private")
        create_folder_if_not_exists(self.output_directory + "/private/scss")
        create_folder_if_not_exists(self.output_directory + "/private/scss/" + self.application_name)
        copy("private/scss/FlaskBase/_material-announcement.scss", self.output_directory + "/private/scss/" + self.application_name)
        copy_tree("./private/external", self.output_directory + "/private/external")
        self.create_scss_file(self.output_directory + "/private/scss/" + self.application_name.lower() + ".scss")
        for file in os.listdir("tests"):
            with open(os.path.join("tests", file), "r", encoding="utf-8") as infile:
                data = infile.read()
                data = data.replace("FlaskBase", self.application_name)
                with open(self.output_directory + "/tests/" + file, "w", encoding="utf-8") as outfile:
                    outfile.write(data)
        for file in [f for f in os.listdir(".") if os.path.isfile(os.path.join(".", f))]:
            if file == "configuration.json":
                with open(os.path.join(self.output_directory, file), "w", encoding="utf-8") as out_config:
                    out_config.write(json.dumps(self.configuration_file))
                continue
            if file == "CreateFlaskProject.py":
                continue
            with open(file, "r", encoding="utf-8") as infile:
                print("Parsing file: %s", file)
                data = infile.read()
                data = data.replace("FlaskBase", self.application_name)
                with open(os.path.join(self.output_directory, file), "w", encoding="utf-8") as outfile:
                    outfile.write(data)

        # Expand HTML templates
        self.expander.walk_and_parse()

        # Populate css
        css_generator = CSSGenerator(root_directory=self.output_directory + "/private/scss/",
                                     output_directory=self.output_directory + "/" + self.application_name + "/static/",
                                     configuration_file=self.configuration_file)
        css_generator.run()


if __name__ == "__main__":
    parser = build_argument_parser()
    arguments = parser.parse_args()
    print(arguments.path)
    project_builder = ProjectBuilder("configuration.json", arguments.path, arguments.name)
    project_builder.modify_configuration_parameters()
    project_builder.create_output_file_structure()
