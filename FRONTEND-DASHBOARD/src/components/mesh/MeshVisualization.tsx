import React from "react";
import type { MeshResponse } from "@/types/mesh";

// Minimal placeholder visualization that lists node/link counts
// Can be swapped to force-graph later.
export default function MeshVisualization({ data }: { data: MeshResponse }) {
  return (
    <div className="w-full h-80 rounded-lg border bg-background/50 p-4 flex flex-col gap-2">
      <div className="text-sm text-muted-foreground">Mesh Preview</div>
      <div className="text-lg font-medium">{data.nodes.length} nodes • {data.links.length} links</div>
      <div className="grid grid-cols-2 gap-2 overflow-auto">
        <div>
          <div className="text-xs mb-1">Sample Nodes</div>
          <ul className="text-xs space-y-1">
            {data.nodes.slice(0, 8).map((n) => (
              <li key={n.id} className="truncate">
                {n.type}:{" "}
                <span className="font-mono">{n.label || n.id}</span>
                {n.weight !== undefined ? ` (w=${n.weight})` : ""}
              </li>
            ))}
          </ul>
        </div>
        <div>
          <div className="text-xs mb-1">Sample Links</div>
          <ul className="text-xs space-y-1">
            {data.links.slice(0, 8).map((l, i) => (
              <li key={i} className="truncate">
                <span className="font-mono">{l.source}</span> → <span className="font-mono">{l.target}</span>
                {l.weight !== undefined ? ` (w=${l.weight})` : ""}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
