const DEFAULT_API_BASE = "http://127.0.0.1:10892";

export function getApiBase(): string {
  const stored = localStorage.getItem("sdr-api-base");
  if (stored) {
    return stored;
  }
  if (typeof window !== "undefined" && window.location.port === "10890") {
    return "";
  }
  return DEFAULT_API_BASE;
}

export function setApiBase(value: string): void {
  localStorage.setItem("sdr-api-base", value);
}

export type StatusSnapshot = {
  success: boolean;
  mcp: { online: boolean };
  hardware: {
    available: boolean;
    device_count: number;
    devices: Array<{ index: number; serial: string }>;
    initialized: boolean;
    center_freq_mhz: number;
  };
  gnuradio: {
    reachable: boolean;
    service_url: string;
    demod_running: boolean;
    config: Record<string, unknown>;
  };
  mock?: {
    active: boolean;
    setting: string;
  };
};

export async function fetchStatus(): Promise<StatusSnapshot> {
  const response = await fetch(`${getApiBase()}/api/status`);
  if (!response.ok) {
    throw new Error(`Status request failed: ${response.status}`);
  }
  return response.json();
}

export async function sendChat(message: string): Promise<{
  success: boolean;
  tool: string;
  params: Record<string, unknown>;
  result: Record<string, unknown>;
}> {
  const response = await fetch(`${getApiBase()}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });
  if (!response.ok) {
    throw new Error(`Chat request failed: ${response.status}`);
  }
  return response.json();
}

export async function invokeTool(
  tool: string,
  params: Record<string, unknown>,
): Promise<Record<string, unknown>> {
  const response = await fetch(`${getApiBase()}/api/invoke`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ tool, params }),
  });
  if (!response.ok) {
    throw new Error(`Invoke request failed: ${response.status}`);
  }
  const payload = await response.json();
  return payload.result;
}

export async function testConnection(baseUrl?: string): Promise<boolean> {
  const url = baseUrl ?? getApiBase();
  const response = await fetch(`${url}/api/health`);
  return response.ok;
}
