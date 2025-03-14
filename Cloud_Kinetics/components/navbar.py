# # Cloud_Kinetics/components/navbar.py
# import reflex as rx
# from Cloud_Kinetics.chat.state import State

# def sidebar_chat(chat: str) -> rx.Component:
#     """A sidebar chat item."""
#     return rx.drawer.close(
#         rx.hstack(
#             rx.button(
#                 chat,
#                 on_click=lambda: State.set_chat(chat),
#                 width="80%",
#                 variant="surface",
#             ),
#             rx.button(
#                 rx.icon(
#                     tag="trash",
#                     on_click=State.delete_chat,
#                     stroke_width=1,
#                 ),
#                 width="20%",
#                 variant="surface",
#                 color_scheme="red",
#             ),
#             width="100%",
#         )
#     )

# def sidebar(trigger) -> rx.Component:
#     """The sidebar component."""
#     return rx.drawer.root(
#         rx.drawer.trigger(trigger),
#         rx.drawer.overlay(),
#         rx.drawer.portal(
#             rx.drawer.content(
#                 rx.vstack(
#                     rx.heading("Chats", color=rx.color("mauve", 11)),
#                     rx.divider(),
#                     rx.foreach(State.chat_titles, lambda chat: sidebar_chat(chat)),
#                     align_items="stretch",
#                     width="100%",
#                 ),
#                 top="auto",
#                 right="auto",
#                 height="100%",
#                 width="20em",
#                 padding="2em",
#                 background_color=rx.color("mauve", 2),
#                 outline="none",
#             )
#         ),
#         direction="left",
#     )

# def modal() -> rx.Component:
#     """A modal to create a new chat."""
#     return rx.dialog.root(
#         rx.dialog.trigger(
#             rx.button("+ New chat")  # Move the button here as the trigger
#         ),
#         rx.dialog.content(
#             rx.hstack(
#                 rx.input(
#                     placeholder="Type something...",
#                     value=State.new_chat_name,
#                     on_change=State.set_new_chat_name,  # Update state on change
#                     width=["15em", "20em", "30em", "30em", "30em", "30em"],
#                 ),
#                 rx.dialog.close(
#                     rx.button(
#                         "Create chat",
#                         on_click=State.create_chat,
#                     ),
#                 ),
#                 background_color=rx.color("mauve", 1),
#                 spacing="2",
#                 width="100%",
#             ),
#         ),
#     )

# def navbar() -> rx.Component:
#     return rx.box(
#         rx.hstack(
#             rx.hstack(
#                 rx.avatar(fallback="RC", variant="solid"),
#                 rx.heading("Reflex Chat"),
#                 rx.desktop_only(
#                     rx.badge(
#                         State.current_chat,
#                         rx.tooltip(rx.icon("info", size=14), content="The current selected chat."),
#                         variant="soft",
#                     )
#                 ),
#                 align_items="center",
#             ),
#             rx.hstack(
#                 modal(),  # Use the modal component directly
#                 sidebar(
#                     rx.button(
#                         rx.icon(
#                             tag="messages-square",
#                             color=rx.color("mauve", 12),
#                         ),
#                         background_color=rx.color("mauve", 6),
#                     )
#                 ),
#                 rx.button(
#                     rx.icon(tag="upload", color=rx.color("mauve", 12)),
#                     background_color=rx.color("mauve", 6),
#                     on_click=rx.redirect("/upload"),
#                 ),
#                 align_items="center",
#             ),
#             justify_content="space-between",
#         ),
#         backdrop_filter="auto",
#         backdrop_blur="lg",
#         padding="12px",
#         border_bottom=f"1px solid {rx.color('mauve', 3)}",
#         background_color=rx.color("mauve", 2),
#         position="sticky",
#         top="0",
#         z_index="100",
#     )

import reflex as rx
from Cloud_Kinetics.chat.state import State

def sidebar_chat(chat: str) -> rx.Component:
    """A sidebar chat item."""
    return rx.drawer.close(
        rx.hstack(
            rx.button(
                chat,
                on_click=lambda: State.set_chat(chat),
                width="80%",
                variant="surface",
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
        )
    )

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

def modal() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.trigger(rx.button("+ New chat")),
        rx.dialog.content(
            rx.dialog.title("Create New Chat"),  # Required for accessibility
            rx.dialog.description("Enter a name for your new chat."),  # Optional but recommended
            rx.hstack(
                rx.input(
                    placeholder="Type something...",
                    value=State.new_chat_name,
                    on_change=State.set_new_chat_name,
                ),
                rx.dialog.close(
                    rx.button("Create chat", on_click=State.create_chat),
                ),
            ),
        ),
    )

def navbar() -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.hstack(
                rx.avatar(fallback="RC", variant="solid"),
                rx.heading("Reflex Chat"),
                rx.desktop_only(
                    rx.badge(
                        State.current_chat,
                        rx.tooltip(rx.icon("info", size=14), content="The current selected chat."),
                        variant="soft",
                    )
                ),
                align_items="center",
            ),
            rx.hstack(
                modal(),  # Use the modal component directly
                sidebar(
                    rx.button(
                        rx.icon(
                            tag="messages-square",
                            color=rx.color("mauve", 12),
                        ),
                        background_color=rx.color("mauve", 6),
                    )
                ),
                rx.button(
                    rx.icon(tag="upload", color=rx.color("mauve", 12)),
                    background_color=rx.color("mauve", 6),
                    on_click=rx.redirect("/upload"),
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