import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { 
  User, 
  MessageCircle, 
  TrendingUp, 
  TrendingDown, 
  Hash,
  Link,
  Calendar,
  BarChart
} from 'lucide-react';

const PersonaNetwork = ({ userId, onNodeClick }) => {
  const svgRef = useRef(null);
  const [networkData, setNetworkData] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [personaDetails, setPersonaDetails] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchNetworkData();
  }, [userId]);

  const fetchNetworkData = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/v1/personas/network/${userId}`);
      const data = await response.json();
      setNetworkData(data);
      renderNetwork(data);
    } catch (error) {
      console.error('Failed to fetch network data:', error);
    } finally {
      setLoading(false);
    }
  };

  const renderNetwork = (data) => {
    if (!data || !svgRef.current) return;

    const width = 1200;
    const height = 800;

    // Clear previous visualization
    d3.select(svgRef.current).selectAll("*").remove();

    const svg = d3.select(svgRef.current)
      .attr("width", width)
      .attr("height", height);

    // Create container for zoom
    const container = svg.append("g");

    // Add zoom behavior
    const zoom = d3.zoom()
      .scaleExtent([0.5, 3])
      .on("zoom", (event) => {
        container.attr("transform", event.transform);
      });

    svg.call(zoom);

    // Create force simulation
    const simulation = d3.forceSimulation(data.nodes)
      .force("link", d3.forceLink(data.links)
        .id(d => d.id)
        .distance(d => 100 / (d.strength || 1)))
      .force("charge", d3.forceManyBody().strength(-300))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide().radius(30));

    // Define arrow markers for directed edges
    svg.append("defs").selectAll("marker")
      .data(["positive", "negative", "neutral"])
      .enter().append("marker")
      .attr("id", d => `arrow-${d}`)
      .attr("viewBox", "0 -5 10 10")
      .attr("refX", 25)
      .attr("refY", 0)
      .attr("markerWidth", 6)
      .attr("markerHeight", 6)
      .attr("orient", "auto")
      .append("path")
      .attr("d", "M0,-5L10,0L0,5")
      .attr("fill", d => {
        if (d === "positive") return "#10b981";
        if (d === "negative") return "#ef4444";
        return "#6b7280";
      });

    // Create links
    const link = container.append("g")
      .selectAll("line")
      .data(data.links)
      .enter().append("line")
      .attr("stroke", d => {
        if (d.sentiment > 0.3) return "#10b981";
        if (d.sentiment < -0.3) return "#ef4444";
        return "#6b7280";
      })
      .attr("stroke-opacity", d => 0.3 + d.strength * 0.7)
      .attr("stroke-width", d => Math.sqrt(d.strength * 10))
      .attr("marker-end", d => {
        if (d.sentiment > 0.3) return "url(#arrow-positive)";
        if (d.sentiment < -0.3) return "url(#arrow-negative)";
        return "url(#arrow-neutral)";
      });

    // Create node groups
    const node = container.append("g")
      .selectAll("g")
      .data(data.nodes)
      .enter().append("g")
      .call(drag(simulation));

    // Add circles for nodes
    node.append("circle")
      .attr("r", d => 10 + Math.sqrt(d.influence * 100))
      .attr("fill", d => {
        if (d.type === "primary") return "#3b82f6";
        if (d.dominant_sentiment === "positive") return "#10b981";
        if (d.dominant_sentiment === "negative") return "#ef4444";
        return "#6b7280";
      })
      .attr("stroke", "#fff")
      .attr("stroke-width", 2);

    // Add labels
    node.append("text")
      .text(d => d.username || d.id)
      .attr("x", 0)
      .attr("y", d => -(15 + Math.sqrt(d.influence * 100)))
      .attr("text-anchor", "middle")
      .attr("font-size", "12px")
      .attr("font-weight", "bold");

    // Add post count indicator
    node.append("text")
      .text(d => `${d.post_count || 0} posts`)
      .attr("x", 0)
      .attr("y", d => 20 + Math.sqrt(d.influence * 100))
      .attr("text-anchor", "middle")
      .attr("font-size", "10px")
      .attr("fill", "#6b7280");

    // Click handler
    node.on("click", (event, d) => {
      setSelectedNode(d);
      fetchPersonaDetails(d.id);
      if (onNodeClick) onNodeClick(d);
    });

    // Tooltip
    node.append("title")
      .text(d => `${d.username}\n` +
        `Influence: ${(d.influence * 100).toFixed(1)}%\n` +
        `Posts: ${d.post_count}\n` +
        `Sentiment: ${d.dominant_sentiment}`);

    // Update positions on tick
    simulation.on("tick", () => {
      link
        .attr("x1", d => d.source.x)
        .attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x)
        .attr("y2", d => d.target.y);

      node.attr("transform", d => `translate(${d.x},${d.y})`);
    });

    // Drag functions
    function drag(simulation) {
      function dragstarted(event, d) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
      }

      function dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
      }

      function dragended(event, d) {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
      }

      return d3.drag()
        .on("start", dragstarted)
        .on("drag", dragged)
        .on("end", dragended);
    }
  };

  const fetchPersonaDetails = async (personaId) => {
    try {
      const response = await fetch(`/api/v1/personas/${personaId}/details`);
      const data = await response.json();
      setPersonaDetails(data);
    } catch (error) {
      console.error('Failed to fetch persona details:', error);
    }
  };

  const SentimentIndicator = ({ sentiment, score }) => {
    const color = sentiment === 'positive' ? 'text-green-600' : 
                  sentiment === 'negative' ? 'text-red-600' : 'text-gray-600';
    const Icon = sentiment === 'positive' ? TrendingUp : 
                 sentiment === 'negative' ? TrendingDown : BarChart;
    
    return (
      <div className={`flex items-center gap-2 ${color}`}>
        <Icon className="w-4 h-4" />
        <span className="text-sm font-medium">{(score * 100).toFixed(1)}%</span>
      </div>
    );
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
      {/* Network Visualization */}
      <div className="lg:col-span-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <User className="w-5 h-5" />
              페르소나 네트워크
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex items-center justify-center h-96">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
              </div>
            ) : (
              <svg ref={svgRef}></svg>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Persona Details Panel */}
      <div className="lg:col-span-1">
        {selectedNode && personaDetails && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <User className="w-5 h-5" />
                {personaDetails.username}
              </CardTitle>
              <div className="flex gap-2 mt-2">
                <Badge variant={personaDetails.dominant_sentiment === 'positive' ? 'success' : 
                              personaDetails.dominant_sentiment === 'negative' ? 'destructive' : 
                              'secondary'}>
                  {personaDetails.dominant_sentiment}
                </Badge>
                <Badge variant="outline">
                  영향력: {(personaDetails.influence * 100).toFixed(1)}%
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <Tabs defaultValue="overview">
                <TabsList className="grid w-full grid-cols-3">
                  <TabsTrigger value="overview">개요</TabsTrigger>
                  <TabsTrigger value="topics">주제</TabsTrigger>
                  <TabsTrigger value="history">활동</TabsTrigger>
                </TabsList>

                <TabsContent value="overview" className="space-y-4">
                  {/* 감정 분포 */}
                  <div className="space-y-2">
                    <h4 className="text-sm font-medium">감정 분포</h4>
                    <div className="space-y-1">
                      <div className="flex justify-between items-center">
                        <span className="text-sm">긍정</span>
                        <SentimentIndicator 
                          sentiment="positive" 
                          score={personaDetails.sentiment_distribution.positive} 
                        />
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm">부정</span>
                        <SentimentIndicator 
                          sentiment="negative" 
                          score={personaDetails.sentiment_distribution.negative} 
                        />
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm">중립</span>
                        <SentimentIndicator 
                          sentiment="neutral" 
                          score={personaDetails.sentiment_distribution.neutral} 
                        />
                      </div>
                    </div>
                  </div>

                  {/* 활동 통계 */}
                  <div className="space-y-2">
                    <h4 className="text-sm font-medium">활동 통계</h4>
                    <div className="grid grid-cols-2 gap-2">
                      <div className="flex items-center gap-2">
                        <MessageCircle className="w-4 h-4 text-gray-500" />
                        <div>
                          <p className="text-xs text-gray-500">게시물</p>
                          <p className="text-sm font-medium">{personaDetails.total_posts}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <MessageCircle className="w-4 h-4 text-gray-500" />
                        <div>
                          <p className="text-xs text-gray-500">댓글</p>
                          <p className="text-sm font-medium">{personaDetails.total_comments}</p>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* 언어 스타일 */}
                  <div className="space-y-2">
                    <h4 className="text-sm font-medium">언어 스타일</h4>
                    <div className="space-y-1">
                      <div className="flex justify-between">
                        <span className="text-xs text-gray-500">논증 스타일</span>
                        <Badge variant="outline" className="text-xs">
                          {personaDetails.argumentation_style}
                        </Badge>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-xs text-gray-500">격식 수준</span>
                        <span className="text-xs font-medium">
                          {(personaDetails.formality_level * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>
                  </div>
                </TabsContent>

                <TabsContent value="topics" className="space-y-2">
                  <h4 className="text-sm font-medium">주요 관심사</h4>
                  <div className="flex flex-wrap gap-2">
                    {personaDetails.key_topics.map((topic, idx) => (
                      <Badge key={idx} variant="secondary" className="flex items-center gap-1">
                        <Hash className="w-3 h-3" />
                        {topic}
                      </Badge>
                    ))}
                  </div>
                </TabsContent>

                <TabsContent value="history" className="space-y-2">
                  <h4 className="text-sm font-medium">최근 활동</h4>
                  <ScrollArea className="h-64">
                    <div className="space-y-2">
                      {personaDetails.tracked_sources.map((source, idx) => (
                        <div key={idx} className="p-2 border rounded-lg">
                          <div className="flex items-center justify-between">
                            <Badge variant="outline" className="text-xs">
                              {source.type}
                            </Badge>
                            <span className="text-xs text-gray-500">
                              {new Date(source.created_at).toLocaleDateString()}
                            </span>
                          </div>
                          {source.url && (
                            <a 
                              href={source.url} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              className="text-xs text-blue-600 hover:underline flex items-center gap-1 mt-1"
                            >
                              <Link className="w-3 h-3" />
                              원본 보기
                            </a>
                          )}
                        </div>
                      ))}
                    </div>
                  </ScrollArea>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default PersonaNetwork;
