import { useState } from "react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { GlassCard } from "@/components/ui/glass-card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { searchAgent, type AgentResult } from "@/lib/agent";
import { Search, Sparkles, BookOpen, MessageSquare, ThumbsUp, ThumbsDown, Clock, ExternalLink, Save, Share2 } from "lucide-react";

const searchResults = [
  {
    id: 1,
    topic: "보험료율 인상 반대",
    relevance: 95,
    sentiment: "negative",
    mentions: 1247,
    summary: "국민연금 보험료율 13% 인상 정책에 대한 강한 반대 의견이 주를 이루고 있습니다. 특히 경제적 부담 증가를 우려하는 목소리가 많습니다.",
    keywords: ["보험료율", "13%", "반대", "부담", "경제"],
    evidence: [
      { text: "보험료율 13% 인상은 서민들에게 너무 큰 부담입니다", source: "네이버 뉴스 댓글", sentiment: "negative" },
      { text: "이미 물가상승으로 어려운데 추가 부담은 감당하기 어렵습니다", source: "커뮤니티", sentiment: "negative" },
      { text: "점진적 인상이 필요하다고 생각합니다", source: "온라인 미디어", sentiment: "neutral" }
    ]
  },
  {
    id: 2,
    topic: "청년층 가입률 개선",
    relevance: 87,
    sentiment: "positive",
    mentions: 534,
    summary: "청년층 국민연금 가입률이 지속적으로 개선되고 있어 긍정적인 반응을 보이고 있습니다. 정부의 청년 지원 정책이 효과를 보이고 있는 것으로 분석됩니다.",
    keywords: ["청년층", "가입률", "개선", "지원", "정책"],
    evidence: [
      { text: "청년들이 국민연금에 대한 인식이 개선되고 있는 것 같습니다", source: "소셜미디어", sentiment: "positive" },
      { text: "정부 지원책이 실제로 도움이 되고 있네요", source: "커뮤니티", sentiment: "positive" },
      { text: "아직 부족하지만 긍정적인 변화입니다", source: "온라인 미디어", sentiment: "neutral" }
    ]
  }
];

const savedQueries = [
  { query: "보험료율 13% 찬반 논리", date: "2024-01-07", results: 156 },
  { query: "수급연령 상향 조정 영향", date: "2024-01-06", results: 89 },
  { query: "청년층 국민연금 인식", date: "2024-01-05", results: 234 }
];

export default function Explore() {
  const [searchQuery, setSearchQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [summary, setSummary] = useState("");
  const [engine, setEngine] = useState<"pplx" | "cd">("pplx");
  const [results, setResults] = useState<AgentResult[]>([]);
  const [warning, setWarning] = useState<string | undefined>(undefined);
  const [error, setError] = useState<string | undefined>(undefined);

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    setIsSearching(true);
    setError(undefined);
    setWarning(undefined);
    try {
      const res = await searchAgent({ q: searchQuery, engine });
      setResults(res.results || []);
      if (res.warning) setWarning(res.warning);
      else setWarning(undefined);
    } catch (e: any) {
      setError(e?.message || String(e));
    } finally {
      setIsSearching(false);
    }
  };

  const generateSummary = (result: any) => {
    setSummary(`${result.topic}에 대한 종합 분석:

주요 발견사항:
- 총 ${result.mentions}건의 언급이 확인되었습니다
- 전체적으로 ${result.sentiment === 'negative' ? '부정적' : result.sentiment === 'positive' ? '긍정적' : '중립적'}인 반응을 보이고 있습니다
- 관련성 점수: ${result.relevance}%

핵심 논점:
${result.evidence.map((e: any, i: number) => `${i + 1}. ${e.text} (출처: ${e.source})`).join('\n')}

권장사항:
이 이슈에 대한 지속적인 모니터링과 함께 시민들의 우려사항을 적극적으로 수렴할 필요가 있습니다.`);
  };

  const getSentimentBadge = (sentiment: string) => {
    switch (sentiment) {
      case "positive":
        return <Badge className="bg-sentiment-positive/10 text-sentiment-positive border-sentiment-positive/20">긍정</Badge>;
      case "negative":
        return <Badge className="bg-sentiment-negative/10 text-sentiment-negative border-sentiment-negative/20">부정</Badge>;
      default:
        return <Badge variant="secondary">중립</Badge>;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20">
      <PageHeader
        title="이슈 탐색"
        description="자연어 검색을 통해 특정 이슈에 대한 깊이 있는 분석과 인사이트를 얻을 수 있습니다."
        badge="AI 기반"
      />

      <div className="p-6 space-y-6">
        {/* Search Section */}
        <GlassCard>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Search className="h-5 w-5" />
              자연어 검색
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-2">
              <Input
                placeholder="예: '보험료율 13% 반대 논거', '청년층 국민연금 인식 변화'"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                className="flex-1"
              />
              <Select value={engine} onValueChange={(v) => setEngine(v as any)}>
                <SelectTrigger className="w-[120px]">
                  <SelectValue placeholder="엔진" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="pplx">Perplexity</SelectItem>
                  <SelectItem value="cd">ChangeDet</SelectItem>
                </SelectContent>
              </Select>
              <Button onClick={handleSearch} disabled={isSearching}>
                {isSearching ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current mr-2"></div>
                    검색 중...
                  </>
                ) : (
                  <>
                    <Search className="h-4 w-4 mr-2" />
                    검색
                  </>
                )}
              </Button>
            </div>
            
            <div className="flex flex-wrap gap-2">
              <span className="text-sm text-muted-foreground">추천 검색어:</span>
              {["보험료율 인상", "수급연령 상향", "청년층 가입률", "기금운용 성과"].map((keyword) => (
                <Button
                  key={keyword}
                  variant="outline"
                  size="sm"
                  onClick={() => setSearchQuery(keyword)}
                  className="h-7 text-xs"
                >
                  {keyword}
                </Button>
              ))}
            </div>
          </CardContent>
        </GlassCard>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Search Results */}
          <div className="lg:col-span-2 space-y-6">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold">검색 결과</h3>
              <span className="text-sm text-muted-foreground">{results.length}개 결과 • 엔진: {engine.toUpperCase()}</span>
            </div>

            {error && (
              <div className="text-sm text-destructive">검색 실패: {error}</div>
            )}
            {warning && (
              <div className="text-xs text-amber-600 border border-amber-200 bg-amber-50 rounded p-2">{warning}</div>
            )}
            {isSearching && (
              <div className="text-sm text-muted-foreground">검색 중...</div>
            )}

            {!isSearching && results.map((r, idx) => (
              <GlassCard key={idx} className="hover:shadow-elevated transition-all duration-300">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="space-y-2">
                      <CardTitle className="text-lg">
                        <a href={r.url} target="_blank" rel="noreferrer" className="hover:underline">
                          {r.title || r.url}
                        </a>
                      </CardTitle>
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className="text-xs">{r.source}</Badge>
                        {typeof r.score === "number" && (
                          <Badge variant="secondary" className="text-xs">유사도 {Math.round(r.score * 100)}%</Badge>
                        )}
                        {r.uuid && (
                          <Badge variant="outline" className="text-xs">UUID {r.uuid.slice(0, 8)}</Badge>
                        )}
                      </div>
                    </div>
                    <div className="flex gap-1">
                      <Button asChild variant="ghost" size="sm">
                        <a href={r.url} target="_blank" rel="noreferrer">
                          <ExternalLink className="h-4 w-4" />
                        </a>
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-2">
                  {r.snippet && <p className="text-sm leading-relaxed">{r.snippet}</p>}
                </CardContent>
              </GlassCard>
            ))}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* AI Summary */}
            {summary && (
              <GlassCard>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-base">
                    <Sparkles className="h-4 w-4" />
                    AI 요약
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ScrollArea className="h-64">
                    <Textarea
                      value={summary}
                      onChange={(e) => setSummary(e.target.value)}
                      className="min-h-[200px] text-sm resize-none border-none bg-transparent p-0"
                      placeholder="AI가 생성한 요약이 여기에 표시됩니다..."
                    />
                  </ScrollArea>
                  <div className="flex justify-end gap-2 mt-4">
                    <Button variant="outline" size="sm">
                      <Save className="h-4 w-4 mr-2" />
                      저장
                    </Button>
                    <Button size="sm">
                      <Share2 className="h-4 w-4 mr-2" />
                      공유
                    </Button>
                  </div>
                </CardContent>
              </GlassCard>
            )}

            {/* Saved Queries */}
            <GlassCard>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <BookOpen className="h-4 w-4" />
                  저장된 검색
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {savedQueries.map((query, index) => (
                    <div key={index} className="p-3 rounded-lg bg-muted/10 hover:bg-muted/20 transition-colors cursor-pointer">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm font-medium">{query.query}</span>
                        <ExternalLink className="h-3 w-3 text-muted-foreground" />
                      </div>
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <Clock className="h-3 w-3" />
                        {query.date}
                        <span>•</span>
                        <span>{query.results} 결과</span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </GlassCard>
          </div>
        </div>
      </div>
    </div>
  );
}