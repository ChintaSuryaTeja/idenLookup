import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Switch } from "@/components/ui/switch";
import { Separator } from "@/components/ui/separator";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from "@/components/ui/alert-dialog";
import { User, Camera, Trash2, Shield } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

// Placeholder data
const userProfile = {
  name: "John Doe",
  email: "john.doe@example.com",
  phone: "+1 (555) 123-4567",
  avatar: "/placeholder.svg"
};

const searchHistory = [
  { query: "Jane Smith", platform: "LinkedIn", date: "2024-01-15", results: 5 },
  { query: "Mike Johnson", platform: "Facebook", date: "2024-01-14", results: 3 },
  { query: "Sarah Wilson", platform: "X.com", date: "2024-01-13", results: 2 },
  { query: "Alex Brown", platform: "GitHub", date: "2024-01-12", results: 4 },
  { query: "Emily Davis", platform: "Instagram", date: "2024-01-11", results: 1 },
];

export default function Account() {
  const [profileData, setProfileData] = useState(userProfile);
  const [dataRemovalRequested, setDataRemovalRequested] = useState(false);
  const { toast } = useToast();

  const handleProfileUpdate = (field: string) => (e: React.ChangeEvent<HTMLInputElement>) => {
    setProfileData(prev => ({ ...prev, [field]: e.target.value }));
  };

  const handleSaveProfile = () => {
    // Placeholder save logic
    console.log("Saving profile:", profileData);
    toast({
      title: "Profile updated",
      description: "Your profile information has been saved successfully.",
    });
  };

  const handleDataRemovalRequest = () => {
    setDataRemovalRequested(true);
    toast({
      title: "Data removal requested",
      description: "Your request has been submitted and will be processed within 30 days.",
    });
  };

  const clearSearchHistory = () => {
    toast({
      title: "Search history cleared",
      description: "All search history has been permanently deleted.",
    });
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Account Settings</h1>
        <p className="text-foreground-muted">
          Manage your profile, privacy settings, and search history
        </p>
      </div>

      <div className="grid gap-8 lg:grid-cols-2">
        {/* Profile Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <User className="h-5 w-5" />
              Profile Information
            </CardTitle>
            <CardDescription>
              Update your personal information and profile picture
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Avatar Section */}
            <div className="flex items-center space-x-4">
              <Avatar className="h-20 w-20">
                <AvatarImage src={profileData.avatar} />
                <AvatarFallback className="text-lg">
                  {profileData.name.split(' ').map(n => n[0]).join('')}
                </AvatarFallback>
              </Avatar>
              <div className="space-y-2">
                <Button variant="outline" size="sm">
                  <Camera className="mr-2 h-4 w-4" />
                  Change Photo
                </Button>
                <p className="text-xs text-foreground-muted">
                  JPG, PNG or GIF. Max size 2MB.
                </p>
              </div>
            </div>

            <Separator />

            {/* Profile Form */}
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="name">Full Name</Label>
                <Input
                  id="name"
                  value={profileData.name}
                  onChange={handleProfileUpdate("name")}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  value={profileData.email}
                  onChange={handleProfileUpdate("email")}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="phone">Phone Number</Label>
                <Input
                  id="phone"
                  value={profileData.phone}
                  onChange={handleProfileUpdate("phone")}
                />
              </div>
            </div>

            <Button onClick={handleSaveProfile} className="w-full">
              Save Changes
            </Button>
          </CardContent>
        </Card>

        {/* Privacy Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="h-5 w-5" />
              Privacy & Data
            </CardTitle>
            <CardDescription>
              Control your data and privacy preferences
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-4">
              <div className="flex items-center justify-between space-x-2">
                <div className="space-y-0.5">
                  <Label>Email Notifications</Label>
                  <p className="text-xs text-foreground-muted">
                    Receive updates about your searches
                  </p>
                </div>
                <Switch defaultChecked />
              </div>
              
              <div className="flex items-center justify-between space-x-2">
                <div className="space-y-0.5">
                  <Label>Search History</Label>
                  <p className="text-xs text-foreground-muted">
                    Save your search queries for reference
                  </p>
                </div>
                <Switch defaultChecked />
              </div>

              <div className="flex items-center justify-between space-x-2">
                <div className="space-y-0.5">
                  <Label>Analytics</Label>
                  <p className="text-xs text-foreground-muted">
                    Help improve our service with usage data
                  </p>
                </div>
                <Switch defaultChecked />
              </div>
            </div>

            <Separator />

            {/* Data Removal */}
            <div className="space-y-4">
              <div className="space-y-2">
                <Label className="text-destructive">Data Removal</Label>
                <p className="text-xs text-foreground-muted">
                  Request permanent deletion of all your data
                </p>
              </div>
              
              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button 
                    variant="destructive" 
                    className="w-full"
                    disabled={dataRemovalRequested}
                  >
                    <Trash2 className="mr-2 h-4 w-4" />
                    {dataRemovalRequested ? "Request Submitted" : "Request Data Removal"}
                  </Button>
                </AlertDialogTrigger>
                <AlertDialogContent>
                  <AlertDialogHeader>
                    <AlertDialogTitle>Delete All Data</AlertDialogTitle>
                    <AlertDialogDescription>
                      This action cannot be undone. This will permanently delete your
                      account and remove all associated data from our servers.
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel>Cancel</AlertDialogCancel>
                    <AlertDialogAction 
                      onClick={handleDataRemovalRequest}
                      className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                    >
                      Confirm Deletion
                    </AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Search History */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>Search History</CardTitle>
            <CardDescription>
              Your recent identity lookup searches
            </CardDescription>
          </div>
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button variant="outline" size="sm">
                <Trash2 className="mr-2 h-4 w-4" />
                Clear History
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Clear Search History</AlertDialogTitle>
                <AlertDialogDescription>
                  This will permanently delete all your search history. This action cannot be undone.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction onClick={clearSearchHistory}>
                  Clear History
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </CardHeader>
        <CardContent>
          <div className="border rounded-lg">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Search Query</TableHead>
                  <TableHead>Platform</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead>Results</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {searchHistory.map((search, index) => (
                  <TableRow key={index}>
                    <TableCell className="font-medium">{search.query}</TableCell>
                    <TableCell>{search.platform}</TableCell>
                    <TableCell className="text-foreground-muted">
                      {new Date(search.date).toLocaleDateString()}
                    </TableCell>
                    <TableCell>
                      <Badge variant="secondary">
                        {search.results} result{search.results !== 1 ? 's' : ''}
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}