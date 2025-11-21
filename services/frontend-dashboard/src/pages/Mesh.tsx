import React from "react";
import { PageHeader } from "@/components/layout/PageHeader";
import { useQuery } from "@tanstack/react-query";
import { fetchMesh } from "@/lib/api";
import MeshVisualization from "@/components/mesh/MeshVisualization";
import FilterSidebar, { type MeshFilters } from "@/components/mesh/FilterSidebar";
import { GlassCard } from "@/components/ui/glass-card";

export default function MeshPage() {
  const [filters, setFilters] = React.useState<MeshFilters>({ agg: "day", max_nodes: 500 });
  const [applied, setApplied] = React.useState<MeshFilters>(filters);

  const q = useQuery({
    queryKey: ["mesh", applied],
    queryFn: () => fetchMesh({
      from: applied.from,
      to: applied.to,
      keywords: applied.keywords,
      persona: applied.persona,
      emotion: applied.emotion,
      experience: applied.experience,
      agg: applied.agg,
      max_nodes: applied.max_nodes,
      scope: "global",
    }),
  });

  const onApply = () => setApplied(filters);

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20">
      <PageHeader
        title="메쉬 분석"
        description="감정-페르소나-경험-키워드 연관 메쉬"
        badge="프리뷰"
      />

      <div className="p-6 grid grid-cols-1 md:grid-cols-[18rem_1fr] gap-4">
        <FilterSidebar value={filters} onChange={setFilters} onApply={onApply} />

        <div className="space-y-4">
          <GlassCard className="p-4">
            {q.isLoading && <div className="text-sm text-muted-foreground">불러오는 중...</div>}
            {q.isError && (
              <div className="text-sm text-destructive">데이터 로드 실패: {(q.error as any)?.message || "unknown"}</div>
            )}
            {q.data && <MeshVisualization data={q.data} />}
          </GlassCard>
        </div>
      </div>
    </div>
  );
}
