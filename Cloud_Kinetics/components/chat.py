# Cloud_Kinetics/components/chat.py
import reflex as rx
import reflex_chakra as rc
from Cloud_Kinetics.components.loading_icon import loading_icon
from Cloud_Kinetics.chat.state import QA, State
from Cloud_Kinetics.components.navbar import navbar

message_style = dict(display="inline-block", padding="1em", border_radius="8px", max_width=["30em", "30em", "50em", "50em", "50em", "50em"])

def message(qa: QA) -> rx.Component:
    """A single question/answer message."""
    return rx.box(
        rx.box(
            rx.markdown(
                qa.question,
                background_color=rx.color("mauve", 4),
                color=rx.color("mauve", 12),
                **message_style,
            ),
            text_align="right",
            margin_top="1em",
        ),
        rx.box(
            rx.markdown(
                qa.answer,
                background_color=rx.color("accent", 4),
                color=rx.color("accent", 12),
                **message_style,
            ),
            text_align="left",
            padding_top="1em",
        ),
        width="100%",
    )

def chat() -> rx.Component:
    """List all the messages in a single conversation."""
    return rx.vstack(
        rx.box(rx.foreach(State.chats[State.current_chat], message), width="100%"),
        py="8",
        flex="1",
        width="100%",
        max_width="50em",
        padding_x="4px",
        align_self="center",
        overflow="hidden",
        padding_bottom="5em",
    )

def action_bar() -> rx.Component:
    """The action bar to send a new message."""
    return rx.center(
        rx.vstack(
            rc.form(
                rc.form_control(
                    rx.hstack(
                        rx.input(
                            rx.input.slot(
                                rx.tooltip(
                                    rx.icon("info", size=18),
                                    content="Enter a question to get a response.",
                                )
                            ),
                            placeholder="Type something...",
                            id="question",
                            width=["15em", "20em", "45em", "50em", "50em", "50em"],
                        ),
                        rx.button(
                            rx.cond(
                                State.processing,
                                loading_icon(height="1em"),
                                rx.text("Send"),
                            ),
                            type="submit",
                        ),
                        align_items="center",
                    ),
                    is_disabled=State.processing,
                ),
                on_submit=State.process_question,
                reset_on_submit=True,
            ),
            rx.text(
                "ReflexGPT may return factually incorrect or misleading responses. Use discretion.",
                text_align="center",
                font_size=".75em",
                color=rx.color("mauve", 10),
            ),
            rx.logo(margin_top="-1em", margin_bottom="-1em"),
            align_items="center",
        ),
        position="sticky",
        bottom="0",
        left="0",
        padding_y="16px",
        backdrop_filter="auto",
        backdrop_blur="lg",
        border_top=f"1px solid {rx.color('mauve', 3)}",
        background_color=rx.color("mauve", 2),
        align_items="stretch",
        width="100%",
    )

def chat_page() -> rx.Component:
    """Full chat page with navbar integration."""
    return rx.vstack(
        navbar(),  # Include the navbar at the top
        chat(),
        action_bar(),
        align_items="center",
        spacing="4",
        padding="2em",
        background_color=rx.color("mauve", 1),
        min_height="100vh",
    )

# # Cloud_Kinetics/components/chat.py
# import reflex as rx
# import reflex_chakra as rc
# from Cloud_Kinetics.components.loading_icon import loading_icon
# from Cloud_Kinetics.chat.state import QA, State

# message_style = dict(display="inline-block", padding="1em", border_radius="8px", max_width=["30em", "30em", "50em", "50em", "50em", "50em"])

# def message(qa: QA) -> rx.Component:
#     """A single question/answer message."""
#     return rx.box(
#         rx.box(
#             rx.markdown(
#                 qa.question,
#                 background_color=rx.color("mauve", 4),
#                 color=rx.color("mauve", 12),
#                 **message_style,
#             ),
#             text_align="right",
#             margin_top="1em",
#         ),
#         rx.box(
#             rx.markdown(
#                 qa.answer,
#                 background_color=rx.color("accent", 4),
#                 color=rx.color("accent", 12),
#                 **message_style,
#             ),
#             text_align="left",
#             padding_top="1em",
#         ),
#         width="100%",
#     )

# def chat() -> rx.Component:
#     """List all the messages in a single conversation."""
#     return rx.vstack(
#         rx.box(rx.foreach(State.chats[State.current_chat], message), width="100%"),
#         py="8",
#         flex="1",
#         width="100%",
#         max_width="50em",
#         padding_x="4px",
#         align_self="center",
#         overflow="hidden",
#         padding_bottom="5em",
#     )

# def action_bar() -> rx.Component:
#     """The action bar to send a new message."""
#     return rx.center(
#         rx.vstack(
#             rc.form(
#                 rc.form_control(
#                     rx.hstack(
#                         rx.input(
#                             rx.input.slot(
#                                 rx.tooltip(
#                                     rx.icon("info", size=18),
#                                     content="Enter a question to get a response.",
#                                 )
#                             ),
#                             placeholder="Type something...",
#                             id="question",
#                             width=["15em", "20em", "45em", "50em", "50em", "50em"],
#                         ),
#                         rx.button(
#                             rx.cond(
#                                 State.processing,
#                                 loading_icon(height="1em"),
#                                 rx.text("Send"),
#                             ),
#                             type="submit",
#                         ),
#                         align_items="center",
#                     ),
#                     is_disabled=State.processing,
#                 ),
#                 on_submit=State.process_question,
#                 reset_on_submit=True,
#             ),
#             rx.text(
#                 "ReflexGPT may return factually incorrect or misleading responses. Use discretion.",
#                 text_align="center",
#                 font_size=".75em",
#                 color=rx.color("mauve", 10),
#             ),
#             rx.logo(margin_top="-1em", margin_bottom="-1em"),
#             align_items="center",
#         ),
#         position="sticky",
#         bottom="0",
#         left="0",
#         padding_y="16px",
#         backdrop_filter="auto",
#         backdrop_blur="lg",
#         border_top=f"1px solid {rx.color('mauve', 3)}",
#         background_color=rx.color("mauve", 2),
#         align_items="stretch",
#         width="100%",
#     )

# def chat_page() -> rx.Component:
#     """Full chat page with new chat functionality."""
#     return rx.vstack(
#         rx.heading("Chatbot", size="4"),
#         rx.hstack(
#             rx.input(
#                 placeholder="New chat name",
#                 value=State.new_chat_name,
#                 on_change=State.set_new_chat_name,
#                 width="200px",
#             ),
#             rx.button(
#                 "Add New Chat",
#                 on_click=State.create_chat,
#                 color="rgb(107,99,246)",
#                 bg="white",
#                 border="1px solid rgb(107,99,246)",
#             ),
#             rx.button(
#                 "Delete Chat",
#                 on_click=State.delete_chat,
#                 color="red",
#                 bg="white",
#                 border="1px solid red",
#             ),
#             rx.select(
#                 State.chat_titles,
#                 value=State.current_chat,
#                 on_change=State.set_chat,
#                 width="200px",
#             ),
#             spacing="2",
#         ),
#         chat(),
#         action_bar(),
#         rx.link("Back to Upload", href="/upload", margin_top="2em"),
#         align_items="center",
#         spacing="4",
#         padding="2em",
#         background_color=rx.color("mauve", 1),
#         min_height="100vh",
#     )