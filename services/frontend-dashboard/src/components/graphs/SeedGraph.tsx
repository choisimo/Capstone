import React, { useMemo } from "react";
import type { MeshLink, MeshNode } from "@/types/mesh";

export type SeedGraphProps = {
  nodes: MeshNode[];
  links: MeshLink[];
  width?: number;
  height?: number;
};

const clamp = (n: number, min: number, max: number) => Math.max(min, Math.min(max, n));

export function SeedGraph({ nodes, links, width = 800, height = 420 }: SeedGraphProps) {
  const layout = useMemo(() => {
    const seedNodes = nodes.filter((n) => n.type === "seed");
    const otherNodes = nodes.filter((n) => n.type !== "seed");

    const cx = width / 2;
    const cy = height / 2;
    const rSeed = Math.min(width, height) * 0.32;

    const pos: Record<string, { x: number; y: number }> = {};

    // Place seeds in a circle
    const seedCount = Math.max(1, seedNodes.length);
    seedNodes.forEach((s, i) => {
      const angle = (2 * Math.PI * i) / seedCount;
      pos[s.id] = {
        x: cx + rSeed * Math.cos(angle),
        y: cy + rSeed * Math.sin(angle),
      };
    });

    // Group docs by seed via links
    const groupBySeed: Record<string, MeshNode[]> = {};
    links.forEach((l) => {
      if (l.source.startsWith("seed:")) {
        const arr = groupBySeed[l.source] || (groupBySeed[l.source] = []);
        const target = otherNodes.find((n) => n.id === l.target);
        if (target && !arr.find((n) => n.id === target.id)) arr.push(target);
      }
    });

    // Place docs around their seed in small orbit
    const rDoc = Math.min(width, height) * 0.16;
    Object.entries(groupBySeed).forEach(([seedId, docs]) => {
      const center = pos[seedId];
      if (!center) return;
      const count = Math.max(1, docs.length);
      docs.forEach((d, idx) => {
        const a = (2 * Math.PI * idx) / count;
        pos[d.id] = {
          x: center.x + rDoc * Math.cos(a),
          y: center.y + rDoc * Math.sin(a),
        };
      });
    });

    // Any remaining nodes: scatter near center
    otherNodes.forEach((n, i) => {
      if (!pos[n.id]) {
        const a = (2 * Math.PI * i) / Math.max(1, otherNodes.length);
        pos[n.id] = { x: cx + rDoc * 0.6 * Math.cos(a), y: cy + rDoc * 0.6 * Math.sin(a) };
      }
    });

    return { pos };
  }, [nodes, links, width, height]);

  const get = (id: string) => layout.pos[id] || { x: width / 2, y: height / 2 };

  return (
    <svg width={width} height={height} className="w-full h-full">
      {/* Links */}
      <g stroke="#cbd5e1" strokeWidth={1.2} opacity={0.9}>
        {links.map((l, i) => {
          const s = get(l.source);
          const t = get(l.target);
          return <line key={i} x1={s.x} y1={s.y} x2={t.x} y2={t.y} />;
        })}
      </g>

      {/* Nodes */}
      <g>
        {nodes.map((n) => {
          const p = get(n.id);
          const isSeed = n.type === "seed";
          const r = isSeed ? 8 : 6;
          const fill = isSeed ? "#2563eb" : "#64748b";
          const stroke = isSeed ? "#93c5fd" : "#cbd5e1";
          return (
            <g key={n.id}>
              <circle cx={p.x} cy={p.y} r={r} fill={fill} stroke={stroke} strokeWidth={1.5} />
              {n.label && (
                <text x={p.x + 10} y={p.y + 4} fontSize={11} className="fill-muted-foreground">
                  {n.label}
                </text>
              )}
            </g>
          );
        })}
      </g>
    </svg>
  );
}

export default SeedGraph;
