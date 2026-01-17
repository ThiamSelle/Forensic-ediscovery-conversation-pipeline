import re
from dataclasses import dataclass
from typing import Tuple

import pandas as pd

# ---------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
BLOCK_RE = re.compile(r"^APD\d+$")

# Strict UUID v4 pattern (used only as a quality flag, not for validation)
UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-"
    r"[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{12}$"
)

# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class TransformConfig:
    """
    Configuration object for the transformation logic.
    """
    datetime_format: str = "%m/%d/%y %I:%M:%S %p"
    deleted_marker: str = "[Deleted Message]"


# ---------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------

def _pull_meta(df: pd.DataFrame, key_name: str) -> pd.Series:
    """
    Within each conversation block (conv_seq), extract the first value
    of a given metadata key and propagate it to all rows in the block.
    """
    return (
        df["col2"]
        .where(df["col1"].eq(key_name))
        .groupby(df["conv_seq"])
        .transform("first")
    )


# ---------------------------------------------------------------------
# Main transformation
# ---------------------------------------------------------------------

def transform_conversation_export(
    raw: pd.DataFrame,
    config: TransformConfig = TransformConfig(),
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Transform a block-structured conversation export into:
      1) a message-level dataset
      2) a conversation-level summary

    Forensic principles applied:
    - raw data is never modified
    - transformations are deterministic
    - all rows remain traceable to the source export
    """

    df = raw.copy()
    df["col1"] = df["col1"].astype("string")
    df["col2"] = df["col2"].astype("string")

    # -----------------------------------------------------------------
    # Row-level traceability
    # -----------------------------------------------------------------

    df["row_num"] = range(1, len(df) + 1)

    # -----------------------------------------------------------------
    # Conversation block detection
    # -----------------------------------------------------------------

    df["is_conv_start"] = df["col1"].fillna("").str.match(BLOCK_RE)
    df["conv_seq"] = df["is_conv_start"].cumsum()

    # APD marker = extraction / batch artifact (NOT a unique conversation ID)
    df["extraction_group_id"] = (
        df["col1"]
        .where(df["is_conv_start"])
        .groupby(df["conv_seq"])
        .transform("first")
    )

    # -----------------------------------------------------------------
    # Metadata extraction
    # -----------------------------------------------------------------

    df["conversation_id"] = _pull_meta(df, "Conversation Identifier:")
    df["platform_call_id"] = _pull_meta(df, "Platform Call ID:")
    df["datetime_raw"] = _pull_meta(df, "Date and time:")

    df["conversation_datetime"] = pd.to_datetime(
        df["datetime_raw"],
        format=config.datetime_format,
        errors="coerce",
    )

    # -----------------------------------------------------------------
    # Message identification
    # -----------------------------------------------------------------

    df["is_message"] = df["col1"].fillna("").str.match(EMAIL_RE)
    messages = df[df["is_message"]].copy()

    messages["sender_email"] = messages["col1"].fillna("")
    messages["message_text"] = messages["col2"].fillna("")

    messages["message_status"] = messages["message_text"].eq(
        config.deleted_marker
    ).map({True: "deleted", False: "normal"})

    # -----------------------------------------------------------------
    # Stable identifiers (explicit and non-ambiguous)
    # -----------------------------------------------------------------

    # Unique technical identifier for a conversation block in this export
    messages["conversation_block_id"] = messages["conv_seq"]

    # Human-readable unique identifier (safe to expose)
    messages["conversation_uid"] = (
        messages["extraction_group_id"].astype("string")
        + "-"
        + messages["conv_seq"].astype(str)
    )

    # -----------------------------------------------------------------
    # Data quality flags (do NOT alter source identifiers)
    # -----------------------------------------------------------------

    messages["conversation_id_is_uuid"] = (
        messages["conversation_id"].fillna("").str.match(UUID_RE)
    )

    # -----------------------------------------------------------------
    # Investigation-oriented features
    # -----------------------------------------------------------------

    messages["message_len"] = messages["message_text"].str.len()

    messages["has_deleted_in_conversation"] = (
        messages.groupby("conv_seq")["message_status"]
        .transform(lambda s: (s == "deleted").any())
    )

    # -----------------------------------------------------------------
    # Message ordering
    # -----------------------------------------------------------------

    messages["message_sequence"] = (
        messages.groupby("conv_seq").cumcount() + 1
    )

    # -----------------------------------------------------------------
    # Final message-level dataset
    # -----------------------------------------------------------------

    messages = messages[
        [
            "extraction_group_id",
            "conversation_uid",
            "conversation_block_id",
            "conversation_id",
            "conversation_id_is_uuid",
            "platform_call_id",
            "conversation_datetime",
            "sender_email",
            "message_text",
            "message_len",
            "message_status",
            "has_deleted_in_conversation",
            "message_sequence",
            "row_num",
            "conv_seq",
        ]
    ].reset_index(drop=True)

    # -----------------------------------------------------------------
    # Conversation-level summary
    # -----------------------------------------------------------------

    conv_summary = (
        messages.groupby(
            [
                "conv_seq",
                "extraction_group_id",
                "conversation_uid",
                "conversation_id",
                "platform_call_id",
                "conversation_datetime",
            ],
            dropna=False,
        )
        .agg(
            message_count=("message_text", "size"),
            participants=("sender_email", lambda x: sorted(set(x))),
            deleted_count=("message_status", lambda x: (x == "deleted").sum()),
        )
        .reset_index()
    )

    conv_summary["has_deleted_messages"] = conv_summary["deleted_count"] > 0

    return messages, conv_summary
