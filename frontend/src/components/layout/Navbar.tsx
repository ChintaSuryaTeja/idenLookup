import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { User, Settings, LogOut } from "lucide-react";
import logo from "@/assets/logo.png";

export function Navbar() {
  const location = useLocation();
  const [isLoggedIn, setIsLoggedIn] = useState(false); // Placeholder state

  // Check if current page should show profile only
  const showProfileOnly = ["/home", "/dashboard", "/account", "/recognition"].includes(location.pathname);

  const getPageTitle = () => {
    switch (location.pathname) {
      case "/home": return "Upload Identity";
      case "/upload": return "Upload Identity";
      case "/dashboard": return "Dashboard";
      case "/recognition": return "Recognition Results";
      case "/profile": return "Profile Settings";
      case "/account": return "Profile Settings";
      case "/login": return "Sign In";
      case "/register": return "Sign Up";
      default: return "Identity Lookup Platform";
    }
  };

  return (
    <nav className="sticky top-0 z-50 w-full border-b border-border bg-nav backdrop-blur-md">
      <div className="flex h-14 sm:h-16 items-center px-4 sm:px-6">
        {/* Logo */}
        <Link to="/home" className="flex items-center space-x-2 sm:space-x-3">
          <img src={logo} alt="Identity Lookup Platform" className="h-6 w-6 sm:h-8 sm:w-8" />
          <span className="font-semibold text-foreground text-sm sm:text-base hidden xs:block">Identity Lookup</span>
        </Link>

        {/* Page Title - Center */}
        <div className="flex-1 text-center px-2">
          <h1 className="text-sm sm:text-lg font-medium text-foreground truncate">{getPageTitle()}</h1>
        </div>

        {/* Profile Actions */}
        <div className="flex items-center space-x-2">
          {isLoggedIn || showProfileOnly ? (
            <Button variant="ghost" className="relative h-8 w-8 rounded-full" asChild>
              <Link to="/account">
                <Avatar className="h-8 w-8">
                  <AvatarFallback className="bg-primary text-primary-foreground">
                    JD
                  </AvatarFallback>
                </Avatar>
              </Link>
            </Button>
          ) : (
            <div className="flex items-center space-x-1 sm:space-x-2">
              <Button variant="ghost" size="sm" asChild>
                <Link to="/login">Sign In</Link>
              </Button>
              <Button variant="default" size="sm" asChild>
                <Link to="/register">Sign Up</Link>
              </Button>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
}