import "@testing-library/jest-dom/vitest";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { App as AntdApp } from "antd";
import { cleanup, render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { BilingualEvidenceView } from "../../src/features/evidence-db/components/BilingualEvidenceView";
import type { EvidenceGroupDetailResponse } from "../../src/features/evidence-search/types/evidenceSearch";

const detailState = vi.hoisted(() => ({
  detail: null as EvidenceGroupDetailResponse | null,
}));

vi.mock("@/features/evidence-search/hooks/useEvidenceGroupDetail", () => ({
  useEvidenceGroupDetail: () => ({
    detail: detailState.detail,
    isLoading: false,
    isFetching: false,
    error: null,
    refetch: vi.fn(),
  }),
}));

vi.mock("@/features/evidence-search/services/annotations", () => ({
  listAnnotations: vi.fn().mockResolvedValue([]),
  createAnnotation: vi.fn(),
  updateAnnotation: vi.fn(),
  deleteAnnotation: vi.fn(),
}));

vi.mock("@/features/evidence-search/services/evidenceCorrection", () => ({
  patchEvidence: vi.fn(),
}));

vi.mock("@/features/evidence-search/components/annotationLayer", () => ({
  AnnotationLayer: ({ paragraphId, track }: { paragraphId: string; track: string }) => (
    <div data-testid={`annotation-layer-${track}-${paragraphId}`} />
  ),
}));

function factTrace(
  canonicalEvidenceId: string,
  fieldId: string,
  originalValue: string,
  translatedValue: string,
) {
  return {
    canonical_evidence_id: canonicalEvidenceId,
    field_id: fieldId,
    field_name: fieldId === "A.gene_symbol" ? "Gene symbol" : "Variant (c.)",
    original_value: originalValue,
    translated_value: translatedValue,
  };
}

function detailWithFactTraces(): EvidenceGroupDetailResponse {
  return {
    group_id: "gene=FLCN|variant=c.1A>G",
    source_document_id: "doc-1",
    title: "FLCN case report",
    gene: "FLCN",
    variant: "c.1A>G",
    item_count: 0,
    distribution: {
      by_category: {},
      by_field: {},
      by_status: {},
      by_track: {},
    },
    items: [],
    traces: [
      factTrace("ev-1", "A.gene_symbol", "携带FLCN变异", "carried an FLCN variant"),
      factTrace("ev-2", "A.gene_symbol", "另一个FLCN变异", "another FLCN variant"),
    ],
  };
}

function renderView() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, staleTime: 0 },
      mutations: { retry: false },
    },
  });
  return render(
    <MemoryRouter>
      <AntdApp>
        <QueryClientProvider client={queryClient}>
          <BilingualEvidenceView variantSlug="gene=FLCN|variant=c.1A>G" sourceDocumentId="doc-1" />
        </QueryClientProvider>
      </AntdApp>
    </MemoryRouter>,
  );
}

describe("BilingualEvidenceView fact-level bilingual panel", () => {
  beforeEach(() => {
    detailState.detail = detailWithFactTraces();
  });

  afterEach(() => {
    cleanup();
  });

  it("renders every fact pair when there is no whole-document translation", () => {
    renderView();

    expect(screen.getByText("Fact-level bilingual view")).toBeInTheDocument();
    expect(screen.getByText("携带FLCN变异")).toBeInTheDocument();
    expect(screen.getByText("carried an FLCN variant")).toBeInTheDocument();
    expect(screen.getByText("另一个FLCN变异")).toBeInTheDocument();
    expect(screen.getByText("another FLCN variant")).toBeInTheDocument();
  });

  it("does not merge two facts that share the same field id", () => {
    renderView();

    const panel = screen.getByText("Fact-level bilingual view").closest("div")?.parentElement;
    expect(panel).not.toBeNull();
    expect(within(panel as HTMLElement).getAllByText("Gene symbol · Original Text")).toHaveLength(2);
    expect(within(panel as HTMLElement).getAllByText("Gene symbol · Translated Text (English)")).toHaveLength(2);
  });
});
