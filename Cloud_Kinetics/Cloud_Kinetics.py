"""Welcome to Reflex! This file outlines the steps to create a basic app."""

import reflex as rx
import reflex_chakra as rc

from Cloud_Kinetics.components import chat, navbar
from Cloud_Kinetics.components.chat import action_bar
from Cloud_Kinetics.pages.upload_page import upload_page

from rxconfig import config


class State(rx.State):
    """The app state."""

    ...

def index() -> rx.Component:
    """The main app."""
    return rc.vstack(
        navbar.navbar(),
        chat.chat(),
        action_bar(),
        background_color=rx.color("mauve", 1),
        color=rx.color("mauve", 12),
        min_height="100vh",
        align_items="stretch",
        spacing="0",
    )

app = rx.App()
# app.add_page(index)
app.add_page(index, route="/")
app.add_page(upload_page, route="/upload")