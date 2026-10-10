// Fleet API base: same-origin relative ("") by default so browser tabs on any
// hostname (localhost, LAN, Tailscale) ride the vite proxy to the registry
// backend (sdr-mcp 11119, see mcp-central-docs/operations/WEBAPP_PORTS.md).
// Absolute URL only inside Tauri WebView. Registry single source of truth:
// operations/WEBAPP_PORTS.md (frontend 11118, backend 11119, gnuradio 11223).
declare global {
  interface Window {
    __TAURI__?: unknown;
    __TAURI_INTERNALS__?: unknown;
  }
}

function isTauri(): boolean {
  if (typeof window === "undefined") return false;
  return (
    "__TAURI__" in window ||
    "__TAURI_INTERNALS__" in window ||
    window.location.protocol === "tauri:"
  );
}

export const API_BASE: string = isTauri() ? "http://127.0.0.1:11119" : "";
