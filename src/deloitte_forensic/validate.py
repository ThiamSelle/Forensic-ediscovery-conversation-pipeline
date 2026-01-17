import pandas as pd


def basic_validation(messages: pd.DataFrame) -> None:
    """
    Lightweight checks to ensure outputs are coherent and investigation-ready.
    """
    required_cols = {
        "conversation_id",
        "platform_call_id",
        "conversation_datetime",
        "sender_email",
        "message_text",
        "message_sequence",
    }
    missing = required_cols - set(messages.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    if messages["sender_email"].isna().any():
        raise ValueError("sender_email contains null values")

    if (messages["message_sequence"] < 1).any():
        raise ValueError("message_sequence must be >= 1")
