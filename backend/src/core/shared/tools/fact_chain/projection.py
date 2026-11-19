"""Projection of a chain run into Phase 4 evidence and display payloads.

Only facts whose source-window verification label is ``supported`` become
clinical evidence. The original track carries the source-language value; the
translated track carries the fact-level English presentation. Facts are never
translated twice and English text never becomes an extraction input.
"""

from __future__ import annotations

from src.core.agents.extraction.contracts import (
    DocumentEvidenceMap,
    DualEvidenceExtractionResult,
    EvidenceChain,
    EvidenceExtractionResult,
    EvidenceExtractionStatus,
    EvidenceItem,
    EvidenceStatus,
    ExtractionTarget,
    FieldEligibilitySummary,
    SourceLocation,
    SourcePrecision,
    Track,
)
from src.core.agents.extraction.core.grouping import make_group_id, normalize_group_token
from src.core.agents.extraction.domain.catalog import get_field_spec

from .contracts import (
    EVIDENCE_LABELS,
    ChainRun,
    EnglishStatus,
    EnglishView,
    SourceFact,
    VerificationLabel,
)

_PRESENTED_STATUSES = frozenset(
    {EnglishStatus.TRANSLATED.value, EnglishStatus.PASSTHROUGH.value, EnglishStatus.PRESERVED.value}
)

_GENE_FIELD = "A.gene_symbol"
_VARIANT_FIELDS = frozenset({"A.variant_hgvs_c", "A.variant_hgvs_p"})


def supported_facts(run: ChainRun) -> list[SourceFact]:
    return [
        fact
        for fact in run.facts
        if (verification := run.verification_for(fact.fact_id)) is not None
        and verification.label.value in EVIDENCE_LABELS
    ]


def english_text(view: EnglishView | None) -> str | None:
    if view is None or view.status.value not in _PRESENTED_STATUSES:
        return None
    text = (view.english_text or "").strip()
    return text or None


def _ordered(facts: list[SourceFact]) -> list[SourceFact]:
    return sorted(facts, key=lambda fact: (fact.span_start, fact.span_end, fact.fact_id))


def _unique_values(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        text = value.strip()
        token = normalize_group_token(text)
        if token in seen:
            continue
        seen.add(token)
        ordered.append(text)
    return ordered


def _context_gene(fact: SourceFact, gene_facts: list[SourceFact], genes: list[str]) -> str:
    """Attribute a fact to the gene introduced most recently before its span.

    Case reports introduce a gene and then describe that gene's variants and
    phenotypes. Span order is the only linkage the chain records, so it is the
    deterministic basis here; a fact before the first gene fact falls forward
    to that first gene.
    """
    selected = ""
    for gene_fact in gene_facts:
        if gene_fact.span_start <= fact.span_start:
            selected = gene_fact.raw_value.strip()
        else:
            break
    if selected:
        return selected
    if gene_facts:
        return gene_facts[0].raw_value.strip()
    return genes[0] if genes else ""


def _group_plan(
    facts: list[SourceFact],
    *,
    fallback_gene: str,
    fallback_variant: str,
) -> tuple[list[str], dict[str, tuple[str, str]], dict[str, str]]:
    """Build per-fact gene/variant groups instead of one global gene × all variants.

    Returns ordered group ids, the ``(gene, variant)`` behind each id, and the
    group id of every fact. Variants and other facts belong to the gene context
    they follow in the document, so a second gene can never inherit the first
    gene's variants.
    """
    gene_facts = _ordered([fact for fact in facts if fact.field_id == _GENE_FIELD])
    genes = _unique_values([fact.raw_value for fact in gene_facts])
    if not genes and fallback_gene.strip():
        genes = [fallback_gene.strip()]
    if not genes:
        genes = [""]

    variants_by_gene: dict[str, list[str]] = {gene: [] for gene in genes}
    fact_gene: dict[str, str] = {}
    for fact in _ordered(facts):
        gene = _context_gene(fact, gene_facts, genes)
        fact_gene[fact.fact_id] = gene
        if fact.field_id in _VARIANT_FIELDS:
            variants_by_gene.setdefault(gene, []).append(fact.raw_value)
    variants_by_gene = {gene: _unique_values(values) for gene, values in variants_by_gene.items()}
    if fallback_variant.strip() and not any(variants_by_gene.values()):
        variants_by_gene[genes[0]] = [fallback_variant.strip()]

    group_ids: list[str] = []
    groups: dict[str, tuple[str, str]] = {}
    for gene in genes:
        for variant in variants_by_gene.get(gene) or [""]:
            group_id = make_group_id(gene, variant)
            if group_id in groups:
                continue
            groups[group_id] = (gene, variant)
            group_ids.append(group_id)

    fact_group: dict[str, str] = {}
    for fact in facts:
        gene = fact_gene[fact.fact_id]
        if fact.field_id in _VARIANT_FIELDS:
            group_id = make_group_id(gene, fact.raw_value)
            if group_id in groups:
                fact_group[fact.fact_id] = group_id
                continue
        variants = variants_by_gene.get(gene) or [""]
        fact_group[fact.fact_id] = make_group_id(gene, variants[0])
    return group_ids, groups, fact_group


def _page_for_offset(page_ranges: list[tuple[int, int, int]], offset: int) -> int:
    for start, end, page in page_ranges:
        if start <= offset < end:
            return page
    return page_ranges[-1][2] if page_ranges else 1


def _item(
    fact: SourceFact,
    *,
    value: str,
    track: Track,
    group_id: str,
    status: EvidenceStatus,
    language: str,
    page_ranges: list[tuple[int, int, int]],
    note: str,
    target_gene: str,
    target_disease: str,
    target_variant: str,
) -> EvidenceItem:
    try:
        spec = get_field_spec(fact.field_id)
        category, field_name = spec.category_id, spec.field_name
    except KeyError:
        category, field_name = fact.field_id.split(".", 1)[0], fact.field_id
    return EvidenceItem(
        field_id=fact.field_id,
        category=category,
        field_name=field_name,
        status=status,
        value=value,
        source=SourceLocation(
            span_id=f"{track.value}-{fact.fact_id}",
            page=_page_for_offset(page_ranges, fact.span_start),
            start_offset=fact.span_start,
            end_offset=fact.span_end,
            context_type="case_report",
            context_ref=fact.window_id,
            text_snippet=fact.quote,
            block_type="text",
            source_precision=SourcePrecision.EXACT,
        ),
        confidence=0.9,
        group_id=group_id,
        notes=note,
        inference_basis=["source_fact_chain"],
        article_language=language,
        evidence_source_language=language,
        target_gene=target_gene,
        target_disease=target_disease,
        target_variant=target_variant,
    )


def _result(
    *,
    document_id: str,
    track: Track,
    items: list[EvidenceItem],
    chains: list[EvidenceChain],
    language: str,
    relevant: bool,
) -> EvidenceExtractionResult:
    gene_terms: list[str] = []
    variant_terms: list[str] = []
    disease_terms: list[str] = []
    for chain in chains:
        for values, text in (
            (gene_terms, chain.gene_text),
            (variant_terms, chain.variant_text),
            (disease_terms, chain.disease_text),
        ):
            if text and text not in values:
                values.append(text)
    return EvidenceExtractionResult(
        status=EvidenceExtractionStatus.COMPLETED if relevant else EvidenceExtractionStatus.NOT_RELEVANT,
        document_id=document_id,
        track=track,
        evidence_map=DocumentEvidenceMap(
            relevant=relevant,
            disease_terms=disease_terms,
            gene_terms=gene_terms,
            variant_terms=variant_terms,
        ),
        evidence_items=items,
        evidence_chains=chains,
        field_eligibility_summary=FieldEligibilitySummary(eligible_field_count=len(items)),
    )


def project_dual_result(
    run: ChainRun,
    *,
    extraction_target: ExtractionTarget | None = None,
    page_ranges: list[tuple[int, int, int]] | None = None,
    target_gene: str = "",
    target_disease: str = "",
    target_variant: str = "",
) -> DualEvidenceExtractionResult:
    """Build the Phase 4 input, keeping original and fact-English tracks separate."""
    ranges = page_ranges or []
    supported = supported_facts(run)
    if not supported:
        empty = _result(
            document_id=run.document_id,
            track=Track.ORIGINAL,
            items=[],
            chains=[],
            language=run.language,
            relevant=False,
        )
        translated_empty = empty.model_copy(update={"track": Track.TRANSLATED})
        return DualEvidenceExtractionResult(
            document_id=run.document_id,
            original_result=empty,
            translated_result=translated_empty,
        )

    group_ids, groups, fact_group = _group_plan(
        supported,
        fallback_gene=target_gene,
        fallback_variant=target_variant,
    )
    target_token = normalize_group_token(target_gene).upper() if target_gene.strip() else ""
    relevant_group_ids = [
        group_id
        for group_id in group_ids
        if not target_token or normalize_group_token(groups[group_id][0]).upper() == target_token
    ]
    relevant_group_set = set(relevant_group_ids)

    chains: list[EvidenceChain] = []
    for group_id in relevant_group_ids:
        gene, variant = groups[group_id]
        field_ids = [fact.field_id for fact in supported if fact_group[fact.fact_id] == group_id]
        chains.append(
            EvidenceChain(
                chain_id=group_id,
                chain_level="full" if gene and variant else ("partial" if gene else "singleton"),
                gene_text=gene,
                disease_text=target_disease.strip(),
                variant_text=variant,
                evidence_field_ids=field_ids,
            )
        )

    original_items: list[EvidenceItem] = []
    translated_items: list[EvidenceItem] = []
    for fact in supported:
        verification = run.verification_for(fact.fact_id)
        label = verification.label.value if verification is not None else VerificationLabel.UNVERIFIED.value
        group_id = fact_group[fact.fact_id]
        gene, variant = groups[group_id]
        # Off-target documents keep their facts for audit but must not enter
        # Phase 4 candidate generation, matching the legacy target guard.
        off_target = bool(target_token) and group_id not in relevant_group_set
        status = EvidenceStatus.CONTEXT_CONTAMINATION if off_target else EvidenceStatus.FOUND
        note = f"verification={label}"
        if verification is not None and verification.reason:
            note += f"; {verification.reason}"
        if off_target:
            note += f"; target_guard:off_target_gene={gene or 'unknown'}"
        original_items.append(
            _item(
                fact,
                value=fact.raw_value,
                track=Track.ORIGINAL,
                group_id=group_id,
                status=status,
                language=run.language,
                page_ranges=ranges,
                note=note,
                target_gene=gene,
                target_disease=target_disease,
                target_variant=variant,
            )
        )
        view = next(
            (candidate for candidate in run.english_for(fact.fact_id) if english_text(candidate) is not None),
            None,
        )
        text = english_text(view)
        if text is not None:
            translated_items.append(
                _item(
                    fact,
                    value=text,
                    track=Track.TRANSLATED,
                    group_id=group_id,
                    status=status,
                    language=run.language,
                    page_ranges=ranges,
                    note=note,
                    target_gene=gene,
                    target_disease=target_disease,
                    target_variant=variant,
                )
            )

    relevant = bool(chains)
    # Chain-level identity must be visible to Phase 4's gene-linked filter.
    original_result = _result(
        document_id=run.document_id,
        track=Track.ORIGINAL,
        items=original_items,
        chains=chains,
        language=run.language,
        relevant=relevant,
    )
    translated_result = _result(
        document_id=run.document_id,
        track=Track.TRANSLATED,
        items=translated_items,
        chains=chains,
        language=run.language,
        relevant=relevant and bool(translated_items),
    )
    if extraction_target is not None:
        original_result = original_result.model_copy(update={"extraction_target": extraction_target})
        translated_result = translated_result.model_copy(update={"extraction_target": extraction_target})
    return DualEvidenceExtractionResult(
        document_id=run.document_id,
        original_result=original_result,
        translated_result=translated_result,
    )


__all__ = ["english_text", "project_dual_result", "supported_facts"]
