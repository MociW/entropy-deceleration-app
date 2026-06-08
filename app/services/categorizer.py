from pathlib import Path

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from app.core.config import settings
from app.services.constants import (
    FIELDS,
    EFFICIENCY_KEYWORDS,
    EFFICIENCY_CUE_WORDS,
)
from app.services.cleaner import clean_title
from app.services.keyword_store import load_thresholds, load_field_keywords, load_efficiency_keywords, load_cue_words


class ResearchCategorizer:
    def __init__(
        self,
        model_name: str | None = None,
        confidence_threshold: float | None = None,
        gap_threshold: float | None = None,
        eff_threshold: float | None = None,
        field_keywords: dict[str, str] | None = None,
        efficiency_keywords: list[str] | None = None,
        efficiency_cue_words: list[str] | None = None,
        use_db: bool = True,
    ):
        model_name = model_name or settings.CATEGORIZER_MODEL

        if use_db:
            thresholds = load_thresholds()
            self.confidence_threshold = (
                confidence_threshold if confidence_threshold is not None
                else thresholds["confidence_threshold"]
            )
            self.gap_threshold = (
                gap_threshold if gap_threshold is not None
                else thresholds["gap_threshold"]
            )
            self.eff_threshold = (
                eff_threshold if eff_threshold is not None
                else thresholds["eff_threshold"]
            )
        else:
            from app.services.constants import (
                DEFAULT_CONFIDENCE_THRESHOLD, DEFAULT_GAP_THRESHOLD, DEFAULT_EFF_THRESHOLD,
            )
            self.confidence_threshold = confidence_threshold or DEFAULT_CONFIDENCE_THRESHOLD
            self.gap_threshold = gap_threshold or DEFAULT_GAP_THRESHOLD
            self.eff_threshold = eff_threshold or DEFAULT_EFF_THRESHOLD

        print(f"\n[1/3] Loading model '{model_name}' ...")
        self.model = SentenceTransformer(model_name)

        if field_keywords is not None:
            fields = field_keywords
        elif use_db:
            fields = load_field_keywords()
        else:
            fields = dict(FIELDS)

        if efficiency_keywords is not None:
            eff_kw_en = efficiency_keywords
            eff_kw_id = []
        elif use_db:
            eff_kw_en = load_efficiency_keywords(lang="EN")
            eff_kw_id = load_efficiency_keywords(lang="ID")
        else:
            eff_kw_en = list(EFFICIENCY_KEYWORDS)
            eff_kw_id = []

        if efficiency_cue_words is not None:
            self.efficiency_cue_words = efficiency_cue_words
        elif use_db:
            self.efficiency_cue_words = load_cue_words()
        else:
            self.efficiency_cue_words = list(EFFICIENCY_CUE_WORDS)

        self.field_names = list(fields.keys())

        print("[2/3] Encoding category descriptions and efficiency groups ...")
        self.field_embeddings = self.model.encode(list(fields.values()), show_progress_bar=False)
        self.eff_embeddings_en = self.model.encode(eff_kw_en, show_progress_bar=False) if eff_kw_en else None
        self.eff_embeddings_id = self.model.encode(eff_kw_id, show_progress_bar=False) if eff_kw_id else None

    def categorize(self, texts: list[str]) -> list[dict]:
        """Categorize a list of texts (abstracts or titles, already cleaned)."""
        cleaned = [clean_title(t) for t in texts]
        print(f"[3/3] Categorizing {len(cleaned)} items ...")
        embeddings = self.model.encode(cleaned, show_progress_bar=True)

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

            # Calculate English efficiency score
            if sims_eff_en is not None:
                eff_scores_en = sims_eff_en[i]
                eff_score_en = float(np.max(eff_scores_en))
                best_eff_group_en = int(np.argmax(eff_scores_en))
                num_groups_en = len(eff_scores_en)
                cue_groups_en = {3, 4, 5, 6} if num_groups_en == 7 else ({2, 3, 4} if num_groups_en == 5 else set())
                if best_eff_group_en in cue_groups_en:
                    title_lower = cleaned[i].lower()
                    has_cue = any(cue in title_lower for cue in self.efficiency_cue_words)
                    if not has_cue:
                        eff_scores_excl = [score for idx, score in enumerate(eff_scores_en) if idx not in cue_groups_en]
                        eff_score_en = float(np.max(eff_scores_excl)) if eff_scores_excl else 0.0
            else:
                eff_score_en = 0.0

            # Calculate Indonesian efficiency score
            if sims_eff_id is not None:
                eff_scores_id = sims_eff_id[i]
                eff_score_id = float(np.max(eff_scores_id))
                best_eff_group_id = int(np.argmax(eff_scores_id))
                num_groups_id = len(eff_scores_id)
                cue_groups_id = {3, 4, 5, 6} if num_groups_id == 7 else ({2, 3, 4} if num_groups_id == 5 else set())
                if best_eff_group_id in cue_groups_id:
                    title_lower = cleaned[i].lower()
                    has_cue = any(cue in title_lower for cue in self.efficiency_cue_words)
                    if not has_cue:
                        eff_scores_excl = [score for idx, score in enumerate(eff_scores_id) if idx not in cue_groups_id]
                        eff_score_id = float(np.max(eff_scores_excl)) if eff_scores_excl else 0.0
            else:
                eff_score_id = 0.0

            # Take the maximum of the two language similarity scores (Bilingual Max-Pooling)
            eff_score = max(eff_score_en, eff_score_id)
            is_efficiency = "Yes" if eff_score >= self.eff_threshold else "No"

            results.append({
                "category": best_cat,
                "status": status,
                "confidence_score": round(best_score, 4),
                "alt_category": alt_cat,
                "alt_score": round(alt_score, 4),
                "gap": round(gap, 4),
                "reason": reason,
                "is_efficiency": is_efficiency,
                "efficiency_score": round(eff_score, 4),
            })

        return results


def load_data(path: str) -> pd.DataFrame:
    """Load data from CSV or Excel. Returns a DataFrame with title, year, and abstract (if available)."""
    p = Path(path)
    df = pd.read_excel(p) if p.suffix in {".xlsx", ".xls"} else pd.read_csv(p)
    df.columns = [c.strip().lower() for c in df.columns]
    if "title" not in df.columns:
        raise ValueError("File must have a 'title' column.")
    if "year" not in df.columns:
        df["year"] = None

    cols = ["title", "year"]
    if "abstract" in df.columns:
        cols.append("abstract")

    return df[cols].fillna("").copy()


def get_categorization_texts(df: pd.DataFrame) -> list[str]:
    """Return the best available text for categorization: abstract if present and non-empty, else title."""
    if "abstract" not in df.columns:
        return df["title"].tolist()

    texts = []
    for _, row in df.iterrows():
        abstract = str(row.get("abstract", "")).strip()
        title = str(row["title"]).strip()
        # Prefer abstract if it exists and is meaningful (>10 chars to filter noise)
        if abstract and len(abstract) > 10:
            texts.append(abstract)
        else:
            texts.append(title)
    return texts


def save_outputs(df: pd.DataFrame, out_dir: Path, out_filename: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    export_cols = [
        "title", "year", "category", "status", "is_efficiency",
        "confidence_score", "gap", "efficiency_score",
        "alt_category", "alt_score", "reason"
    ]
    # Only include abstract in export if it exists
    if "abstract" in df.columns:
        export_cols.insert(2, "abstract")

    export = df[export_cols].copy()

    rename_map = {
        "title": "Title",
        "year": "Year",
        "abstract": "Abstract",
        "category": "Category",
        "status": "Status",
        "is_efficiency": "Efficiency Focus",
        "confidence_score": "Category Score",
        "gap": "Category Gap",
        "efficiency_score": "Max Efficiency Score",
        "alt_category": "Alt Category",
        "alt_score": "Alt Score",
        "reason": "Reason",
    }
    export.columns = [rename_map.get(c, c) for c in export.columns]

    csv_path = out_dir / f"{out_filename}.csv"
    export.to_csv(csv_path, index=False)

    xlsx_path = out_dir / f"{out_filename}.xlsx"

    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        export.to_excel(writer, index=False, sheet_name="Results")

        sum_cat = df.groupby(["category", "status"]).size().reset_index(name="Count")
        sum_cat.to_excel(writer, index=False, sheet_name="Summary_Bidang")

        sum_eff = df["is_efficiency"].value_counts().reset_index()
        sum_eff.columns = ["Efficiency Focus", "Count"]
        sum_eff.to_excel(writer, index=False, sheet_name="Summary_Efisiensi")

    print(f"\nProcess complete. Files saved to: {xlsx_path}")
    print(f"  CSV also available at: {csv_path}")
