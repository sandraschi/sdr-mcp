import { useCallback, useEffect, useRef, useState } from "react";

export interface SpectrumData {
  frequencies: number[];
  spectrum: number[];
  waterfall: number[][];
  timestamp: number;
}

export interface SDRConfig {
  sdr_info: {
    center_freq: number;
    sample_rate: number;
    gain: string;
    available: boolean;
  };
  fft_size: number;
  sample_rate: number;
}

type ConnectionState = "disconnected" | "connecting" | "connected" | "error";

export function useSDRWebSocket(url: string = "ws://localhost:8765") {
  const wsRef = useRef<WebSocket | null>(null);
  const [connectionState, setConnectionState] =
    useState<ConnectionState>("disconnected");
  const [config, setConfig] = useState<SDRConfig | null>(null);
  const [latestSpectrum, setLatestSpectrum] = useState<SpectrumData | null>(
    null,
  );
  const onSpectrumRef = useRef<((data: SpectrumData) => void) | null>(null);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    setConnectionState("connecting");
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnectionState("connected");
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === "config") {
          setConfig(data as SDRConfig);
        } else if (data.frequencies && data.spectrum) {
          const spectrumData = data as SpectrumData;
          setLatestSpectrum(spectrumData);
          if (onSpectrumRef.current) {
            onSpectrumRef.current(spectrumData);
          }
        }
      } catch {
        // ignore parse errors
      }
    };

    ws.onerror = () => {
      setConnectionState("error");
    };

    ws.onclose = () => {
      setConnectionState("disconnected");
      wsRef.current = null;
    };
  }, [url]);

  const disconnect = useCallback(() => {
    wsRef.current?.close();
    wsRef.current = null;
    setConnectionState("disconnected");
  }, []);

  const sendCommand = useCallback(
    (command: string, params: Record<string, unknown> = {}) => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(
          JSON.stringify({ type: "command", command, params }),
        );
      }
    },
    [],
  );

  const onSpectrum = useCallback((cb: (data: SpectrumData) => void) => {
    onSpectrumRef.current = cb;
  }, []);

  useEffect(() => {
    return () => {
      wsRef.current?.close();
    };
  }, []);

  return {
    connectionState,
    config,
    latestSpectrum,
    connect,
    disconnect,
    sendCommand,
    onSpectrum,
  };
}
