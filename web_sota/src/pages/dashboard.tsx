import {
  Activity,
  ArrowRight,
  Cpu,
  HelpCircle,
  Radio,
  Satellite,
  Sparkles,
  Waves,
} from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchStatus, type StatusSnapshot } from "@/common/api-client";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function Dashboard() {
  const [status, setStatus] = useState<StatusSnapshot | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    async function load() {
      try {
        const snapshot = await fetchStatus();
        if (active) {
          setStatus(snapshot);
          setError(null);
        }
      } catch (err) {
        if (active) {
          setError(err instanceof Error ? err.message : String(err));
        }
      }
    }
    void load();
    const timer = window.setInterval(() => void load(), 5000);
    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, []);

  const hardwareOnline = status?.hardware.available ?? false;
  const mockActive = status?.mock?.active ?? false;
  const gnuradioOnline = status?.gnuradio.reachable ?? false;

  return (
    <div className="space-y-8">
      <section className="relative overflow-hidden rounded-2xl border border-slate-800 bg-gradient-to-br from-slate-950 via-slate-900 to-cyan-950/40 px-6 py-10 md:px-10 md:py-12">
        <div className="absolute inset-0 opacity-30">
          <div className="absolute -top-24 right-0 h-64 w-64 rounded-full bg-cyan-500/20 blur-3xl" />
          <div className="absolute bottom-0 left-1/4 h-48 w-48 rounded-full bg-blue-600/20 blur-3xl" />
        </div>
        <div className="relative max-w-3xl">
          <p className="text-xs font-semibold uppercase tracking-widest text-cyan-400/90">
            Software Defined Radio · MCP
          </p>
          <h1 className="mt-3 text-3xl font-bold tracking-tight text-white md:text-4xl">
            Turn a USB stick into a radio lab
          </h1>
          <p className="mt-4 text-base text-slate-300 leading-relaxed md:text-lg">
            <strong className="text-white">SDR</strong> means your computer does
            the tuning — not a fixed FM chip. Plug in a dongle, see live
            spectrum and waterfall, listen to stations, and let AI control it
            through chat.
          </p>
          <p className="mt-2 text-sm text-slate-400">
            No dongle? Mock mode still shows FFT, waterfall, and demo audio.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Button
              asChild
              className="bg-cyan-600 hover:bg-cyan-500 text-white"
            >
              <Link to="/spectrum">
                Open Spectrum
                <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
            <Button
              asChild
              variant="outline"
              className="border-slate-600 text-slate-200 hover:bg-slate-800"
            >
              <Link to="/help">New here? Read Help</Link>
            </Button>
            <Button
              asChild
              variant="outline"
              className="border-slate-600 text-slate-200 hover:bg-slate-800"
            >
              <Link to="/chat">Try AI Command</Link>
            </Button>
          </div>
        </div>
        <div className="relative mt-10 grid gap-3 sm:grid-cols-3">
          <div className="rounded-xl border border-slate-700/60 bg-slate-950/50 p-4 backdrop-blur-sm">
            <Radio className="h-5 w-5 text-cyan-400" />
            <p className="mt-2 font-medium text-white">Listen</p>
            <p className="text-xs text-slate-400 mt-1">
              Tune FM (e.g. 100 MHz), hear audio in the browser
            </p>
          </div>
          <div className="rounded-xl border border-slate-700/60 bg-slate-950/50 p-4 backdrop-blur-sm">
            <Waves className="h-5 w-5 text-blue-400" />
            <p className="mt-2 font-medium text-white">See signals</p>
            <p className="text-xs text-slate-400 mt-1">
              FFT spectrum + scrolling waterfall
            </p>
          </div>
          <div className="rounded-xl border border-slate-700/60 bg-slate-950/50 p-4 backdrop-blur-sm">
            <Sparkles className="h-5 w-5 text-purple-400" />
            <p className="mt-2 font-medium text-white">Ask AI</p>
            <p className="text-xs text-slate-400 mt-1">
              “list devices”, “spectrum”, “tune bbc longwave”
            </p>
          </div>
        </div>
      </section>

      {error ? (
        <Card className="border-red-900/50 bg-red-950/20">
          <CardContent className="pt-6 text-red-300">
            Web API unreachable: {error}. Run `just dev` or `uv run sdr-mcp
            serve --http`.
          </CardContent>
        </Card>
      ) : null}

      {!hardwareOnline && mockActive ? (
        <Card className="border-cyan-900/40 bg-cyan-950/20">
          <CardContent className="pt-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <p className="font-medium text-cyan-200">Mock IQ active</p>
              <p className="text-sm text-slate-400 mt-1">
                Exploring without hardware — spectrum, waterfall, and demo audio
                work.
              </p>
            </div>
            <Button
              asChild
              variant="outline"
              className="border-cyan-800 text-cyan-200 shrink-0"
            >
              <Link to="/help">
                <HelpCircle className="h-4 w-4 mr-2" />
                Buying a dongle
              </Link>
            </Button>
          </CardContent>
        </Card>
      ) : null}

      <div>
        <h2 className="text-lg font-semibold text-white mb-1">Live status</h2>
        <p className="text-sm text-slate-400 mb-4">Refreshes every 5 seconds</p>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card className="border-slate-800 bg-slate-950/50">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-slate-200">
                RTL-SDR
              </CardTitle>
              <Radio
                className={`h-4 w-4 ${hardwareOnline ? "text-emerald-500" : mockActive ? "text-cyan-500" : "text-slate-500"}`}
              />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-white">
                {hardwareOnline
                  ? "Detected"
                  : mockActive
                    ? "Mock"
                    : "Not found"}
              </div>
              <p className="text-xs text-slate-400">
                {status?.hardware.device_count ?? 0} device(s)
              </p>
            </CardContent>
          </Card>

          <Card className="border-slate-800 bg-slate-950/50">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-slate-200">
                GNU Radio
              </CardTitle>
              <Satellite
                className={`h-4 w-4 ${gnuradioOnline ? "text-emerald-500" : "text-slate-500"}`}
              />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-white">
                {gnuradioOnline ? "Online" : "Offline"}
              </div>
              <p className="text-xs text-slate-400">
                Demod {status?.gnuradio.demod_running ? "running" : "idle"}
              </p>
            </CardContent>
          </Card>

          <Card className="border-slate-800 bg-slate-950/50">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-slate-200">
                Center Freq
              </CardTitle>
              <Activity className="h-4 w-4 text-purple-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-white">
                {status?.hardware.center_freq_mhz ?? 0} MHz
              </div>
              <p className="text-xs text-slate-400">
                {status?.hardware.initialized
                  ? "Initialized"
                  : "Not initialized"}
              </p>
            </CardContent>
          </Card>

          <Card className="border-slate-800 bg-slate-950/50">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-slate-200">
                MCP Bridge
              </CardTitle>
              <Cpu className="h-4 w-4 text-blue-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-white">Online</div>
              <p className="text-xs text-slate-400">Web API :10892</p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
