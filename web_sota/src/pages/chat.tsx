import {
  Bot,
  Download,
  Eraser,
  Loader2,
  Send,
  Sparkles,
  User,
  Wifi,
  WifiOff,
} from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { sendChat } from "@/common/api-client";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

const LS_HISTORY = "sdr-mcp-chat-history";
const LS_PERSONALITY = "sdr-mcp-chat-personality";
const MAX_HISTORY = 100;

type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  text: string;
  meta?: string;
};

const PERSONALITIES = [
  {
    id: "operator",
    label: "Radio Operator",
    prompt:
      "You are a radio operator. Be precise, technical, and use radio jargon.",
  },
  {
    id: "researcher",
    label: "Signal Researcher",
    prompt:
      "You are a signal processing researcher. Explain theory and practical implications.",
  },
  {
    id: "teacher",
    label: "RF Educator",
    prompt:
      "You are an RF engineering educator. Explain concepts clearly with analogies.",
  },
  { id: "custom", label: "Custom", prompt: "" },
];

const EXAMPLE_PROMPTS = [
  "list devices",
  "tune 101.5 mhz",
  "show spectrum",
  "gnuradio health",
  "tune bbc longwave",
  "scan fm band",
  "demodulate current frequency",
  "what devices are available?",
  "start recording",
];

function formatResult(result: Record<string, unknown>): string {
  const conversation = result.conversation as
    | Record<string, unknown>
    | undefined;
  if (conversation?.message) return String(conversation.message);
  if (result.message) return String(result.message);
  return JSON.stringify(result, null, 2);
}

function loadHistory(): ChatMessage[] {
  try {
    const saved = localStorage.getItem(LS_HISTORY);
    if (saved) return JSON.parse(saved);
  } catch {
    /* ignore */
  }
  return [];
}

export function Chat() {
  const [messages, setMessages] = useState<ChatMessage[]>(() => {
    const saved = loadHistory();
    if (saved.length > 0) return saved;
    return [
      {
        id: "boot",
        role: "assistant",
        text: "Ready. Try: list devices, tune 101.5 mhz, spectrum, gnuradio health, tune bbc longwave.",
      },
    ];
  });
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [personality, setPersonality] = useState(
    () => localStorage.getItem(LS_PERSONALITY) || "operator",
  );
  const [backendOk, setBackendOk] = useState<boolean | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    try {
      localStorage.setItem(
        LS_HISTORY,
        JSON.stringify(messages.slice(-MAX_HISTORY)),
      );
    } catch {
      /* ignore */
    }
  }, [messages]);

  useEffect(() => {
    localStorage.setItem(LS_PERSONALITY, personality);
  }, [personality]);

  useEffect(() => {
    fetch("/api/health")
      .then((r) => setBackendOk(r.ok))
      .catch(() => setBackendOk(false));
  }, []);

  // biome-ignore lint/correctness/useExhaustiveDependencies: rescroll on new messages by design
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = useCallback(async () => {
    const text = input.trim();
    if (!text || busy) return;

    const userMessage: ChatMessage = {
      id: `${Date.now()}-user`,
      role: "user",
      text,
    };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setBusy(true);

    try {
      const response = await sendChat(text);
      const assistantMessage: ChatMessage = {
        id: `${Date.now()}-assistant`,
        role: "assistant",
        text: formatResult(response.result),
        meta: `${response.tool}(${Object.entries(response.params)
          .map(([key, value]) => `${key}=${value}`)
          .join(", ")})`,
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          id: `${Date.now()}-error`,
          role: "assistant",
          text: `Bridge error: ${error instanceof Error ? error.message : String(error)}. Start backend with: just dev`,
        },
      ]);
    } finally {
      setBusy(false);
    }
  }, [input, busy]);

  const handleClear = useCallback(() => {
    setMessages([
      {
        id: "boot",
        role: "assistant",
        text: "Ready. Try: list devices, tune 101.5 mhz, spectrum, gnuradio health, tune bbc longwave.",
      },
    ]);
    try {
      localStorage.removeItem(LS_HISTORY);
    } catch {
      /* ignore */
    }
  }, []);

  const handleExport = useCallback(() => {
    const text = messages
      .map((m) => `[${m.role.toUpperCase()}] ${m.text}`)
      .join("\n\n");
    const blob = new Blob([text], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `sdr-mcp-chat-${new Date().toISOString().slice(0, 10)}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  }, [messages]);

  return (
    <div
      data-testid="chat-page"
      className="flex h-[calc(100vh-8rem)] flex-col space-y-4"
    >
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">
            Command Interface
          </h2>
          <p className="text-slate-400">
            Natural language commands routed to MCP portmanteau tools
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-[10px] uppercase tracking-wider text-slate-500 font-mono bg-slate-800 px-2 py-0.5 rounded">
            skill:sdr-operator
          </span>
          <select
            data-testid="personality-select"
            value={personality}
            onChange={(e) => setPersonality(e.target.value)}
            className="bg-slate-800 text-xs text-slate-300 border border-slate-700 rounded px-2 py-1"
          >
            {PERSONALITIES.map((p) => (
              <option key={p.id} value={p.id}>
                {p.label}
              </option>
            ))}
          </select>
          {backendOk === true && (
            <span className="flex items-center gap-1 text-xs text-emerald-400">
              <Wifi className="w-3 h-3" />
              Online
            </span>
          )}
          {backendOk === false && (
            <span className="flex items-center gap-1 text-xs text-red-400">
              <WifiOff className="w-3 h-3" />
              Offline
            </span>
          )}
          {backendOk === null && (
            <span className="flex items-center gap-1 text-xs text-slate-500">
              <Loader2 className="w-3 h-3 animate-spin" />
              Checking...
            </span>
          )}
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        {EXAMPLE_PROMPTS.map((p) => (
          <button
            type="button"
            key={p}
            onClick={() => {
              setInput(p);
            }}
            className="flex items-center gap-1 px-2.5 py-1 rounded-full text-[10px] border border-slate-700 text-slate-400 hover:text-white hover:border-slate-500 transition-colors bg-slate-900/50"
          >
            <Sparkles className="w-2.5 h-2.5" />
            {p}
          </button>
        ))}
      </div>

      <Card
        data-testid="chat-messages"
        className="flex-1 border-slate-800 bg-slate-950/50 flex flex-col overflow-hidden"
      >
        <CardContent className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((message) => (
            <div key={message.id} className="flex gap-3">
              <div
                className={`h-8 w-8 rounded-full flex items-center justify-center border ${message.role === "user" ? "bg-slate-800 border-slate-700" : "bg-blue-900/20 border-blue-800"}`}
              >
                {message.role === "user" ? (
                  <User className="h-4 w-4 text-slate-400" />
                ) : (
                  <Bot className="h-4 w-4 text-blue-400" />
                )}
              </div>
              <div className="flex-1 space-y-1">
                <div className="flex items-center gap-2">
                  <span
                    className={`text-sm font-medium ${message.role === "user" ? "text-slate-200" : "text-blue-400"}`}
                  >
                    {message.role === "user" ? "Operator" : "SDR MCP"}
                  </span>
                  {message.meta ? (
                    <span className="text-xs text-slate-500 font-mono">
                      {message.meta}
                    </span>
                  ) : null}
                </div>
                <pre className="text-sm text-slate-300 bg-slate-900/50 p-3 rounded-md border border-slate-800 whitespace-pre-wrap font-sans">
                  {message.text}
                </pre>
              </div>
            </div>
          ))}
          {busy && (
            <div className="flex gap-3">
              <div className="h-8 w-8 rounded-full flex items-center justify-center border border-blue-800 bg-blue-900/20">
                <Bot className="h-4 w-4 text-blue-400" />
              </div>
              <div className="flex items-center gap-2 text-sm text-slate-500">
                <Loader2 className="h-4 w-4 animate-spin" /> Processing...
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </CardContent>
        <div className="p-4 border-t border-slate-800 bg-slate-900/30">
          <div className="flex gap-2 mb-2">
            <div className="flex gap-1">
              <Button
                data-testid="chat-export"
                size="icon"
                variant="ghost"
                onClick={handleExport}
                disabled={messages.length === 0}
                className="h-8 w-8 text-slate-500"
                title="Export chat"
              >
                <Download className="h-3.5 w-3.5" />
              </Button>
              <Button
                data-testid="chat-clear"
                size="icon"
                variant="ghost"
                onClick={handleClear}
                disabled={messages.length <= 1}
                className="h-8 w-8 text-slate-500"
                title="Clear chat"
              >
                <Eraser className="h-3.5 w-3.5" />
              </Button>
            </div>
          </div>
          <div className="flex gap-2">
            <input
              data-testid="chat-input"
              className="flex-1 bg-slate-950 border border-slate-800 rounded-md px-4 py-2 text-sm text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
              placeholder="list devices, tune 101.5 mhz, spectrum, gnuradio health..."
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter") void handleSend();
              }}
              disabled={busy}
            />
            <Button
              data-testid="chat-send"
              size="icon"
              className="bg-blue-600 hover:bg-blue-700"
              onClick={() => void handleSend()}
              disabled={busy || !input.trim()}
            >
              {busy ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
}
