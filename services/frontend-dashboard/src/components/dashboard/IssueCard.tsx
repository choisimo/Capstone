import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import { cn } from "@/lib/utils";

interface IssueCardProps {
  title: string;
  sentiment: "positive" | "negative" | "neutral";
  mentions: number;
  trend: "up" | "down" | "stable";
  category: string;
}

export function IssueCard({ title, sentiment, mentions, trend, category }: IssueCardProps) {
  const sentimentConfig = {
    positive: {
      bg: "bg-sentiment-positive-light",
      text: "text-sentiment-positive",
      label: "긍정"
    },
    negative: {
      bg: "bg-sentiment-negative-light",
      text: "text-sentiment-negative",
      label: "부정"
    },
    neutral: {
      bg: "bg-sentiment-neutral-light",
      text: "text-sentiment-neutral",
      label: "중립"
    }
  };

  const trendConfig = {
    up: { icon: TrendingUp, color: "text-sentiment-positive" },
    down: { icon: TrendingDown, color: "text-sentiment-negative" },
    stable: { icon: Minus, color: "text-sentiment-neutral" }
  };

  const sentimentStyle = sentimentConfig[sentiment];
  const trendStyle = trendConfig[trend];
  const TrendIcon = trendStyle.icon;

  return (
    <Card className="cursor-pointer transition-all hover:shadow-elevated">
      <CardContent className="p-4">
        <div className="flex items-start justify-between mb-3">
          <Badge variant="outline" className="text-xs">
            {category}
          </Badge>
          <div className="flex items-center gap-1">
            <TrendIcon className={cn("h-3 w-3", trendStyle.color)} />
            <span className="text-xs text-muted-foreground">{mentions}</span>
          </div>
        </div>
        
        <h3 className="font-medium text-sm mb-2 line-clamp-2 leading-relaxed">
          {title}
        </h3>
        
        <div className="flex items-center justify-between">
          <Badge 
            className={cn(
              "text-xs font-medium",
              sentimentStyle.bg,
              sentimentStyle.text
            )}
            variant="secondary"
          >
            {sentimentStyle.label}
          </Badge>
          <span className="text-xs text-muted-foreground">
            {mentions.toLocaleString()} 언급
          </span>
        </div>
      </CardContent>
    </Card>
  );
}