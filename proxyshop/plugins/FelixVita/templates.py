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

class RetroTemplate (temp.NormalClassicTemplate):
    """
     * Notes about my template here
     * Created by FelixVita
    """
    def template_file_name (self):
        return "FelixVita/retro"

    def template_suffix (self):
        return "Retro"

    # OPTIONAL
    def __init__ (self, layout, file):
        #     if self.layout['scryfall']['border_color'] == 'white':
        #         psd.getLayer("<layer name>", "<layer group, if its in a group>").visible = True
        #     else: psd.getLayer("<layer name>", "<layer group>").visible = False
        super().__init__(layout, file)

    # OPTIONAL
    def enable_frame_layers (self):
        if self.layout.scryfall['border_color'] == 'white':
            psd.getLayer("WhiteBorder").visible = True
        super().enable_frame_layers()