import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { 
  Search, 
  Shield, 
  Target, 
  Zap, 
  Users, 
  CheckCircle, 
  ArrowRight,
  Upload,
  Eye,
  BarChart3
} from "lucide-react";
import logo from "@/assets/logo.png";

export default function LandingPage() {
  const features = [
    {
      icon: Upload,
      title: "Easy Upload",
      description: "Simply upload a photo and let our AI do the work"
    },
    {
      icon: Search,
      title: "Smart Recognition",
      description: "Advanced AI technology for accurate identity matching"
    },
    {
      icon: Shield,
      title: "Secure & Private",
      description: "Your data is protected with enterprise-grade security"
    },
    {
      icon: Target,
      title: "High Accuracy",
      description: "Get confidence scores and detailed match results"
    },
    {
      icon: Zap,
      title: "Lightning Fast",
      description: "Results in seconds, not minutes"
    },
    {
      icon: BarChart3,
      title: "Analytics Dashboard",
      description: "Track your lookups and view detailed analytics"
    }
  ];

  const steps = [
    {
      icon: Upload,
      title: "Upload",
      description: "Upload a photo of the person you want to identify"
    },
    {
      icon: Eye,
      title: "Analyze",
      description: "Our AI analyzes the image across multiple platforms"
    },
    {
      icon: CheckCircle,
      title: "Results",
      description: "Get detailed results with confidence scores"
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-background">
      {/* Header */}
      <header className="border-b border-border bg-nav backdrop-blur-md">
        <div className="container mx-auto px-4 sm:px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <img src={logo} alt="Identity Lookup Platform" className="h-8 w-8" />
              <span className="font-bold text-foreground text-lg">Identity Lookup</span>
            </div>
            <div className="flex items-center space-x-3">
              <Button variant="ghost" asChild>
                <Link to="/login">Sign In</Link>
              </Button>
              <Button asChild>
                <Link to="/register">Sign Up</Link>
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="py-16 sm:py-24">
        <div className="container mx-auto px-4 sm:px-6 text-center">
          <Badge variant="secondary" className="mb-6">
            Powered by Advanced AI
          </Badge>
          <h1 className="text-4xl sm:text-6xl font-bold tracking-tight mb-6">
            Identity Lookup
            <span className="text-primary block mt-2">Made Simple</span>
          </h1>
          <p className="text-lg sm:text-xl text-muted-foreground max-w-3xl mx-auto mb-8">
            Upload a photo and discover digital identities across multiple platforms with 
            AI-powered recognition technology. Fast, accurate, and secure.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <Button size="lg" asChild className="w-full sm:w-auto">
              <Link to="/register" className="flex items-center gap-2">
                Get Started <ArrowRight className="h-4 w-4" />
              </Link>
            </Button>
            <Button variant="outline" size="lg" asChild className="w-full sm:w-auto">
              <Link to="/login">Sign In</Link>
            </Button>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="py-16 bg-muted/20">
        <div className="container mx-auto px-4 sm:px-6">
          <div className="text-center mb-12">
            <h2 className="text-3xl sm:text-4xl font-bold mb-4">
              Why Choose Our Platform?
            </h2>
            <p className="text-lg text-muted-foreground">
              Powerful features designed for modern identity verification needs
            </p>
          </div>
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {features.map((feature, index) => (
              <Card key={index} className="text-center hover:shadow-lg transition-shadow">
                <CardContent className="p-6">
                  <feature.icon className="h-12 w-12 text-primary mx-auto mb-4" />
                  <h3 className="text-xl font-semibold mb-2">{feature.title}</h3>
                  <p className="text-muted-foreground">{feature.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-16">
        <div className="container mx-auto px-4 sm:px-6">
          <div className="text-center mb-12">
            <h2 className="text-3xl sm:text-4xl font-bold mb-4">
              How It Works
            </h2>
            <p className="text-lg text-muted-foreground">
              Three simple steps to get accurate identity results
            </p>
          </div>
          <div className="grid gap-8 md:grid-cols-3">
            {steps.map((step, index) => (
              <div key={index} className="text-center">
                <div className="relative">
                  <div className="bg-primary/10 rounded-full p-6 inline-block mb-4">
                    <step.icon className="h-8 w-8 text-primary" />
                  </div>
                  <Badge variant="default" className="absolute -top-2 -right-2 h-6 w-6 rounded-full p-0 flex items-center justify-center text-xs">
                    {index + 1}
                  </Badge>
                </div>
                <h3 className="text-xl font-semibold mb-2">{step.title}</h3>
                <p className="text-muted-foreground">{step.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-16 bg-muted/20">
        <div className="container mx-auto px-4 sm:px-6">
          <div className="grid gap-8 md:grid-cols-3 text-center">
            <div>
              <div className="text-4xl font-bold text-primary mb-2">10K+</div>
              <p className="text-muted-foreground">Searches Completed</p>
            </div>
            <div>
              <div className="text-4xl font-bold text-primary mb-2">95%</div>
              <p className="text-muted-foreground">Accuracy Rate</p>
            </div>
            <div>
              <div className="text-4xl font-bold text-primary mb-2">25+</div>
              <p className="text-muted-foreground">Platforms Covered</p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16">
        <div className="container mx-auto px-4 sm:px-6 text-center">
          <Card className="max-w-2xl mx-auto">
            <CardHeader>
              <CardTitle className="text-2xl sm:text-3xl">
                Ready to Get Started?
              </CardTitle>
              <CardDescription className="text-lg">
                Join thousands of users who trust our platform for accurate identity verification
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Button size="lg" asChild className="w-full sm:w-auto">
                  <Link to="/register" className="flex items-center gap-2">
                    Start Your First Search <ArrowRight className="h-4 w-4" />
                  </Link>
                </Button>
                <Button variant="outline" size="lg" asChild className="w-full sm:w-auto">
                  <Link to="/login">Already have an account?</Link>
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border py-8">
        <div className="container mx-auto px-4 sm:px-6">
          <div className="flex flex-col sm:flex-row justify-between items-center">
            <div className="flex items-center space-x-3 mb-4 sm:mb-0">
              <img src={logo} alt="Identity Lookup Platform" className="h-6 w-6" />
              <span className="font-semibold text-foreground">Identity Lookup</span>
            </div>
            <p className="text-sm text-muted-foreground">
              © 2024 Identity Lookup Platform. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}