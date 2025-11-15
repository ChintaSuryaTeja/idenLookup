import { Navbar } from "./Navbar";
import { Footer } from "./Footer";

interface LayoutProps {
  children: React.ReactNode;
}

export function Layout({ children }: LayoutProps) {
  return (
    <div className="min-h-screen bg-gradient-background">
      <div className="flex flex-col min-h-screen w-full">
        <Navbar />
        <main className="flex-1 overflow-auto">
          <div className="container mx-auto px-4 sm:px-6 py-4 sm:py-8">
            {children}
          </div>
        </main>
        <Footer />
      </div>
    </div>
  );
}