import type { ReactNode } from "react";
import { Link } from "react-router-dom";

export type HelpTab = {
  id: string;
  label: string;
  content: ReactNode;
};

const docLink = (path: string, label: string) => (
  <a
    href={`https://github.com/sandraschi/sdr-mcp/blob/main/${path}`}
    target="_blank"
    rel="noreferrer"
    className="text-cyan-400 hover:text-cyan-300 underline-offset-2 hover:underline"
  >
    {label}
  </a>
);

export const HELP_TABS: HelpTab[] = [
  {
    id: "start",
    label: "Start here",
    content: (
      <div className="space-y-4 text-sm text-slate-300 leading-relaxed">
        <p className="text-base text-white font-medium">
          SDR = Software Defined Radio — a USB stick that lets your computer
          listen to radio waves.
        </p>
        <p>
          A normal FM radio is built for one band. An SDR captures raw signals
          and your PC (or AI assistant via MCP) decides what to do with them:
          show a spectrum, draw a waterfall, tune to FM, or search station
          databases.
        </p>
        <div className="grid gap-3 md:grid-cols-3">
          <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-4">
            <p className="font-semibold text-cyan-300">1. Plug in</p>
            <p className="mt-1 text-slate-400">
              RTL-SDR USB dongle (~€30), or skip hardware and use mock mode
              (auto when no dongle).
            </p>
          </div>
          <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-4">
            <p className="font-semibold text-cyan-300">2. Open Spectrum</p>
            <p className="mt-1 text-slate-400">
              <Link to="/spectrum" className="text-cyan-400 hover:underline">
                Connect
              </Link>{" "}
              — see live FFT and hear FM audio.
            </p>
          </div>
          <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-4">
            <p className="font-semibold text-cyan-300">3. Ask AI</p>
            <p className="mt-1 text-slate-400">
              <Link to="/chat" className="text-cyan-400 hover:underline">
                AI Command
              </Link>{" "}
              — “tune 100 mhz”, “spectrum”, “list devices”.
            </p>
          </div>
        </div>
        <p>
          Deep dive:{" "}
          {docLink("docs/SDR_TECHNOLOGY.md", "SDR Technology primer")}
        </p>
      </div>
    ),
  },
  {
    id: "concepts",
    label: "Radio basics",
    content: (
      <div className="space-y-4 text-sm text-slate-300">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-slate-800 text-slate-400">
              <th className="py-2 pr-4">Term</th>
              <th className="py-2">Plain English</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            <tr>
              <td className="py-2 font-mono text-cyan-300">Frequency</td>
              <td className="py-2">Where on the dial you listen (MHz).</td>
            </tr>
            <tr>
              <td className="py-2 font-mono text-cyan-300">FFT / Spectrum</td>
              <td className="py-2">Graph of signal strength vs frequency.</td>
            </tr>
            <tr>
              <td className="py-2 font-mono text-cyan-300">Waterfall</td>
              <td className="py-2">Spectrum over time — scrolling heat map.</td>
            </tr>
            <tr>
              <td className="py-2 font-mono text-cyan-300">IQ samples</td>
              <td className="py-2">
                Raw digitized radio data from the dongle.
              </td>
            </tr>
            <tr>
              <td className="py-2 font-mono text-cyan-300">Gain</td>
              <td className="py-2">
                Sensitivity boost — too high causes overload.
              </td>
            </tr>
            <tr>
              <td className="py-2 font-mono text-cyan-300">Demod</td>
              <td className="py-2">Turn RF into audio (FM, AM, SSB).</td>
            </tr>
          </tbody>
        </table>
        <p className="text-slate-400">
          Bands: LW/MW (AM radio), FM 88–108 MHz, aviation, ADS-B planes,
          weather satellites — all reachable depending on antenna and dongle.
        </p>
      </div>
    ),
  },
  {
    id: "hardware",
    label: "Hardware",
    content: (
      <div className="space-y-4 text-sm text-slate-300">
        <p>
          <strong className="text-white">Budget RX:</strong> NooElec NESDR SMArt
          (~€30) — RTL2832U + R820T2, SMA, TCXO.
        </p>
        <p>
          <strong className="text-white">Best for this repo:</strong> RTL-SDR
          Blog v4 (~€40) — better image rejection, same software path.
        </p>
        <p>
          <strong className="text-white">No dongle yet?</strong> Mock mode runs
          synthetic spectrum/waterfall/audio for learning the UI. It is
          automatic when no RTL-SDR is detected; chat “enable mock” to force it.
          No USB driver needed.
        </p>
        <p>
          <strong className="text-white">Windows driver (real dongle):</strong>{" "}
          the stick ships as a DVB-T TV tuner. Replace that USB driver with{" "}
          <strong className="text-white">WinUSB</strong> via Zadig on{" "}
          <span className="font-mono text-xs">Bulk-In, Interface 0</span> — not
          the dongle itself. Then run{" "}
          <span className="font-mono text-xs">sdr-mcp check</span>.
        </p>
        <p>
          <strong className="text-white">Not for DVB-T2 TV</strong> in Austria —
          use a DVB-T2 receiver stick for terrestrial TV. SDR is for radio
          experimentation, not ORF via antenna out of the box.
        </p>
        <p>
          {docLink("docs/INSTALL.md", "Install & drivers")} ·{" "}
          {docLink("docs/HACKRF.md", "Hardware buying guide")} ·{" "}
          {docLink("docs/RTL_SDR_V4.md", "RTL-SDR Blog v4")} ·{" "}
          {docLink("docs/MOCK_SDR.md", "Mock mode")}
        </p>
      </div>
    ),
  },
  {
    id: "dashboard",
    label: "This dashboard",
    content: (
      <div className="space-y-3 text-sm text-slate-300">
        <ul className="space-y-2">
          <li>
            <Link to="/" className="text-cyan-400 hover:underline">
              Overview
            </Link>{" "}
            — hero, status cards, quick links.
          </li>
          <li>
            <Link to="/spectrum" className="text-cyan-400 hover:underline">
              Spectrum
            </Link>{" "}
            — live FFT + FM audio (Connect, tune e.g. 100.0 MHz).
          </li>
          <li>
            <Link to="/waterfall" className="text-cyan-400 hover:underline">
              Waterfall
            </Link>{" "}
            — time/frequency heat map + same audio stream.
          </li>
          <li>
            <Link to="/stations" className="text-cyan-400 hover:underline">
              Stations
            </Link>{" "}
            — preset frequencies and schedules.
          </li>
          <li>
            <Link to="/chat" className="text-cyan-400 hover:underline">
              AI Command
            </Link>{" "}
            — natural language → MCP tools.
          </li>
          <li>
            <Link to="/tools" className="text-cyan-400 hover:underline">
              Tools
            </Link>{" "}
            — portmanteau MCP tool reference.
          </li>
          <li>
            <Link to="/status" className="text-cyan-400 hover:underline">
              Status
            </Link>{" "}
            — hardware, mock IQ, GNU Radio sidecar.
          </li>
        </ul>
        <p className="text-slate-400">
          Ports: Web UI <span className="font-mono">10890</span>, MCP HTTP{" "}
          <span className="font-mono">10891</span>, Web API{" "}
          <span className="font-mono">10892</span>, WebSocket{" "}
          <span className="font-mono">8765</span>.
        </p>
      </div>
    ),
  },
  {
    id: "audio",
    label: "Listen",
    content: (
      <div className="space-y-4 text-sm text-slate-300">
        <p>
          <strong className="text-white">WebSocket path (easiest):</strong>{" "}
          Spectrum or Waterfall → Connect → tune to an FM station. Audio plays
          in the browser; use Mute if needed.
        </p>
        <p>
          <strong className="text-white">GNU Radio sidecar:</strong> for
          AM/USB/LSB — start rtl_tcp + Docker sidecar, then{" "}
          <span className="font-mono text-xs">
            sdr_gnuradio(operation=&apos;start&apos;)
          </span>
          . Audio goes to PC speakers and the dashboard when WebSocket is
          connected.
        </p>
        <p className="text-slate-400">
          Chat examples: “tune 101.5 mhz”, “spectrum”, “demod 101.5 fm”, “enable
          mock”.
        </p>
        <p>{docLink("docs/GNURADIO.md", "GNU Radio + audio setup")}</p>
      </div>
    ),
  },
  {
    id: "mcp",
    label: "MCP tools",
    content: (
      <div className="space-y-4 text-sm text-slate-300">
        <p>
          Five portmanteau tools (each uses an{" "}
          <span className="font-mono">operation</span> parameter):
        </p>
        <ul className="list-disc list-inside space-y-1 text-slate-400">
          <li>
            <span className="font-mono text-cyan-300">sdr_device</span> — list,
            tune, scan, mock_mode
          </li>
          <li>
            <span className="font-mono text-cyan-300">sdr_spectrum</span> —
            spectrum, waterfall, websocket
          </li>
          <li>
            <span className="font-mono text-cyan-300">sdr_stations</span> —
            search, bands, schedules
          </li>
          <li>
            <span className="font-mono text-cyan-300">sdr_online</span> —
            radio-browser, SigID Wiki
          </li>
          <li>
            <span className="font-mono text-cyan-300">sdr_gnuradio</span> —
            FM/AM/SSB demod sidecar
          </li>
        </ul>
        <p>
          Works in Cursor, Claude Desktop, or via{" "}
          <span className="font-mono">/api/chat</span> on port 10892.
        </p>
        <p>{docLink("docs/MCP_SERVER.md", "Full MCP tool reference")}</p>
      </div>
    ),
  },
  {
    id: "setup",
    label: "Install",
    content: (
      <div className="space-y-4 text-sm text-slate-300">
        <pre className="overflow-x-auto rounded-lg border border-slate-800 bg-slate-950 p-4 font-mono text-xs text-slate-300">
          {`git clone https://github.com/sandraschi/sdr-mcp
cd sdr-mcp
just bootstrap
just dev`}
        </pre>
        <p>
          <strong className="text-white">Real RTL-SDR (Windows):</strong>{" "}
          replace the stick&apos;s DVB/TV USB driver with{" "}
          <strong className="text-white">WinUSB</strong> using{" "}
          <a
            href="https://zadig.akeo.ie/"
            target="_blank"
            rel="noreferrer"
            className="text-cyan-400 hover:underline"
          >
            Zadig
          </a>{" "}
          (Options → List All Devices → Bulk-In, Interface 0 → Replace Driver).
          Then <span className="font-mono">uv run sdr-mcp check</span>.
        </p>
        <p>
          <strong className="text-white">No dongle:</strong> mock mode is
          automatic. Force with{" "}
          <span className="font-mono">
            $env:SDR_MCP_MOCK = &quot;enable&quot;
          </span>{" "}
          or chat “enable mock”. No driver install.
        </p>
        <p>
          Launch UI: <span className="font-mono">web_sota\\start.bat</span> or{" "}
          open http://127.0.0.1:10890/
        </p>
        <p>{docLink("docs/INSTALL.md", "Install guide")}</p>
      </div>
    ),
  },
  {
    id: "legal",
    label: "Legal",
    content: (
      <div className="space-y-4 text-sm text-slate-300">
        <p>
          <strong className="text-white">Receive-only RTL-SDR</strong> —
          listening is generally fine in the EU; respect privacy and local laws.
        </p>
        <p>
          <strong className="text-white">Transmit (HackRF etc.)</strong> —
          buying hardware does not grant transmit rights. Austria: RTR / ÖVSV
          rules apply on ham bands; ISM has strict power limits.
        </p>
        <p>{docLink("docs/HACKRF.md", "HackRF licensing & buying guide")}</p>
      </div>
    ),
  },
  {
    id: "repo",
    label: "Repo docs",
    content: (
      <div className="grid gap-2 text-sm md:grid-cols-2">
        {[
          ["docs/INSTALL.md", "Install & drivers"],
          ["docs/ARCHITECTURE.md", "Architecture"],
          ["docs/MCP_SERVER.md", "MCP tools"],
          ["docs/SDR_TECHNOLOGY.md", "SDR primer"],
          ["docs/GNURADIO.md", "GNU Radio sidecar"],
          ["docs/MOCK_SDR.md", "Mock mode"],
          ["docs/HACKRF.md", "HackRF & hardware"],
          ["docs/RTL_SDR_V4.md", "RTL-SDR v4"],
          ["docs/OSCILLOSCOPE_MCP.md", "Scope MCP notes"],
          ["CHANGELOG.md", "Changelog"],
        ].map(([path, label]) => (
          <div key={path} className="rounded border border-slate-800 px-3 py-2">
            {docLink(path, label)}
          </div>
        ))}
      </div>
    ),
  },
];
