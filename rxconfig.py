import reflex as rx

config = rx.Config(
    app_name="Cloud_Kinetics",
    pages={
        "/": "Cloud_Kinetics.components.chat_page",
        "/upload": "Cloud_Kinetics.pages.upload_page"
    }
)