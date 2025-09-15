import React from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { Label } from "@/components/ui/label";

export type MeshFilters = {
  from?: string;
  to?: string;
  keywords?: string[];
  persona?: string[];
  emotion?: string[];
  experience?: string[];
  agg?: "hour" | "day" | "week";
  max_nodes?: number;
};

export default function FilterSidebar({ value, onChange, onApply }: {
  value: MeshFilters;
  onChange: (next: MeshFilters) => void;
  onApply: () => void;
}) {
  const [kw, setKw] = React.useState("");

  const update = (patch: Partial<MeshFilters>) => onChange({ ...value, ...patch });

  return (
    <div className="w-full md:w-72 shrink-0 p-4 border rounded-lg bg-background/50 space-y-4">
      <div className="space-y-1">
        <div className="font-medium">필터</div>
        <div className="text-xs text-muted-foreground">기간/태그/제한 설정</div>
      </div>

      <div className="space-y-2">
        <Label className="text-xs">키워드</Label>
        <div className="flex gap-2">
          <Input placeholder="comma,separated" value={kw} onChange={(e) => setKw(e.target.value)} />
          <Button type="button" variant="secondary" onClick={() => update({ keywords: kw.split(",").map(s => s.trim()).filter(Boolean) })}>
            적용
          </Button>
        </div>
        {value.keywords && value.keywords.length > 0 && (
          <div className="text-xs text-muted-foreground">{value.keywords.join(", ")}</div>
        )}
      </div>

      <div className="grid grid-cols-2 gap-2">
        <div>
          <Label className="text-xs">집계</Label>
          <select
            className="w-full h-9 rounded-md border bg-background px-2 text-sm"
            value={value.agg || "day"}
            onChange={(e) => update({ agg: e.target.value as any })}
          >
            <option value="hour">시간</option>
            <option value="day">일</option>
            <option value="week">주</option>
          </select>
        </div>
        <div>
          <Label className="text-xs">최대 노드</Label>
          <Input
            type="number"
            placeholder="e.g., 500"
            value={value.max_nodes ?? ""}
            onChange={(e) => update({ max_nodes: e.target.value ? Number(e.target.value) : undefined })}
          />
        </div>
      </div>

      <Separator />
      <Button onClick={onApply} className="w-full">메쉬 불러오기</Button>
    </div>
  );
}
