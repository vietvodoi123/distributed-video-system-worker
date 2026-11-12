import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import joblib
import numpy as np
from scipy.sparse import hstack

from .features import (
    extract_unicode_script_features,
    is_chapter_heading,
    normalize_for_model,
    split_cjk_tail,
    strip_tail_at_cjk_boundary,
)

DEFAULT_MODEL_PATH = Path(__file__).parent / "spam_model.joblib"


class SpamCleaner:
    """
    Lightweight, high-speed chapter text cleaner using a dual-classifier architecture:
      - Model A (Full-line classifier): flags and removes entire spam lines.
      - Model B (Tail-window classifier): detects obfuscated inline tails (e.g. 69shux,
        emojis, QQ groups, unknown web watermarks) and cleanly strips them at the CJK boundary.
    """

    def __init__(
        self,
        model_path: Optional[Union[str, Path]] = None,
        full_threshold: float = 0.80,
        tail_threshold: float = 0.80,
    ):
        target_path = Path(model_path) if model_path else DEFAULT_MODEL_PATH
        if not target_path.exists():
            raise FileNotFoundError(
                f"Spam cleaner model not found at {target_path}. "
                "Ensure spam_model.joblib is present in the module folder."
            )
        self.bundle: Dict[str, Any] = joblib.load(target_path)
        self.full_threshold = full_threshold
        self.tail_threshold = tail_threshold

    def clean(
        self,
        raw_text: str,
        full_threshold: Optional[float] = None,
        tail_threshold: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Clean raw text of a single chapter.

        Args:
            raw_text: Raw Chinese text with line breaks.
            full_threshold: Override default threshold for full-line removal (default: 0.80).
            tail_threshold: Override default threshold for inline-tail stripping (default: 0.80).

        Returns:
            {
                "cleaned_text": str,
                "removed_lines": [{"index": int, "prob": float, "text": str}],
                "stripped_tails": [{"index": int, "prob": float, "before": str, "after": str}],
            }
        """
        f_th = full_threshold if full_threshold is not None else self.full_threshold
        t_th = tail_threshold if tail_threshold is not None else self.tail_threshold

        lines = [ln.strip() for ln in raw_text.splitlines() if ln.strip()]
        if not lines:
            return {"cleaned_text": "", "removed_lines": [], "stripped_tails": []}

        total = len(lines)

        # 1. Batch score tail windows with Model B (65-char tail window)
        win_texts = [ln[-65:] for ln in lines]
        win_norms = [normalize_for_model(w) for w in win_texts]
        tail_num = np.array(
            [
                extract_unicode_script_features(w) + extract_unicode_script_features(split_cjk_tail(ln)[1])
                for ln, w in zip(lines, win_texts)
            ],
            dtype=np.float32,
        )
        Xt = hstack([
            self.bundle["vec_tail_norm"].transform(win_norms),
            self.bundle["vec_tail_raw"].transform(win_texts),
            self.bundle["tail_scaler"].transform(tail_num),
        ]).tocsr()
        tail_probs = self.bundle["tail_clf"].predict_proba(Xt)[:, 1]

        # 2. Batch score full lines with Model A
        norm_texts = [normalize_for_model(ln) for ln in lines]
        full_num = []
        pos_ratios = []
        for idx, ln in enumerate(lines):
            pos = round(idx / max(total - 1, 1), 4)
            pos_ratios.append(pos)
            is_edge = 1.0 if (pos <= 0.08 or pos >= 0.92) else 0.0
            full_num.append(
                extract_unicode_script_features(ln) + [pos, is_edge, is_chapter_heading(ln, pos)]
            )
        Xf = hstack([
            self.bundle["vec_norm"].transform(norm_texts),
            self.bundle["vec_raw"].transform(lines),
            self.bundle["scaler"].transform(np.array(full_num, dtype=np.float32)),
        ]).tocsr()
        full_probs = self.bundle["full_clf"].predict_proba(Xf)[:, 1]

        kept: List[str] = []
        removed: List[Dict[str, Any]] = []
        stripped_tails: List[Dict[str, Any]] = []

        for idx, (ln, p_full, p_tail) in enumerate(zip(lines, full_probs, tail_probs)):
            _, tail_after_cjk, _ = split_cjk_tail(ln)

            # Case 1: Whole line is spam
            if p_full >= f_th:
                removed.append({"index": idx, "prob": round(float(p_full), 4), "text": ln})
                continue

            # Case 2: Obfuscated tail attached to a sentence
            if p_tail >= t_th and len(tail_after_cjk) >= 4:
                cleaned_ln = strip_tail_at_cjk_boundary(ln)
                if cleaned_ln:
                    # Double-check remainder with full_clf
                    pos = pos_ratios[idx]
                    is_edge = 1.0 if (pos <= 0.08 or pos >= 0.92) else 0.0
                    rem_num = np.array(
                        [
                            extract_unicode_script_features(cleaned_ln)
                            + [pos, is_edge, is_chapter_heading(cleaned_ln, pos)]
                        ],
                        dtype=np.float32,
                    )
                    X_rem = hstack([
                        self.bundle["vec_norm"].transform([normalize_for_model(cleaned_ln)]),
                        self.bundle["vec_raw"].transform([cleaned_ln]),
                        self.bundle["scaler"].transform(rem_num),
                    ]).tocsr()
                    p_rem = float(self.bundle["full_clf"].predict_proba(X_rem)[0, 1])
                    if p_rem >= f_th:
                        removed.append({"index": idx, "prob": round(p_rem, 4), "text": ln})
                        continue

                    kept.append(cleaned_ln)

                stripped_tails.append({
                    "index": idx,
                    "prob": round(float(p_tail), 4),
                    "before": ln,
                    "after": cleaned_ln,
                })
                continue

            # Case 3: Clean story line
            kept.append(ln)

        return {
            "cleaned_text": "\n".join(kept),
            "removed_lines": removed,
            "stripped_tails": stripped_tails,
        }

    def clean_text(self, raw_text: str) -> str:
        """Helper that directly returns the cleaned string."""
        return self.clean(raw_text)["cleaned_text"]
