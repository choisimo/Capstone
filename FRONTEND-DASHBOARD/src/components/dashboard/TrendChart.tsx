import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const trendData = [
  { date: "01-01", positive: 45, neutral: 35, negative: 20 },
  { date: "01-02", positive: 42, neutral: 38, negative: 20 },
  { date: "01-03", positive: 40, neutral: 35, negative: 25 },
  { date: "01-04", positive: 38, neutral: 37, negative: 25 },
  { date: "01-05", positive: 42, neutral: 35, negative: 23 },
  { date: "01-06", positive: 44, neutral: 34, negative: 22 },
  { date: "01-07", positive: 42, neutral: 35, negative: 23 },
];

export function TrendChart() {
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-background border border-border rounded-lg p-3 shadow-lg">
          <p className="text-sm font-medium mb-2">{label}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {entry.name}: {entry.value}%
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
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={trendData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
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
                dataKey="positive" 
                stroke="hsl(var(--sentiment-positive))" 
                strokeWidth={2}
                name="긍정"
                dot={{ fill: "hsl(var(--sentiment-positive))", strokeWidth: 2, r: 4 }}
              />
              <Line 
                type="monotone" 
                dataKey="neutral" 
                stroke="hsl(var(--sentiment-neutral))" 
                strokeWidth={2}
                name="중립"
                dot={{ fill: "hsl(var(--sentiment-neutral))", strokeWidth: 2, r: 4 }}
              />
              <Line 
                type="monotone" 
                dataKey="negative" 
                stroke="hsl(var(--sentiment-negative))" 
                strokeWidth={2}
                name="부정"
                dot={{ fill: "hsl(var(--sentiment-negative))", strokeWidth: 2, r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}