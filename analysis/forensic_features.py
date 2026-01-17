import pandas as pd
from pathlib import Path


DATA_PATH = Path("data/processed/clean_messages.csv")
OUTPUT_DIR = Path("analysis/outputs/features")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_messages() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH, parse_dates=["conversation_datetime"])
    df = df.sort_values(by=["conversation_uid", "conversation_datetime", "message_sequence"])
    return df


def compute_time_gaps(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute time gaps (in seconds) between consecutive messages within the same conversation.
    """
    df = df.copy()
    df["prev_message_time"] = df.groupby("conversation_uid")["conversation_datetime"].shift(1)
    df["time_gap_seconds"] = (df["conversation_datetime"] - df["prev_message_time"]).dt.total_seconds()
    return df


def conversation_duration(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute total duration of each conversation (in seconds).
    """
    result = (
        df.groupby("conversation_uid")
        .agg(
            conversation_start=("conversation_datetime", "min"),
            conversation_end=("conversation_datetime", "max"),
            message_count=("message_text", "count"),
            participant_count=("sender_email", "nunique"),
            has_deleted=("has_deleted_in_conversation", "max"),
        )
        .reset_index()
    )

    result["conversation_duration_seconds"] = (
        result["conversation_end"] - result["conversation_start"]
    ).dt.total_seconds()

    return result


def burst_activity(df: pd.DataFrame, burst_threshold_seconds: int = 60) -> pd.DataFrame:
    """
    Identify burst activity: messages sent within a short time window compared to the previous message.
    A burst message is defined as a message whose time gap to the previous message is <= threshold.
    """
    df = df.copy()
    df["is_burst_message"] = df["time_gap_seconds"].le(burst_threshold_seconds)

    burst_summary = (
        df.groupby("conversation_uid")
        .agg(
            burst_message_count=("is_burst_message", "sum"),
            total_messages=("message_text", "count"),
        )
        .reset_index()
    )

    burst_summary["burst_ratio"] = burst_summary["burst_message_count"] / burst_summary["total_messages"]
    burst_summary["burst_threshold_seconds"] = burst_threshold_seconds

    return burst_summary


def main():
    df = load_messages()
    df = compute_time_gaps(df)

    # Message-level features (time gaps)
    message_time_gaps = df[
        [
            "conversation_uid",
            "sender_email",
            "conversation_datetime",
            "message_sequence",
            "time_gap_seconds",
            "message_status",
        ]
    ].copy()

    # Conversation-level features (duration, burst)
    duration = conversation_duration(df)
    burst = burst_activity(df, burst_threshold_seconds=60)

    # Save outputs
    message_time_gaps.to_csv(OUTPUT_DIR / "message_time_gaps.csv", index=False)
    duration.to_csv(OUTPUT_DIR / "conversation_duration.csv", index=False)
    burst.to_csv(OUTPUT_DIR / "burst_activity.csv", index=False)

    print("Forensic temporal features generated:")
    print(f"- {OUTPUT_DIR / 'message_time_gaps.csv'}")
    print(f"- {OUTPUT_DIR / 'conversation_duration.csv'}")
    print(f"- {OUTPUT_DIR / 'burst_activity.csv'}")


if __name__ == "__main__":
    main()
