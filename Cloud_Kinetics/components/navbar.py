import reflex as rx
from Cloud_Kinetics.chat.state import State

def sidebar_chat(chat: str) -> rx.Component:
    """A sidebar chat item.

    Args:
        chat: The chat item.
    """
    return  rx.drawer.close(rx.hstack(
        rx.button(
            chat, on_click=lambda: State.set_chat(chat), width="80%", variant="surface"
        ),
        rx.button(
            rx.icon(
                tag="trash",
                on_click=State.delete_chat,
                stroke_width=1,
            ),
            width="20%",
            variant="surface",
            color_scheme="red",
        ),
        width="100%",
    ))

def sidebar(trigger) -> rx.Component:
    """The sidebar component."""
    return rx.drawer.root(
        rx.drawer.trigger(trigger),
        rx.drawer.overlay(),
        rx.drawer.portal(
            rx.drawer.content(
                rx.vstack(
                    rx.heading("Chats", color=rx.color("mauve", 11)),
                    rx.divider(),
                    rx.foreach(State.chat_titles, lambda chat: sidebar_chat(chat)),
                    align_items="stretch",
                    width="100%",
                ),
                top="auto",
                right="auto",
                height="100%",
                width="20em",
                padding="2em",
                background_color=rx.color("mauve", 2),
                outline="none",
            )
        ),
        direction="left",
    )

def modal(trigger) -> rx.Component:
    """A modal to create a new chat."""
    return rx.dialog.root(
        rx.dialog.trigger(trigger),
        rx.dialog.content(
            rx.hstack(
                rx.input(
                    placeholder="Type something...",
                    on_blur=State.set_new_chat_name,
                    width=["15em", "20em", "30em", "30em", "30em", "30em"],
                ),
                rx.dialog.close(
                    rx.button(
                        "Create chat",
                        on_click=State.create_chat,
                    ),
                ),
                background_color=rx.color("mauve", 1),
                spacing="2",
                width="100%",
            ),
        ),
    )

def upload_modal() -> rx.Component:
    """A modal for uploading files."""
    return rx.dialog.root(
        rx.dialog.trigger(
            rx.button(
                rx.icon(tag="upload", color=rx.color("mauve", 12)),
                background_color=rx.color("mauve", 6),
            )
        ),
        rx.dialog.content(
            rx.vstack(
                rx.upload(
                    rx.text("Select file to upload"),
                    on_upload=State.handle_upload,
                ),
                rx.dialog.close(
                    rx.button("Close")
                ),
                align_items="center",
            ),
            background_color=rx.color("mauve", 1),
            padding="1em",
        ),
    )

def navbar() -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.hstack(
                rx.avatar(fallback="RC", variant="solid"),
                rx.heading("Reflex Chat"),
                align_items="center",
            ),
            rx.hstack(
                rx.button("+ New chat"),  # Simplified for brevity
                rx.button(
                    rx.icon(tag="upload", color=rx.color("mauve", 12)),
                    background_color=rx.color("mauve", 6),
                    on_click=rx.redirect("/upload"),  # Navigate to upload page
                ),
                align_items="center",
            ),
            justify_content="space-between",
        ),
        backdrop_filter="auto",
        backdrop_blur="lg",
        padding="12px",
        border_bottom=f"1px solid {rx.color('mauve', 3)}",
        background_color=rx.color("mauve", 2),
        position="sticky",
        top="0",
        z_index="100",
    )