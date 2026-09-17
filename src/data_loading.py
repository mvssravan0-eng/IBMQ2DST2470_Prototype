"""
data_loading.py
----------------
Loads the NSL-KDD dataset (KDDTrain+.txt / KDDTest+.txt) with the correct
41-feature schema and maps the ~40 fine-grained attack labels down to the
5 standard categories: Normal, DoS, Probe, R2L, U2R.

The raw files are comma-separated with NO header row. Some distributions
of the file include a trailing 'difficulty' column, others don't -- this
loader auto-detects which schema it received (42 vs 43 columns) so it
never silently misaligns columns.
"""

import pandas as pd
import os

# ---------------------------------------------------------------------------
# Official NSL-KDD column names, in order (41 features + label [+ difficulty])
# Source: NSL-KDD dataset documentation (kddcup.names / field descriptions)
# ---------------------------------------------------------------------------
COLUMN_NAMES = [
    "duration", "protocol_type", "service", "flag", "src_bytes", "dst_bytes",
    "land", "wrong_fragment", "urgent", "hot", "num_failed_logins",
    "logged_in", "num_compromised", "root_shell", "su_attempted",
    "num_root", "num_file_creations", "num_shells", "num_access_files",
    "num_outbound_cmds", "is_host_login", "is_guest_login", "count",
    "srv_count", "serror_rate", "srv_serror_rate", "rerror_rate",
    "srv_rerror_rate", "same_srv_rate", "diff_srv_rate",
    "srv_diff_host_rate", "dst_host_count", "dst_host_srv_count",
    "dst_host_same_srv_rate", "dst_host_diff_srv_rate",
    "dst_host_same_src_port_rate", "dst_host_srv_diff_host_rate",
    "dst_host_serror_rate", "dst_host_srv_serror_rate",
    "dst_host_rerror_rate", "dst_host_srv_rerror_rate",
    "label",
]
DIFFICULTY_COL = "difficulty"

# ---------------------------------------------------------------------------
# Fine-grained attack name -> 5-class category mapping.
# This covers all attack types that appear across KDDTrain+ and KDDTest+
# (KDDTest+ contains several attack types that never appear in KDDTrain+ --
# those are exactly the "zero-day" attacks Part 2 needs to catch).
# ---------------------------------------------------------------------------
ATTACK_CATEGORY_MAP = {
    "normal": "Normal",

    # DoS
    "back": "DoS", "land": "DoS", "neptune": "DoS", "pod": "DoS",
    "smurf": "DoS", "teardrop": "DoS", "mailbomb": "DoS",
    "processtable": "DoS", "udpstorm": "DoS", "apache2": "DoS",
    "worm": "DoS",

    # Probe
    "satan": "Probe", "ipsweep": "Probe", "nmap": "Probe",
    "portsweep": "Probe", "mscan": "Probe", "saint": "Probe",

    # R2L (Remote to Local)
    "guess_passwd": "R2L", "ftp_write": "R2L", "imap": "R2L",
    "phf": "R2L", "multihop": "R2L", "warezmaster": "R2L",
    "warezclient": "R2L", "spy": "R2L", "xlock": "R2L", "xsnoop": "R2L",
    "snmpguess": "R2L", "snmpgetattack": "R2L", "httptunnel": "R2L",
    "sendmail": "R2L", "named": "R2L",

    # U2R (User to Root)
    "buffer_overflow": "U2R", "loadmodule": "U2R", "rootkit": "U2R",
    "perl": "U2R", "sqlattack": "U2R", "xterm": "U2R", "ps": "U2R",
}


def _read_raw(path: str) -> pd.DataFrame:
    """Read a raw NSL-KDD file, auto-detecting whether it has the trailing
    'difficulty' column (42 cols = no difficulty, 43 cols = has difficulty)."""
    # peek at the first line to count fields
    with open(path, "r") as f:
        first_line = f.readline().strip()
    n_fields = len(first_line.split(","))

    if n_fields == len(COLUMN_NAMES):
        names = COLUMN_NAMES
    elif n_fields == len(COLUMN_NAMES) + 1:
        names = COLUMN_NAMES + [DIFFICULTY_COL]
    else:
        raise ValueError(
            f"Unexpected column count in {path}: got {n_fields}, "
            f"expected {len(COLUMN_NAMES)} or {len(COLUMN_NAMES) + 1}"
        )

    df = pd.read_csv(path, header=None, names=names, skipinitialspace=True)
    # some mirrors leave a trailing '.' on the label (old kddcup format) or \r
    df["label"] = df["label"].astype(str).str.strip().str.rstrip(".")
    return df


def load_nslkdd(data_dir: str):
    """
    Loads KDDTrain+ and KDDTest+ and adds two derived label columns:
      - 'attack_type'  : the raw fine-grained label (e.g. 'neptune')
      - 'category'     : 5-class mapping (Normal/DoS/Probe/R2L/U2R)
      - 'binary_label' : 0 = Normal, 1 = Attack

    Unknown fine-grained labels (shouldn't happen, but datasets are messy)
    are mapped to 'Unknown' rather than crashing.
    """
    train_path = os.path.join(data_dir, "KDDTrain+.txt")
    test_path = os.path.join(data_dir, "KDDTest+.txt")

    train_df = _read_raw(train_path)
    test_df = _read_raw(test_path)

    for df in (train_df, test_df):
        df["attack_type"] = df["label"]
        df["category"] = df["attack_type"].map(ATTACK_CATEGORY_MAP).fillna("Unknown")
        df["binary_label"] = (df["category"] != "Normal").astype(int)

    return train_df, test_df


def summarize(train_df: pd.DataFrame, test_df: pd.DataFrame):
    print("=" * 70)
    print(f"KDDTrain+ shape: {train_df.shape}")
    print(f"KDDTest+  shape: {test_df.shape}")
    print("-" * 70)
    print("Category distribution (train):")
    print(train_df["category"].value_counts())
    print("-" * 70)
    print("Category distribution (test):")
    print(test_df["category"].value_counts())
    print("-" * 70)

    train_attacks = set(train_df["attack_type"].unique())
    test_attacks = set(test_df["attack_type"].unique())
    novel = test_attacks - train_attacks
    print(f"Attack types in TEST but NOT in TRAIN (true zero-day set): "
          f"{len(novel)}")
    print(sorted(novel))
    print("=" * 70)


if __name__ == "__main__":
    train_df, test_df = load_nslkdd(os.path.join(os.path.dirname(__file__), "..", "data"))
    summarize(train_df, test_df)
