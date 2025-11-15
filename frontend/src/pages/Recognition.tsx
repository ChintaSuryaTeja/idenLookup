import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Progress } from "@/components/ui/progress";
import { Mail, Phone, MapPin, User } from "lucide-react";

// Placeholder data
const profileData = {
  name: "John Doe",
  email: "john.doe@example.com",
  phone: "+1 (555) 123-4567",
  location: "San Francisco, CA",
  bio: "Software engineer passionate about technology and innovation. Active on various social media platforms and professional networks.",
  avatar: "/placeholder.svg"
};

const platformMatches = [
  { platform: "LinkedIn", confidence: 99, url: "linkedin.com/in/johndoe" },
  { platform: "Facebook", confidence: 89, url: "facebook.com/johndoe" },
  { platform: "X.com", confidence: 69, url: "x.com/johndoe" },
  { platform: "GitHub", confidence: 59, url: "github.com/johndoe" },
  { platform: "Instagram", confidence: 45, url: "instagram.com/johndoe" },
];

const getConfidenceBadge = (confidence: number) => {
  if (confidence >= 80) return "default";
  if (confidence >= 60) return "secondary";
  return "outline";
};

const getConfidenceColor = (confidence: number) => {
  if (confidence >= 80) return "hsl(var(--success))";
  if (confidence >= 60) return "hsl(var(--warning))";
  return "hsl(var(--foreground-muted))";
};

export default function Recognition() {
  return (
    <div className="space-y-4 md:space-y-8 overflow-hidden">
      <div className="px-1">
        <h1 className="text-2xl md:text-3xl font-bold tracking-tight">Recognition Results</h1>
        <p className="text-muted-foreground text-sm md:text-base">
          Identity lookup results with platform matches and confidence scores
        </p>
      </div>

      <div className="grid gap-4 md:gap-8 lg:grid-cols-2 overflow-hidden">
        {/* Profile Details */}
        <Card className="overflow-hidden">
          <CardHeader className="pb-4">
            <CardTitle className="flex items-center gap-2 text-base md:text-lg">
              <User className="h-4 w-4 md:h-5 md:w-5" />
              Profile Details
            </CardTitle>
            <CardDescription className="text-xs md:text-sm">
              Extracted information from the uploaded image
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 md:space-y-6 overflow-hidden">
            <div className="flex items-start space-x-3 md:space-x-4">
              <Avatar className="h-12 w-12 md:h-16 md:w-16 flex-shrink-0">
                <AvatarImage src={profileData.avatar} />
                <AvatarFallback className="text-sm md:text-lg">JD</AvatarFallback>
              </Avatar>
              <div className="space-y-1 min-w-0 flex-1">
                <h3 className="text-lg md:text-xl font-semibold truncate">{profileData.name}</h3>
                <p className="text-xs md:text-sm text-muted-foreground">Identity Profile</p>
              </div>
            </div>

            <div className="space-y-3 md:space-y-4">
              <div className="flex items-center space-x-3 min-w-0">
                <Mail className="h-3 w-3 md:h-4 md:w-4 text-muted-foreground flex-shrink-0" />
                <span className="text-xs md:text-sm truncate">{profileData.email}</span>
              </div>
              <div className="flex items-center space-x-3 min-w-0">
                <Phone className="h-3 w-3 md:h-4 md:w-4 text-muted-foreground flex-shrink-0" />
                <span className="text-xs md:text-sm truncate">{profileData.phone}</span>
              </div>
              <div className="flex items-center space-x-3 min-w-0">
                <MapPin className="h-3 w-3 md:h-4 md:w-4 text-muted-foreground flex-shrink-0" />
                <span className="text-xs md:text-sm truncate">{profileData.location}</span>
              </div>
            </div>

            <div className="space-y-2">
              <h4 className="font-medium text-sm md:text-base">Biography</h4>
              <p className="text-xs md:text-sm text-muted-foreground leading-relaxed">
                {profileData.bio}
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Platform Matches */}
        <Card className="overflow-hidden">
          <CardHeader className="pb-4">
            <CardTitle className="text-base md:text-lg">Platform Matches</CardTitle>
            <CardDescription className="text-xs md:text-sm">
              Social media and professional platforms with confidence scores
            </CardDescription>
          </CardHeader>
          <CardContent className="overflow-hidden">
            <div className="overflow-x-auto -mx-1">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="text-xs md:text-sm min-w-[120px]">Platform</TableHead>
                    <TableHead className="text-xs md:text-sm min-w-[80px]">Confidence</TableHead>
                    <TableHead className="text-xs md:text-sm min-w-[100px]">Score</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {platformMatches.map((match, index) => (
                    <TableRow key={index}>
                      <TableCell className="font-medium min-w-0">
                        <div className="space-y-1">
                          <div className="text-xs md:text-sm">{match.platform}</div>
                          <div className="text-[10px] md:text-xs text-muted-foreground truncate max-w-[100px] md:max-w-none">
                            {match.url}
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant={getConfidenceBadge(match.confidence)} className="text-[10px] md:text-xs px-1 md:px-2">
                          {match.confidence}%
                        </Badge>
                      </TableCell>
                      <TableCell className="w-20 md:w-32">
                        <div className="space-y-1">
                          <Progress 
                            value={match.confidence} 
                            className="h-1.5 md:h-2"
                            style={{
                              backgroundColor: `${getConfidenceColor(match.confidence)}20`
                            }}
                          />
                          <div className="text-[10px] md:text-xs text-right text-muted-foreground">
                            {match.confidence}%
                          </div>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Summary Stats */}
      <div className="grid gap-3 md:gap-6 grid-cols-3 md:grid-cols-3">
        <Card>
          <CardContent className="pt-4 md:pt-6">
            <div className="text-center space-y-1 md:space-y-2">
              <div className="text-xl md:text-2xl font-bold text-primary">5</div>
              <div className="text-[10px] md:text-sm text-muted-foreground">Platforms Found</div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 md:pt-6">
            <div className="text-center space-y-1 md:space-y-2">
              <div className="text-xl md:text-2xl font-bold text-secondary">72%</div>
              <div className="text-[10px] md:text-sm text-muted-foreground">Average Confidence</div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 md:pt-6">
            <div className="text-center space-y-1 md:space-y-2">
              <div className="text-xl md:text-2xl font-bold text-success">3</div>
              <div className="text-[10px] md:text-sm text-muted-foreground">High Confidence</div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}