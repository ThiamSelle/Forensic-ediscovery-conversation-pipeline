import pandas as pd


def read_raw_csv(path: str) -> pd.DataFrame:
    """
    Read the corrupted conversation export.
    The file has no reliable header, and data is stored as key/value rows.
    """
    return pd.read_csv(path, header=None, names=["col1", "col2"], dtype=str)
