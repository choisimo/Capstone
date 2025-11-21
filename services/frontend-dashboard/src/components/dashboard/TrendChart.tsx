import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useEffect, useState } from "react";
import { fetchSentimentTrend } from "@/lib/api";

type TrendRow = { date: string; score: number; volume: number };

export function TrendChart() {
  const [data, setData] = useState<TrendRow[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const to = new Date();
        const from = new Date(to.getTime() - 7 * 24 * 3600 * 1000);
        const res = await fetchSentimentTrend({ from: from.toISOString(), to: to.toISOString(), agg: 'day' });
        const rows: TrendRow[] = (res.trends || []).map((t: any) => ({
          date: new Date(t.date).toLocaleDateString('ko-KR', { month: '2-digit', day: '2-digit' }),
          score: typeof t.sentiment_score === 'number' ? t.sentiment_score : 0,
          volume: typeof t.volume === 'number' ? t.volume : 0,
        }));
        setData(rows);
      } catch (e: any) {
        setError(e?.message || '데이터 로드 실패');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-background border border-border rounded-lg p-3 shadow-lg">
          <p className="text-sm font-medium mb-2">{label}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {entry.name}: {entry.value}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <Card className="col-span-2">
      <CardHeader>
        <CardTitle className="text-lg font-semibold">감정 추이 (7일)</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-64">
          {loading && (
            <div className="h-full flex items-center justify-center text-sm text-muted-foreground">로딩 중...</div>
          )}
          {error && !loading && (
            <div className="h-full flex items-center justify-center text-sm text-destructive">{error}</div>
          )}
          {!loading && !error && (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis 
                  dataKey="date" 
                  stroke="hsl(var(--muted-foreground))"
                  fontSize={12}
                />
                <YAxis 
                  stroke="hsl(var(--muted-foreground))"
                  fontSize={12}
                />
                <Tooltip content={<CustomTooltip />} />
                <Legend />
                <Line 
                  type="monotone" 
                  dataKey="score" 
                  stroke="#3b82f6"
                  strokeWidth={2}
                  name="감성 점수"
                  dot={{ fill: "#3b82f6", strokeWidth: 2, r: 3 }}
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>
      </CardContent>
    </Card>
  );
}