import { useState } from "react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Clock, Image, Plus } from "lucide-react";
import { cn } from "@/lib/utils";

interface HistoryItem {
  id: string;
  name: string;
  timestamp: Date;
  imageUrl?: string;
  status: 'completed' | 'processing' | 'failed';
}

interface HistoryBarProps {
  className?: string;
  onNewUpload?: () => void;
}

export function HistoryBar({ className, onNewUpload }: HistoryBarProps) {
  const [historyItems] = useState<HistoryItem[]>([
    {
      id: '1',
      name: 'John Smith',
      timestamp: new Date(Date.now() - 1000 * 60 * 30), // 30 mins ago
      status: 'completed'
    },
    {
      id: '2', 
      name: 'Sarah Johnson',
      timestamp: new Date(Date.now() - 1000 * 60 * 60 * 2), // 2 hours ago
      status: 'completed'
    },
    {
      id: '3',
      name: 'Mike Davis',
      timestamp: new Date(Date.now() - 1000 * 60 * 60 * 24), // 1 day ago
      status: 'processing'
    }
  ]);

  const formatTimeAgo = (date: Date) => {
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / (1000 * 60));
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));

    if (days > 0) return `${days}d ago`;
    if (hours > 0) return `${hours}h ago`;
    if (minutes > 0) return `${minutes}m ago`;
    return 'Just now';
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'text-secondary';
      case 'processing':
        return 'text-warning';
      case 'failed':
        return 'text-destructive';
      default:
        return 'text-foreground-muted';
    }
  };

  return (
    <div className={cn("border-b border-border bg-card", className)}>
      <div className="flex items-center gap-4 px-6 py-4">
        <div className="flex items-center gap-2">
          <Clock className="h-5 w-5 text-foreground-muted" />
          <span className="text-sm font-medium">Recent Uploads</span>
        </div>
        
        <ScrollArea className="flex-1">
          <div className="flex items-center gap-3">
            {historyItems.map((item) => (
              <Button
                key={item.id}
                variant="ghost"
                className="h-auto p-3 flex-shrink-0 hover:bg-accent"
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center">
                    <Image className="h-4 w-4 text-foreground-muted" />
                  </div>
                  <div className="text-left">
                    <div className="text-sm font-medium">{item.name}</div>
                    <div className={cn("text-xs", getStatusColor(item.status))}>
                      {formatTimeAgo(item.timestamp)}
                    </div>
                  </div>
                </div>
              </Button>
            ))}
          </div>
        </ScrollArea>

        <Button
          onClick={onNewUpload}
          variant="outline"
          size="sm"
          className="flex-shrink-0"
        >
          <Plus className="h-4 w-4 mr-2" />
          New Upload
        </Button>
      </div>
    </div>
  );
}