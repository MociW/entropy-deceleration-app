import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from dateutil import parser as date_parser
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.models import (
    Research,
    ResearchValidationFlag,
    Author,
    Institution,
    research_authors,
)
from app.services.cleaner import clean_title, sanitize_casing
from app.services.constants import (
    FIELDS,
    EFFICIENCY_KEYWORDS,
    EFFICIENCY_CUE_WORDS,
)
from app.services.keyword_store import (
    load_thresholds,
    load_field_keywords,
    load_efficiency_keywords,
    load_cue_words,
)


# ══════════════════════════════════════════════════════════════════════════════
# Config layer — loads thresholds / keywords from DB (falls back to constants)
# ══════════════════════════════════════════════════════════════════════════════


@dataclass
class CategorizerConfig:
    confidence_threshold: float
    gap_threshold: float
    eff_threshold: float
    field_names: list[str]
    field_descriptions: list[str]
    efficiency_keywords_en: list[str] | None
    efficiency_keywords_id: list[str] | None
    efficiency_cue_words: list[str]


def load_config(session: Session | None = None) -> CategorizerConfig:
    thresholds = load_thresholds(session)
    fields = load_field_keywords(session)
    eff_kw_en = load_efficiency_keywords(lang="EN", session=session)
    eff_kw_id = load_efficiency_keywords(lang="ID", session=session)
    cue_words = load_cue_words(session)

    return CategorizerConfig(
        confidence_threshold=thresholds["confidence_threshold"],
        gap_threshold=thresholds["gap_threshold"],
        eff_threshold=thresholds["eff_threshold"],
        field_names=list(fields.keys()),
        field_descriptions=list(fields.values()),
        efficiency_keywords_en=eff_kw_en if eff_kw_en else None,
        efficiency_keywords_id=eff_kw_id if eff_kw_id else None,
        efficiency_cue_words=cue_words,
    )


# ══════════════════════════════════════════════════════════════════════════════
# ML layer — pure inference, no DB, no I/O
# ══════════════════════════════════════════════════════════════════════════════


class ResearchCategorizer:
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
        """Categorize pre-cleaned texts (caller must apply clean_title/sanitize_casing beforehand)."""
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

            eff_score_en = 0.0
            if sims_eff_en is not None:
                scores = sims_eff_en[i]
                eff_score_en = float(np.max(scores))
                best_group = int(np.argmax(scores))
                n_groups = len(scores)
                cue_groups = {3, 4, 5, 6} if n_groups == 7 else ({2, 3, 4} if n_groups == 5 else set())
                if best_group in cue_groups:
                    if not any(cue in text_lower for cue in self.efficiency_cue_words):
                        excl = [s for idx, s in enumerate(scores) if idx not in cue_groups]
                        eff_score_en = float(np.max(excl)) if excl else 0.0

            eff_score_id = 0.0
            if sims_eff_id is not None:
                scores = sims_eff_id[i]
                eff_score_id = float(np.max(scores))
                best_group = int(np.argmax(scores))
                n_groups = len(scores)
                cue_groups = {3, 4, 5, 6} if n_groups == 7 else ({2, 3, 4} if n_groups == 5 else set())
                if best_group in cue_groups:
                    if not any(cue in text_lower for cue in self.efficiency_cue_words):
                        excl = [s for idx, s in enumerate(scores) if idx not in cue_groups]
                        eff_score_id = float(np.max(excl)) if excl else 0.0

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


# ══════════════════════════════════════════════════════════════════════════════
# Data layer — file loading, preprocessing, text extraction
# ══════════════════════════════════════════════════════════════════════════════


def load_data(path: str) -> pd.DataFrame:
    p = Path(path)
    df = pd.read_excel(p) if p.suffix in {".xlsx", ".xls"} else pd.read_csv(p)
    df.columns = [c.strip().lower() for c in df.columns]
    if "title" not in df.columns:
        raise ValueError("File must have a 'title' column.")
    if "year" not in df.columns:
        df["year"] = None

    cols = ["title", "year"]
    for c in ("abstract", "data_id", "author", "institution", "start_at", "finish_at"):
        if c in df.columns:
            cols.append(c)

    res_df = df[cols].copy()
    if "abstract" in res_df.columns:
        res_df["abstract"] = res_df["abstract"].fillna("")
    return res_df


def preprocess(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Sanitize casing, clean titles, extract categorization texts. Returns (clean_df, texts)."""
    df = df.copy()
    df["title"] = df["title"].apply(sanitize_casing)
    if "abstract" in df.columns:
        df["abstract"] = df["abstract"].apply(sanitize_casing)

    df["title"] = df["title"].apply(clean_title)
    texts = [clean_title(t) for t in get_categorization_texts(df)]
    return df, texts


def get_categorization_texts(df: pd.DataFrame) -> list[str]:
    """Return abstract if present and non-empty (>10 chars), else title."""
    if "abstract" not in df.columns:
        return df["title"].tolist()

    texts = []
    for _, row in df.iterrows():
        abstract = str(row.get("abstract", "")).strip()
        title = str(row["title"]).strip()
        if abstract and len(abstract) > 10:
            texts.append(abstract)
        else:
            texts.append(title)
    return texts


# ══════════════════════════════════════════════════════════════════════════════
# Persistence layer — CSV/Excel export + DB save
# ══════════════════════════════════════════════════════════════════════════════

_EXPORT_COLS = [
    "title", "year", "category", "status", "is_efficiency",
    "confidence_score", "gap", "efficiency_score",
    "alt_category", "alt_score", "reason",
]

_RENAME_MAP = {
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


def save_outputs(df: pd.DataFrame, out_dir: Path, out_filename: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    export_cols = list(_EXPORT_COLS)
    if "abstract" in df.columns:
        export_cols.insert(2, "abstract")

    export = df[export_cols].copy()
    export.columns = [_RENAME_MAP.get(c, c) for c in export.columns]

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


def save_to_db(df: pd.DataFrame, contribution_category: str, session: Session) -> int:
    """Persist categorization results + metadata to database. Returns record count."""
    session.query(Research).filter_by(contribution_category=contribution_category).delete()
    session.commit()

    has_abstract = "abstract" in df.columns
    has_author = "author" in df.columns
    has_institution = "institution" in df.columns

    author_cache: dict[str, Author] = {}
    institution_cache: dict[str, Institution] = {}
    for auth in session.query(Author).all():
        author_cache[auth.nidn or auth.name] = auth
    for inst in session.query(Institution).all():
        institution_cache[inst.name] = inst

    for _, row in df.iterrows():
        start_at = None
        if pd.notna(row.get("start_at")) and row["start_at"]:
            try:
                start_at = date_parser.parse(str(row["start_at"])).date()
            except Exception:
                pass
        finish_at = None
        if pd.notna(row.get("finish_at")) and row["finish_at"]:
            try:
                finish_at = date_parser.parse(str(row["finish_at"])).date()
            except Exception:
                pass

        data_id = int(row["data_id"]) if pd.notna(row.get("data_id")) and row.get("data_id") else None

        research = Research(
            data_id=data_id,
            title=row["title"],
            abstract=row.get("abstract") if has_abstract else None,
            year=int(row["year"]) if row["year"] else 0,
            contribution_category=contribution_category,
            start_at=start_at,
            finish_at=finish_at,
        )
        research.validation_flag = ResearchValidationFlag(
            category=row.get("category"),
            status=row.get("status"),
            confidence_score=row.get("confidence_score"),
            alt_category=row.get("alt_category"),
            alt_score=row.get("alt_score"),
            gap=row.get("gap"),
            reason=row.get("reason") or None,
            is_efficiency=row.get("is_efficiency"),
            efficiency_score=row.get("efficiency_score"),
            is_entropy=(row.get("is_efficiency") == "Yes"),
        )
        session.add(research)
        session.flush()

        seen_institutions = set()
        if has_institution:
            inst_str = str(row.get("institution", ""))
            if inst_str and inst_str.lower() != "nan":
                for inst_name in (i.strip() for i in inst_str.split(";") if i.strip()):
                    inst = institution_cache.get(inst_name)
                    if not inst:
                        inst = Institution(name=inst_name)
                        session.add(inst)
                        session.flush()
                        institution_cache[inst_name] = inst
                    if inst.id not in seen_institutions:
                        research.institutions.append(inst)
                        seen_institutions.add(inst.id)

        seen_authors = set()
        if has_author:
            author_str = str(row.get("author", ""))
            if author_str and author_str.lower() != "nan":
                for auth_item in (a.strip() for a in author_str.split(";") if a.strip()):
                    match = re.search(r"([^\[\(]+)(?:\[NIDN:\s*([^\]]+)\])?(?:\(([^\)]+)\))?", auth_item)
                    if match:
                        name = match.group(1).strip()
                        nidn = match.group(2).strip() if match.group(2) else None
                        raw_role = match.group(3).strip() if match.group(3) else None
                        role = None
                        if raw_role:
                            role = "Leader" if "ketua" in raw_role.lower() else ("Member" if "anggota" in raw_role.lower() else raw_role)

                        key = nidn or name
                        auth = author_cache.get(key)
                        if not auth:
                            auth = Author(name=name, nidn=nidn)
                            session.add(auth)
                            session.flush()
                            author_cache[key] = auth
                        if auth.id not in seen_authors:
                            session.execute(
                                research_authors.insert().values(
                                    research_id=research.id,
                                    author_id=auth.id,
                                    role=role,
                                )
                            )
                            seen_authors.add(auth.id)

    session.commit()
    return session.query(Research).filter_by(contribution_category=contribution_category).count()
