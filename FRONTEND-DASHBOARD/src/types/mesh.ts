// Types mirrored from BACKEND-ANALYSIS-SERVICE/app/schemas.py
export type MeshNode = {
  id: string;
  type: string;
  label?: string;
  weight?: number;
};

export type MeshLink = {
  source: string;
  target: string;
  weight?: number;
  pmi?: number;
};

export type MeshWindow = {
  from: string; // ISO timestamp
  to: string;   // ISO timestamp
  agg: "hour" | "day" | "week";
};

export type MeshMeta = {
  window: MeshWindow;
  filters: Record<string, any>;
  computed_at: string; // ISO timestamp
};

export type MeshResponse = {
  nodes: MeshNode[];
  links: MeshLink[];
  meta: MeshMeta;
};

export type ArticlesResponse = {
  total: number;
  items: Array<{
    id: string;
    title: string;
    url: string;
    published_at: string;
    source: string;
    keywords: string[];
  }>;
  agg: {
    by_source: Array<Record<string, any>>;
    by_time: Array<Record<string, any>>;
  };
};

export type DocumentsResponse = {
  total: number;
  items: Array<{
    id: string;
    ts: string;
    source: string;
    channel: string;
    article_id?: string;
    text: string;
    meta: {
      sentiment?: string;
      persona: string[];
      experience: string[];
      keywords: string[];
      lang?: string;
    };
  }>;
};

export type GenerateReportRequest = {
  nodes: Array<{ type: string; id?: string; label?: string }>;
  template?: string;
  options?: { style?: string; length?: string; audience?: string };
};

export type GenerateReportResponse = {
  report_id: string;
  markdown: string;
  citations: Array<{ doc_id: string; span?: string }>;
  meta: Record<string, any>;
};
