"""Field-id groups used by evidence search and presentation."""

from __future__ import annotations

GENE_FIELDS = ("A.gene_symbol", "A.gene_aliases")
VARIANT_FIELDS = (
    "A.variant_hgvs_c",
    "A.variant_hgvs_p",
    "A.variant_hgvs_g",
    "A.variant_legacy_name",
)
DISEASE_FIELDS = ("B.disease_diagnosis", "B.clinical_diagnosis", "B.hpo_terms")
CLASSIFICATION_FIELDS = ("J.authority_classification", "J.clinvar_assertion")
