# core/utils_text.py
import textwrap

def wrap_text_to_width(text: str, max_width_px: float, font_size: int = 18):
    """
    Approximates wrapping by converting pixel width → max characters.
    Works on all Arcade versions without needing text measurement.
    """
    approx_char_width = font_size * 0.6  # heuristique : 0.6 * font_size
    max_chars = max(1, int(max_width_px / approx_char_width))
    return textwrap.wrap(text, width=max_chars)


def wrap_dialog_history(dialog_history, max_width_px: float, font_size: int = 18):
    """
    Transforme l'historique [(speaker, msg), ...] en une liste de lignes déjà wrap.
    Chaque entrée est un simple string prêt à être affiché.
    """
    lines = []
    for speaker, message in dialog_history:
        full = f"{speaker}: {message}"
        wrapped = wrap_text_to_width(full, max_width_px, font_size)
        lines.extend(wrapped)
        lines.append("")
    return lines


def count_wrapped_lines(dialog_history, max_width_px: float, font_size: int = 18):
    """Nombre total de lignes une fois le wrapping appliqué."""
    return len(wrap_dialog_history(dialog_history, max_width_px, font_size))
