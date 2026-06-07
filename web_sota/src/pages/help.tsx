import { HelpCircle } from "lucide-react";
import { HELP_TABS } from "@/common/help-content";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

export function Help() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
          <HelpCircle className="h-7 w-7 text-cyan-400" />
          Help & Documentation
        </h2>
        <p className="text-slate-400 mt-1">
          From “what is SDR?” to MCP tools, hardware, audio, and repo docs
        </p>
      </div>

      <Tabs defaultValue="start" className="w-full">
        <div className="overflow-x-auto pb-1 -mx-1 px-1">
          <TabsList className="inline-flex h-auto min-w-full w-max flex-nowrap gap-1 rounded-lg border border-slate-800 bg-slate-950/80 p-1">
            {HELP_TABS.map((tab) => (
              <TabsTrigger
                key={tab.id}
                value={tab.id}
                className="rounded-md px-3 py-2 text-xs sm:text-sm data-[state=active]:bg-cyan-950 data-[state=active]:text-cyan-300 text-slate-400"
              >
                {tab.label}
              </TabsTrigger>
            ))}
          </TabsList>
        </div>

        {HELP_TABS.map((tab) => (
          <TabsContent key={tab.id} value={tab.id} className="mt-4">
            <Card className="border-slate-800 bg-slate-950/50">
              <CardHeader className="pb-2">
                <CardTitle className="text-lg text-white">
                  {tab.label}
                </CardTitle>
              </CardHeader>
              <CardContent>{tab.content}</CardContent>
            </Card>
          </TabsContent>
        ))}
      </Tabs>
    </div>
  );
}
