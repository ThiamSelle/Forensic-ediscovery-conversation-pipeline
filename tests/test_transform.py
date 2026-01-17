import pandas as pd

from deloitte_forensic.transform import transform_conversation_export


def test_transform_adds_expected_fields_and_flags():
    raw = pd.DataFrame(
        {
            "col1": [
                "APD1",
                "Conversation Identifier:",
                "Platform Call ID:",
                "Date and time:",
                "a@b.com",
                "c@d.com",
            ],
            "col2": [
                "",
                "uuid-1",
                "platform-1",
                "10/10/19 4:10:12 PM",
                "hello",
                "[Deleted Message]",
            ],
        }
    )

    messages, summary = transform_conversation_export(raw)

    # Basic shapes
    assert len(messages) == 2
    assert len(summary) == 1

    # Core columns we expect in the improved schema
    expected_cols = [
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
    for col in expected_cols:
        assert col in messages.columns

    # Message ordering within a conversation
    assert messages["message_sequence"].tolist() == [1, 2]

    # Deleted flags
    assert set(messages["message_status"]) == {"normal", "deleted"}
    assert bool(messages["has_deleted_in_conversation"].iloc[0]) is True
    assert bool(messages["has_deleted_in_conversation"].iloc[1]) is True

    # Summary should reflect deletion
    assert int(summary.loc[0, "message_count"]) == 2
    assert bool(summary.loc[0, "has_deleted_messages"]) is True
