import { Book, Code, HelpCircle, Info } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function Help() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">
            Help & Documentation
          </h2>
          <p className="text-slate-400">
            Guidelines, standards, and usage patterns
          </p>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Book className="h-5 w-5 text-emerald-500" />
              <CardTitle className="text-white">Getting Started</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="text-sm text-slate-400 space-y-4">
            <p>
              This MCP server provides a standardized interface for Software
              Defined Radio operations. It acts as a bridge between high-level
              RF queries and local SDR hardware (RTL-SDR, HackRF, etc.).
            </p>
            <p>Key concepts:</p>
            <ul className="list-disc list-inside space-y-1">
              <li>FFT spectral analysis</li>
              <li>SOTA aesthetics following the Alsergrund Blueprint</li>
              <li>FastMCP 2.14.4+ dual-transport bridge</li>
            </ul>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Code className="h-5 w-5 text-blue-500" />
              <CardTitle className="text-white">Developer Standards</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="text-sm text-slate-400 space-y-4">
            <p>
              Follow the
              [AGENT_PROTOCOLS.md](file:///D:/Dev/repos/mcp-central-docs/standards/AGENT_PROTOCOLS.md)
              for all modifications. Ensure all new tools follow the portmanteau
              pattern.
            </p>
            <div className="p-3 bg-slate-900 rounded border border-slate-800 font-mono text-xs">
              <p># Always check port adjacency</p>
              <p>WEB_PORT = 10886</p>
              <p>BACKEND_PORT = 10887</p>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card className="border-slate-800 bg-slate-950/50">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Info className="h-5 w-5 text-purple-500" />
            <CardTitle className="text-white">System Information</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <table className="w-full text-sm text-left text-slate-400">
            <tbody className="divide-y divide-slate-800">
              <tr>
                <td className="py-2 font-medium text-slate-300">
                  FastMCP Version
                </td>
                <td className="py-2 font-mono">2.14.4</td>
              </tr>
              <tr>
                <td className="py-2 font-medium text-slate-300">
                  Template Mode
                </td>
                <td className="py-2">SOTA v2.0 (Feb 2026)</td>
              </tr>
              <tr>
                <td className="py-2 font-medium text-slate-300">Locale</td>
                <td className="py-2">Vienna (Alsergrund)</td>
              </tr>
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
}
