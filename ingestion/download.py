"""Download opcional do dataset via Kaggle (requer a CLI `kaggle` configurada).

Alternativa sem CLI: baixe o zip manualmente (veja data/README.md) e extraia em data/raw/.
"""

from __future__ import annotations

import shutil
import subprocess

from ingestion.config import get_data_dir

DATASET = "olistbr/brazilian-ecommerce"


def download() -> None:
    if shutil.which("kaggle") is None:
        raise SystemExit(
            "CLI do Kaggle não encontrada (pip install kaggle + ~/.kaggle/kaggle.json). "
            "Ou baixe manualmente: https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce"
        )
    target = get_data_dir()
    target.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["kaggle", "datasets", "download", "-d", DATASET, "-p", str(target), "--unzip"], check=True
    )


if __name__ == "__main__":
    download()
