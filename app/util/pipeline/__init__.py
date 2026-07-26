"""
Categorization pipeline public API.

Import from here instead of individual sub-modules:

    from app.util.pipeline import ResearchCategorizer, load_config, research_load_data
"""
from app.util.pipeline.config import CategorizerConfig, load_config
from app.util.pipeline.model import ResearchCategorizer
from app.util.pipeline.loader import (
    research_load_data,
    research_preprocess,
    get_categorization_texts,
    load_uncategorized_from_db,
)
from app.util.pipeline.persistence import (
    save_outputs,
    create_research_records,
    delete_research_records,
    update_categorization_results,
)

__all__ = [
    "CategorizerConfig",
    "load_config",
    "ResearchCategorizer",
    "research_load_data",
    "research_preprocess",
    "get_categorization_texts",
    "load_uncategorized_from_db",
    "save_outputs",
    "create_research_records",
    "delete_research_records",
    "update_categorization_results",
]
