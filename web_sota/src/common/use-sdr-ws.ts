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
  audio?: {
    enabled: boolean;
    sample_rate: number;
    mode: string;
    sidecar_active?: boolean;
  };
}

type ConnectionState = "disconnected" | "connecting" | "connected" | "error";

function createPcmPlayer(sampleRate: number) {
  const AudioCtx =
    window.AudioContext ||
    (window as unknown as { webkitAudioContext?: typeof AudioContext })
      .webkitAudioContext;
  if (!AudioCtx) {
    return null;
  }
  const ctx = new AudioCtx({ sampleRate });
  let nextTime = ctx.currentTime;

  return {
    context: ctx,
    play(samples: Float32Array) {
      if (ctx.state === "suspended") {
        void ctx.resume();
      }
      const buffer = ctx.createBuffer(1, samples.length, sampleRate);
      buffer.copyToChannel(samples, 0);
      const src = ctx.createBufferSource();
      src.buffer = buffer;
      src.connect(ctx.destination);
      if (nextTime < ctx.currentTime) {
        nextTime = ctx.currentTime + 0.02;
      }
      src.start(nextTime);
      nextTime += buffer.duration;
    },
    stop() {
      void ctx.close();
    },
  };
}

export function useSDRWebSocket(url: string = "ws://localhost:8765") {
  const wsRef = useRef<WebSocket | null>(null);
  const [connectionState, setConnectionState] =
    useState<ConnectionState>("disconnected");
  const [config, setConfig] = useState<SDRConfig | null>(null);
  const [latestSpectrum, setLatestSpectrum] = useState<SpectrumData | null>(
    null,
  );
  const [audioEnabled, setAudioEnabled] = useState(true);
  const [audioActive, setAudioActive] = useState(false);
  const onSpectrumRef = useRef<((data: SpectrumData) => void) | null>(null);
  const playerRef = useRef<ReturnType<typeof createPcmPlayer> | null>(null);
  const audioEnabledRef = useRef(true);

  useEffect(() => {
    audioEnabledRef.current = audioEnabled;
  }, [audioEnabled]);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    setConnectionState("connecting");
    const ws = new WebSocket(url);
    ws.binaryType = "arraybuffer";
    wsRef.current = ws;

    ws.onopen = () => {
      setConnectionState("connected");
    };

    ws.onmessage = (event) => {
      if (typeof event.data === "string") {
        try {
          const data = JSON.parse(event.data);
          if (data.type === "config") {
            setConfig(data as SDRConfig);
            const rate = data.audio?.sample_rate ?? 48_000;
            playerRef.current?.stop();
            playerRef.current = createPcmPlayer(rate);
            if (data.audio?.enabled === false) {
              setAudioEnabled(false);
            }
          } else if (data.frequencies && data.spectrum) {
            const spectrumData = data as SpectrumData;
            setLatestSpectrum(spectrumData);
            onSpectrumRef.current?.(spectrumData);
          }
        } catch {
          // ignore parse errors
        }
        return;
      }

      if (!audioEnabledRef.current || !playerRef.current) {
        return;
      }

      const buffer =
        event.data instanceof ArrayBuffer
          ? event.data
          : event.data instanceof Blob
            ? null
            : null;
      if (!buffer) {
        if (event.data instanceof Blob) {
          void event.data.arrayBuffer().then((ab) => {
            if (!audioEnabledRef.current || !playerRef.current) return;
            const pcm = new Float32Array(ab);
            if (pcm.length > 0) {
              setAudioActive(true);
              playerRef.current.play(pcm);
            }
          });
        }
        return;
      }

      const pcm = new Float32Array(buffer);
      if (pcm.length > 0) {
        setAudioActive(true);
        playerRef.current.play(pcm);
      }
    };

    ws.onerror = () => {
      setConnectionState("error");
    };

    ws.onclose = () => {
      setConnectionState("disconnected");
      wsRef.current = null;
      playerRef.current?.stop();
      playerRef.current = null;
      setAudioActive(false);
    };
  }, [url]);

  const disconnect = useCallback(() => {
    wsRef.current?.close();
    wsRef.current = null;
    setConnectionState("disconnected");
    playerRef.current?.stop();
    playerRef.current = null;
    setAudioActive(false);
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

  const toggleAudio = useCallback(
    (enabled: boolean) => {
      setAudioEnabled(enabled);
      sendCommand("set_audio", { enabled });
      if (!enabled) {
        setAudioActive(false);
      }
    },
    [sendCommand],
  );

  const onSpectrum = useCallback((cb: (data: SpectrumData) => void) => {
    onSpectrumRef.current = cb;
  }, []);

  useEffect(() => {
    return () => {
      wsRef.current?.close();
      playerRef.current?.stop();
    };
  }, []);

  return {
    connectionState,
    config,
    latestSpectrum,
    audioEnabled,
    audioActive,
    connect,
    disconnect,
    sendCommand,
    toggleAudio,
    onSpectrum,
  };
}
