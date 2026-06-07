import { useState } from "react";
import { getApiBase, setApiBase, testConnection } from "@/common/api-client";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export function Settings() {
  const [apiBase, setApiBaseState] = useState(getApiBase());
  const [testResult, setTestResult] = useState<string | null>(null);

  async function handleTest() {
    const ok = await testConnection(apiBase);
    setTestResult(ok ? "Connected" : "Failed");
  }

  function handleSave() {
    setApiBase(apiBase);
    setTestResult("Saved");
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white">
          Configuration
        </h2>
        <p className="text-slate-400">Manage Web API bridge connection</p>
      </div>

      <Card className="border-slate-800 bg-slate-950/50">
        <CardHeader>
          <CardTitle className="text-white">Web API Bridge</CardTitle>
          <CardDescription className="text-slate-400">
            REST bridge on port 10892 (started with `just dev`)
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-2">
            <Label className="text-slate-300">API Base URL</Label>
            <Input
              className="bg-slate-900 border-slate-800 text-slate-100"
              value={apiBase}
              onChange={(event) => setApiBaseState(event.target.value)}
            />
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              className="border-slate-800 text-slate-300 hover:bg-slate-800"
              onClick={() => void handleTest()}
            >
              Test Connection
            </Button>
            <Button
              variant="outline"
              className="border-slate-800 text-slate-300 hover:bg-slate-800"
              onClick={handleSave}
            >
              Save
            </Button>
          </div>
          {testResult ? (
            <p className="text-sm text-slate-400">{testResult}</p>
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
}
