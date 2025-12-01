# src/styles.py

import streamlit as st


def inject_custom_css() -> None:
    """
    Inject custom CSS to mimic a luxury car dashboard:
    dark background, rounded tiles, soft glow.
    """
    st.markdown(
        """
        <style>
        /* Global dark background */
        .stApp {
            background-color: #02040a;
        }

        /* Tighter layout */
        .block-container {
            padding-top: 1.5rem !important;
            padding-bottom: 1.5rem !important;
            padding-left: 1.75rem !important;
            padding-right: 1.75rem !important;
        }

        /* Headline style */
        h1, h2, h3, h4, h5 {
            color: #f5f7fb !important;
            letter-spacing: 0.04em;
        }

        /* Subtext style */
        .eg-subtext {
            color: #9ca3af;
            font-size: 0.85rem;
        }

        /* Main card tile */
        .eg-card {
            background: radial-gradient(circle at top left, #151824 0, #05060a 55%);
            border-radius: 24px;
            padding: 18px 20px;
            border: 1px solid #2a2d3a;
            box-shadow: 0 18px 45px rgba(0, 0, 0, 0.75);
        }

        /* Small pill card for stats */
        .eg-pill {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 12px;
            border-radius: 999px;
            background: #10121a;
            border: 1px solid #262938;
            font-size: 0.8rem;
            color: #e5e7eb;
        }

        /* Status colors */
        .eg-status-efficient {
            color: #7ee787;
        }
        .eg-status-moderate {
            color: #e9d26b;
        }
        .eg-status-poor {
            color: #fb7185;
        }

        /* Make widgets blend in better */
        .stSelectbox, .stMultiSelect, .stTextInput, .stFileUploader {
            background-color: transparent !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
