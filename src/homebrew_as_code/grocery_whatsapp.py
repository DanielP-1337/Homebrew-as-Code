"""Offline, human-reviewed WhatsApp text for the grocery channel only.

This adapter makes purchase suggestions, not claims of exact retail pack sizes.
No messaging, external process, login, or network access.
"""
from __future__ import annotations

from typing import Any

from .supplier_split import split_request

# Explicit, human-readable retail advice. These descriptions are purchase
# suggestions, not weights to add to the brew. Keep recipe grams alongside.
GROCERY_GUIDANCE = {
    'Mild honey': ('Milder Honig', '250 g benötigt; möglichst milde Sorte'),
    'Ceylon cinnamon sticks': ('Ceylon-Zimtstangen', '1 kleine Packung; 5 g benötigt; echten Ceylon-Zimt'),
    'Fresh ginger': ('Frischer Ingwer', '1 kleines Stück; ca. 12 g benötigt'),
    'Whole cloves': ('Ganze Gewürznelken', '1 kleines Gewürzgläschen; 0,2 g benötigt; nicht gemahlen'),
    'Nutmeg': ('Ganze Muskatnuss', '1 Nuss; 0,3 g benötigt; nicht gemahlen'),
    'Orange zest': ('Unbehandelte Bio-Orange', '1 Stück; ca. 8 g Schalenabrieb benötigt'),
}


def render_whatsapp(recipe: dict[str, Any], catalog: dict[str, Any]) -> str:
    """Render one copy-and-paste message, refusing unfamiliar groceries.

    The supplier split is the classification source of truth. Never route other
    channels into this message or silently omit newly classified groceries.
    """
    channels, _report = split_request(recipe, catalog)
    grocery = channels['grocery']['positions']
    names = [row['ingredient'] for row in grocery]
    if not names:
        raise ValueError('No grocery items in supplier split')
    if len(names) != len(set(names)) or set(names) != set(GROCERY_GUIDANCE):
        raise ValueError('Grocery guidance requires review after ingredient changes')
    lines = [f"🛒 Einkaufsliste – {recipe['recipe']['name']}", '',
             'Für Supermarkt oder Wochenmarkt:', '']
    for row in grocery:
        label, hint = GROCERY_GUIDANCE[row['ingredient']]
        lines.append(f'☐ {label} – {hint}')
    lines += ['', 'Wichtig: Gewürze möglichst ganz/ungemahlen kaufen.',
              'Falls etwas nicht eindeutig ist oder fehlt: bitte kurz nachfragen. 😊']
    return '\n'.join(lines) + '\n'
