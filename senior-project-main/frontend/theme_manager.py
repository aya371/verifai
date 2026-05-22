import os

STREAMLIT_CONFIG = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".streamlit", "config.toml")

DARK_THEME = '[theme]\nbase = "dark"\nprimaryColor = "#38bdf8"\nbackgroundColor = "#080f17"\nsecondaryBackgroundColor = "#111f2e"\ntextColor = "#f1f8ff"\nfont = "monospace"\n'

LIGHT_THEME = '[theme]\nbase = "light"\nprimaryColor = "#0284c7"\nbackgroundColor = "#f0f6ff"\nsecondaryBackgroundColor = "#e1eaf5"\ntextColor = "#0f172a"\nfont = "monospace"\n'

def set_theme(theme: str):
    os.makedirs(os.path.dirname(STREAMLIT_CONFIG), exist_ok=True)
    with open(STREAMLIT_CONFIG, "w", encoding="utf-8", newline="\n") as f:
        f.write(DARK_THEME if theme == "dark" else LIGHT_THEME)