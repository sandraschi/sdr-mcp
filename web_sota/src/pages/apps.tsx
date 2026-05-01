import { Box, ExternalLink, Grid } from "lucide-react";
import { APPS_CATALOG } from "@/common/apps-catalog";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function Apps() {
  const apps = [
    {
      name: "SDR MCP",
      port: 10890,
      description: "Software Defined Radio spectrum analysis and control",
    },
    {
      name: "Reversing MCP",
      port: 10750,
      description: "Binary instrumentation hub",
    },
    {
      name: "Ring MCP",
      port: 10728,
      description: "Doorbell & security monitoring",
    },
    { name: "Obsidian MCP", port: 10892, description: "Knowledge base bridge" },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">
            App Hub
          </h2>
          <p className="text-slate-400">
            Discover and navigate the Antigravity ecosystem
          </p>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {apps.map((app) => (
          <Card
            key={app.name}
            className="border-slate-800 bg-slate-950/50 hover:bg-slate-900/50 transition-colors group cursor-pointer"
            onClick={() =>
              window.open(`http://localhost:${app.port}`, "_blank")
            }
          >
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-slate-200">
                {app.name}
              </CardTitle>
              <Box className="h-4 w-4 text-blue-500 group-hover:scale-110 transition-transform" />
            </CardHeader>
            <CardContent>
              <p className="text-xs text-slate-400 mb-4">{app.description}</p>
              <div className="flex items-center text-xs text-blue-400 font-medium">
                <span>localhost:{app.port}</span>
                <ExternalLink className="h-3 w-3 ml-1" />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card className="border-slate-800 bg-slate-950/50 border-dashed">
        <CardContent className="flex flex-col items-center justify-center py-10 text-center">
          <Grid className="h-10 w-10 text-slate-700 mb-4" />
          <h3 className="text-lg font-medium text-slate-300">
            Fleet Auto-Discovery Active
          </h3>
          <p className="text-sm text-slate-500 max-w-sm">
            Scanning local ports for registered MCP SOTA webapps...
          </p>
        </CardContent>
      </Card>

      <Card className="border-slate-800 bg-slate-950/50">
        <CardHeader>
          <CardTitle className="text-white">Fleet Registry</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-2">
            {APPS_CATALOG.map((app) => (
              <div
                key={app.id}
                className="flex items-center justify-between p-2 rounded bg-slate-900/30 border border-slate-800"
              >
                <div className="flex items-center gap-2">
                  <app.icon className="h-4 w-4 text-slate-400" />
                  <span className="text-sm text-slate-300">{app.label}</span>
                </div>
                <span className="text-xs text-slate-500 font-mono">
                  {app.port}
                </span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
