import { Activity, Cpu, HardDrive, Radio, Satellite } from "lucide-react";
import { useEffect, useState } from "react";
import { fetchStatus, type StatusSnapshot } from "@/common/api-client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function Status() {
  const [status, setStatus] = useState<StatusSnapshot | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void fetchStatus()
      .then(setStatus)
      .catch((err) =>
        setError(err instanceof Error ? err.message : String(err)),
      );
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white">
          System Status
        </h2>
        <p className="text-slate-400">Live telemetry from Web API bridge</p>
      </div>

      {error ? (
        <Card className="border-red-900/50 bg-red-950/20">
          <CardContent className="pt-6 text-red-300">{error}</CardContent>
        </Card>
      ) : null}

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">
              Hardware
            </CardTitle>
            <Radio className="h-4 w-4 text-emerald-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">
              {status?.hardware.available ? "Present" : "Missing"}
            </div>
          </CardContent>
        </Card>
        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">
              GNU Radio
            </CardTitle>
            <Satellite className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">
              {status?.gnuradio.reachable ? "Reachable" : "Down"}
            </div>
          </CardContent>
        </Card>
        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">
              Demod
            </CardTitle>
            <Cpu className="h-4 w-4 text-purple-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">
              {status?.gnuradio.demod_running ? "Running" : "Idle"}
            </div>
          </CardContent>
        </Card>
        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">
              Devices
            </CardTitle>
            <HardDrive className="h-4 w-4 text-orange-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">
              {status?.hardware.device_count ?? 0}
            </div>
          </CardContent>
        </Card>
      </div>

      <Card className="border-slate-800 bg-slate-950/50">
        <CardHeader>
          <CardTitle className="text-white">Health Check Details</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4 font-mono text-sm text-slate-400">
            <div className="flex justify-between border-b border-slate-800 pb-2">
              <span>Service: Web API</span>
              <span className={error ? "text-red-400" : "text-emerald-500"}>
                {error ? "OFFLINE" : "OPERATIONAL"}
              </span>
            </div>
            <div className="flex justify-between border-b border-slate-800 pb-2">
              <span>Hardware: RTL-SDR</span>
              <span
                className={
                  status?.hardware.available
                    ? "text-emerald-500"
                    : "text-yellow-500"
                }
              >
                {status?.hardware.available ? "CONNECTED" : "NOT FOUND"}
              </span>
            </div>
            <div className="flex justify-between border-b border-slate-800 pb-2">
              <span>Mock IQ</span>
              <span
                className={
                  status?.mock?.active ? "text-cyan-400" : "text-slate-500"
                }
              >
                {status?.mock?.active
                  ? `ACTIVE (${status.mock.setting})`
                  : (status?.mock?.setting ?? "off")}
              </span>
            </div>
            <div className="flex justify-between border-b border-slate-800 pb-2">
              <span>Sidecar: GNU Radio</span>
              <span
                className={
                  status?.gnuradio.reachable
                    ? "text-emerald-500"
                    : "text-yellow-500"
                }
              >
                {status?.gnuradio.reachable ? "REACHABLE" : "UNREACHABLE"}
              </span>
            </div>
            <div className="flex justify-between">
              <span>Activity</span>
              <Activity className="h-4 w-4 text-slate-500" />
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
