/**
 * Real-Time Dashboard Component
 * 
 * 실시간 감성 분석 대시보드:
 * - 감성 분포 파이 차트
 * - 트렌드 라인 차트
 * - 키워드 클라우드
 * - 자동 리프레시
 */

import React, { useState, useEffect, useCallback } from 'react';
import { 
  fetchSentimentStats, 
  fetchSentimentTrend, 
  fetchTopKeywords,
  cachedRequest,
  clearCache 
} from '@/lib/api';

// Chart libraries (using recharts for React)
import { 
  PieChart, 
  Pie, 
  Cell, 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend,
  ResponsiveContainer 
} from 'recharts';

// Types
interface SentimentData {
  positive: number;
  negative: number;
  neutral: number;
  total: number;
}

interface TrendPoint {
  date: string;
  score: number;
  volume: number;
}

interface Keyword {
  keyword: string;
  score: number;
  count?: number;
}

interface DashboardState {
  sentiment: SentimentData | null;
  trends: TrendPoint[];
  keywords: Keyword[];
  loading: boolean;
  error: string | null;
  lastUpdate: Date | null;
}

// Constants
const COLORS = {
  positive: '#10b981', // green
  negative: '#ef4444', // red
  neutral: '#6b7280'   // gray
};

const REFRESH_INTERVAL = 30000; // 30 seconds
const DATE_RANGE_DAYS = 7;

export function RealTimeDashboard() {
  const [state, setState] = useState<DashboardState>({
    sentiment: null,
    trends: [],
    keywords: [],
    loading: true,
    error: null,
    lastUpdate: null
  });

  const [autoRefresh, setAutoRefresh] = useState(true);
  const [dateRange, setDateRange] = useState<'1d' | '7d' | '30d'>('7d');

  // Calculate date range
  const getDateRange = useCallback(() => {
    const end = new Date();
    const start = new Date();
    
    switch (dateRange) {
      case '1d':
        start.setDate(start.getDate() - 1);
        break;
      case '7d':
        start.setDate(start.getDate() - 7);
        break;
      case '30d':
        start.setDate(start.getDate() - 30);
        break;
    }
    
    return {
      from: start.toISOString().split('T')[0],
      to: end.toISOString().split('T')[0]
    };
  }, [dateRange]);

  // Fetch all dashboard data
  const fetchDashboardData = useCallback(async (useCache: boolean = true) => {
    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      const { from, to } = getDateRange();
      
      // Clear cache if manual refresh
      if (!useCache) {
        clearCache();
      }

      const fetchFn = useCache ? cachedRequest : (key: string, fn: () => Promise<any>) => fn();

      // Fetch sentiment stats
      const sentimentPromise = fetchFn(
        `sentiment-${from}-${to}`,
        () => fetchSentimentStats({ from, to })
      );

      // Fetch trend data
      const trendPromise = fetchFn(
        `trend-${from}-${to}`,
        () => fetchSentimentTrend({ from, to, agg: dateRange === '1d' ? 'day' : 'day' })
      );

      // Fetch keywords
      const keywordPromise = fetchFn(
        `keywords-${from}-${to}`,
        () => fetchTopKeywords({ from, to, size: 20 })
      );

      const [sentimentData, trendData, keywordData] = await Promise.all([
        sentimentPromise,
        trendPromise,
        keywordPromise
      ]);

      // Transform sentiment data
      const sentiment: SentimentData = {
        positive: sentimentData.positive || 0,
        negative: sentimentData.negative || 0,
        neutral: sentimentData.neutral || 0,
        total: sentimentData.total || 0
      };

      // Transform trend data
      const trends: TrendPoint[] = (trendData.trends || []).map((t: any) => ({
        date: new Date(t.date).toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' }),
        score: t.sentiment_score || 0,
        volume: t.volume || 0
      }));

      // Transform keyword data
      const keywords: Keyword[] = (keywordData.keywords || []).map((k: any) => ({
        keyword: k.keyword || k.word,
        score: k.score || k.count,
        count: k.count
      }));

      setState({
        sentiment,
        trends,
        keywords,
        loading: false,
        error: null,
        lastUpdate: new Date()
      });

    } catch (error: any) {
      console.error('Dashboard fetch error:', error);
      setState(prev => ({
        ...prev,
        loading: false,
        error: error.message || 'Failed to fetch dashboard data'
      }));
    }
  }, [getDateRange, dateRange]);

  // Initial load and auto-refresh
  useEffect(() => {
    fetchDashboardData(true);

    if (autoRefresh) {
      const interval = setInterval(() => {
        fetchDashboardData(true);
      }, REFRESH_INTERVAL);

      return () => clearInterval(interval);
    }
  }, [fetchDashboardData, autoRefresh]);

  // Prepare pie chart data
  const pieData = state.sentiment ? [
    { name: '긍정', value: state.sentiment.positive, color: COLORS.positive },
    { name: '부정', value: state.sentiment.negative, color: COLORS.negative },
    { name: '중립', value: state.sentiment.neutral, color: COLORS.neutral }
  ] : [];

  // Manual refresh handler
  const handleRefresh = () => {
    fetchDashboardData(false);
  };

  // Render loading state
  if (state.loading && !state.sentiment) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-gray-600">데이터 로딩 중...</p>
        </div>
      </div>
    );
  }

  // Render error state
  if (state.error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <h3 className="text-red-800 font-semibold mb-2">오류 발생</h3>
        <p className="text-red-600">{state.error}</p>
        <button
          onClick={handleRefresh}
          className="mt-4 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
        >
          다시 시도
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with controls */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">실시간 감성 분석 대시보드</h2>
          {state.lastUpdate && (
            <p className="text-sm text-gray-500 mt-1">
              마지막 업데이트: {state.lastUpdate.toLocaleTimeString('ko-KR')}
            </p>
          )}
        </div>

        <div className="flex items-center gap-4">
          {/* Date range selector */}
          <select
            value={dateRange}
            onChange={(e) => setDateRange(e.target.value as '1d' | '7d' | '30d')}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            <option value="1d">1일</option>
            <option value="7d">7일</option>
            <option value="30d">30일</option>
          </select>

          {/* Auto-refresh toggle */}
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
            />
            <span className="text-sm text-gray-700">자동 새로고침</span>
          </label>

          {/* Manual refresh button */}
          <button
            onClick={handleRefresh}
            disabled={state.loading}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <svg className={`w-4 h-4 ${state.loading ? 'animate-spin' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            새로고침
          </button>
        </div>
      </div>

      {/* Stats cards */}
      {state.sentiment && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <StatsCard
            title="전체 분석"
            value={state.sentiment.total.toLocaleString()}
            subtitle="건"
            color="blue"
          />
          <StatsCard
            title="긍정"
            value={state.sentiment.positive.toLocaleString()}
            subtitle={`${((state.sentiment.positive / state.sentiment.total) * 100).toFixed(1)}%`}
            color="green"
          />
          <StatsCard
            title="부정"
            value={state.sentiment.negative.toLocaleString()}
            subtitle={`${((state.sentiment.negative / state.sentiment.total) * 100).toFixed(1)}%`}
            color="red"
          />
          <StatsCard
            title="중립"
            value={state.sentiment.neutral.toLocaleString()}
            subtitle={`${((state.sentiment.neutral / state.sentiment.total) * 100).toFixed(1)}%`}
            color="gray"
          />
        </div>
      )}

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Sentiment distribution pie chart */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">감성 분포</h3>
          {pieData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-gray-500 text-center py-12">데이터가 없습니다</p>
          )}
        </div>

        {/* Trend line chart */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">감성 트렌드</h3>
          {state.trends.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={state.trends}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="score" stroke="#3b82f6" name="감성 점수" />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-gray-500 text-center py-12">데이터가 없습니다</p>
          )}
        </div>
      </div>

      {/* Keywords word cloud */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">주요 키워드</h3>
        {state.keywords.length > 0 ? (
          <div className="flex flex-wrap gap-3">
            {state.keywords.slice(0, 20).map((keyword, index) => {
              const size = Math.max(12, Math.min(32, 12 + (keyword.score / state.keywords[0].score) * 20));
              return (
                <span
                  key={index}
                  className="inline-block px-3 py-1 bg-blue-100 text-blue-800 rounded-full hover:bg-blue-200 transition-colors cursor-pointer"
                  style={{ fontSize: `${size}px` }}
                  title={`점수: ${keyword.score}`}
                >
                  {keyword.keyword}
                </span>
              );
            })}
          </div>
        ) : (
          <p className="text-gray-500 text-center py-12">데이터가 없습니다</p>
        )}
      </div>
    </div>
  );
}

// Stats card component
interface StatsCardProps {
  title: string;
  value: string;
  subtitle: string;
  color: 'blue' | 'green' | 'red' | 'gray';
}

function StatsCard({ title, value, subtitle, color }: StatsCardProps) {
  const colorClasses = {
    blue: 'bg-blue-50 text-blue-700',
    green: 'bg-green-50 text-green-700',
    red: 'bg-red-50 text-red-700',
    gray: 'bg-gray-50 text-gray-700'
  };

  return (
    <div className={`${colorClasses[color]} rounded-lg p-6`}>
      <p className="text-sm font-medium opacity-80">{title}</p>
      <p className="text-3xl font-bold mt-2">{value}</p>
      <p className="text-sm mt-1 opacity-80">{subtitle}</p>
    </div>
  );
}

export default RealTimeDashboard;
