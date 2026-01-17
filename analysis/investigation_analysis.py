import pandas as pd
from pathlib import Path


DATA_PATH = Path("data/processed/clean_messages.csv")
OUTPUT_DIR = Path("analysis/outputs")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_messages() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH, parse_dates=["conversation_datetime"])
    return df


def conversations_with_deleted_messages(df: pd.DataFrame) -> pd.DataFrame:
    """
    Identify conversations that contain at least one deleted message.
    """
    result = (
        df[df["message_status"] == "deleted"]
        .groupby("conversation_uid")
        .agg(
            deleted_message_count=("message_status", "count"),
            total_messages=("message_status", "size"),
        )
        .reset_index()
        .sort_values("deleted_message_count", ascending=False)
    )
    return result


def participant_activity(df: pd.DataFrame) -> pd.DataFrame:
    """
    Count messages sent per participant.
    """
    result = (
        df.groupby("sender_email")
        .agg(
            message_count=("message_text", "count"),
            conversations_involved=("conversation_uid", "nunique"),
        )
        .reset_index()
        .sort_values("message_count", ascending=False)
    )
    return result


def conversation_volume(df: pd.DataFrame) -> pd.DataFrame:
    """
    Measure message volume per conversation.
    """
    result = (
        df.groupby("conversation_uid")
        .agg(
            message_count=("message_text", "count"),
            participant_count=("sender_email", "nunique"),
            has_deleted=("has_deleted_in_conversation", "max"),
        )
        .reset_index()
        .sort_values("message_count", ascending=False)
    )
    return result


def timeline_activity(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate message activity over time (hour-level).
    """
    df["hour"] = df["conversation_datetime"].dt.floor("h")
    result = (
        df.groupby("hour")
        .size()
        .reset_index(name="message_count")
        .sort_values("hour")
    )
    return result


def main():
    df = load_messages()

    deleted_conv = conversations_with_deleted_messages(df)
    participants = participant_activity(df)
    conv_volume = conversation_volume(df)
    timeline = timeline_activity(df)

    deleted_conv.to_csv(OUTPUT_DIR / "conversations_with_deleted_messages.csv", index=False)
    participants.to_csv(OUTPUT_DIR / "participant_activity.csv", index=False)
    conv_volume.to_csv(OUTPUT_DIR / "conversation_volume.csv", index=False)
    timeline.to_csv(OUTPUT_DIR / "timeline_activity.csv", index=False)

    print("Investigation-ready analyses generated:")
    print(f"- {OUTPUT_DIR / 'conversations_with_deleted_messages.csv'}")
    print(f"- {OUTPUT_DIR / 'participant_activity.csv'}")
    print(f"- {OUTPUT_DIR / 'conversation_volume.csv'}")
    print(f"- {OUTPUT_DIR / 'timeline_activity.csv'}")


if __name__ == "__main__":
    main()
