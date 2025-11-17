import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useEffect, useState } from "react";
import { fetchSentimentStats } from "@/lib/api";

type PieDatum = { name: string; value: number; color: string };

export function SentimentChart() {
  const [data, setData] = useState<PieDatum[] | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const stats = await fetchSentimentStats();
        const total = Math.max(1, stats.total || (stats.positive + stats.negative + stats.neutral));
        const next: PieDatum[] = [
          { name: "긍정", value: Math.round((stats.positive / total) * 100), color: "hsl(var(--sentiment-positive))" },
          { name: "중립", value: Math.round((stats.neutral / total) * 100), color: "hsl(var(--sentiment-neutral))" },
          { name: "부정", value: Math.round((stats.negative / total) * 100), color: "hsl(var(--sentiment-negative))" },
        ];
        setData(next);
      } catch (e: any) {
        setError(e?.message || "데이터 로드 실패");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0];
      return (
        <div className="bg-background border border-border rounded-lg p-2 shadow-lg">
          <p className="text-sm font-medium">{data.name}</p>
          <p className="text-sm text-muted-foreground">{data.value}%</p>
        </div>
      );
    }
    return null;
  };

  return (
    <Card className="col-span-1">
      <CardHeader>
        <CardTitle className="text-lg font-semibold">감정 분포</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-64">
          {loading && (
            <div className="h-full flex items-center justify-center text-sm text-muted-foreground">
              로딩 중...
            </div>
          )}
          {error && !loading && (
            <div className="h-full flex items-center justify-center text-sm text-destructive">
              {error}
            </div>
          )}
          {!loading && !error && data && (
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={data}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  dataKey="value"
                  strokeWidth={2}
                  stroke="hsl(var(--background))"
                >
                  {data.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
                <Legend 
                  verticalAlign="bottom" 
                  height={36}
                  formatter={(value, entry) => (
                    <span style={{ color: entry.color }}>{value}</span>
                  )}
                />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>
      </CardContent>
    </Card>
  );
}