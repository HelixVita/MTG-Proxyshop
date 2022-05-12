"""
FelixVita TEMPLATES
"""
import os
import proxyshop.frame_logic as frame_logic
import proxyshop.format_text as format_text
import proxyshop.text_layers as txt_layers
import proxyshop.templates as temp
import proxyshop.constants as con
import proxyshop.settings as cfg
import proxyshop.helpers as psd
import photoshop.api as ps
app = ps.Application()

list_of_all_mtg_sets = list(con.set_symbols.keys())

pre_modern_sets = list_of_all_mtg_sets[:list_of_all_mtg_sets.index("8ED")]

pre_mmq_sets = list_of_all_mtg_sets[:list_of_all_mtg_sets.index("MMQ")]
# Mercadian Masques changed the color of the copyright/collector's info on red cards from black to white (though strangely HML had a mix of black & white).

pre_exodus_sets = list_of_all_mtg_sets[:list_of_all_mtg_sets.index("EXO")]
# Exodus featured a couple of important and lasting changes:
# 1. Colored set symbols for uncommons and rares (silver & gold color)
# 2. Artist+Collector text field at the bottom of the card is now centered (previously left-justified)

pre_mirage_sets = list_of_all_mtg_sets[:list_of_all_mtg_sets.index("MIR")]
# Mirage featured some changes to the frame, including but not limited to:
# 1. Citations in flavor text are now right-justified
# 2. The rules box of white cards is now less patterned (less contrast)
# 3. Frame of black cards is now darker

pre_hml_sets = list_of_all_mtg_sets[:list_of_all_mtg_sets.index("HML")]
# Homelands changed the color of the copyright/collector's info on blue cards from black to white

pre_legends_sets = list_of_all_mtg_sets[:list_of_all_mtg_sets.index("LEG")]
# Legends made white text (cardname, typeline, P/T) white instead of gray

pre_atq_sets = list_of_all_mtg_sets[:list_of_all_mtg_sets.index("ATQ")]
# Antiquities gave white frames a hint of yellow tint

# pre_exodus_sets = [
#     "LEA",
#     "LEB",
#     "2ED",
#     "ARN",
#     "ATQ",
#     "3ED",
#     "LEG",
#     "DRK",
#     "FEM",
#     "4ED",
#     "ICE",
#     "CHR",
#     "HML",
#     "ALL",
#     "MIR",
#     "VIS",
#     "5ED",
#     "POR",
#     "WTH",
#     "TMP",
#     "STH",
# ]

sets_without_set_symbol = [
    "LEA",
    "LEB",
    "2ED",
    "3ED",
    "4ED",
    "5ED",
]

sets_with_hollow_set_symbol = [
    "6ED",
    "DKM",
    "TOR",
    "JUD", # Probably
    "ONS", # Probably
    # Maybe:
    # POR
    "ATQ",
]

sets_lacking_symbol_stroke = [
    # The result of putting a set here is that it will get a near-invisible 1-pixel thick BLACK stroke. (Because can't apply 0-px thick stroke.... WAIT A SEC, what about just not applying a stroke at all?)  # TODO: Finish writing this
    # Only pre-exodus sets should go into this list, as putting a set into this list will result in no gold/silver/mythic color being applied to the set symbol.
    "VIS",
    "ARN", # Probably
    "LEG", # Probably
    "POR",
    "ICE", # Nope, because even a 1px black stroke is too much; it needs to be white.
    "P02",
    "ATQ",
]

sets_with_black_copyright_for_lands = [_ for _ in pre_mmq_sets if _ not in ["USG", "S99"]]

# pre_legends_sets = [
#     "LEA",
#     "LEB",
#     "2ED",
#     "ARN",
#     "ATQ",
#     "3ED",
# ]

special_land_frames = {
    "ARN": "Arabian Nights",
    "ATQ": "Antiquities",
    "LEG": "Legends",
    "DRK": "The Dark",
    "FEM": "Fallen Empires",
    "ICE": "Ice Age",
    "HML": "Homelands",
    "ALL": "Alliances",
    "MIR": "Mirage",
    "VIS": "Visions",
    "4ED": "Fourth Edition",
}

original_dual_lands = [
    "Tundra",
    "Underground Sea",
    "Badlands",
    "Taiga",
    "Savannah",
    "Scrubland",
    "Volcanic Island",
    "Bayou",
    "Plateau",
    "Tropical Island",
]

# pre_mirage_sets = [
#     "LEA",
#     "LEB",
#     "2ED",
#     "ARN",
#     "ATQ",
#     "3ED",
#     "LEG",
#     "DRK",
#     "FEM",
#     "4ED",
#     "ICE",
#     "ALL",
# ]

all_keyrune_pre_eighth_symbols_for_debugging = ""

# Overwrite constants
con.set_symbols["ICE"] = ""  # Use ss-ice2 (instead of ss-ice)


def unhide(psdpath: tuple, is_group=False):
    # Example: psdpath = ("RW", "ABUR Duals (ME4)", "Land")
    revpath = list(reversed(psdpath))
    # Example: revpath = ("Land", "ABUR Duals (ME4)", "RW")
    selection = psd.getLayerSet(revpath[0])
    psdpath_iter = revpath[1:] if is_group else revpath[1:-1]
    for _ in psdpath_iter:
        selection = psd.getLayerSet(_, selection)
    if not is_group:
        selection = psd.getLayer(revpath[-1], selection)
    selection.visible = True


def frame_expansion_symbol_customscale(layer, reference_layer, centered, scale_percent=100):
    """
     * Scale a layer equally to the bounds of a reference layer, then centre the layer vertically and horizontally
     * within those bounds.
    """
    layer_dimensions = psd.compute_layer_dimensions(layer)
    reference_dimensions = psd.compute_layer_dimensions(reference_layer)

    # Determine how much to scale the layer by such that it fits into the reference layer's bounds
    scale_factor = scale_percent * min(reference_dimensions['width'] / layer_dimensions['width'], reference_dimensions['height'] / layer_dimensions['height'])
    layer.resize(scale_factor, scale_factor, ps.AnchorPosition.MiddleRight)

    psd.select_layer_pixels(reference_layer)
    app.activeDocument.activeLayer = layer

    if centered: psd.align_horizontal()
    psd.align_vertical()
    psd.clear_selection()


class RetroExpansionSymbolField (txt_layers.TextField):
    """
     * Created by FelixVita
     * A TextField which represents a card's expansion symbol.
     * `layer`: Expansion symbol layer
     * `text_contents`: The symbol character
     * `rarity`: The clipping mask to enable (uncommon, rare, mythic)
     * `reference`: Reference layer to scale and center
     * `centered`: Whether to center horizontally, ex: Ixalan
     * `symbol_stroke_size`: The symbol stroke size (thickness).
    """
    def __init__ (self, layer, text_contents, rarity, reference, centered=False, is_pre_exodus=None, has_hollow_set_symbol=None, setcode=None, background=None):
        super().__init__(layer, text_contents, psd.rgb_black())
        self.centered = centered
        self.rarity = rarity
        self.reference = reference
        self.is_pre_exodus = is_pre_exodus
        self.has_hollow_set_symbol = has_hollow_set_symbol
        self.setcode = setcode
        self.background = background
        if rarity in (con.rarity_bonus, con.rarity_special):
            self.rarity = con.rarity_mythic

    def execute (self):
        super().execute()

        # Size to fit reference?
        if cfg.cfg.auto_symbol_size:
            scale_percent = 70 if self.setcode in ["ATQ", "FEM"] else 85 if self.setcode == "STH" else 125 if self.setcode == "ARN" else 100
            if self.centered: frame_expansion_symbol_customscale(self.layer, self.reference, True, scale_percent)
            else: frame_expansion_symbol_customscale(self.layer, self.reference, False, scale_percent)
        app.activeDocument.activeLayer = self.layer

        # Symbol stroke size (thickness)
        symbol_stroke_size = cfg.cfg.symbol_stroke
        # Special cases
        nostroke = False
        if self.setcode == "DRK":
            if self.background == "B":
                symbol_stroke_size = 2
            else:
                nostroke = True
        elif self.setcode == "EXO": symbol_stroke_size = str(int(symbol_stroke_size) + 2)

        # Make RetroExpansionGroup the active layer
        text_and_icons = psd.getLayerSet(con.layers['TEXT_AND_ICONS'])
        retro_expansion_group = psd.getLayerSet("RetroExpansionGroup", text_and_icons)
        app.activeDocument.activeLayer = retro_expansion_group

        # Apply set symbol stroke (white/black) and rarity color (silver/gold/mythic)
        if nostroke or self.setcode in sets_lacking_symbol_stroke: pass  # Apply neither
        elif self.rarity == con.rarity_common or self.is_pre_exodus:
            # Apply white stroke only
            if self.setcode in pre_legends_sets or self.setcode in ["HML", "MIR"]:  # TODO: Verify if this is better for MIR than white
                val = 204 if self.setcode == "MIR" else 186
                psd.apply_stroke(symbol_stroke_size, psd.get_rgb(val, val, val))
            else:
                psd.apply_stroke(symbol_stroke_size, psd.rgb_white())
        else:
            # Apply white stroke and rarity color
            mask_layer = psd.getLayer(self.rarity, self.layer.parent)
            mask_layer.visible = True
            if self.setcode in pre_legends_sets or self.setcode == "HML":
                psd.apply_stroke(symbol_stroke_size, psd.get_rgb(186, 186, 186))
            else:
                psd.apply_stroke(symbol_stroke_size, psd.rgb_white())
            psd.select_layer_pixels(self.layer)
            app.activeDocument.activeLayer = mask_layer
            psd.align_horizontal()
            psd.align_vertical()
            psd.clear_selection()

        # Fill in the expansion symbol?
        if cfg.cfg.fill_symbol and not self.has_hollow_set_symbol:
            app.activeDocument.activeLayer = self.layer
            if self.setcode in pre_legends_sets or self.setcode == "HML":
                psd.fill_expansion_symbol(self.reference, psd.get_rgb(186, 186, 186))
            else:
                psd.fill_expansion_symbol(self.reference, psd.rgb_white())


class StarterTemplate (temp.BaseTemplate):
    """
    A BaseTemplate with a few extra features. In most cases this will be your starter template
    you want to extend for the most important functionality.
    """
    def __init__(self, layout):
        super().__init__(layout)
        try: self.is_creature = bool(self.layout.power and self.layout.toughness)
        except AttributeError: self.is_creature = False
        try: self.is_legendary = bool(self.layout.type_line.find("Legendary") >= 0)
        except AttributeError: self.is_legendary = False
        try: self.is_land = bool(self.layout.type_line.find("Land") >= 0)
        except AttributeError: self.is_land = False
        try: self.is_companion = bool("companion" in self.layout.frame_effects)
        except AttributeError: self.is_companion = False

    def basic_text_layers(self, text_and_icons):
        """
        Set up the card's mana cost, name (scaled to not overlap with mana cost), expansion symbol, and type line
        (scaled to not overlap with the expansion symbol).
        """
        # Shift name if necessary (hiding the unused layer)
        name = psd.getLayer(con.layers['NAME'], text_and_icons)
        name_selected = name
        try:
            if self.name_shifted:
                name_selected = psd.getLayer(con.layers['NAME_SHIFT'], text_and_icons)
                name.visible, name_selected.visible = False, True
        except AttributeError: pass

        # Shift typeline if necessary
        type_line = psd.getLayer(con.layers['TYPE_LINE'], text_and_icons)
        type_line_selected = type_line
        try:
            # Handle error if type line shift / color indicator doesn't exist
            if self.type_line_shifted:
                type_line_selected = psd.getLayer(con.layers['TYPE_LINE_SHIFT'], text_and_icons)
                psd.getLayer(self.layout.pinlines, con.layers['COLOR_INDICATOR']).visible = True
                type_line.visible, type_line_selected.visible = False, True
        except AttributeError: pass

        # Mana, expansion
        mana_cost = psd.getLayer(con.layers['MANA_COST'], text_and_icons)
        # expansion_symbol = psd.getLayer(con.layers['EXPANSION_SYMBOL'], text_and_icons)
        retro_expansion_group = psd.getLayerSet("RetroExpansionGroup", text_and_icons)          # FelixVita
        expansion_symbol = psd.getLayer(con.layers['EXPANSION_SYMBOL'], retro_expansion_group)  # FelixVita: Changed in order to make stroke + innershadow work.
        expansion_reference = psd.getLayer(con.layers['EXPANSION_REFERENCE'], text_and_icons)

        # Setcode & booleans
        setcode = self.layout.set.upper()
        is_pre_exodus = setcode in pre_exodus_sets
        has_hollow_set_symbol = setcode in sets_with_hollow_set_symbol

        # Add text layers
        self.tx_layers.extend([
            txt_layers.BasicFormattedTextField(
                layer=mana_cost,
                text_contents=self.layout.mana_cost,
                text_color=psd.rgb_black()
            ),
            txt_layers.ScaledTextField(
                layer=name_selected,
                text_contents=self.layout.name,
                text_color=psd.get_rgb(186, 186, 186) if setcode in pre_legends_sets else psd.get_text_layer_color(name_selected),
                reference_layer=mana_cost
            ),
            # RetroExpansionSymbolField(
            #     layer = expansion_symbol,
            #     text_contents = self.layout.symbol,
            #     rarity = self.layout.rarity,
            #     reference = expansion_reference,
            #     is_pre_exodus = is_pre_exodus,
            #     has_hollow_set_symbol = has_hollow_set_symbol,
            #     setcode = setcode
            #     ),
            # txt_layers.ExpansionSymbolField(
            #     layer=expansion_symbol,
            #     text_contents=self.layout.symbol,
            #     rarity=self.layout.rarity,
            #     reference=expansion_reference
            # ),
            txt_layers.ScaledTextField(
                layer=type_line_selected,
                text_contents=self.layout.type_line,
                text_color=psd.get_rgb(186, 186, 186) if setcode in pre_legends_sets else psd.get_text_layer_color(type_line_selected),
                reference_layer=expansion_symbol
            ),
        ])

        # Add expansion symbol field
        if setcode not in sets_without_set_symbol and setcode != "ALL":
            self.tx_layers.extend([
                RetroExpansionSymbolField(
                    layer = expansion_symbol,
                    text_contents = self.layout.symbol,
                    rarity = self.layout.rarity,
                    reference = expansion_reference,
                    is_pre_exodus = is_pre_exodus,
                    has_hollow_set_symbol = has_hollow_set_symbol,
                    setcode = setcode,
                    background = self.layout.background
                    )
            ])

class NormalClassicTemplate (StarterTemplate):
    """
     * A template for 7th Edition frame. Each frame is flattened into its own singular layer.
    """
    def template_file_name(self): return "normal-classic"
    def template_suffix(self): return "Classic"

    def __init__(self, layout):
        # Collector info
        cfg.real_collector = True  # FelixVita
        cfg.cfg.real_collector = True  # FelixVita
        if layout.background == con.layers['COLORLESS']: layout.background = con.layers['ARTIFACT']
        super().__init__(layout)
        self.art_reference = psd.getLayer(con.layers['ART_FRAME'])

        # Basic text
        text_and_icons = psd.getLayerSet(con.layers['TEXT_AND_ICONS'])
        super().basic_text_layers(text_and_icons)

        # Text reference and rules text
        if self.is_land: reference_layer = psd.getLayer(con.layers['TEXTBOX_REFERENCE_LAND'], text_and_icons)
        else: reference_layer = psd.getLayer(con.layers['TEXTBOX_REFERENCE'], text_and_icons)
        rules_text = psd.getLayer(con.layers['RULES_TEXT'], text_and_icons)
        is_centered = bool(
            len(self.layout.flavor_text) <= 1
            and len(self.layout.oracle_text) <= 70
            and self.layout.oracle_text.find("\n") < 0
        )

        # Add to text layers
        self.tx_layers.append(
            txt_layers.FormattedTextArea(
                layer=rules_text,
                text_contents=self.layout.oracle_text,
                text_color=psd.get_text_layer_color(rules_text),
                flavor_text=self.layout.flavor_text,
                is_centered=is_centered,
                reference_layer=reference_layer,
                fix_length=False
            )
        )

        # Add creature text layers
        power_toughness = psd.getLayer(con.layers['POWER_TOUGHNESS'], text_and_icons)
        if self.is_creature:
            self.tx_layers.append(
                txt_layers.TextField(
                    layer=power_toughness,
                    text_contents=str(self.layout.power) + "/" + str(self.layout.toughness),
                    text_color=psd.get_rgb(186, 186, 186) if self.layout.set.upper() in pre_legends_sets else psd.get_text_layer_color(power_toughness)
                )
            )
        else: power_toughness.visible = False


class RetroNinetysevenTemplate (NormalClassicTemplate):
    """
     * Notes about my template here
     * Created by FelixVita
    """
    def template_file_name (self):
        return "FelixVita/retro-1997"

    def template_suffix (self):
        return "Retro-1997"

    # OPTIONAL
    def __init__ (self, layout):

        # Right-justify citations in flavor text for all sets starting with Mirage
        if layout.set.upper() not in pre_mirage_sets:
            con.align_classic_quote = True

        super().__init__(layout)

        # # Overwrite the expansion symbol field text layer using custom class
        # setcode = layout.set.upper()
        # text_and_icons = psd.getLayerSet(con.layers['TEXT_AND_ICONS'])
        # retro_expansion_group = psd.getLayerSet("RetroExpansionGroup", text_and_icons)
        # expansion_symbol = psd.getLayer(con.layers['EXPANSION_SYMBOL'], retro_expansion_group)
        # try: expansion_reference = psd.getLayer(con.layers['EXPANSION_REFERENCE'], text_and_icons)
        # except: expansion_reference = None

        # # Disable RetroExpansionSymbolField for Alliances cards
        # if setcode in sets_without_set_symbol or setcode == "ALL":
        #     for i, layer in enumerate(self.tx_layers):
        #         if isinstance(layer, RetroExpansionSymbolField): del self.tx_layers[i]

        # for i, layer in enumerate(self.tx_layers):
        #     if isinstance(layer, txt_layers.ExpansionSymbolField):
        #         if setcode in sets_without_set_symbol:
        #             del self.tx_layers[i]
        #         else:
        #             self.tx_layers[i] = RetroExpansionSymbolField(
        #                 layer = expansion_symbol,
        #                 text_contents = self.layout.symbol,
        #                 rarity = self.layout.rarity,
        #                 reference = expansion_reference,
        #                 is_pre_exodus = setcode in pre_exodus_sets,
        #                 has_hollow_set_symbol = setcode in sets_with_hollow_set_symbol,
        #                 setcode = setcode
        #             )

    def collector_info(self):
        """
        Format and add the collector info at the bottom.
        """

        setcode = self.layout.set.upper()
        color = self.layout.background

        legal_layer = psd.getLayerSet(con.layers['LEGAL'])
        # if setcode in sets_with_gray_text:
        if setcode in pre_exodus_sets:
            # Hide set & artist layers; and reveal left-justified ones
            psd.getLayer(con.layers['SET'], legal_layer).visible = False
            psd.getLayer(con.layers['ARTIST'], legal_layer).visible = False
            legal_layer = psd.getLayerSet("Left-Justified", con.layers['LEGAL'])
            legal_layer.visible = True

        # Artist layer & set/copyright/collector info layer
        collector_layer = psd.getLayer(con.layers['SET'], legal_layer)
        artist_layer = psd.getLayer(con.layers['ARTIST'], legal_layer)

        # Color the artist info gray for old cards
        if setcode in pre_legends_sets:
            artist_layer.textItem.color = psd.get_rgb(186, 186, 186)  # Gray

        # Fill in artist info ("Illus. Artist" --> "Illus. Pablo Picasso")
        psd.replace_text(artist_layer, "Artist", self.layout.artist)

        # Some cards have black or gray collector's info instead of white. The logic for this is roughly thus:
        print(f"{color=}")
        app.activeDocument.activeLayer = collector_layer
        if color == "W":
            collector_layer.textItem.color = psd.rgb_black()
            psd.apply_stroke(1, psd.rgb_black())
        elif setcode in pre_legends_sets:
            collector_layer.textItem.color = psd.get_rgb(186, 186, 186)  # Gray
            psd.apply_stroke(1, psd.get_rgb(186, 186, 186))
        elif (
            (color == "R" and setcode in pre_mmq_sets) or
            (color == "U" and setcode in pre_hml_sets) or
            (color == "Gold" and setcode in pre_mirage_sets) or  # TODO: Check if "Gold" is the correct term here for multicolor cards
            (color == "Land" and setcode in sets_with_black_copyright_for_lands)  # TODO: Check if "Land" is the correct term here for Land cards
            ):
            collector_layer.textItem.color = psd.rgb_black()
            psd.apply_stroke(1, psd.rgb_black())
        else:
            psd.apply_stroke(1, psd.get_rgb(238, 238, 238))  # White (#EEEEEE)

        # Fill in detailed collector info, if available ("SET • 999/999 C" --> "ABC • 043/150 R")
        collector_layer.visible = True

        # Try to obtain release year
        try:
            release_year = self.layout.scryfall['released_at'][:4]
        except:
            release_year = None

        # Conditionally build up the collector info string (leaving out any unavailable info)
        collector_string = ""
        collector_string += "Proxy • Not for Sale — "
        collector_string += f"{self.layout.set} • "
        if not cfg.real_collector:
            collector_string += "EN"
        else:
            collector_string += f"{release_year} • " if release_year else ""
            collector_string += str(self.layout.collector_number).lstrip("0")
            collector_string += "/" + str(self.layout.card_count).lstrip("0") if self.layout.card_count else ""
            collector_string += f" {self.layout.rarity_letter}" if self.layout.rarity else ""

        # Apply the collector info
        collector_layer.textItem.contents = collector_string


    def enable_frame_layers (self):
        # Variables
        border_color = self.layout.scryfall['border_color']
        setcode = self.layout.set.upper()
        cardname = self.layout.scryfall['name']
        print(f"{cardname=}")
        # Enable white border if scryfall says card border is white
        if border_color == 'white':
            psd.getLayer("WhiteBorder").visible = True
        elif border_color == 'black':
            if self.layout.scryfall['colors'] == ["B"]:
                psd.getLayer("Brighter Left & Bottom Frame Bevels", "Nonland").visible = True
        # Hide set symbol for any cards from sets LEA, LEB, 2ED, 3ED, 4ED, and 5ED.
        if setcode in sets_without_set_symbol or setcode == "ALL":
            text_and_icons = psd.getLayerSet(con.layers['TEXT_AND_ICONS'])
            psd.getLayerSet("RetroExpansionGroup", text_and_icons).visible = False
        if setcode in pre_mirage_sets and self.layout.scryfall['colors'] == ["B"]:
            black_group = psd.getLayerSet("B", "Nonland")
            psd.getLayer("1993 Style - Browner Edges", black_group).visible = True
            psd.getLayer("1993 Style - Parchment Hue", black_group).visible = True
            psd.getLayer("1993 Style - Brightness", black_group).visible = True
            psd.getLayer("1993 Style - Parchment Backdrop", black_group).visible = True
            psd.getLayer("1993 Style - B Frame Tint Green", black_group).visible = True
            psd.getLayer("1993 Style - Hue", black_group).visible = True
        elif setcode in pre_mirage_sets and self.layout.scryfall['colors'] == ["G"]:  #TODO: Create a a separate list for sets with darker green box
            green_group = psd.getLayerSet("G", "Nonland")
            psd.getLayer("1993 Style - G Box Darken", green_group).visible = True
            psd.getLayer("1993 Style - G Frame Color Balance", green_group).visible = True
            psd.getLayer("1993 Style - G Box Color Balance", green_group).visible = True
        elif setcode in ["LEA", "LEB"] and self.layout.scryfall['colors'] == ["R"]:
            red_group = psd.getLayerSet("R", "Nonland")
            psd.getLayer("LEA-LEB Inner Bevel Sunlight", red_group).visible = True
            psd.getLayer("LEA-LEB Box Hue", red_group).visible = True
            psd.getLayer("LEA-LEB Hue", red_group).visible = True
            psd.getLayer("LEA-LEB Color Balance", red_group).visible = True
        elif setcode in pre_exodus_sets and self.layout.scryfall['colors'] == ["W"]:
            white_group = psd.getLayerSet("W", "Nonland")
            psd.getLayer("LEA-LEB - Box Levels", white_group).visible = True
            psd.getLayer("LEA-LEB - Box Hue/Saturation", white_group).visible = True
            if setcode in pre_atq_sets:
                # psd.getLayer("LEA-LEB - Box Trim Hue", white_group).visible = True  # TODO: Remove from PSD template -- it just doesn't look good
                psd.getLayer("LEA-LEB - Frame Levels", white_group).visible = True
                psd.getLayer("LEA-LEB - Frame Hue/Saturation", white_group).visible = True
                psd.getLayer("LEA-LEB - Frame Color Balance", white_group).visible = True
        if "Flashback" in self.layout.keywords:
            psd.getLayer("Tombstone").visible = True

         # super().enable_frame_layers()

        if not self.is_land:
            layer_set = psd.getLayerSet(con.layers['NONLAND'])
            selected_layer = self.layout.background
            # psd.getLayer(selected_layer, layer_set).visible = True
            psd.getLayerSet(selected_layer, layer_set).visible = True
        elif self.is_land:
            land = con.layers['LAND']
            abur = "ABUR Duals (ME4)"
            wholes = "Wholes for regular duals and monocolors"
            halves = "Halves for regular duals"
            modifications = "Modifications"
            thicker_trim_stroke = "Trim - Thicker Outer Black Stroke (2px)"
            thickest_trim_stroke = "Trim - Thickest Outer Black Stroke (3px)"
            thicker_bevels_rules_box = "Rules Box - Inner Bevel - Enhance"
            neutral_land_frame_color = "Neutral - Color (v2)"
            pinlines: str = self.layout.pinlines
            print(f"{pinlines=}")
            is_dual = len(pinlines) == 2
            is_mono = len(pinlines) == 1
            groups_to_unhide = []
            layers_to_unhide = []

            if setcode in ["ARN", "LEG", "ATQ", "ALL", "FEM", "DRK", "HML", "ICE", "4ED"]:
                # Then use that set's unique frame
                layers_to_unhide.append((land, wholes, land))
                groups_to_unhide.append((setcode + " - Color", wholes, land))
                if setcode in ["FEM", "ALL"]:
                    # Enable thick colored trim with no black strokes
                    groups_to_unhide.append(("Trim - " + setcode, modifications, land))
                    if setcode == "ALL":
                        # Unhide the shaded-in Alliances set symbol icon (rather than using the ExpansionSymbol class to generate it)
                        groups_to_unhide.append(("Set Symbol - Alliances", modifications, land))
                elif setcode != "LEG":
                    layers_to_unhide.append((thicker_trim_stroke, modifications, land))

            elif setcode in ["MIR", "VIS"]:
                    # Mirage/Visions colorless lands -- Examples: Teferi's Isle (MIR), Griffin Canyon (VIS)
                    layers_to_unhide.append((land, wholes, land))
                    groups_to_unhide.append(("VIS - Color", wholes, land))
                    groups_to_unhide.append((thicker_bevels_rules_box, modifications, land))
                    layers_to_unhide.append((thicker_trim_stroke, modifications, land))
                    if is_mono and setcode == "VIS":
                        # Visions monocolor lands -- Examples: Dormant Volcano (VIS)
                        groups_to_unhide.append((pinlines, wholes, land))
                        layers_to_unhide.append(("Trim - VIS", modifications, land))

            elif is_dual:
                if cardname in original_dual_lands or setcode in ["LEA", "LEB", "2ED", "3ED"]:
                    # ABUR Duals (with the classic 'cascading squares' design in the rules box)
                    layers_to_unhide.append((thicker_trim_stroke, modifications, land))
                    abur_combined_groups = ["WU, UB, UR", "GU, BG, RG, GW"]
                    use_combined_group = None
                    for abur_group in abur_combined_groups:
                        pairs = abur_group.split(", ")
                        if pinlines in pairs:
                            use_combined_group = abur_group
                            break
                    if use_combined_group:
                        selected_abur_group = use_combined_group
                        abur_first_color = "".join(set.intersection(*map(set, selected_abur_group.split(", "))))
                        abur_second_color = pinlines.replace(abur_first_color, "")
                        groups_to_unhide.append((selected_abur_group, abur, land))
                        layers_to_unhide.append((abur_second_color, abur, land))
                    else:
                        selected_abur_group = pinlines
                        abur_second_color = "R" if pinlines in ["RW", "BR"] else "B"
                        groups_to_unhide.append((selected_abur_group, abur, land))
                        layers_to_unhide.append((abur_second_color, abur, land))
                elif setcode in ["TMP", "JUD"]:
                    # Dual lands without colored box, i.e. same box as colorless lands like Crystal Quarry. -- Examples: "Caldera Lake (TMP)", "Riftstone Portal (JUD)"
                    layers_to_unhide.append((land, wholes, land))
                    groups_to_unhide.append((neutral_land_frame_color, wholes, land))
                    layers_to_unhide.append((thickest_trim_stroke, modifications, land))
                    # pass  # TODO: Make sure this results in "Crystal Quarry" type frame for TMP and JUD duals like "Caldera Lake" and "Riftstone Portal"
                else:
                    # Regular duals (vertically split half-n-half color) -- Examples: Adarkar Wastes (6ED)
                    left_half = pinlines[0]
                    right_half = pinlines[1]
                    layers_to_unhide.append((land, wholes, land))
                    groups_to_unhide.append((neutral_land_frame_color, wholes, land))
                    groups_to_unhide.append((left_half, halves, land))
                    groups_to_unhide.append((right_half, wholes, land))
                    groups_to_unhide.append((thicker_bevels_rules_box, modifications, land))
                    layers_to_unhide.append((thicker_trim_stroke, modifications, land))

            elif is_mono:
                    # Monocolored lands with colored rules box -- Examples: Rushwood Grove (MMQ), Spawning Pool (ULG)
                    layers_to_unhide.append((land, wholes, land))
                    groups_to_unhide.append((neutral_land_frame_color, wholes, land))
                    groups_to_unhide.append((pinlines, wholes, land))
                    groups_to_unhide.append((thicker_bevels_rules_box, modifications, land))
                    layers_to_unhide.append((thickest_trim_stroke, modifications, land))
                    if setcode in ["5ED", "USG"]:
                        # Monocolored lands with colored rules box and YELLOW TRIM -- Examples: Hollow Trees (5ED)
                        layers_to_unhide.append(("Trim 5ED-USG", modifications, land))
                        if pinlines == "W":
                            layers_to_unhide.append(("W - Color Correction - 5ED-USG", pinlines, wholes, land))

            else:
                # Colorless lands (post-USG style) -- Examples: Crystal Quarry (ODY)
                layers_to_unhide.append((land, wholes, land))
                groups_to_unhide.append((neutral_land_frame_color, wholes, land))
                layers_to_unhide.append((thickest_trim_stroke, modifications, land))

            # Figure out which group or layer to unhide
            for group in groups_to_unhide:
                unhide(group, is_group=True)
            for layer in layers_to_unhide:
                unhide(layer)

