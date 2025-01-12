"""
CORE LAYOUTS
"""
import re
from functools import cached_property
from typing import Optional, Match, Union, Type

from src.constants import con
from src.settings import cfg
from src import scryfall as scry
from src.frame_logic import select_frame_layers, FrameDetails
from src.utils.strings import normalize_str

# Regex
leveler_regex = re.compile(
    r"(.*?)\nLEVEL (\d*-\d*)\n(\d*/\d*)\n(.*?)\nLEVEL (\d*\+)\n(\d*/\d*)\n(.*?)$"
)
class_regex = re.compile(r"(.+?): Level (\d)\n(.+)")


class NormalLayout:
    """
    Defines unified properties for all cards.
    """
    def __init__(self, scryfall: dict, file: dict):

        # settable properties
        self.file = file
        self.scryfall = scryfall
        self.filename = self.file['filename']
        self._template_path = ''

        # Cache mtgset early
        if self.mtgset:
            print(f"{self.name}: Valid set data has been generated.")
        else:
            print(f"{self.name}: No set data was available.")

    def __str__(self):
        return "{} [{}]".format(self.name, self.set)

    """
    SETTABLE
    """

    @property
    def filename(self) -> str:
        return self._filename

    @filename.setter
    def filename(self, value):
        self._filename = value

    @property
    def template_path(self) -> str:
        return self._template_path

    @template_path.setter
    def template_path(self, value: str):
        self._template_path = value

    """
    GAMEPLAY ITEMS
    """

    @cached_property
    def card(self) -> dict:
        # Double faced card?
        if 'card_faces' in self.scryfall:
            # First card face is the front side
            if normalize_str(self.scryfall['card_faces'][0]['name']) == normalize_str(self.name_raw):
                self.scryfall['card_faces'][0]['front'] = True
                return self.scryfall['card_faces'][0]
            # Second card face is the back side
            self.scryfall['card_faces'][1]['front'] = False
            return self.scryfall['card_faces'][1]
        # Non-MDFC cards are always front
        self.scryfall['front'] = True
        return self.scryfall

    @cached_property
    def frame_effects(self) -> list:
        return self.scryfall.get('frame_effects', [])

    @property
    def keywords(self) -> list:
        return self.scryfall.get('keywords', [])

    @cached_property
    def name(self) -> str:
        if self.lang != 'EN' and 'printed_name' in self.card:
            return self.card['printed_name']
        return self.card['name']

    @cached_property
    def name_raw(self) -> str:
        return self.file['name']

    @cached_property
    def mana_cost(self) -> Optional[str]:
        return self.card.get('mana_cost', '')

    @cached_property
    def oracle_text(self) -> str:
        # Alt lang?
        if self.lang != 'EN' and 'printed_text' in self.card:
            return self.card['printed_text'].replace(
                "\u2212", "-") if 'Planeswalker' in self.type_line_raw else self.card['printed_text']
        return self.card['oracle_text'].replace(
            "\u2212", "-") if 'Planeswalker' in self.type_line_raw else self.card['oracle_text']

    @cached_property
    def oracle_text_raw(self) -> str:
        return self.card['oracle_text']

    @cached_property
    def flavor_text(self) -> str:
        return self.card.get('flavor_text', '')

    @cached_property
    def type_line(self) -> str:
        if self.lang != 'EN' and 'printed_type_line' in self.card:
            return self.card['printed_type_line']
        return self.card['type_line']

    @cached_property
    def type_line_raw(self) -> str:
        return self.card['type_line']

    @cached_property
    def power(self) -> str:
        return self.card.get('power', None)

    @cached_property
    def toughness(self) -> str:
        return self.card.get('toughness', None)

    @cached_property
    def color_identity(self) -> list:
        return self.scryfall['color_identity']

    @cached_property
    def color_indicator(self) -> str:
        return self.card.get('color_indicator', None)

    @cached_property
    def loyalty(self) -> str:
        return self.card.get('loyalty', None)

    @cached_property
    def scryfall_scan(self) -> Optional[str]:
        if 'image_uris' in self.card:
            if 'large' in self.card['image_uris']:
                return self.card['image_uris']['large']
        return

    """
    COLLECTOR INFO
    """

    @cached_property
    def mtgset(self) -> dict:
        return scry.get_mtg_set(self.set) or {}

    @cached_property
    def set(self) -> str:
        return self.scryfall['set'].upper()

    @cached_property
    def rarity(self):
        if self.rarity_raw not in ['common', 'uncommon', 'rare', 'mythic']:
            return 'mythic'
        return self.rarity_raw

    @cached_property
    def rarity_raw(self) -> str:
        return self.scryfall['rarity']

    @cached_property
    def rarity_letter(self) -> str:
        return self.rarity[0:1].upper()

    @cached_property
    def lang(self) -> str:
        if 'lang' in self.scryfall:
            return self.scryfall['lang'].upper()
        return cfg.lang.upper()

    @cached_property
    def card_count(self) -> Optional[str]:
        # Get the lowest number
        least = min(
            int(self.mtgset.get('printed_size', 999999)),
            int(self.mtgset.get('baseSetSize', 999999)),
            int(self.mtgset.get('totalSetSize', 999999)),
            int(self.mtgset.get('card_count', 999999))
        )
        if least < int(self.collector_number):
            return

        # Ensure formatting of count
        if len(str(least)) == 2:
            return f"0{least}"
        elif len(str(least)) == 1:
            return f"00{least}"
        return str(least)

    @cached_property
    def collector_number(self) -> str:
        # Ensure number exists
        if self.scryfall.get('collector_number'):
            # Return number as a 3+ letter string
            num = ''.join(char for char in self.scryfall['collector_number'] if char.isdigit())
            if len(num) == 2:
                return f"0{num}"
            elif len(num) == 1:
                return f"00{num}"
            return num
        return '000'

    @cached_property
    def artist(self) -> str:
        # Custom artist given?
        if self.file.get('artist'):
            return self.file['artist']
        if "&" in self.card['artist']:
            count = []
            # John Smith & Jane Smith => John & Jane Smith
            for w in self.card['artist'].split(" "):
                if w in count:
                    count.remove(w)
                count.append(w)
            return " ".join(count)
        return self.card['artist']

    @cached_property
    def collector_info_top(self) -> str:
        if self.card_count:
            return f"{self.collector_number}/{self.card_count} {self.rarity_letter}"
        return f"{self.collector_number} {self.rarity_letter}"

    @cached_property
    def creator(self) -> str:
        return self.file['creator']

    @cached_property
    def symbol(self) -> str:
        # Automatic set symbol enabled?
        if not cfg.symbol_force_default and self.set in con.set_symbols:
            sym = con.set_symbols[self.set]
            # Check if this is a reference to another symbol
            if isinstance(sym, str) and len(sym) > 1 and sym in con.set_symbols:
                return con.set_symbols[sym]
            return sym
        elif not cfg.symbol_force_default and self.set[1:] in con.set_symbols:
            sym = con.set_symbols[self.set[1:]]
            # Check if this is a reference to another symbol
            if isinstance(sym, str) and len(sym) > 1 and sym in con.set_symbols:
                return con.set_symbols[sym]
            return sym
        return con.set_symbols.get(cfg.symbol_default, con.set_symbols['MTG'])

    @cached_property
    def watermark(self) -> str:
        return self.card.get('watermark')

    """
    BOOL
    """

    @cached_property
    def is_creature(self) -> bool:
        return bool(self.power and self.toughness)

    @cached_property
    def is_land(self) -> bool:
        return 'Land' in self.type_line

    @cached_property
    def is_legendary(self) -> bool:
        return 'Legendary' in self.type_line

    @cached_property
    def is_nyx(self) -> bool:
        return "nyxtouched" in self.frame_effects

    @cached_property
    def is_companion(self) -> bool:
        return "companion" in self.frame_effects

    @cached_property
    def is_colorless(self) -> bool:
        return self.frame['is_colorless']

    @cached_property
    def is_transform(self) -> bool:
        return False

    @cached_property
    def is_mdfc(self) -> bool:
        return False

    """
    FRAME PROPERTIES
    """

    @cached_property
    def frame(self) -> FrameDetails:
        return select_frame_layers(self.card)

    @cached_property
    def twins(self) -> str:
        return self.frame['twins']

    @cached_property
    def pinlines(self) -> str:
        return self.frame['pinlines']

    @cached_property
    def background(self) -> str:
        return self.frame['background']

    """
    DOUBLE FACE PROPERTIES
    """

    @cached_property
    def other_face(self) -> dict:
        if 'card_faces' in self.scryfall:
            if self.scryfall['card_faces'][0]['name'] == self.name_raw:
                return self.scryfall['card_faces'][1]
            return self.scryfall['card_faces'][0]
        return {}

    @cached_property
    def other_face_twins(self) -> Optional[str]:
        if self.other_face:
            return select_frame_layers(self.other_face)['twins']
        return

    @cached_property
    def transform_icon(self) -> Optional[str]:
        return

    @cached_property
    def other_face_power(self) -> Optional[str]:
        return self.other_face.get('power', None)

    @cached_property
    def other_face_toughness(self) -> Optional[str]:
        return self.other_face.get('toughness', None)

    @cached_property
    def other_face_left(self) -> Optional[str]:
        if not self.other_face:
            return
        if self.lang != "EN" and 'printed_type_line' in self.other_face:
            return self.other_face['printed_type_line'].split(" ")[-1]
        return self.other_face['type_line'].split(" ")[-1]

    @cached_property
    def other_face_right(self) -> Optional[str]:
        # Has another face?
        if not self.other_face:
            return

        # Other face is not a land
        if 'Land' not in self.other_face['type_line']:
            return self.other_face.get('mana_cost')

        # Other face is a land, find the mana tap ability
        other_face_oracle_text_split = self.other_face.get('oracle_text', '').split("\n")
        if len(other_face_oracle_text_split) > 1:
            # Find what color mana this land adds
            for line in other_face_oracle_text_split:
                if line[0:3] == "{T}":
                    return line.split(".")[0] + "."
        return self.other_face.get('oracle_text', '')

    """
    TEMPLATE CLASS
    """

    @cached_property
    def card_class(self) -> str:
        """
        Set the card's class (finer grained than layout). Used when selecting a template.
        """
        if "Planeswalker" in self.card['type_line']:
            return con.planeswalker_class
        elif "Mutate" in self.keywords:
            return con.mutate_class
        elif "Miracle" in self.frame_effects and cfg.render_miracle:
            return con.miracle_class
        elif "Prototype" in self.keywords:
            return con.prototype_class
        elif "Snow" in self.card['type_line'] and cfg.render_snow:
            # frame_effects doesn't contain "snow" for pre-KHM snow cards
            return con.snow_class
        return con.normal_class


class TransformLayout (NormalLayout):
    """
    Used for transform cards
    """

    @cached_property
    def card_class(self) -> str:
        # Planeswalker transform
        if 'Planeswalker' in self.card['type_line']:
            if self.card['front']:
                return con.pw_tf_front_class
            return con.pw_tf_back_class
        # Saga transform
        if 'Saga' in self.card['type_line']:
            return con.saga_class
        # Normal transform
        if not self.card['front']:
            # Is back face an Ixalan land?
            if self.transform_icon == 'compasslanddfc':
                return con.ixalan_class
            return con.transform_back_class
        return con.transform_front_class

    """
    BOOL PROPERTIES
    """

    @cached_property
    def is_transform(self) -> bool:
        return True

    """
    OVERWRITE
    """

    @cached_property
    def transform_icon(self) -> str:
        # Safe to assume the first frame effect will be the transform icon?
        if 'frame_effects' in self.scryfall:
            if self.scryfall['frame_effects'][0] != "legendary":
                return self.scryfall['frame_effects'][0]
        return 'land' if 'Land' in self.type_line_raw else 'sunmoondfc'

    """
    SAGA
    """

    @cached_property
    def saga_lines(self) -> list:
        # Not a saga?
        if 'Saga' not in self.type_line_raw:
            return []
        # Unpack oracle text into saga lines
        abilities: list[dict] = []
        for i, line in enumerate(self.oracle_text.split("\n")[1:]):
            icons, text = line.split(" \u2014 ", 1)
            abilities.append({
                "text": text,
                "icons": icons.split(", ")
            })
        return abilities

    @cached_property
    def saga_description(self) -> str:
        # Not a saga?
        if 'Saga' not in self.type_line_raw:
            return ''
        return self.oracle_text.split("\n")[0]


class MeldLayout (NormalLayout):
    """
    Used for Meld cards
    """

    @cached_property
    def card_class(self) -> str:
        # Planeswalker transform
        if 'Planeswalker' in self.card['type_line']:
            if self.card['front']:
                return con.pw_tf_front_class
            return con.pw_tf_back_class
        # Normal transform
        if self.card['front']:
            return con.transform_front_class
        return con.transform_back_class

    """
    BOOL PROPERTIES
    """

    @cached_property
    def is_transform(self) -> bool:
        return True

    """
    OVERWRITE
    """

    @cached_property
    def card(self) -> dict:
        for face in self.scryfall['faces']:
            if normalize_str(face['name']) == normalize_str(self.scryfall['name']):
                if face['component'] == 'meld_result':
                    face['front'] = False
                    return face
                face['front'] = True
                return face

    @cached_property
    def other_face(self) -> Optional[dict]:
        if self.card['front']:
            for face in self.scryfall['faces']:
                if face['component'] == 'meld_result':
                    return face
        return {}

    @cached_property
    def transform_icon(self) -> str:
        # Safe to assume the first frame effect will be the transform icon?
        if 'frame_effects' in self.card:
            if self.card['frame_effects'][0] != "legendary":
                return self.card['frame_effects'][0]
        return 'meld'


class ModalDoubleFacedLayout (NormalLayout):
    """
    Used for Modal Double Faced cards
    """

    @cached_property
    def card_class(self) -> str:
        # Planeswalker MDFC
        if 'Planeswalker' in self.type_line:
            if self.card['front']:
                return con.pw_mdfc_front_class
            return con.pw_mdfc_back_class
        # Normal MDFC
        if self.card['front']:
            return con.mdfc_front_class
        return con.mdfc_back_class

    """
    BOOL PROPERTIES
    """

    @cached_property
    def is_mdfc(self) -> bool:
        return True

    """
    OVERWRITE
    """

    @cached_property
    def oracle_text(self) -> Optional[str]:

        # In alt lang text of both sides is combined, we must separate
        if self.lang != "EN" and 'printed_text' in self.card:
            text = self.card['printed_text']
            num_breaks = self.card['oracle_text'].count('\n')
            if text.count('\n') > num_breaks:
                text = text.split('\n', num_breaks + 1)
                text.pop()
                text = '\n'.join(text)
        else:
            text = self.card['oracle_text']

        # Planeswalker?
        return text.replace("\u2212", "-") if 'Planeswalker' in self.type_line_raw else text

    @cached_property
    def transform_icon(self) -> str:
        return "modal_dfc"


class AdventureLayout (NormalLayout):
    """
    Used for Adventure cards
    """

    @cached_property
    def card_class(self) -> str:
        return con.adventure_class

    """
    Unique Properties
    """

    @cached_property
    def adventure(self) -> dict:
        return {
            'name': self.scryfall['card_faces'][1]['name'],
            'mana_cost': self.scryfall['card_faces'][1]['mana_cost'],
            'type_line': self.scryfall['card_faces'][1]['type_line'],
            'oracle_text': self.scryfall['card_faces'][1]['oracle_text']
        }


class LevelerLayout (NormalLayout):
    """
    Used for Leveler cards
    """

    @cached_property
    def card_class(self) -> str:
        return con.leveler_class

    """
    Unique Properties
    """

    @cached_property
    def leveler_match(self) -> Optional[Match[str]]:
        # Unpack oracle text into: level text, levels x-y text, levels z+ text, middle level,
        # middle level power/toughness, bottom level, and bottom level power/toughness
        return leveler_regex.match(self.oracle_text)

    @cached_property
    def level_up_text(self) -> str:
        return self.leveler_match[1]

    @cached_property
    def middle_level(self) -> str:
        return self.leveler_match[2]

    @cached_property
    def middle_power_toughness(self) -> str:
        return self.leveler_match[3]

    @cached_property
    def levels_x_y_text(self) -> str:
        return self.leveler_match[4]

    @cached_property
    def bottom_level(self) -> str:
        return self.leveler_match[5]

    @cached_property
    def bottom_power_toughness(self) -> str:
        return self.leveler_match[6]

    @cached_property
    def levels_z_plus_text(self) -> str:
        return self.leveler_match[7]


class SagaLayout (NormalLayout):
    """
    Used for Saga cards
    """

    @cached_property
    def card_class(self) -> str:
        return con.saga_class

    """
    Unique Properties
    """

    @cached_property
    def saga_lines(self) -> list:
        # Unpack oracle text into saga lines
        abilities: list[dict] = []
        for i, line in enumerate(self.oracle_text.split("\n")[1:]):
            icons, text = line.split(" \u2014 ", 1)
            abilities.append({
                "text": text,
                "icons": icons.split(", ")
            })
        return abilities

    @cached_property
    def saga_description(self) -> str:
        return self.oracle_text.split("\n")[0]


class ClassLayout (NormalLayout):
    """
    Used for Class cards.
    """

    @cached_property
    def card_class(self) -> str:
        return con.class_class

    """
    Unique Properties
    """

    @cached_property
    def class_lines(self):
        # Split the lines, add first static line
        lines = self.oracle_text.split("\n")
        abilities: list[dict] = [{'text': lines[1], "cost": None, "level": 1}]

        # Set up the dynamic lines
        lines = ["\n".join(lines[i:i+2]) for i in range(0, len(lines), 2)][1:]
        for line in lines:
            details = class_regex.match(line)
            abilities.append({
                'cost': details[1],
                'level': details[2],
                'text': details[3]
            })

        return abilities


class PlanarLayout (NormalLayout):
    """
    Used for Planar cards
    """

    @cached_property
    def card_class(self) -> str:
        return con.planar_class


class BasicLandLayout (NormalLayout):
    """
    No special data entry, just a basic land
    """
    def __init__(self, scryfall: dict,  file: dict):
        # Add artist to Scryfall data
        scryfall['artist'] = file['artist'] or 'Unknown'
        scryfall['creator'] = file['creator'] or None
        super().__init__(scryfall, file)

    @property
    def card_class(self) -> str:
        # Always use basic land
        return con.basic_class

    """
    COLLECTOR
    """

    @property
    def mtgset(self):
        return {}

    """
    BOOL
    """

    @property
    def is_creature(self):
        return False

    @property
    def is_land(self):
        return True

    @property
    def is_nyx(self):
        return False

    @property
    def is_companion(self):
        return False

    @property
    def is_legendary(self):
        return False

    """
    SETTABLE
    """

    @property
    def filename(self) -> str:
        return self._filename

    @filename.setter
    def filename(self, value):
        self._filename = value


# Types
CardLayout = Union[
    NormalLayout,
    TransformLayout,
    ModalDoubleFacedLayout,
    AdventureLayout,
    LevelerLayout,
    SagaLayout,
    ClassLayout,
    PlanarLayout,
    MeldLayout,
    BasicLandLayout
]

# LAYOUT MAP
layout_map: dict[str, Type[CardLayout]] = {
    "normal": NormalLayout,
    "transform": TransformLayout,
    "modal_dfc": ModalDoubleFacedLayout,
    "adventure": AdventureLayout,
    "leveler": LevelerLayout,
    "saga": SagaLayout,
    "class": ClassLayout,
    "planar": PlanarLayout,
    "meld": MeldLayout,
    'basic': BasicLandLayout
}
