import { Database, FlaskConical } from "lucide-react";
import { Switch } from "@/components/ui/switch";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { useMockData } from "@/contexts/mock-data-context";
import { cn } from "@/lib/utils";

/**
 * Toggle switch for mock data mode.
 *
 * - OFF (default): All data is fetched from Databricks (real data).
 * - ON: API calls include X-Mock-Data header; backend returns mock data.
 */
export function MockDataToggle() {
  const { mockEnabled, setMockEnabled } = useMockData();

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <label
          className={cn(
            "flex items-center gap-1.5 cursor-pointer select-none rounded-md px-2 py-1 text-xs font-medium transition-colors",
            mockEnabled
              ? "bg-amber-500/15 text-amber-600 dark:text-amber-400"
              : "text-muted-foreground hover:text-foreground",
          )}
        >
          {mockEnabled ? (
            <FlaskConical className="h-3.5 w-3.5" />
          ) : (
            <Database className="h-3.5 w-3.5" />
          )}
          <span className="hidden sm:inline">
            {mockEnabled ? "Mock" : "Live"}
          </span>
          <Switch
            checked={mockEnabled}
            onCheckedChange={setMockEnabled}
            className="scale-75 origin-left"
          />
        </label>
      </TooltipTrigger>
      <TooltipContent side="bottom" className="max-w-64 text-xs">
        {mockEnabled ? (
          <p>
            <strong>Mock data mode.</strong> The UI is displaying sample data.
            Turn off to fetch real data from Databricks.
          </p>
        ) : (
          <p>
            <strong>Live data mode.</strong> All data is fetched from
            Databricks. Turn on to use mock data for demo/testing.
          </p>
        )}
      </TooltipContent>
    </Tooltip>
  );
}
