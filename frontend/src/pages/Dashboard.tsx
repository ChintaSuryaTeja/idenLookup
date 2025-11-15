import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Search, BarChart3, Users, Target, TrendingUp } from "lucide-react";

export default function Dashboard() {
  const navigate = useNavigate();

  // Load results dynamically (fixes refresh issue)
  const [recentResults, setRecentResults] = useState<any[]>([]);

  useEffect(() => {
    const savedResults = JSON.parse(localStorage.getItem("face_results") || "[]");

    const mapped = savedResults.map((r: any) => ({
      name: r.name,
      platform: "LinkedIn",
      confidence: r.confidence, // FIX: Use backend confidence directly
      date: new Date().toISOString().split("T")[0],
      status: r.confidence >= 50 ? "verified" : "pending", // FIX: Correct status logic
    }));

    setRecentResults(mapped);
  }, []);

  // Dashboard Stats (uses updated recentResults)
  const dashboardStats = [
    { title: "Total Profiles Checked", value: recentResults.length.toString(), change: "+12%", icon: Users },
    {
      title: "Avg Confidence",
      value:
        recentResults.length > 0
          ? Math.round(recentResults.reduce((acc, r) => acc + r.confidence, 0) / recentResults.length) + "%"
          : "0%",
      change: "+5%",
      icon: Target,
    },
    {
      title: "Success Rate",
      value: `${recentResults.filter((r) => r.confidence >= 50).length}/${recentResults.length}`,
      change: "+3%",
      icon: TrendingUp,
    },
    { title: "Platforms", value: "LinkedIn", change: "+8%", icon: BarChart3 },
  ];

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "verified":
        return "default";
      case "pending":
        return "secondary";
      default:
        return "outline";
    }
  };

  const getConfidenceBadge = (confidence: number) => {
    if (confidence >= 80) return "secondary";
    if (confidence >= 45) return "warning";
    return "destructive";
  };

  const [searchTerm, setSearchTerm] = useState("");
  const [platformFilter, setPlatformFilter] = useState("all");
  const [confidenceFilter, setConfidenceFilter] = useState("all");

  const filteredResults = recentResults.filter((result) => {
    const matchesSearch = result.name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesPlatform = platformFilter === "all" || result.platform === platformFilter;
    const matchesConfidence =
      confidenceFilter === "all" ||
      (confidenceFilter === "high" && result.confidence >= 90) ||
      (confidenceFilter === "medium" && result.confidence >= 70 && result.confidence < 90) ||
      (confidenceFilter === "low" && result.confidence < 70);

    return matchesSearch && matchesPlatform && matchesConfidence;
  });

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-sm sm:text-base text-muted-foreground">
          Overview of your identity lookup activities and results
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 sm:gap-6 grid-cols-2 lg:grid-cols-4">
        {dashboardStats.map((stat, index) => (
          <Card key={index}>
            <CardContent className="p-4 sm:p-6">
              <div className="flex items-center justify-between">
                <div className="space-y-1 sm:space-y-2 min-w-0 flex-1">
                  <p className="text-xs sm:text-sm font-medium text-muted-foreground truncate">{stat.title}</p>
                  <div className="flex items-baseline space-x-1 sm:space-x-2">
                    <p className="text-lg sm:text-2xl font-bold">{stat.value}</p>
                    <Badge variant="secondary" className="text-xs">
                      {stat.change}
                    </Badge>
                  </div>
                </div>
                <stat.icon className="h-6 w-6 sm:h-8 sm:w-8 text-primary flex-shrink-0" />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Filters and Search */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Recent Results
          </CardTitle>
          <CardDescription>Latest identity lookup results with filtering options</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search by name..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            <div className="flex flex-col gap-2 sm:flex-row sm:gap-2 min-w-fit">
              <Select value={platformFilter} onValueChange={setPlatformFilter}>
                <SelectTrigger className="w-full sm:w-40">
                  <SelectValue placeholder="Platform" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Platforms</SelectItem>
                  <SelectItem value="LinkedIn">LinkedIn</SelectItem>
                  <SelectItem value="Facebook">Facebook</SelectItem>
                  <SelectItem value="X.com">X.com</SelectItem>
                  <SelectItem value="GitHub">GitHub</SelectItem>
                  <SelectItem value="Instagram">Instagram</SelectItem>
                </SelectContent>
              </Select>
              <Select value={confidenceFilter} onValueChange={setConfidenceFilter}>
                <SelectTrigger className="w-full sm:w-44">
                  <SelectValue placeholder="Confidence" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Confidence</SelectItem>
                  <SelectItem value="high">High (90%+)</SelectItem>
                  <SelectItem value="medium">Medium (70-89%)</SelectItem>
                  <SelectItem value="low">Low (&lt;70%)</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Results Table */}
          <div className="border rounded-lg overflow-hidden">
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="text-left min-w-[120px]">Name</TableHead>
                    <TableHead className="text-center min-w-[100px]">Platform</TableHead>
                    <TableHead className="text-center min-w-[100px]">Confidence</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredResults.map((result, index) => (
                    <TableRow key={index} className="hover:bg-muted/50">
                      <TableCell className="font-medium">
                        <button
                          onClick={() => navigate("/recognition")}
                          className="text-left hover:text-primary hover:underline cursor-pointer transition-colors text-sm sm:text-base"
                        >
                          {result.name}
                        </button>
                      </TableCell>
                      <TableCell className="text-center">
                        <span className="inline-block px-2 py-1 rounded-md bg-muted/30 text-xs sm:text-sm">
                          {result.platform}
                        </span>
                      </TableCell>
                      <TableCell className="text-center">
                        <Badge
                          variant={getConfidenceBadge(result.confidence)}
                          className="justify-center min-w-[50px] sm:min-w-[60px] text-xs"
                        >
                          {result.confidence}%
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </div>

          {filteredResults.length === 0 && (
            <div className="text-center py-8 text-foreground-muted">No results found matching your filters.</div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
