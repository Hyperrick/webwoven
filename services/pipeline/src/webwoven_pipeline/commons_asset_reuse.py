from __future__ import annotations

import os
import shutil
from collections.abc import Mapping
from pathlib import Path
from typing import Protocol


class StoredAsset(Protocol):
    @property
    def asset_path(self) -> str: ...


def materialize_reused_assets[AssetT: StoredAsset](
    source_root: Path,
    destination: Path,
    reusable: Mapping[str, AssetT],
) -> dict[str, AssetT]:
    """Hard-link verified assets into a new pack, copying across filesystems."""
    for asset in reusable.values():
        source = source_root / asset.asset_path
        target = destination / asset.asset_path
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.link(source, target)
        except OSError:
            shutil.copyfile(source, target)
    return dict(reusable)
