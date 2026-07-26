"""
Pure ML inference layer — ResearchCategorizer.

This module has zero I/O: no file reads, no database calls, no Streamlit.
It receives pre-encoded embeddings and returns structured result dicts.
"""
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from app.core.config import settings
from app.util.pipeline.config import CategorizerConfig


class ResearchCategorizer:
    """Encodes research texts and classifies them into field categories.

    Responsibilities:
    - Load a sentence-transformer model.
    - Pre-encode category descriptions and efficiency keyword groups.
    - Classify arbitrary lists of pre-cleaned text strings.

    No database or file I/O is performed by this class. All configuration
    is injected via ``CategorizerConfig``.
    """

    def __init__(self, config: CategorizerConfig, model_name: str | None = None):
        model_name = model_name or settings.CATEGORIZER_MODEL

        self.confidence_threshold = config.confidence_threshold
        self.gap_threshold = config.gap_threshold
        self.eff_threshold = config.eff_threshold
        self.field_names = config.field_names
        self.efficiency_cue_words = config.efficiency_cue_words

        print(f"\n[1/3] Loading model '{model_name}' ...")
        self.model = SentenceTransformer(model_name)

        print("[2/3] Encoding category descriptions and efficiency groups ...")
        self.field_embeddings = self.model.encode(config.field_descriptions, show_progress_bar=False)
        self.eff_embeddings_en = (
            self.model.encode(config.efficiency_keywords_en, show_progress_bar=False)
            if config.efficiency_keywords_en
            else None
        )
        self.eff_embeddings_id = (
            self.model.encode(config.efficiency_keywords_id, show_progress_bar=False)
            if config.efficiency_keywords_id
            else None
        )

    def categorize(self, texts: list[str]) -> list[dict]:
        """Categorize pre-cleaned texts.

        The caller is responsible for applying ``clean_title`` / ``sanitize_casing``
        before passing texts here.

        Args:
            texts: List of cleaned research title/abstract strings.

        Returns:
            List of result dicts with keys:
            category, status, confidence_score, alt_category, alt_score,
            gap, reason, is_efficiency, efficiency_score.
        """
        print(f"[3/3] Categorizing {len(texts)} items ...")
        embeddings = self.model.encode(texts, show_progress_bar=True)

        sims_fields = cosine_similarity(embeddings, self.field_embeddings)
        sims_eff_en = cosine_similarity(embeddings, self.eff_embeddings_en) if self.eff_embeddings_en is not None else None
        sims_eff_id = cosine_similarity(embeddings, self.eff_embeddings_id) if self.eff_embeddings_id is not None else None

        results = []
        for i, row in enumerate(sims_fields):
            top_idx = np.argsort(row)[::-1]
            best_cat = self.field_names[top_idx[0]]
            best_score = float(row[top_idx[0]])
            alt_cat = self.field_names[top_idx[1]]
            alt_score = float(row[top_idx[1]])
            gap = best_score - alt_score

            is_low_conf = best_score < self.confidence_threshold
            is_ambiguous = gap < self.gap_threshold

            if is_low_conf:
                status = "Uncategorized"
                reason = f"Low confidence ({best_score:.3f} < {self.confidence_threshold})"
            elif is_ambiguous:
                status = "Ambiguous"
                reason = (
                    f"Close match between {best_cat} ({best_score:.3f}) "
                    f"and {alt_cat} ({alt_score:.3f}), gap={gap:.3f}"
                )
            else:
                status = "Clear"
                reason = ""

            text_lower = texts[i].lower()

            eff_score_en = self._compute_eff_score(sims_eff_en, i, text_lower)
            eff_score_id = self._compute_eff_score(sims_eff_id, i, text_lower)
            eff_score = max(eff_score_en, eff_score_id)

            results.append({
                "category": best_cat,
                "status": status,
                "confidence_score": round(best_score, 4),
                "alt_category": alt_cat,
                "alt_score": round(alt_score, 4),
                "gap": round(gap, 4),
                "reason": reason,
                "is_efficiency": "Yes" if eff_score >= self.eff_threshold else "No",
                "efficiency_score": round(eff_score, 4),
            })

        return results

    # ── Private helpers ────────────────────────────────────────────────────────

    def _compute_eff_score(self, sims, row_idx: int, text_lower: str) -> float:
        """Compute the effective efficiency score for a single text row."""
        if sims is None:
            return 0.0

        scores = sims[row_idx]
        score = float(np.max(scores))
        best_group = int(np.argmax(scores))
        n_groups = len(scores)
        cue_groups = {3, 4, 5, 6} if n_groups == 7 else ({2, 3, 4} if n_groups == 5 else set())

        if best_group in cue_groups:
            if not any(cue in text_lower for cue in self.efficiency_cue_words):
                excl = [s for idx, s in enumerate(scores) if idx not in cue_groups]
                score = float(np.max(excl)) if excl else 0.0

        return score
