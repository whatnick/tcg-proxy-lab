import os
import shutil
import sys
import tempfile
from pathlib import Path

from app.decklist import parse_decklist


ENGINE_PATH = Path(os.environ.get("SILHOUETTE_CARD_MAKER_PATH", "vendor/silhouette-card-maker")).resolve()
if not ENGINE_PATH.is_dir():
    raise RuntimeError(f"Silhouette Card Maker not found at {ENGINE_PATH}")
sys.path.insert(0, str(ENGINE_PATH))

from plugins.pokemon.deck_formats import DeckFormat, parse_deck  # noqa: E402
from plugins.pokemon.limitless import get_handle_card  # noqa: E402
from utilities import FitMode, Registration, ensure_directory, generate_pdf  # noqa: E402


def generate_proxy_pdf(decklist: str, paper_size: str) -> tuple[Path, Path]:
    if paper_size not in {"a4", "letter"}:
        raise ValueError("Paper size must be a4 or letter")
    parse_decklist(decklist)

    work_dir = Path(tempfile.mkdtemp(prefix="tcg-proxy-"))
    front_dir = work_dir / "front"
    back_dir = work_dir / "back"
    double_sided_dir = work_dir / "double_sided"
    output_path = work_dir / "playtest-proxies.pdf"

    try:
        for directory in (front_dir, back_dir, double_sided_dir):
            ensure_directory(str(directory))

        parse_deck(decklist, DeckFormat.LIMITLESS, get_handle_card(str(front_dir)))
        if not any(front_dir.iterdir()):
            raise ValueError("No card images could be resolved")

        generate_pdf(
            front_dir_path=str(front_dir),
            back_dir_path=str(back_dir),
            ds_dir_path=str(double_sided_dir),
            output_path=str(output_path),
            output_images=False,
            card_size="standard",
            paper_size=paper_size,
            registration=Registration.THREE.value,
            only_fronts=True,
            fit=FitMode.STRETCH.value,
            fit_backs=None,
            crop_string=None,
            crop_backs_string=None,
            extend_edges=None,
            extend_edges_backs=None,
            extend_corners=None,
            extend_corners_backs=None,
            extend_bleed=None,
            extend_bleed_backs=None,
            ppi=300,
            quality=95,
            skip_indices=[],
            load_offset=False,
            label=None,
            borderless=False,
        )
        return output_path, work_dir
    except Exception:
        shutil.rmtree(work_dir, ignore_errors=True)
        raise
