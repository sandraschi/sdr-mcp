import { Bot, Loader2, Send, User } from "lucide-react";
import { useState } from "react";
import { sendChat } from "@/common/api-client";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  text: string;
  meta?: string;
};

function formatResult(result: Record<string, unknown>): string {
  const conversation = result.conversation as
    | Record<string, unknown>
    | undefined;
  if (conversation?.message) {
    return String(conversation.message);
  }
  if (result.message) {
    return String(result.message);
  }
  return JSON.stringify(result, null, 2);
}

export function Chat() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "boot",
      role: "assistant",
      text: "Ready. Try: list devices, tune 101.5 mhz, spectrum, gnuradio health, tune bbc longwave.",
    },
  ]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);

  async function handleSend() {
    const text = input.trim();
    if (!text || busy) {
      return;
    }

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
  }

  return (
    <div className="flex h-[calc(100vh-8rem)] flex-col space-y-4">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white">
          Command Interface
        </h2>
        <p className="text-slate-400">
          Natural language commands routed to MCP portmanteau tools
        </p>
      </div>

      <Card className="flex-1 border-slate-800 bg-slate-950/50 flex flex-col overflow-hidden">
        <CardContent className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((message) => (
            <div key={message.id} className="flex gap-3">
              <div
                className={`h-8 w-8 rounded-full flex items-center justify-center border ${
                  message.role === "user"
                    ? "bg-slate-800 border-slate-700"
                    : "bg-blue-900/20 border-blue-800"
                }`}
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
                    className={`text-sm font-medium ${
                      message.role === "user"
                        ? "text-slate-200"
                        : "text-blue-400"
                    }`}
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
        </CardContent>
        <div className="p-4 border-t border-slate-800 bg-slate-900/30">
          <div className="flex gap-2">
            <input
              className="flex-1 bg-slate-950 border border-slate-800 rounded-md px-4 py-2 text-sm text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
              placeholder="list devices, tune 101.5 mhz, spectrum, gnuradio health..."
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  void handleSend();
                }
              }}
              disabled={busy}
            />
            <Button
              size="icon"
              className="bg-blue-600 hover:bg-blue-700"
              onClick={() => void handleSend()}
              disabled={busy}
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
