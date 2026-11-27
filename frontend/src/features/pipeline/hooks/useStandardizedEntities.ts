import { useQuery } from "@tanstack/react-query";
import { getStandardizedEntities } from "../services/pipeline";

/** Load distinct standardized entities for a completed Phase 4 run. */
export function useStandardizedEntities(runId: string, enabled: boolean) {
  return useQuery({
    queryKey: ["pipeline", "standardized-entities", runId],
    queryFn: () => getStandardizedEntities(runId),
    enabled,
  });
}
