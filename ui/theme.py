"""
SetCursor — Material Design 3 Theme System

Dark and light themes with teal/cyan primary and deep purple accent colors.
"""

# ─── Color Tokens ───────────────────────────────────────────────────────────

COLORS = {
    "primary": "#00BFA5",
    "primary_hover": "#00D9BC",
    "primary_pressed": "#00A892",
    "primary_dim": "rgba(0, 191, 165, 0.15)",
    "accent": "#7C4DFF",
    "accent_hover": "#9C6FFF",
    "success": "#4CAF50",
    "error": "#EF5350",
    "warning": "#FFA726",
}

DARK = {
    "name": "dark",
    "background": "#1E1E2E",
    "surface": "#2A2A3C",
    "surface_elevated": "#35354A",
    "card": "#313145",
    "card_hover": "#3A3A52",
    "card_border": "#44445A",
    "text": "#E8E8F0",
    "text_secondary": "#A0A0B8",
    "text_dim": "#6C6C84",
    "border": "#3E3E54",
    "drop_zone_bg": "#252538",
    "drop_zone_border": "#44445A",
    "drop_zone_hover_bg": "rgba(0, 191, 165, 0.08)",
    "drop_zone_hover_border": "#00BFA5",
    "scrollbar_bg": "#2A2A3C",
    "scrollbar_handle": "#44445A",
    "scrollbar_handle_hover": "#55556A",
    "input_bg": "#252538",
    "shadow": "rgba(0, 0, 0, 0.35)",
}

LIGHT = {
    "name": "light",
    "background": "#F5F5FA",
    "surface": "#FFFFFF",
    "surface_elevated": "#FFFFFF",
    "card": "#FFFFFF",
    "card_hover": "#F0F0F5",
    "card_border": "#E0E0E8",
    "text": "#1A1A2E",
    "text_secondary": "#5A5A72",
    "text_dim": "#9090A8",
    "border": "#E0E0E8",
    "drop_zone_bg": "#FAFAFE",
    "drop_zone_border": "#D0D0D8",
    "drop_zone_hover_bg": "rgba(0, 191, 165, 0.06)",
    "drop_zone_hover_border": "#00BFA5",
    "scrollbar_bg": "#F0F0F5",
    "scrollbar_handle": "#D0D0D8",
    "scrollbar_handle_hover": "#B8B8C4",
    "input_bg": "#FAFAFE",
    "shadow": "rgba(0, 0, 0, 0.08)",
}


# ─── Typography ─────────────────────────────────────────────────────────────

FONT_FAMILY = "'Inter', 'Segoe UI', 'Roboto', 'Helvetica Neue', sans-serif"


# ─── Stylesheet Generator ──────────────────────────────────────────────────

def generate_stylesheet(theme: dict) -> str:
    """Generate a complete QSS stylesheet for the given theme dict."""
    t = theme  # shorthand
    c = COLORS

    return f"""
    /* ── Global ──────────────────────────────────────────── */
    QWidget {{
        font-family: {FONT_FAMILY};
        font-size: 13px;
        color: {t['text']};
        background-color: transparent;
    }}

    QMainWindow {{
        background-color: {t['background']};
    }}

    /* ── Scroll Area ─────────────────────────────────────── */
    QScrollArea {{
        border: none;
        background-color: transparent;
    }}
    QScrollArea > QWidget > QWidget {{
        background-color: transparent;
    }}
    QScrollBar:vertical {{
        background: {t['scrollbar_bg']};
        width: 8px;
        margin: 4px 2px;
        border-radius: 4px;
    }}
    QScrollBar::handle:vertical {{
        background: {t['scrollbar_handle']};
        min-height: 30px;
        border-radius: 4px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {t['scrollbar_handle_hover']};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: none;
    }}

    /* ── Labels ──────────────────────────────────────────── */
    QLabel {{
        background-color: transparent;
        padding: 0;
    }}
    QLabel#title_label {{
        font-size: 18px;
        font-weight: 700;
        color: {t['text']};
    }}
    QLabel#subtitle_label {{
        font-size: 12px;
        color: {t['text_secondary']};
    }}
    QLabel#drop_title {{
        font-size: 16px;
        font-weight: 600;
        color: {t['text_secondary']};
    }}
    QLabel#drop_subtitle {{
        font-size: 12px;
        color: {t['text_dim']};
    }}
    QLabel#card_name {{
        font-size: 14px;
        font-weight: 600;
        color: {t['text']};
    }}
    QLabel#card_info {{
        font-size: 11px;
        color: {t['text_secondary']};
    }}
    QLabel#card_status {{
        font-size: 11px;
        font-weight: 600;
    }}
    QLabel#status_queued {{
        color: {t['text_dim']};
    }}
    QLabel#status_converting {{
        color: {c['primary']};
    }}
    QLabel#status_done {{
        color: {c['success']};
    }}
    QLabel#status_error {{
        color: {c['error']};
    }}
    QLabel#preview_label {{
        font-size: 10px;
        color: {t['text_secondary']};
        padding-top: 2px;
    }}
    QLabel#result_summary {{
        font-size: 12px;
        color: {t['text_secondary']};
        padding: 4px 0;
    }}
    QLabel#output_path_label {{
        font-size: 11px;
        color: {t['text_dim']};
        padding: 2px 0;
    }}

    /* ── Buttons ─────────────────────────────────────────── */
    QPushButton {{
        border: none;
        border-radius: 10px;
        padding: 10px 24px;
        font-size: 13px;
        font-weight: 600;
        background-color: {c['primary']};
        color: #FFFFFF;
    }}
    QPushButton:hover {{
        background-color: {c['primary_hover']};
    }}
    QPushButton:pressed {{
        background-color: {c['primary_pressed']};
    }}
    QPushButton:disabled {{
        background-color: {t['border']};
        color: {t['text_dim']};
    }}

    QPushButton#browse_button {{
        background-color: {t['surface_elevated']};
        color: {c['primary']};
        border: 1px solid {t['border']};
        padding: 8px 20px;
        border-radius: 8px;
        font-size: 12px;
    }}
    QPushButton#browse_button:hover {{
        background-color: {t['card_hover']};
        border-color: {c['primary']};
    }}

    QPushButton#output_button {{
        background-color: {t['surface_elevated']};
        color: {t['text']};
        border: 1px solid {t['border']};
        padding: 8px 16px;
        border-radius: 8px;
        font-size: 12px;
        font-weight: 500;
    }}
    QPushButton#output_button:hover {{
        border-color: {c['primary']};
        color: {c['primary']};
    }}

    QPushButton#convert_button {{
        padding: 12px 32px;
        font-size: 14px;
        border-radius: 12px;
    }}

    QPushButton#install_button {{
        background-color: {c['accent']};
        padding: 8px 16px;
        border-radius: 8px;
        font-size: 12px;
    }}
    QPushButton#install_button:hover {{
        background-color: {c['accent_hover']};
    }}

    QPushButton#open_folder_button {{
        background-color: {t['surface_elevated']};
        color: {t['text']};
        border: 1px solid {t['border']};
        padding: 8px 16px;
        border-radius: 8px;
        font-size: 12px;
        font-weight: 500;
    }}
    QPushButton#open_folder_button:hover {{
        border-color: {c['primary']};
        color: {c['primary']};
    }}

    QPushButton#remove_button {{
        background-color: transparent;
        color: {t['text_dim']};
        border: none;
        padding: 4px 8px;
        border-radius: 6px;
        font-size: 16px;
        font-weight: 400;
    }}
    QPushButton#remove_button:hover {{
        background-color: rgba(239, 83, 80, 0.15);
        color: {c['error']};
    }}

    QPushButton#theme_toggle {{
        background-color: {t['surface_elevated']};
        border: 1px solid {t['border']};
        border-radius: 8px;
        padding: 6px 10px;
        font-size: 16px;
        min-width: 36px;
        max-width: 36px;
        min-height: 36px;
        max-height: 36px;
    }}
    QPushButton#theme_toggle:hover {{
        border-color: {c['primary']};
        background-color: {t['card_hover']};
    }}

    /* ── Progress Bar ────────────────────────────────────── */
    QProgressBar {{
        background-color: {t['border']};
        border: none;
        border-radius: 3px;
        max-height: 6px;
        min-height: 6px;
        text-align: center;
    }}
    QProgressBar::chunk {{
        background: qlineargradient(
            x1:0, y1:0, x2:1, y2:0,
            stop:0 {c['primary']},
            stop:1 {c['accent']}
        );
        border-radius: 3px;
    }}

    /* ── Frames (Cards) ──────────────────────────────────── */
    QFrame#folder_card {{
        background-color: {t['card']};
        border: 1px solid {t['card_border']};
        border-radius: 12px;
    }}
    QFrame#folder_card:hover {{
        background-color: {t['card_hover']};
        border-color: {c['primary_dim'].replace('0.15', '0.3')};
    }}

    QFrame#preview_frame {{
        background-color: {t['surface']};
        border: 1px solid {t['border']};
        border-radius: 8px;
        padding: 8px;
    }}

    QFrame#drop_zone_frame {{
        background-color: {t['drop_zone_bg']};
        border: 2px dashed {t['drop_zone_border']};
        border-radius: 16px;
    }}

    QFrame#bottom_bar {{
        background-color: {t['surface']};
        border-top: 1px solid {t['border']};
        border-radius: 0px;
    }}

    QFrame#separator {{
        background-color: {t['border']};
        max-height: 1px;
        min-height: 1px;
    }}

    /* ── Tooltips ─────────────────────────────────────────── */
    QToolTip {{
        background-color: {t['surface_elevated']};
        color: {t['text']};
        border: 1px solid {t['border']};
        border-radius: 6px;
        padding: 6px 10px;
        font-size: 12px;
    }}
    """
