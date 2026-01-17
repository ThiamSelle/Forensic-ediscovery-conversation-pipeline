from pathlib import Path

import typer
from rich import print

from deloitte_forensic.io import read_raw_csv
from deloitte_forensic.transform import transform_conversation_export
from deloitte_forensic.validate import basic_validation

app = typer.Typer(
    help="Forensic-style transformation pipeline for block-structured conversation exports."
)


@app.command()
def run(
    input_path: str = typer.Option(..., help="Path to raw conversation CSV"),
    out_dir: str = typer.Option("data/processed", help="Output directory"),
):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    raw = read_raw_csv(input_path)
    messages, summary = transform_conversation_export(raw)

    basic_validation(messages)

    msg_path = out / "clean_messages.csv"
    sum_path = out / "conversation_summary.csv"

    messages.to_csv(msg_path, index=False)
    summary.to_csv(sum_path, index=False)

    print("[green]Done.[/green]")
    print(f"- Messages: {msg_path}")
    print(f"- Summary : {sum_path}")
    print(f"- Conversations: {summary.shape[0]}")
    print(f"- Messages total: {messages.shape[0]}")


if __name__ == "__main__":
    app()
