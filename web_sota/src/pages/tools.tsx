import { Radio, Search, Wrench, Zap } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const TOOLS = [
  {
    name: "sdr_device",
    ops: "list, initialize, status, health, set_frequency, set_gain, tune_preset, scan, mock_mode",
  },
  {
    name: "sdr_spectrum",
    ops: "spectrum, waterfall, start_websocket, stop_websocket",
  },
  {
    name: "sdr_stations",
    ops: "search, by_band, by_country, schedule, stats",
  },
  {
    name: "sdr_online",
    ops: "search, signal_id",
  },
  {
    name: "sdr_gnuradio",
    ops: "health, status, start, stop, list_devices (fm/am/usb/lsb, rtl_tcp/hackrf)",
  },
  {
    name: "sdr_agentic_assist",
    ops: "Multi-step plan via ctx.sample (SEP-1577)",
  },
  {
    name: "sdr_sampling_hint",
    ops: "Frequency/band hints via ctx.sample",
  },
];

export function Tools() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white">
          Tool Inventory
        </h2>
        <p className="text-slate-400">
          Portmanteau MCP tools exposed by sdr-mcp
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">
              Spectral Analysis
            </CardTitle>
            <Zap className="h-4 w-4 text-emerald-500" />
          </CardHeader>
          <CardContent>
            <p className="text-xs text-slate-400">
              sdr_spectrum + sdr_device.scan
            </p>
          </CardContent>
        </Card>
        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">
              Device Discovery
            </CardTitle>
            <Search className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <p className="text-xs text-slate-400">
              sdr_device.list + sdr_gnuradio.list_devices
            </p>
          </CardContent>
        </Card>
        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">
              GNU Radio Demod
            </CardTitle>
            <Radio className="h-4 w-4 text-purple-500" />
          </CardHeader>
          <CardContent>
            <p className="text-xs text-slate-400">
              FM, AM, USB, LSB via rtl_tcp or HackRF
            </p>
          </CardContent>
        </Card>
      </div>

      <Card className="border-slate-800 bg-slate-950/50">
        <CardHeader>
          <CardTitle className="text-white">Active Capabilities</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {TOOLS.map((tool) => (
              <div
                key={tool.name}
                className="flex items-center justify-between p-3 rounded-lg bg-slate-900/50 border border-slate-800"
              >
                <div className="flex items-center gap-3">
                  <Wrench className="h-4 w-4 text-slate-400" />
                  <div>
                    <span className="text-sm font-medium text-slate-200 font-mono">
                      {tool.name}
                    </span>
                    <p className="text-xs text-slate-500">{tool.ops}</p>
                  </div>
                </div>
                <span className="text-xs text-emerald-500 font-mono">
                  READY
                </span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
