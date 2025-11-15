import { Link } from "react-router-dom";

export function Footer() {
  return (
    <footer className="border-t border-border bg-background-secondary">
      <div className="container mx-auto px-6 py-8">
        <div className="flex flex-col items-center justify-between space-y-4 md:flex-row md:space-y-0">
          <div className="flex items-center space-x-4 text-sm text-foreground-muted">
            <span>© 2024 Identity Lookup Platform</span>
          </div>
          
          <div className="flex items-center space-x-6">
            <Link
              to="/docs"
              className="text-sm text-foreground-muted hover:text-foreground transition-colors"
            >
              Documentation
            </Link>
            <Link
              to="/privacy"
              className="text-sm text-foreground-muted hover:text-foreground transition-colors"
            >
              Privacy Policy
            </Link>
            <Link
              to="/contact"
              className="text-sm text-foreground-muted hover:text-foreground transition-colors"
            >
              Contact Us
            </Link>
            <a
              href="https://github.com"
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-foreground-muted hover:text-foreground transition-colors"
            >
              GitHub
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}