"""
PROXYSHOP - GUI LAUNCHER
"""
import os
import sys
import threading
from time import perf_counter
from glob import glob
from kivy.app import App
from kivy.config import Config
from kivy.lang import Builder
from kivy.factory import Factory
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.resources import resource_add_path
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.togglebutton import ToggleButton
from photoshop import api as ps
from proxyshop.creator import CreatorPanels
from proxyshop.scryfall import card_info
from proxyshop.constants import con
from proxyshop.core import retrieve_card_info
from proxyshop.settings import cfg
from proxyshop import core, gui, layouts

# App configuration
Config.set('graphics', 'resizable', '0')
Config.set('graphics', 'width', '800')
Config.set('graphics', 'height', '800')
Config.write()

# Core vars
card_types = core.card_types
templates = core.get_templates()
cwd = os.getcwd()


class ProxyshopApp(App):
	"""
	Our main app class
	"""
	def __init__(self, **kwargs):
		super().__init__(**kwargs)

		# App settings
		self.title = f"Proxyshop {__version__}"
		self.icon = 'proxyshop.png'
		self.cont_padding = 10

		# User data
		self.previous = None
		self.result = True
		self.panels = None
		self.temps = {}

	def select_template(self, btn):
		"""
		Call the add_template method of root object
		"""
		if btn.state == "down":
			self.temps[btn.type] = btn.text
			btn.disabled = True
			for key in btn.all:
				if key is not btn.text:
					btn.all[key].disabled = False
					btn.all[key].state = "normal"

	def render_target(self):
		"""
		RENDER TARGET IMAGE
		"""
		# Setup step
		self.disable_buttons()
		cfg.update()
		temps = core.get_my_templates(self.temps)
		console = gui.console_handler

		# Open file in PS
		app = ps.Application()
		file = app.openDialog()
		if file is None:
			self.enable_buttons()
			return None

		# Load default config/constants, assign layout object
		self.load_defaults()
		card = self.assign_layout(file[0])
		if isinstance(card, str):
			console.update(f"[color=#a84747]{card}[/color]")
			self.enable_buttons()

		# Start a new thread
		template = core.get_template(temps[card.card_class])
		thr = threading.Thread(target=self.render, args=(template, card), daemon=True)
		self.start_thread(thr)

		# Return to normal
		self.close_document()
		self.enable_buttons()

	def render_all(self):
		"""
		RENDER ALL IMAGES IN ART FOLDER
		Using our custom JSON
		"""
		# Setup step
		self.disable_buttons()
		cfg.update()
		temps = core.get_my_templates(self.temps)
		console = gui.console_handler

		# Select all images in art folder
		failed = []
		files = []
		cards = []
		types = {}
		folder = os.path.join(cwd, "art")
		extensions = ["*.png", "*.jpg", "*.tif", "*.jpeg"]
		for ext in extensions:
			files.extend(glob(os.path.join(folder, ext)))


		# ========== FelixVita code changes ============================================================================
		from pathlib import Path
		out_folder = "out"
		out_folder = os.path.join("out", "cube")
		extensions = ["*.png", "*.jpg", "*.tif", "*.jpeg"]

		# FelixVita - Also get art from other location(s)
		other_art_folders = [
			# os.path.join(cwd, "art"),
			# os.path.join(cwd, "..\\MTG-Art-Downloader\\d-godkjent_noUpscale"),
			# os.path.join(cwd, "..\\MTG-Art-Downloader\\d-forUpscaling"),
			# os.path.join(cwd, "..\\xinntao\\Real-ESRGAN\\results-godkjent"),
			# os.path.join(cwd, "..\\..\\felixvita-personal\\git\\MTG-Art-Downloader\\downloaded\\felix-16-apr-2022-scryfall"),
			# os.path.join(cwd, "..\\..\\felixvita-personal\\git\\MTG-Art-Downloader\\downloaded\\felix-30-apr-2022-scryfall"),
			# os.path.join(cwd, "..\\..\\felixvita-personal\\git\\MTG-Art-Downloader\\downloaded\\felix-13-may-2022-scryfall"),
			os.path.join(cwd, "..\\..\\felixvita-personal\\git\\MTG-Art-Downloader\\downloaded\\felix-cube-16-may-2022-scryfall"),
			# os.path.join(cwd, "..\\..\\felixvita-personal\\git\\MTG-Art-Downloader\\d-godkjent_noUpscale"),
			# os.path.join(cwd, "..\\..\\felixvita-personal\\git\\MTG-Art-Downloader\\d-forUpscaling"),
			# os.path.join(cwd, "..\\..\\felixvita-personal\\git\\xinntao\\Real-ESRGAN\\results-godkjent"),
			# os.path.join(cwd, "..\\..\\felixvita-personal\\git\\xinntao\\Real-ESRGAN\\results-please-redo"),
		]
		# Iterate through art folders
		for artdir in other_art_folders:
			subfolders = os.listdir(artdir)
			# Create subfolders in out_folder if they don't exist
			for subfolder in subfolders:
				Path(os.path.join(cwd, out_folder, subfolder)).mkdir(mode=511, parents=True, exist_ok=True)
			# In each art folder, add all art files to the list of files
			for ext in extensions:
				files.extend(glob(os.path.join(artdir,"**", ext)))

		# FelixVita - Subfolders to skip
		numbers = ''  # Example: To skip subfolders starting with '1' and '2', let numbers = '12'. Or, to not skip any, let numbers = ''.
		if numbers:
			files = [_ for _ in files if not str(Path(_).parent.relative_to(Path(_).parent.parent)).startswith(tuple(numbers))]

		# FelixVita - Don't re-render already rendered cards
		rerender_all = False
		# already_rendered_cards.extend([Path(_).name for _ in glob(os.path.join(cwd,"out", "**\*"))])
		already_rendered_cards = []
		for artdir in other_art_folders:
			for subfolder in os.listdir(artdir):
				already_rendered_cards.extend([Path(_).stem for _ in glob(os.path.join(cwd, out_folder, subfolder, "*"))])
		if not rerender_all: files = [_ for _ in files if Path(_).stem not in already_rendered_cards]

		# Print files to terminal
		print("Final list of files for rendering:")
		for _ in files:
			print(_)
		# ======= End of FelixVita code changes ===========================================================================


		# Run through each file, assigning layout
		for f in files:
			lay = self.assign_layout(f)
			if isinstance(lay, str): failed.append(lay)
			else: cards.append(lay)

		# Did any cards fail to find?
		if len(failed) > 0:
			# Some cards failed, should we continue?
			proceed = console.error(
				"\n---- [b]I can't render the following cards[/b] ----\n{}".format("\n".join(failed)),
				color=False, continue_msg="---- [b]Would you still like to proceed?[/b] ----"
			)
			if not proceed:
				self.enable_buttons()
				return None

		# Create a segment of renders for each card class
		for c in cards:
			if c.card_class not in types: types[c.card_class] = [c]
			else: types[c.card_class].append(c)

		# Console next line, then render each segment as a different batch
		console.update()
		for card_type, cards in types.items():
			# The template we'll use for this type
			template = core.get_template(temps[card_type])
			for card in cards:
				# Load defaults and start thread
				self.load_defaults()
				console.update(f"[color=#59d461]---- {card.name} ----[/color]")
				thr = threading.Thread(target=self.render, args=(template, card), daemon=True)
				if not self.start_thread(thr):
					self.close_document()
					self.enable_buttons()
					return None
				self.load_defaults()
			self.close_document()

		# Return to normal
		self.close_document()
		self.enable_buttons()

	def render_custom(self, temp, scryfall):
		"""
		Set up custom render job, then execute
		"""
		self.disable_buttons()
		cfg.update()
		self.load_defaults()
		console = gui.console_handler
		try:

			app = ps.Application()
			file = app.openDialog()[0]
			console.update(
				f"Rendering custom card: [b]{scryfall['name']}[/b]"
			)

			# If basic, manually call the BasicLand layout OBJ
			if scryfall['name'] in con.basic_land_names:
				layout = layouts.BasicLand(scryfall['name'], scryfall['artist'], scryfall['set'])
			else:
				# Instantiate layout OBJ, unpack scryfall json and store relevant data as attributes
				try: layout = layouts.layout_map[scryfall['layout']](scryfall, scryfall['name'])
				except KeyError or TypeError as e:
					console.update(f"Layout not supported!\n", e)
					return None

			# Get our template and layout class maps
			try: card_template = core.get_template(temp)
			except Exception as e:
				console.update(f"Template not found!\n", e)
				return None

			# Select and execute the template
			try:
				layout.creator = None
				card_template(layout, file).execute()
				self.close_document()
			except Exception as e:
				console.update(f"Layout '{scryfall['layout']}' is not supported!\n", e)
				self.close_document()
				return None

		except Exception as e:
			console.update(f"General error! Maybe Photoshop was busy?\n", e)
		self.enable_buttons()
		console.update("")

	@staticmethod
	def assign_layout(filename):
		"""
		Assign layout object to a card.
		@param filename: String including card name, plus optionally:
			- artist name
			- set code
		@return: Layout object for this card
		"""
		console = gui.console_handler
		# Get basic card information
		card = retrieve_card_info(os.path.basename(str(filename)))

		# Basic or no?
		if card['name'] in con.basic_land_names:
			# If basic, manually call the BasicLand layout OBJ
			layout = layouts.BasicLand(card['name'], card['artist'], card['set'])
			console.update(f"Basic land found: [b]{card['name']}[/b]")
		else:
			# Get the scryfall info
			scryfall = card_info(card['name'], card['set'])
			if isinstance(scryfall, str):
				console.log_exception(scryfall)
				return f"Scryfall search failed - [color=#a84747]{card['name']}[/color]"

			# Instantiate layout OBJ, unpack scryfall json and store relevant data as attributes
			try: layout = layouts.layout_map[scryfall['layout']](scryfall, card['name'])
			except Exception as e:
				console.log_exception(e)
				return f"Layout incompatible - [color=#a84747]{card['name']}[/color]"

		# Creator name, artist, filename
		if card['artist']: layout.artist = card['artist']
		layout.creator = card['creator']
		layout.file = filename
		return layout

	def render(self, template, card):
		"""
		Execute a render job.
		@param template: Template class to use for this card
		@param card: Card layout object containing scryfall data
		@return: True/False, if False cancel the render operation
		"""
		self.result = template(card).execute()

	def start_thread(self, thr):
		"""
		Create a counter, start a thread, print time completed.
		@param thr: Thread object
		@return: True if success, None if failed
		"""
		start_t = perf_counter()
		thr.start()
		gui.console_handler.await_cancel(thr)
		thr.join()
		end_t = perf_counter()
		if self.result:
			gui.console_handler.update(f"[i]Time completed: {int(end_t - start_t)} seconds[/i]\n")
			return True
		else: return None

	@staticmethod
	def close_document():
		app = ps.Application()
		try: app.activeDocument.close(ps.SaveOptions.DoNotSaveChanges)
		except Exception as e: return e

	@staticmethod
	def load_defaults():
		cfg.reload()
		con.reload()

	def disable_buttons(self):
		self.root.ids.rend_targ_btn.disabled = True
		self.root.ids.rend_all_btn.disabled = True

	def enable_buttons(self):
		self.root.ids.rend_targ_btn.disabled = False
		self.root.ids.rend_all_btn.disabled = False

	def build(self):
		self.panels = ProxyshopPanels()
		self.panels.add_widget(gui.console_handler)
		return self.panels


class ProxyshopPanels(BoxLayout):
	"""
	Container for overall app
	"""
	def __init__(self, **kwargs):
		super().__init__(**kwargs)


class AppTabs(TabbedPanel):
	"""
	Container for both render and creator tabs
	"""
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self._tab_layout.padding = '0dp', '0dp', '0dp', '0dp'


class ProxyshopTab(TabbedPanelItem):
	"""
	Container for the main render tab
	"""
	def __init__(self, **kwargs):
		super().__init__(**kwargs)


class TemplateModule(TabbedPanel):
	"""
	Container for our template tabs
	"""
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self._tab_layout.padding = '0dp', '10dp', '0dp', '0dp'
		self.card_types = []
		temp_tabs = {}
		scroll_box = {}

		# Add a list of buttons inside a scroll box to each tab
		for t in card_types:

			# Get the list of templates for this type
			temps_t = templates[card_types[t][0]]
			temps = ["Normal"]
			temps_t.pop("Normal")
			temps.extend(sorted(temps_t))
			del temps_t

			# Add tab if more than 1 template available
			if len(temps) > 1:
				scroll_box[t] = TemplateView()
				scroll_box[t].add_widget(TemplateList(t, temps))
				temp_tabs[t] = TabbedPanelItem(text=t)
				temp_tabs[t].content = scroll_box[t]
				self.add_widget(temp_tabs[t])
				self.card_types.append(t)


class TemplateList(GridLayout):
	"""
	Builds a listbox of templates based on a given type
	"""
	def __init__(self, c_type, temps, **kwargs):
		super().__init__(**kwargs)

		# Create a list of buttons
		btn = {}
		for name in temps:
			btn[name] = TemplateButton(name, c_type)
			if name == "Normal":
				btn[name].state = "down"
				btn[name].disabled = True
			self.add_widget(btn[name])
		for name in temps:
			btn[name].all = btn


class TemplateView(ScrollView):
	"""
	Scrollable viewport for template lists
	"""
	def __init__(self, **kwargs):
		super().__init__(**kwargs)


class SettingButton(ToggleButton):
	"""
	Toggle button to change user settings.
	"""
	def __init__(self, **kwargs):
		super().__init__(**kwargs)

	@staticmethod
	def initial_state(setting):
		"""
		Retrieve initial state based on user settings.
		"""
		if setting: return "down"
		else: return "normal"


class TemplateButton(ToggleButton):
	"""
	Button to select active template for card type.
	@param name: Name of template display on the button.
	@param c_type: Card type of this template.
	"""
	def __init__(self, name, c_type, **kwargs):
		super().__init__(**kwargs)
		self.text = name
		self.type = c_type
		self.all = {}


class CreatorTab(TabbedPanelItem):
	"""
	Custom card creator tab
	"""
	def __init__(self, **kwargs):
		Builder.load_file(os.path.join(cwd, "proxyshop/creator.kv"))
		self.text = "Custom Creator"
		super().__init__(**kwargs)
		self.add_widget(CreatorPanels())


if __name__ == '__main__':
	# Kivy packaging
	if hasattr(sys, '_MEIPASS'):
		resource_add_path(os.path.join(sys._MEIPASS))

	# Launch the app
	__version__ = "v1.1.2"
	Factory.register('HoverBehavior', gui.HoverBehavior)
	Builder.load_file(os.path.join(cwd, "proxyshop/proxyshop.kv"))
	ProxyshopApp().run()
