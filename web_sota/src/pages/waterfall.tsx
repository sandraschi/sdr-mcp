import { useCallback, useEffect, useRef } from "react";
import { type SpectrumData, useSDRWebSocket } from "@/common/use-sdr-ws";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

function drawWaterfall(canvas: HTMLCanvasElement, data: SpectrumData) {
  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  const { width, height } = canvas;
  const spectrum = data.spectrum;
  if (spectrum.length === 0) return;

  const imageData = ctx.createImageData(width, 1);
  const step = spectrum.length / width;

  for (let x = 0; x < width; x++) {
    const idx = Math.min(Math.floor(x * step), spectrum.length - 1);
    const val = Math.max(0, Math.min(1, (spectrum[idx] + 100) / 60));

    let r: number, g: number, b: number;
    if (val < 0.25) {
      r = 0;
      g = 0;
      b = 128 + val * 512;
    } else if (val < 0.5) {
      r = 0;
      g = (val - 0.25) * 1024;
      b = 255;
    } else if (val < 0.75) {
      r = (val - 0.5) * 1024;
      g = 255;
      b = 255 - (val - 0.5) * 1024;
    } else {
      r = 255;
      g = 255 - (val - 0.75) * 1024;
      b = 0;
    }

    const pixelIdx = x * 4;
    imageData.data[pixelIdx] = Math.min(255, Math.max(0, r));
    imageData.data[pixelIdx + 1] = Math.min(255, Math.max(0, g));
    imageData.data[pixelIdx + 2] = Math.min(255, Math.max(0, b));
    imageData.data[pixelIdx + 3] = 255;
  }

  ctx.drawImage(canvas, 0, -1);
  ctx.putImageData(imageData, 0, height - 1);

  ctx.fillStyle = "rgba(148, 163, 184, 0.6)";
  ctx.font = "10px monospace";
  ctx.fillText(`${(data.frequencies[0] / 1e6).toFixed(2)} MHz`, 4, 12);
  ctx.textAlign = "right";
  ctx.fillText(
    `${(data.frequencies[data.frequencies.length - 1] / 1e6).toFixed(2)} MHz`,
    width - 4,
    12,
  );
}

export function Waterfall() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const {
    connectionState,
    connect,
    disconnect,
    onSpectrum,
    audioEnabled,
    audioActive,
    toggleAudio,
  } = useSDRWebSocket();
  const animRef = useRef<number>(0);

  const draw = useCallback((data: SpectrumData) => {
    if (canvasRef.current) {
      drawWaterfall(canvasRef.current, data);
    }
  }, []);

  useEffect(() => {
    onSpectrum(draw);
  }, [onSpectrum, draw]);

  useEffect(() => {
    return () => cancelAnimationFrame(animRef.current);
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">
            Waterfall Display
          </h2>
          <p className="text-slate-400">
            Time-frequency view with FM audio from the same WebSocket stream
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

      <Card className="border-slate-800 bg-slate-950/50">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-slate-200">
            Waterfall
          </CardTitle>
        </CardHeader>
        <CardContent>
          <canvas
            ref={canvasRef}
            width={700}
            height={400}
            className="w-full h-[400px] rounded border border-slate-800 bg-slate-950"
          />
          {connectionState !== "connected" && (
            <div className="flex items-center justify-center h-[400px] text-slate-500 text-sm -mt-[400px]">
              Click Connect to start receiving waterfall data
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
