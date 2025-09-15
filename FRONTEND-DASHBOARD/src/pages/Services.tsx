import { useState } from "react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Badge } from "@/components/ui/badge";
import { GlassCard } from "@/components/ui/glass-card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

type Service = {
  id: string;
  name: string;
  description: string;
  tags?: string[];
};

type Group = {
  key: string;
  label: string;
  services: Service[];
};

const serviceGroups: Group[] = [
  {
    key: "ingestion",
    label: "수집",
    services: [
      {
        id: "collector-service",
        name: "collector-service",
        description: "웹/소셜/뉴스 등 원천 데이터 수집 및 표준화",
        tags: ["HTTP", "수집기", "표준화"],
      },
      {
        id: "dedup-anonymizer",
        name: "dedup-anonymizer",
        description: "중복 제거 및 개인 정보 비식별화 처리",
        tags: ["ETL", "개인정보", "중복제거"],
      },
      {
        id: "ingest-worker",
        name: "ingest-worker",
        description: "배치/스트림 기반 수집 파이프라인 작업자",
        tags: ["Worker", "Batch", "Stream"],
      },
    ],
  },
  {
    key: "analysis",
    label: "분석",
    services: [
      {
        id: "nlp-preprocess",
        name: "nlp-preprocess",
        description: "형태소 분석, 정규화, 토큰화 등 전처리",
        tags: ["NLP", "전처리"],
      },
      {
        id: "sentiment-service",
        name: "sentiment-service",
        description: "감성 분류 및 점수 산출",
        tags: ["Sentiment", "모델"],
      },
      {
        id: "absa-service",
        name: "absa-service",
        description: "속성 기반 감성 분석(ABSA)",
        tags: ["ABSA", "Aspect"],
      },
      {
        id: "tagging-service",
        name: "tagging-service",
        description: "주제 태깅 및 키워드 추출",
        tags: ["Tagging", "Keyword"],
      },
      {
        id: "topic-modeler",
        name: "topic-modeler",
        description: "토픽 모델링 및 군집 분석",
        tags: ["Topic", "Clustering"],
      },
      {
        id: "summarizer-rag",
        name: "summarizer-rag",
        description: "RAG 기반 요약 및 인사이트 생성",
        tags: ["RAG", "요약"],
      },
      {
        id: "mesh-aggregator",
        name: "mesh-aggregator",
        description: "여러 분석 결과의 집계 및 스코어링",
        tags: ["Aggregation", "Ranking"],
      },
      {
        id: "event-analysis",
        name: "event-analysis",
        description: "이벤트 탐지 및 이상 징후 분석",
        tags: ["Anomaly", "Event"],
      },
    ],
  },
  {
    key: "platform",
    label: "플랫폼",
    services: [
      {
        id: "api-gateway",
        name: "api-gateway",
        description: "프론트엔드/외부 연계를 위한 API 게이트웨이",
        tags: ["API", "Gateway"],
      },
      {
        id: "alert-service",
        name: "alert-service",
        description: "임계치/규칙 기반 알림 발송",
        tags: ["Alert", "Webhook"],
      },
      {
        id: "dashboard-web",
        name: "dashboard-web",
        description: "대시보드 프론트엔드 애플리케이션",
        tags: ["Web", "UI"],
      },
    ],
  },
];

export default function Services() {
  const [activeTab, setActiveTab] = useState<string>(serviceGroups[0].key);

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20">
      <PageHeader
        title="서비스"
        description="마이크로서비스 카탈로그 개요 및 그룹별 구성"
        badge="베타"
      />

      <div className="p-6 space-y-6">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-3 bg-muted/50">
            {serviceGroups.map((g) => (
              <TabsTrigger
                key={g.key}
                value={g.key}
                className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground"
              >
                {g.label}
              </TabsTrigger>
            ))}
          </TabsList>

          {serviceGroups.map((g) => (
            <TabsContent key={g.key} value={g.key} className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                {g.services.map((svc) => (
                  <GlassCard key={svc.id} className="p-5">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <h3 className="text-base font-semibold">{svc.name}</h3>
                        <p className="mt-1 text-sm text-muted-foreground">{svc.description}</p>
                      </div>
                    </div>
                    {svc.tags && svc.tags.length > 0 && (
                      <div className="mt-4 flex flex-wrap gap-2">
                        {svc.tags.map((t) => (
                          <Badge key={t} variant="secondary" className="text-xs">
                            {t}
                          </Badge>
                        ))}
                      </div>
                    )}
                  </GlassCard>
                ))}
              </div>
            </TabsContent>
          ))}
        </Tabs>
      </div>
    </div>
  );
}
