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

pre_exodus_sets = [
    "LEA",
    "LEB",
    "2ED",
    "ARN",
    "ATQ",
    "3ED",
    "LEG",
    "DRK",
    "FEM",
    "4ED",
    "ICE",
    "CHR",
    "HML",
    "ALL",
    "MIR",
    "VIS",
    "5ED",
    "POR",
    "WTH",
    "TMP",
    "STH",
]

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
    def __init__ (self, layer, text_contents, rarity, reference, centered=False, is_pre_exodus=None, has_hollow_set_symbol=None, setcode=None):
        super().__init__(layer, text_contents, psd.rgb_black())
        self.centered = centered
        self.rarity = rarity
        self.reference = reference
        self.is_pre_exodus = is_pre_exodus
        self.has_hollow_set_symbol = has_hollow_set_symbol
        self.setcode = setcode
        if rarity in (con.rarity_bonus, con.rarity_special):
            self.rarity = con.rarity_mythic

    def execute (self):
        super().execute()

        # Size to fit reference?
        if cfg.cfg.auto_symbol_size:
            scale_percent = 70 if self.setcode in ["ATQ", "FEM"] else 100
            if self.centered: frame_expansion_symbol_customscale(self.layer, self.reference, True, scale_percent)
            else: frame_expansion_symbol_customscale(self.layer, self.reference, False, scale_percent)
        app.activeDocument.activeLayer = self.layer

        # Symbol stroke size (thickness)
        symbol_stroke_size = cfg.cfg.symbol_stroke
        # Special cases
        if self.setcode == "DRK": symbol_stroke_size = 2
        elif self.setcode == "EXO": symbol_stroke_size = str(int(symbol_stroke_size) + 2)

        # Make RetroExpansionGroup the active layer
        text_and_icons = psd.getLayerSet(con.layers['TEXT_AND_ICONS'])
        retro_expansion_group = psd.getLayerSet("RetroExpansionGroup", text_and_icons)
        app.activeDocument.activeLayer = retro_expansion_group

        # Apply set symbol stroke (white/black) and rarity color (silver/gold/mythic)
        if self.setcode in sets_lacking_symbol_stroke: pass  # Apply neither
        elif self.rarity == con.rarity_common or self.is_pre_exodus: psd.apply_stroke(symbol_stroke_size, psd.rgb_white())  # Apply white stroke only
        else:
            # Apply white stroke and rarity color
            mask_layer = psd.getLayer(self.rarity, self.layer.parent)
            mask_layer.visible = True
            psd.apply_stroke(symbol_stroke_size, psd.rgb_white())
            psd.select_layer_pixels(self.layer)
            app.activeDocument.activeLayer = mask_layer
            psd.align_horizontal()
            psd.align_vertical()
            psd.clear_selection()

        # Fill in the expansion symbol?
        if cfg.cfg.fill_symbol and not self.has_hollow_set_symbol:
            app.activeDocument.activeLayer = self.layer
            psd.fill_expansion_symbol(self.reference, psd.rgb_white())


class RetroNinetysevenTemplate (temp.NormalClassicTemplate):
    """
     * Notes about my template here
     * Created by FelixVita
    """
    def template_file_name (self):
        return "FelixVita/retro-1997"

    def template_suffix (self):
        return "Retro-1997"

    # OPTIONAL
    def __init__ (self, layout, file):
        #     if self.layout['scryfall']['border_color'] == 'white':
        #         psd.getLayer("<layer name>", "<layer group, if its in a group>").visible = True
        #     else: psd.getLayer("<layer name>", "<layer group>").visible = False
        super().__init__(layout, file)
        # Overwrite the expansion symbol field text layer using custom class
        setcode = layout.set.upper()
        text_and_icons = psd.getLayerSet(con.layers['TEXT_AND_ICONS'])
        retro_expansion_group = psd.getLayerSet("RetroExpansionGroup", text_and_icons)
        expansion_symbol = psd.getLayer(con.layers['EXPANSION_SYMBOL'], retro_expansion_group)
        try: expansion_reference = psd.getLayer(con.layers['EXPANSION_REFERENCE'], text_and_icons)
        except: expansion_reference = None
        for i, layer in enumerate(self.tx_layers):
            if isinstance(layer, txt_layers.ExpansionSymbolField):
                if setcode in sets_without_set_symbol:
                    del self.tx_layers[i]
                else:
                    self.tx_layers[i] = RetroExpansionSymbolField(
                        layer = expansion_symbol,
                        text_contents = self.layout.symbol,
                        rarity = self.layout.rarity,
                        reference = expansion_reference,
                        is_pre_exodus = setcode in pre_exodus_sets,
                        has_hollow_set_symbol = setcode in sets_with_hollow_set_symbol,
                        setcode = setcode
                    )


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
                psd.getLayer("Brighter Left & Bottom Frame Bevels", "Nonland").visible = True  # TODO: Fix this since it is probably what is causing "Oppression" to fail.
        # Hide set symbol for any cards from sets LEA, LEB, 2ED, 3ED, 4ED, and 5ED.
        if setcode in sets_without_set_symbol or setcode == "ALL":
            text_and_icons = psd.getLayerSet(con.layers['TEXT_AND_ICONS'])
            psd.getLayerSet("RetroExpansionGroup", text_and_icons).visible = False
        if setcode in ["DRK", "ATQ", "LEG", ] and self.layout.scryfall['colors'] == ["B"]:
            psd.getLayer("B - DRK Brightness", "Nonland").visible = True
            psd.getLayer("B - DRK Color Balance", "Nonland").visible = True
        if "Flashback" in self.layout.keywords:
            psd.getLayer("Tombstone").visible = True
        # super().enable_frame_layers()
        if not self.is_land:
            layer_set = psd.getLayerSet(con.layers['NONLAND'])
            selected_layer = self.layout.background
            psd.getLayer(selected_layer, layer_set).visible = True
        elif self.is_land:
            land = con.layers['LAND']
            abur = "ABUR Duals (ME4)"
            wholes = "Wholes for regular duals and monocolors"
            halves = "Halves for regular duals"
            uniques = "Uniques"
            thicker_trim_stroke = "Trim - Thicker Outer Black Stroke (2px)"
            thickest_trim_stroke = "Trim - Thickest Outer Black Stroke (3px)"
            pinlines: str = self.layout.pinlines
            print(f"{pinlines=}")
            is_dual = len(pinlines) == 2
            is_mono = len(pinlines) == 1
            groups_to_unhide = []
            layers_to_unhide = []

            if setcode in special_land_frames.keys() and not (setcode == "VIS" and is_mono):
                if setcode in ["ARN", "ATQ", "ALL", "FEM", "DRK", "HML"]:
                    layers_to_unhide.append((thicker_trim_stroke, land))
                    groups_to_unhide.append((wholes, land))
                    layers_to_unhide.append((land, wholes, land))
                    groups_to_unhide.append((setcode + " - Color", wholes, land))
                    if setcode in ["FEM", "ALL"]:
                        groups_to_unhide.append(("Trim - " + setcode, land))
                    if setcode == "ALL":
                        layers_to_unhide(("Set Symbol - Alliances"))
                else:
                    if setcode == "VIS":
                        groups_to_unhide.append((wholes, land))
                        groups_to_unhide.append(("Land - Visions", wholes, land))
                        layers_to_unhide.append(("Rules Box - Inner - Mirage - NoText - Enhanced", wholes, land))
                        # unique_frame = unique_frame.replace("Visions", "Mirage")  # Use the MIR frame for colorless VIS lands.
                    else:
                        groups_to_unhide.append((uniques, land))
                        unique_frame = "Land " + special_land_frames[setcode].replace(" ", "")
                        if setcode in ["LEG", "4ED"]:
                            groups_to_unhide.append((unique_frame, uniques, land))
                        else:
                            layers_to_unhide.append((unique_frame, uniques, land))

            elif is_dual:
                if cardname in original_dual_lands or setcode in ["LEA", "LEB", "2ED", "3ED"]:
                    groups_to_unhide.append((abur, land))
                    abur_combined_groups = ["WU, UB, UR", "GU, BG, RG, GW"]
                    use_combined_group = None
                    for abur_group in abur_combined_groups:
                        pairs = abur_group.split(", ")
                        if pinlines in pairs:
                            use_combined_group = abur_group
                            break
                    if use_combined_group:
                        selected_abur_group = use_combined_group
                        groups_to_unhide.append((selected_abur_group, abur, land))
                        abur_first_color = "".join(set.intersection(*map(set, selected_abur_group.split(", "))))
                        abur_second_color = pinlines.replace(abur_first_color, "")
                        layers_to_unhide.append((abur_second_color, abur, land))
                    else:
                        selected_abur_group = pinlines
                        groups_to_unhide.append((selected_abur_group, abur, land))
                        abur_second_color = "R" if pinlines in ["RW", "BR"] else "B"
                        layers_to_unhide.append((abur_second_color, abur, land))
                else:
                    groups_to_unhide.append((halves, land))
                    groups_to_unhide.append((wholes, land))
                    groups_to_unhide.append(("Land - Color", wholes, land))
                    left_half = pinlines[0] + "_"
                    layers_to_unhide.append((left_half, halves, land))
                    right_half = pinlines[1]
                    layers_to_unhide.append((right_half, wholes, land))
                    layers_to_unhide.append((land, wholes, land))
                    layers_to_unhide.append((thicker_trim_stroke, land))

            elif is_mono:
                if setcode == "VIS":
                    groups_to_unhide.append((wholes, land))
                    layers_to_unhide.append((thicker_trim_stroke, land))
                    layers_to_unhide.append((pinlines, wholes, land))
                    layers_to_unhide.append(("Land - Visions", wholes, land))
                if setcode in ["5ED", "USG"]:
                    groups_to_unhide.append((wholes, land))
                    layers_to_unhide.append((pinlines, wholes, land))
                    layers_to_unhide.append((land, wholes, land))
                    layers_to_unhide.append(("Trim 5ED-USG", wholes, land))
                    layers_to_unhide.append(("W - Color Correction - 5ED-USG", wholes, land))
                    layers_to_unhide.append((thickest_trim_stroke, land))

            else:
                groups_to_unhide.append((wholes, land))
                groups_to_unhide.append(("Land - Color", wholes, land))
                layers_to_unhide.append((land, wholes, land))
                layers_to_unhide.append((thickest_trim_stroke, land))

            # Figure out which group or layer to unhide
            for group in groups_to_unhide:
                unhide(group, is_group=True)
            for layer in layers_to_unhide:
                unhide(layer)

            # if selected_group:
            #     layer_set = psd.getLayerSet(selected_group, con.layers['LAND'])
            #     if selected_inner_group:
            #         layer_set.visible = True
            #         layer_set = psd.getLayerSet(selected_inner_group, layer_set)
            #     layer_set.visible = True
            # if selected_layer:
            #     if selected_layer_is_from_inner:
            #         selected_layer = psd.getLayer(selected_layer, selected_inner_group)
            #     elif selected_group:
            #         selected_layer = psd.getLayer(selected_layer, selected_group)
            #     else:
            #         selected_layer = psd.getLayer(selected_layer)
            #     selected_layer.visible = True
