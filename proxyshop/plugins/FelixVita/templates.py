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

sets_with_set_symbol_lacking_outer_stroke = [
    # TODO: Test all of these
    "VIS",
    "ARN", # Probably
    "LEG", # Probably
    "POR",
    "ICE",
]

# Overwrite constants
con.set_symbol_library["ICE"] = ""  # Use ss-ice2 (instead of ss-ice)

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
            if self.centered: psd.frame_expansion_symbol(self.layer, self.reference, True)
            else: psd.frame_expansion_symbol(self.layer, self.reference, False)
        app.activeDocument.activeLayer = self.layer

        # Symbol stroke size (thickness)
        if self.setcode is None: symbol_stroke_size = cfg.cfg.symbol_stroke
        elif self.setcode in ["ICE", "DRK"]: symbol_stroke_size = 1
        elif self.setcode in sets_with_set_symbol_lacking_outer_stroke: symbol_stroke_size = 1

        # Symbol stroke color

        # symbol_stroke_color = psd.rgb_black if self.symbol_stroke_size <= 1 else psd.rgb_white

        # Symbol color
        if self.setcode in ["ICE"]: psd.apply_stroke(symbol_stroke_size, psd.rgb_white())
        elif self.setcode in sets_with_set_symbol_lacking_outer_stroke: psd.apply_stroke(symbol_stroke_size, psd.rgb_black())
        elif self.rarity == con.rarity_common or self.is_pre_exodus: psd.apply_stroke(symbol_stroke_size, psd.rgb_white())
        else:
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
        expansion_symbol = psd.getLayer(con.layers['EXPANSION_SYMBOL'], text_and_icons)
        try: expansion_reference = psd.getLayer(con.layers['EXPANSION_REFERENCE'], text_and_icons)
        except: expansion_reference = None
        for i, layer in enumerate(self.tx_layers):
            if isinstance(layer, txt_layers.ExpansionSymbolField):
                if setcode in sets_without_set_symbol:
                    del self.tx_layers[i]
                else:
                    self.tx_layers[i] = RetroExpansionSymbolField(
                        layer = expansion_symbol,
                        text_contents = self.symbol_char,
                        rarity = self.layout.rarity,
                        reference = expansion_reference,
                        is_pre_exodus = setcode in pre_exodus_sets,
                        has_hollow_set_symbol = setcode in sets_with_hollow_set_symbol,
                        setcode = setcode
                    )

    def enable_frame_layers (self):
        # Enable white border if scryfall says card border is white
        if self.layout.scryfall['border_color'] == 'white':
            psd.getLayer("WhiteBorder").visible = True
        # Hide set symbol for any cards from sets LEA, LEB, 2ED, 3ED, 4ED, and 5ED.
        if self.layout.set.upper() in sets_without_set_symbol:
            psd.getLayer("Expansion Symbol", "Text and Icons").visible = False
        super().enable_frame_layers()