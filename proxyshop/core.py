"""
LOADS PLUGINS AND TEMPLATES
"""
import os
import sys
import json
from glob import glob
from pathlib import Path
from datetime import datetime as dt
from importlib import util, import_module
from proxyshop import helpers as psd
cwd = os.getcwd()

def get_template(template, layout=None):
    """
    Get template based on input and layout
    """
    # Was layout provided?
    if layout:
        # Get templates json
        templates = get_templates()

        # Select our template
        if layout in templates:
            if template in templates[layout]:
                selected_template = templates[layout][template]
            else: selected_template = templates[layout]["Normal"]
        else: return None
    else: selected_template = template
    
    # Built-in template?
    if selected_template[0] is None:
        return getattr(import_module("proxyshop.templates"), selected_template[1])

    # Plugin template
    spec = util.spec_from_file_location("templates", os.path.join(cwd, selected_template[0]))
    temp_mod = util.module_from_spec(spec)
    spec.loader.exec_module(temp_mod)
    return getattr(temp_mod, selected_template[1])

def get_templates():
    """
    Roll templates from our plugins into our main json
    """

    # Plugin folders
    folders = glob(os.path.join(cwd, "proxyshop\\plugins\\*\\"))

    # Get our main json
    with open(os.path.join(cwd, "proxyshop\\templates.json"), encoding="utf-8") as json_file:
        this_json = json.load(json_file)
        main_json = {}
        for key, val in this_json.items():
            main_json[key] = {}
            for k,v in val.items():
                main_json[key][k] = [None,v]

    # Iterate through folders
    for folder in folders:
        if Path(folder).stem == "__pycache__": pass
        else:
            j = []
            for name in os.listdir(folder):

                # Load json
                if name == "template_map.json":
                    with open(os.path.join(cwd, f"proxyshop\\plugins\\{Path(folder).stem}\\{name}"), encoding="utf-8") as this_json:
                        j = json.load(this_json)

            # Loop through keys in plugin json
            try:
                for key, val in j.items():
                    # Add to existing templates
                    for k,v in val.items():
                        main_json[key][k] = [f"proxyshop\\plugins\\{Path(folder).stem}\\templates.py",v]
            except: pass

    return main_json

def handle(text, card=None, template=None):
    """
    Handle error messages smoothly
    """
    if card:

        # Log the failure
        time = dt.now().strftime("%m/%d/%Y %H:%M")
        if template: log_text = f"{card} ({template}) [{time}]\n"
        else: log_text = f"{card} [{time}]\n"
        with open(os.path.join(cwd, "tmp/failed.txt"), "a", encoding="utf-8") as log:
            log.write(log_text)

        # Ask user if we should continue?
        choice = input(f"{text}\nI've saved {card} to the Failed.txt log.\nContinue to the next card? (y/n)\n")
        while True:
            if choice == "y":
                print("")
                return True
            if choice == "n":
                psd.close_document()
                sys.exit()
            choice = input("No, seriously should I continue or not?\n")

    input(f"{text}\nPress enter to exit...")
    sys.exit()

def exit_app():
    """
    Exit the application
    """
    sys.exit()