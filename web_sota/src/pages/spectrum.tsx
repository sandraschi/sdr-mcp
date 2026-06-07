import { useCallback, useEffect, useRef, useState } from "react";
import { type SpectrumData, useSDRWebSocket } from "@/common/use-sdr-ws";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

function drawSpectrum(
  canvas: HTMLCanvasElement,
  data: SpectrumData,
  config: { centerFreq: number; sampleRate: number },
) {
  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  const { width, height } = canvas;
  const spectrum = data.spectrum;
  if (spectrum.length === 0) return;

  ctx.clearRect(0, 0, width, height);

  const minDb = -80;
  const maxDb = -20;

  ctx.beginPath();
  ctx.moveTo(0, height);

  const step = width / spectrum.length;
  for (let i = 0; i < spectrum.length; i++) {
    const x = i * step;
    const normalized = Math.max(
      0,
      Math.min(1, (spectrum[i] - minDb) / (maxDb - minDb)),
    );
    const y = height - normalized * height;
    ctx.lineTo(x, y);
  }
  ctx.lineTo(width, height);
  ctx.closePath();

  const gradient = ctx.createLinearGradient(0, 0, 0, height);
  gradient.addColorStop(0, "rgba(34, 211, 238, 0.6)");
  gradient.addColorStop(0.5, "rgba(59, 130, 246, 0.3)");
  gradient.addColorStop(1, "rgba(59, 130, 246, 0.05)");
  ctx.fillStyle = gradient;
  ctx.fill();

  ctx.strokeStyle = "#22d3ee";
  ctx.lineWidth = 1.5;
  ctx.beginPath();
  for (let i = 0; i < spectrum.length; i++) {
    const x = i * step;
    const normalized = Math.max(
      0,
      Math.min(1, (spectrum[i] - minDb) / (maxDb - minDb)),
    );
    const y = height - normalized * height;
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  }
  ctx.stroke();

  ctx.fillStyle = "rgba(148, 163, 184, 0.6)";
  ctx.font = "10px monospace";
  const freqSpan = config.sampleRate / 2 / 1e6;
  const centerFreq = config.centerFreq / 1e6;
  ctx.fillText(`${(centerFreq - freqSpan).toFixed(1)} MHz`, 4, height - 4);
  ctx.textAlign = "center";
  ctx.fillText(`${centerFreq.toFixed(1)} MHz`, width / 2, height - 4);
  ctx.textAlign = "right";
  ctx.fillText(
    `${(centerFreq + freqSpan).toFixed(1)} MHz`,
    width - 4,
    height - 4,
  );
}

export function Spectrum() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const {
    connectionState,
    config,
    connect,
    disconnect,
    sendCommand,
    onSpectrum,
    audioEnabled,
    audioActive,
    toggleAudio,
  } = useSDRWebSocket();
  const [frequency, setFrequency] = useState("100.0");
  const [gain, setGain] = useState("auto");
  const animRef = useRef<number>(0);

  const draw = useCallback(
    (data: SpectrumData) => {
      if (canvasRef.current && config) {
        drawSpectrum(canvasRef.current, data, {
          centerFreq: config.sdr_info.center_freq,
          sampleRate: config.sdr_info.sample_rate,
        });
      }
    },
    [config],
  );

  useEffect(() => {
    onSpectrum(draw);
  }, [onSpectrum, draw]);

  useEffect(() => {
    return () => cancelAnimationFrame(animRef.current);
  }, []);

  const handleSetFrequency = () => {
    const freq = parseFloat(frequency);
    if (!Number.isNaN(freq)) {
      sendCommand("set_frequency", { frequency: freq * 1e6 });
    }
  };

  const handleSetGain = () => {
    sendCommand("set_gain", { gain });
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">
            Spectrum Analyzer
          </h2>
          <p className="text-slate-400">
            Real-time FFT spectrum with FM audio (tune to a station, e.g. 100.0
            MHz)
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span
            className={`h-2 w-2 rounded-full ${
              connectionState === "connected"
                ? "bg-emerald-500"
                : connectionState === "connecting"
                  ? "bg-yellow-500"
                  : connectionState === "error"
                    ? "bg-red-500"
                    : "bg-slate-500"
            }`}
          />
          <span className="text-xs text-slate-400">{connectionState}</span>
          {connectionState === "connected" ? (
            <Button
              size="sm"
              variant="outline"
              onClick={() => toggleAudio(!audioEnabled)}
              className="border-slate-700 text-slate-300"
            >
              {audioEnabled
                ? audioActive
                  ? "Audio on"
                  : "Audio idle"
                : "Muted"}
            </Button>
          ) : null}
          {connectionState !== "connected" ? (
            <Button
              size="sm"
              variant="outline"
              onClick={connect}
              className="border-slate-700 text-slate-300"
            >
              Connect
            </Button>
          ) : (
            <Button
              size="sm"
              variant="outline"
              onClick={disconnect}
              className="border-slate-700 text-slate-300"
            >
              Disconnect
            </Button>
          )}
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card className="border-slate-800 bg-slate-950/50 col-span-2">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">
              FFT Plot
            </CardTitle>
          </CardHeader>
          <CardContent>
            <canvas
              ref={canvasRef}
              width={700}
              height={300}
              className="w-full h-[300px] rounded border border-slate-800 bg-slate-900/50"
            />
            {connectionState !== "connected" && (
              <div className="flex items-center justify-center h-[300px] text-slate-500 text-sm">
                Click Connect to start receiving spectrum data
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">
              Controls
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label htmlFor="center-freq" className="text-xs text-slate-400">
                Center Frequency (MHz)
              </label>
              <div className="flex gap-2">
                <Input
                  id="center-freq"
                  className="bg-slate-900 border-slate-800 text-slate-100 font-mono text-sm"
                  value={frequency}
                  onChange={(e) => setFrequency(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleSetFrequency()}
                />
                <Button
                  size="sm"
                  variant="outline"
                  onClick={handleSetFrequency}
                  className="border-slate-700 text-slate-300"
                >
                  Set
                </Button>
              </div>
            </div>
            <div className="space-y-2">
              <label htmlFor="gain-slider" className="text-xs text-slate-400">
                Gain ({gain})
              </label>
              <input
                id="gain-slider"
                type="range"
                min="0"
                max="49.6"
                step="0.1"
                defaultValue={0}
                onChange={(e) => {
                  setGain(e.target.value);
                }}
                onMouseUp={handleSetGain}
                className="w-full accent-blue-500"
              />
            </div>
            {config && (
              <div className="space-y-1 text-xs text-slate-500 font-mono">
                <p>FFT: {config.fft_size} pts</p>
                <p>
                  Rate: {(config.sdr_info.sample_rate / 1e6).toFixed(1)} Msps
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
