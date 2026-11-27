import { useState } from "react";
import { Alert, Segmented, Table, Tag } from "antd";
import { useI18n } from "@/lib/i18n";
import { useStandardizedEntities } from "../hooks/useStandardizedEntities";
import type { StandardizedEntity } from "../types/pipeline";

type EntityFilter = "all" | "standardized" | "ambiguous" | "unmapped";

const FILTER_ORDER: EntityFilter[] = ["all", "standardized", "ambiguous", "unmapped"];

const STATUS_COLORS: Record<string, string> = {
  standardized: "green",
  ambiguous: "orange",
  unmapped: "default",
};

const ENTITY_TYPE_KEYS: Record<string, string> = {
  gene: "pipeline.standardization.entityType.gene",
  variant: "pipeline.standardization.entityType.variant",
  disease: "pipeline.standardization.entityType.disease",
  phenotype: "pipeline.standardization.entityType.phenotype",
};

const STATUS_KEYS: Record<string, string> = {
  standardized: "pipeline.standardization.status.standardized",
  ambiguous: "pipeline.standardization.status.ambiguous",
  unmapped: "pipeline.standardization.status.unmapped",
};

function rawTextLabel(entity: StandardizedEntity): string {
  if (entity.raw_texts.length === 0) return "—";
  const shown = entity.raw_texts.slice(0, 3).join(", ");
  return entity.raw_texts.length > 3 ? `${shown} +${entity.raw_texts.length - 3}` : shown;
}

/** Phase 4 detail table: normalized entities bound to one run's evidence. */
export function StandardizationEntityTable({ runId }: { runId: string }) {
  const { t } = useI18n();
  const [filter, setFilter] = useState<EntityFilter>("all");
  const { data, isLoading, error } = useStandardizedEntities(runId, true);

  if (isLoading) {
    return <p style={{ fontSize: 12, color: "var(--color-text-muted)" }}>{t("pipeline.standardization.loading")}</p>;
  }
  if (error) {
    return (
      <Alert
        type="error"
        showIcon
        message={t("pipeline.standardization.loadError")}
        description={error instanceof Error ? error.message : String(error)}
      />
    );
  }

  const items = data?.items ?? [];
  if (items.length === 0) {
    return <p style={{ fontSize: 12, color: "var(--color-text-muted)" }}>{t("pipeline.standardization.empty")}</p>;
  }

  const counts: Record<EntityFilter, number> = {
    all: items.length,
    standardized: items.filter((item) => item.standardization_status === "standardized").length,
    ambiguous: items.filter((item) => item.standardization_status === "ambiguous").length,
    unmapped: items.filter((item) => item.standardization_status === "unmapped").length,
  };
  const rows = filter === "all" ? items : items.filter((item) => item.standardization_status === filter);
  const filterOptions = FILTER_ORDER.map((value) => ({
    value,
    label: `${t(`pipeline.standardization.filter.${value}`)} (${counts[value]})`,
  }));

  const columns = [
    {
      title: t("pipeline.standardization.type"),
      dataIndex: "entity_type",
      width: 100,
      render: (value: string) => (
        <Tag color="blue">{t(ENTITY_TYPE_KEYS[value] ?? value)}</Tag>
      ),
    },
    {
      title: t("pipeline.standardization.rawText"),
      dataIndex: "raw_texts",
      render: (_: unknown, entity: StandardizedEntity) => (
        <span title={entity.raw_texts.join(", ")} style={{ fontFamily: "var(--font-mono, monospace)" }}>
          {rawTextLabel(entity)}
        </span>
      ),
    },
    {
      title: t("pipeline.standardization.displayName"),
      dataIndex: "display_name",
      render: (value: string) => <span style={{ fontWeight: 500 }}>{value}</span>,
    },
    {
      title: t("pipeline.standardization.externalId"),
      dataIndex: "external_id",
      width: 220,
      render: (value: string | null | undefined) =>
        value ? (
          <code style={{ fontFamily: "var(--font-mono, monospace)", fontSize: 12 }}>{value}</code>
        ) : (
          "—"
        ),
    },
    {
      title: t("pipeline.standardization.statusColumn"),
      dataIndex: "standardization_status",
      width: 120,
      render: (value: string) => (
        <Tag color={STATUS_COLORS[value] ?? "default"}>
          {t(STATUS_KEYS[value] ?? value)}
        </Tag>
      ),
    },
    {
      title: t("pipeline.standardization.occurrences"),
      dataIndex: "occurrence_count",
      width: 100,
      align: "right" as const,
      render: (value: number) => value.toLocaleString(),
    },
  ];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 8,
        }}
      >
        <div>
          <p style={{ fontSize: 13, fontWeight: 600, color: "var(--color-text-strong)" }}>
            {t("pipeline.standardization.detailTitle")}
          </p>
          <p style={{ fontSize: 12, color: "var(--color-text-muted)" }}>
            {t("pipeline.standardization.detailDescription", { total: data?.total ?? items.length })}
          </p>
        </div>
        <Segmented
          size="small"
          value={filter}
          options={filterOptions}
          onChange={(value) => setFilter(value as EntityFilter)}
        />
      </div>
      <Table<StandardizedEntity>
        rowKey="entity_id"
        size="small"
        columns={columns}
        dataSource={rows}
        pagination={{ pageSize: 8, showSizeChanger: false, size: "small" }}
        scroll={{ x: 760 }}
      />
    </div>
  );
}
