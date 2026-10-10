import { useEffect, useState } from "react";
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
import { API_BASE } from "@/lib/api";

function LLMSettings() {
  const [providers, setProviders] = useState<
    Record<string, { name: string }[]>
  >({});
  const [selectedProvider, setSelectedProvider] = useState("ollama");
  const [selectedModel, setSelectedModel] = useState("");
  const [status, setStatus] = useState<"loading" | "ready" | "error">(
    "loading",
  );
  useEffect(() => {
    fetch(`${API_BASE}/api/llm/providers`)
      .then((r) => r.json())
      .then((d) => {
        setProviders(d);
        const savedP = localStorage.getItem("llm_provider") || "ollama";
        const savedM = localStorage.getItem("llm_model") || "";
        setSelectedProvider(savedP);
        const models = d[savedP === "ollama" ? "ollama" : "lm_studio"] || [];
        setSelectedModel(
          savedM && models.some((m: { name: string }) => m.name === savedM)
            ? savedM
            : models[0]?.name || "",
        );
        setStatus(models.length > 0 ? "ready" : "error");
      })
      .catch(() => {
        setProviders({ ollama: [{ name: "llama3.2:3b" }] });
        setSelectedModel(localStorage.getItem("llm_model") || "llama3.2:3b");
        setStatus("ready");
      });
  }, []);
  const save = (p: string, m: string) => {
    localStorage.setItem("llm_provider", p);
    localStorage.setItem("llm_model", m);
  };
  const models =
    providers[selectedProvider === "ollama" ? "ollama" : "lm_studio"] || [];
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-950/50 p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-slate-200">Local LLM</h3>
        <span
          className={`inline-flex items-center gap-1.5 text-xs ${status === "ready" ? "text-emerald-400" : "text-amber-400"}`}
        >
          <span
            className={`h-2 w-2 rounded-full ${status === "ready" ? "bg-emerald-400" : "bg-amber-400"}`}
          />
          {status === "ready" ? "connected" : "probing"}
        </span>
      </div>
      <select
        className="h-9 w-full rounded-md border border-slate-700 bg-slate-900 px-3 text-sm text-slate-200"
        value={selectedProvider}
        onChange={(e) => {
          setSelectedProvider(e.target.value);
          save(e.target.value, "");
        }}
      >
        <option value="ollama">Ollama</option>
        <option value="lm_studio">LM Studio</option>
      </select>
      <select
        className="h-9 w-full rounded-md border border-slate-700 bg-slate-900 px-3 text-sm text-slate-200"
        value={selectedModel}
        onChange={(e) => {
          setSelectedModel(e.target.value);
          save(selectedProvider, e.target.value);
        }}
      >
        {models.map((m) => (
          <option key={m.name} value={m.name}>
            {m.name}
          </option>
        ))}
      </select>
      <p className="text-xs text-slate-500">
        Used by AI tools. Saved to browser storage.
      </p>
    </div>
  );
}

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
            REST backend on port 11119 (registry; served by start.ps1)
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

      <Card className="border-slate-800 bg-slate-950/50">
        <CardHeader>
          <CardTitle className="text-white">LLM Provider</CardTitle>
          <CardDescription className="text-slate-400">
            Local model endpoint configuration
          </CardDescription>
        </CardHeader>
        <CardContent>
          <LLMSettings />
        </CardContent>
      </Card>
    </div>
  );
}
