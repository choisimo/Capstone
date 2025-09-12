import { useState } from "react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { GlassCard } from "@/components/ui/glass-card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { ScrollArea } from "@/components/ui/scroll-area";
import { HelpCircle, Search, BookOpen, AlertCircle, Shield, FileText, ExternalLink, Phone, Mail } from "lucide-react";

const faqs = [
  {
    category: "기본 사용법",
    items: [
      {
        question: "대시보드는 어떻게 사용하나요?",
        answer: "홈 대시보드에서는 국민연금 관련 여론의 전체적인 현황을 한눈에 확인할 수 있습니다. 감정 분포, 주요 이슈, 채널별 활동 등의 핵심 지표를 제공합니다."
      },
      {
        question: "필터 기능은 어떻게 사용하나요?",
        answer: "각 페이지 상단의 필터를 통해 기간, 채널, 키워드 등으로 데이터를 세분화해서 볼 수 있습니다. 복합 필터 적용도 가능합니다."
      },
      {
        question: "데이터는 얼마나 자주 업데이트되나요?",
        answer: "대부분의 데이터는 5분마다 업데이트됩니다. 실시간 모니터링 페이지에서는 거의 실시간으로 데이터가 갱신됩니다."
      }
    ]
  },
  {
    category: "분석 기능",
    items: [
      {
        question: "감정 분석은 어떻게 작동하나요?",
        answer: "AI 기반의 자연어 처리 기술을 사용하여 텍스트의 감정을 긍정, 중립, 부정으로 분류합니다. 한국어에 특화된 모델을 사용합니다."
      },
      {
        question: "토픽 분석이란 무엇인가요?",
        answer: "BERTopic 알고리즘을 사용하여 유사한 내용의 글들을 자동으로 그룹화하고 주제를 추출합니다. 새로운 이슈나 트렌드를 발견하는 데 유용합니다."
      },
      {
        question: "이벤트 분석(ITS)은 무엇인가요?",
        answer: "Interrupted Time Series 분석으로, 특정 정책 발표나 이벤트가 여론에 미친 통계적 영향을 측정합니다."
      }
    ]
  },
  {
    category: "알림 시스템",
    items: [
      {
        question: "알림은 어떻게 설정하나요?",
        answer: "설정 페이지에서 이메일, Slack 등의 알림 채널을 설정할 수 있습니다. 알림 규칙도 임계값에 따라 커스터마이징 가능합니다."
      },
      {
        question: "어떤 상황에서 알림이 발송되나요?",
        answer: "언급량 급증, 감정 점수 급락, 새로운 이슈 키워드 감지, 플랫폼별 활동 급증 등의 상황에서 자동으로 알림이 발송됩니다."
      }
    ]
  }
];

const modelCards = [
  {
    name: "감정 분석 모델",
    version: "v2.1",
    description: "한국어 텍스트의 감정을 분류하는 BERT 기반 모델",
    accuracy: "92.3%",
    limitations: ["구어체 표현 인식 제한", "맥락 의존적 감정 해석의 어려움"],
    bias: ["특정 연령층 언어 패턴에 편향 가능성", "정치적 성향 편향 최소화 노력"]
  },
  {
    name: "토픽 모델링",
    version: "v1.8",
    description: "BERTopic 기반의 토픽 추출 및 클러스터링 모델",
    accuracy: "89.7%",
    limitations: ["짧은 텍스트에서의 토픽 추출 한계", "신조어나 은어 처리 제약"],
    bias: ["주류 매체 콘텐츠에 편향 가능성", "특정 플랫폼 언어 특성 반영"]
  }
];

const dataQuality = {
  totalSources: 12,
  activeSources: 10,
  dailyVolume: "15,234건",
  duplicateRate: "2.1%",
  missingRate: "0.8%",
  lastUpdate: "2024-01-07 14:35"
};

export default function Help() {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("all");

  const filteredFaqs = faqs.filter(category => {
    if (selectedCategory !== "all" && category.category !== selectedCategory) return false;
    if (searchQuery) {
      return category.items.some(item => 
        item.question.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.answer.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }
    return true;
  });

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20">
      <PageHeader
        title="도움말"
        description="시스템 사용법, 모델 정보, 데이터 품질 등에 대한 상세한 정보를 제공합니다."
        badge="가이드"
        actions={
          <div className="flex gap-2">
            <Button variant="outline" size="sm">
              <Phone className="h-4 w-4 mr-2" />
              전화 지원
            </Button>
            <Button variant="outline" size="sm">
              <Mail className="h-4 w-4 mr-2" />
              이메일 지원
            </Button>
          </div>
        }
      />

      <div className="p-6">
        <Tabs defaultValue="faq" className="space-y-6">
          <TabsList className="grid w-full grid-cols-4 bg-muted/50">
            <TabsTrigger value="faq" className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
              자주 묻는 질문
            </TabsTrigger>
            <TabsTrigger value="models" className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
              모델 정보
            </TabsTrigger>
            <TabsTrigger value="data" className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
              데이터 품질
            </TabsTrigger>
            <TabsTrigger value="contact" className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
              연락처
            </TabsTrigger>
          </TabsList>

          <TabsContent value="faq" className="space-y-6">
            {/* Search */}
            <GlassCard>
              <CardContent className="p-4">
                <div className="flex items-center gap-4">
                  <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      placeholder="질문을 검색하세요..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="pl-10"
                    />
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant={selectedCategory === "all" ? "default" : "outline"}
                      size="sm"
                      onClick={() => setSelectedCategory("all")}
                    >
                      전체
                    </Button>
                    {faqs.map((category) => (
                      <Button
                        key={category.category}
                        variant={selectedCategory === category.category ? "default" : "outline"}
                        size="sm"
                        onClick={() => setSelectedCategory(category.category)}
                      >
                        {category.category}
                      </Button>
                    ))}
                  </div>
                </div>
              </CardContent>
            </GlassCard>

            {/* FAQ List */}
            <div className="space-y-6">
              {filteredFaqs.map((category, categoryIndex) => (
                <GlassCard key={categoryIndex}>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <BookOpen className="h-5 w-5" />
                      {category.category}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <Accordion type="single" collapsible className="space-y-2">
                      {category.items.map((item, itemIndex) => (
                        <AccordionItem key={itemIndex} value={`${categoryIndex}-${itemIndex}`} className="border border-border/50 rounded-lg px-4">
                          <AccordionTrigger className="text-left">
                            {item.question}
                          </AccordionTrigger>
                          <AccordionContent className="text-sm text-muted-foreground leading-relaxed">
                            {item.answer}
                          </AccordionContent>
                        </AccordionItem>
                      ))}
                    </Accordion>
                  </CardContent>
                </GlassCard>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="models" className="space-y-6">
            <div className="space-y-6">
              {modelCards.map((model, index) => (
                <GlassCard key={index}>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle className="flex items-center gap-2">
                        <Shield className="h-5 w-5" />
                        {model.name}
                      </CardTitle>
                      <Badge variant="outline">{model.version}</Badge>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <p className="text-sm text-muted-foreground">{model.description}</p>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="p-4 rounded-lg bg-muted/20">
                        <h4 className="font-medium mb-2 flex items-center gap-2">
                          <AlertCircle className="h-4 w-4" />
                          모델 성능
                        </h4>
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-muted-foreground">정확도</span>
                          <span className="font-semibold">{model.accuracy}</span>
                        </div>
                      </div>

                      <div className="p-4 rounded-lg bg-muted/20">
                        <h4 className="font-medium mb-2">한계점</h4>
                        <ul className="text-sm text-muted-foreground space-y-1">
                          {model.limitations.map((limitation, idx) => (
                            <li key={idx} className="flex items-start gap-2">
                              <span className="text-sentiment-negative">•</span>
                              {limitation}
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>

                    <div className="p-4 rounded-lg bg-warning/5 border border-warning/20">
                      <h4 className="font-medium mb-2 text-warning">편향 고지</h4>
                      <ul className="text-sm space-y-1">
                        {model.bias.map((biasItem, idx) => (
                          <li key={idx} className="flex items-start gap-2">
                            <span className="text-warning">•</span>
                            {biasItem}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </CardContent>
                </GlassCard>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="data" className="space-y-6">
            <GlassCard>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="h-5 w-5" />
                  데이터 품질 현황
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="p-4 rounded-lg bg-muted/20 text-center">
                    <div className="text-2xl font-bold text-primary">{dataQuality.activeSources}/{dataQuality.totalSources}</div>
                    <div className="text-sm text-muted-foreground">활성 데이터 소스</div>
                  </div>
                  <div className="p-4 rounded-lg bg-muted/20 text-center">
                    <div className="text-2xl font-bold text-sentiment-positive">{dataQuality.dailyVolume}</div>
                    <div className="text-sm text-muted-foreground">일일 수집량</div>
                  </div>
                  <div className="p-4 rounded-lg bg-muted/20 text-center">
                    <div className="text-2xl font-bold text-sentiment-positive">{dataQuality.duplicateRate}</div>
                    <div className="text-sm text-muted-foreground">중복률</div>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <h4 className="font-medium">데이터 수집 현황</h4>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">마지막 업데이트:</span>
                        <span className="font-mono">{dataQuality.lastUpdate}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">결측률:</span>
                        <span className="font-mono text-sentiment-positive">{dataQuality.missingRate}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">데이터 신선도:</span>
                        <Badge className="bg-sentiment-positive/10 text-sentiment-positive text-xs">우수</Badge>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <h4 className="font-medium">품질 지표</h4>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-sm">완전성</span>
                        <div className="flex items-center gap-2">
                          <div className="w-20 h-2 bg-muted rounded-full">
                            <div className="w-[95%] h-2 bg-sentiment-positive rounded-full"></div>
                          </div>
                          <span className="text-xs font-mono">95%</span>
                        </div>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm">정확성</span>
                        <div className="flex items-center gap-2">
                          <div className="w-20 h-2 bg-muted rounded-full">
                            <div className="w-[92%] h-2 bg-sentiment-positive rounded-full"></div>
                          </div>
                          <span className="text-xs font-mono">92%</span>
                        </div>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm">일관성</span>
                        <div className="flex items-center gap-2">
                          <div className="w-20 h-2 bg-muted rounded-full">
                            <div className="w-[88%] h-2 bg-sentiment-positive rounded-full"></div>
                          </div>
                          <span className="text-xs font-mono">88%</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </GlassCard>
          </TabsContent>

          <TabsContent value="contact" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <GlassCard>
                <CardHeader>
                  <CardTitle>기술 지원</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center gap-3">
                    <Phone className="h-5 w-5 text-primary" />
                    <div>
                      <div className="font-medium">전화 지원</div>
                      <div className="text-sm text-muted-foreground">1588-4321 (평일 9:00-18:00)</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <Mail className="h-5 w-5 text-primary" />
                    <div>
                      <div className="font-medium">이메일 지원</div>
                      <div className="text-sm text-muted-foreground">support@nps-analytics.gov.kr</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <ExternalLink className="h-5 w-5 text-primary" />
                    <div>
                      <div className="font-medium">온라인 문서</div>
                      <div className="text-sm text-muted-foreground">docs.nps-analytics.gov.kr</div>
                    </div>
                  </div>
                </CardContent>
              </GlassCard>

              <GlassCard>
                <CardHeader>
                  <CardTitle>빠른 문의</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">문의 유형</label>
                    <select className="w-full p-2 border border-border rounded-md bg-background">
                      <option>기술적 문제</option>
                      <option>사용법 문의</option>
                      <option>기능 요청</option>
                      <option>기타</option>
                    </select>
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">제목</label>
                    <Input placeholder="문의 제목을 입력하세요" />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">내용</label>
                    <textarea 
                      className="w-full p-2 border border-border rounded-md bg-background min-h-[100px] text-sm"
                      placeholder="상세한 문의 내용을 입력하세요"
                    />
                  </div>
                  <Button className="w-full">
                    문의 전송
                  </Button>
                </CardContent>
              </GlassCard>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}