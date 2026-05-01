import {
  BookOpen,
  ExternalLink,
  Globe,
  Loader2,
  Radio,
  Search,
  Star,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

interface Station {
  name: string;
  callsign: string;
  frequency_khz: number;
  frequency_mhz: number;
  band: string;
  country: string;
  city: string;
  type: string;
  power: number;
  language: string;
  description: string;
}

interface OnlineStation {
  name: string;
  country: string;
  language: string;
  tags: string[];
  codec: string;
  bitrate: number;
  url: string;
  clicks: number;
}

interface SignalInfo {
  title: string;
  description: string;
  page_url: string;
}

const PRESET_STATIONS: Station[] = [
  {
    name: "BBC Radio 4",
    callsign: "BBC LW",
    frequency_khz: 198,
    frequency_mhz: 0.198,
    band: "LW",
    country: "United Kingdom",
    city: "Droitwich",
    type: "public",
    power: 500,
    language: "English",
    description: "BBC's flagship speech radio station",
  },
  {
    name: "ORF Radio OE1",
    callsign: "ORF LW",
    frequency_khz: 198,
    frequency_mhz: 0.198,
    band: "LW",
    country: "Austria",
    city: "Moosbrunn",
    type: "public",
    power: 100,
    language: "German",
    description: "ORF's cultural and information station",
  },
  {
    name: "France Inter",
    callsign: "France Inter LW",
    frequency_khz: 162,
    frequency_mhz: 0.162,
    band: "LW",
    country: "France",
    city: "Allouis",
    type: "public",
    power: 2000,
    language: "French",
    description: "France's main public radio station",
  },
  {
    name: "RTL Radio",
    callsign: "RTL LW",
    frequency_khz: 234,
    frequency_mhz: 0.234,
    band: "LW",
    country: "Luxembourg",
    city: "Junglinster",
    type: "commercial",
    power: 300,
    language: "French",
    description: "Popular commercial radio station",
  },
  {
    name: "BBC World Service",
    callsign: "BBC WS",
    frequency_khz: 5975,
    frequency_mhz: 5.975,
    band: "SW",
    country: "United Kingdom",
    city: "Woofferton",
    type: "international",
    power: 250,
    language: "English",
    description: "BBC's international news service",
  },
  {
    name: "Voice of America",
    callsign: "VOA",
    frequency_khz: 5955,
    frequency_mhz: 5.955,
    band: "SW",
    country: "United States",
    city: "Delano",
    type: "international",
    power: 250,
    language: "English",
    description: "US international broadcasting",
  },
  {
    name: "Radio France Internationale",
    callsign: "RFI",
    frequency_khz: 6165,
    frequency_mhz: 6.165,
    band: "SW",
    country: "France",
    city: "Issoudun",
    type: "international",
    power: 500,
    language: "French",
    description: "France's international radio service",
  },
  {
    name: "BBC Radio 5 Live",
    callsign: "BBC 5L",
    frequency_khz: 909,
    frequency_mhz: 0.909,
    band: "MW",
    country: "United Kingdom",
    city: "Wrotham",
    type: "public",
    power: 50,
    language: "English",
    description: "BBC's sports and live events",
  },
  {
    name: "France Info",
    callsign: "France Info",
    frequency_khz: 837,
    frequency_mhz: 0.837,
    band: "MW",
    country: "France",
    city: "Paris",
    type: "public",
    power: 100,
    language: "French",
    description: "24/7 news and information",
  },
  {
    name: "Deutsche Welle",
    callsign: "DW",
    frequency_khz: 943,
    frequency_mhz: 0.943,
    band: "MW",
    country: "Germany",
    city: "Berlin",
    type: "international",
    power: 150,
    language: "German",
    description: "Germany's international broadcaster",
  },
  {
    name: "BFBS Radio 1",
    callsign: "BFBS 1",
    frequency_khz: 89000,
    frequency_mhz: 89.0,
    band: "VHF",
    country: "United Kingdom",
    city: "Various (Europe)",
    type: "military",
    power: 10,
    language: "English",
    description: "British Forces Broadcasting Service",
  },
];

function loadFavorites(): string[] {
  try {
    const saved = localStorage.getItem("sdr-favorites");
    return saved ? JSON.parse(saved) : [];
  } catch {
    return [];
  }
}

function saveFavorites(favorites: string[]) {
  localStorage.setItem("sdr-favorites", JSON.stringify(favorites));
}

export function Stations() {
  const [searchQuery, setSearchQuery] = useState("");
  const [favorites, setFavorites] = useState<string[]>(loadFavorites);
  const [activeTab, setActiveTab] = useState("all");
  const [manualFreq, setManualFreq] = useState("");

  const [onlineQuery, setOnlineQuery] = useState("");
  const [onlineResults, setOnlineResults] = useState<OnlineStation[]>([]);
  const [onlineLoading, setOnlineLoading] = useState(false);
  const [onlineMode, setOnlineMode] = useState<"name" | "country" | "tag">(
    "name",
  );

  const [signalQuery, setSignalQuery] = useState("");
  const [signalResult, setSignalResult] = useState<SignalInfo | null>(null);
  const [signalLoading, setSignalLoading] = useState(false);

  useEffect(() => {
    saveFavorites(favorites);
  }, [favorites]);

  const toggleFavorite = (callsign: string) => {
    setFavorites((prev) =>
      prev.includes(callsign)
        ? prev.filter((f) => f !== callsign)
        : [...prev, callsign],
    );
  };

  const filteredStations = PRESET_STATIONS.filter((s) => {
    if (
      activeTab === "online" ||
      activeTab === "signal-id" ||
      activeTab === "favorites"
    ) {
      if (activeTab === "favorites" && !favorites.includes(s.callsign))
        return false;
      if (activeTab === "online" || activeTab === "signal-id") return false;
    }
    const bandMap: Record<string, string[]> = {
      lw: ["LW"],
      mw: ["MW"],
      sw: ["SW"],
      vhf: ["VHF", "UHF"],
    };
    if (
      activeTab !== "all" &&
      activeTab !== "favorites" &&
      activeTab !== "online" &&
      activeTab !== "signal-id"
    ) {
      if (!bandMap[activeTab]?.includes(s.band)) return false;
    }
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      s.name.toLowerCase().includes(q) ||
      s.callsign.toLowerCase().includes(q) ||
      s.country.toLowerCase().includes(q) ||
      s.band.toLowerCase().includes(q)
    );
  });

  const searchOnline = useCallback(async () => {
    if (!onlineQuery.trim()) return;
    setOnlineLoading(true);
    setOnlineResults([]);
    try {
      const mirror = "https://de1.api.radio-browser.info";
      const path =
        onlineMode === "country"
          ? `${mirror}/json/stations/bycountry/${encodeURIComponent(onlineQuery)}?limit=30`
          : onlineMode === "tag"
            ? `${mirror}/json/stations/bytag/${encodeURIComponent(onlineQuery)}?limit=30`
            : `${mirror}/json/stations/byname/${encodeURIComponent(onlineQuery)}?limit=30`;
      const resp = await fetch(path, {
        headers: { "User-Agent": "sdr-mcp-web/0.1" },
      });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();
      if (Array.isArray(data)) {
        setOnlineResults(
          data.slice(0, 30).map((s: Record<string, unknown>) => ({
            name: (s.name as string) || "Unknown",
            country: (s.country as string) || "",
            language: (s.language as string) || "",
            tags:
              typeof s.tags === "string"
                ? (s.tags as string)
                    .split(",")
                    .map((t: string) => t.trim())
                    .filter(Boolean)
                : [],
            codec: (s.codec as string) || "",
            bitrate: (s.bitrate as number) || 0,
            url: (s.url as string) || "",
            clicks: (s.clicks as number) || 0,
          })),
        );
      }
    } catch (err) {
      console.error("Online search failed:", err);
    } finally {
      setOnlineLoading(false);
    }
  }, [onlineQuery, onlineMode]);

  const searchSignal = useCallback(async () => {
    if (!signalQuery.trim()) return;
    setSignalLoading(true);
    setSignalResult(null);
    try {
      const params = new URLSearchParams({
        action: "query",
        list: "search",
        srsearch: signalQuery,
        srlimit: 1,
        format: "json",
        origin: "*",
      });
      const resp = await fetch(`https://www.sigidwiki.com/api.php?${params}`);
      const data = await resp.json();
      const pages = data?.query?.search;
      if (pages?.length > 0) {
        const top = pages[0];
        setSignalResult({
          title: top.title,
          description: top.snippet?.replace(/<[^>]+>/g, "") || "",
          page_url: `https://www.sigidwiki.com/wiki/${encodeURIComponent(top.title)}`,
        });
      }
    } catch (err) {
      console.error("Signal search failed:", err);
    } finally {
      setSignalLoading(false);
    }
  }, [signalQuery]);

  const openFrequency = () => {
    const freq = parseFloat(manualFreq);
    if (!isNaN(freq)) {
      if (freq < 30) {
        window.open(`http://websdr.org/?freq=${freq * 1000}`, "_blank");
      } else {
        window.open(`http://websdr.org/?freq=${freq}`, "_blank");
      }
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">
            Frequency Browser
          </h2>
          <p className="text-slate-400">
            Search stations, online databases, signal identification
          </p>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card className="border-slate-800 bg-slate-950/50 col-span-2">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-medium text-slate-200">
                Stations & Online DB
              </CardTitle>
              <div className="flex items-center gap-2">
                {(activeTab === "all" ||
                  activeTab === "lw" ||
                  activeTab === "mw" ||
                  activeTab === "sw" ||
                  activeTab === "vhf" ||
                  activeTab === "favorites") && (
                  <div className="relative">
                    <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-3 w-3 text-slate-500" />
                    <Input
                      className="bg-slate-900 border-slate-800 text-slate-100 pl-7 h-8 text-sm w-48"
                      placeholder="Search stations..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                    />
                  </div>
                )}
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <Tabs value={activeTab} onValueChange={setActiveTab}>
              <TabsList className="bg-slate-900 border border-slate-800 flex-wrap h-auto">
                <TabsTrigger value="all" className="text-xs">
                  All
                </TabsTrigger>
                <TabsTrigger value="lw" className="text-xs">
                  LW
                </TabsTrigger>
                <TabsTrigger value="mw" className="text-xs">
                  MW
                </TabsTrigger>
                <TabsTrigger value="sw" className="text-xs">
                  SW
                </TabsTrigger>
                <TabsTrigger value="vhf" className="text-xs">
                  VHF/UHF
                </TabsTrigger>
                <TabsTrigger value="favorites" className="text-xs">
                  Favorites ({favorites.length})
                </TabsTrigger>
                <TabsTrigger
                  value="online"
                  className="text-xs flex items-center gap-1"
                >
                  <Globe className="h-3 w-3" /> Online DB
                </TabsTrigger>
                <TabsTrigger
                  value="signal-id"
                  className="text-xs flex items-center gap-1"
                >
                  <BookOpen className="h-3 w-3" /> Signal ID
                </TabsTrigger>
              </TabsList>

              {/* Local stations tabs */}
              {(activeTab === "all" ||
                activeTab === "lw" ||
                activeTab === "mw" ||
                activeTab === "sw" ||
                activeTab === "vhf" ||
                activeTab === "favorites") && (
                <ScrollArea className="h-[400px] mt-4">
                  <div className="space-y-2">
                    {filteredStations.map((station) => (
                      <div
                        key={station.callsign}
                        className="flex items-center justify-between p-3 rounded bg-slate-900/30 border border-slate-800 hover:bg-slate-900/50 transition-colors"
                      >
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-medium text-slate-200">
                              {station.name}
                            </span>
                            <Badge
                              variant="outline"
                              className="text-[10px] px-1 py-0 h-4 border-slate-700 text-slate-400"
                            >
                              {station.band}
                            </Badge>
                            <Badge
                              variant="outline"
                              className="text-[10px] px-1 py-0 h-4 border-slate-700 text-slate-400"
                            >
                              {station.country}
                            </Badge>
                          </div>
                          <div className="flex items-center gap-3 mt-1">
                            <span className="text-xs font-mono text-cyan-400">
                              {station.frequency_mhz < 1
                                ? `${station.frequency_khz} kHz`
                                : `${station.frequency_mhz} MHz`}
                            </span>
                            <span className="text-xs text-slate-500">
                              {station.language}
                            </span>
                            {station.power > 100 && (
                              <span className="text-xs text-yellow-500">
                                {station.power} kW
                              </span>
                            )}
                          </div>
                          <p className="text-xs text-slate-500 mt-1 truncate">
                            {station.description}
                          </p>
                        </div>
                        <Button
                          size="icon"
                          variant="ghost"
                          className="h-7 w-7 ml-2 shrink-0"
                          onClick={() => toggleFavorite(station.callsign)}
                        >
                          <Star
                            className={`h-3.5 w-3.5 ${favorites.includes(station.callsign) ? "fill-yellow-500 text-yellow-500" : "text-slate-600"}`}
                          />
                        </Button>
                      </div>
                    ))}
                    {filteredStations.length === 0 && (
                      <p className="text-sm text-slate-500 text-center py-8">
                        No stations found
                      </p>
                    )}
                  </div>
                </ScrollArea>
              )}

              {/* Online DB tab */}
              <TabsContent value="online" className="mt-4">
                <div className="space-y-3">
                  <div className="flex gap-2">
                    <select
                      className="bg-slate-900 border border-slate-800 text-slate-300 text-xs rounded px-2 py-1"
                      value={onlineMode}
                      onChange={(e) =>
                        setOnlineMode(
                          e.target.value as "name" | "country" | "tag",
                        )
                      }
                    >
                      <option value="name">By Name</option>
                      <option value="country">By Country</option>
                      <option value="tag">By Genre/Tag</option>
                    </select>
                    <Input
                      className="bg-slate-900 border-slate-800 text-slate-100 flex-1 h-8 text-sm"
                      placeholder={
                        onlineMode === "country"
                          ? "e.g. Austria, France, Japan"
                          : onlineMode === "tag"
                            ? "e.g. rock, news, jazz"
                            : "e.g. BBC, NPR, ORF"
                      }
                      value={onlineQuery}
                      onChange={(e) => setOnlineQuery(e.target.value)}
                      onKeyDown={(e) => e.key === "Enter" && searchOnline()}
                    />
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={searchOnline}
                      disabled={onlineLoading}
                      className="border-slate-700 text-slate-300 h-8"
                    >
                      {onlineLoading ? (
                        <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      ) : (
                        <Search className="h-3.5 w-3.5" />
                      )}
                    </Button>
                  </div>
                  <p className="text-[10px] text-slate-600">
                    Powered by radio-browser.info (open API, no key required)
                  </p>
                  <ScrollArea className="h-[340px]">
                    <div className="space-y-2">
                      {onlineResults.map((station, i) => (
                        <div
                          key={i}
                          className="flex items-center justify-between p-2 rounded bg-slate-900/30 border border-slate-800"
                        >
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-1.5">
                              <span className="text-sm font-medium text-slate-200 truncate">
                                {station.name}
                              </span>
                              {station.country && (
                                <span className="text-[10px] text-slate-500 shrink-0">
                                  {station.country}
                                </span>
                              )}
                            </div>
                            <div className="flex items-center gap-2 mt-0.5">
                              {station.language && (
                                <span className="text-[10px] text-slate-500">
                                  {station.language}
                                </span>
                              )}
                              {station.bitrate > 0 && (
                                <span className="text-[10px] font-mono text-cyan-400">
                                  {station.bitrate} kbps
                                </span>
                              )}
                              {station.codec && (
                                <span className="text-[10px] text-slate-500">
                                  {station.codec}
                                </span>
                              )}
                              {station.clicks > 0 && (
                                <span className="text-[10px] text-slate-600">
                                  {station.clicks} clicks
                                </span>
                              )}
                            </div>
                            {station.tags.length > 0 && (
                              <div className="flex gap-1 mt-0.5 flex-wrap">
                                {station.tags.slice(0, 4).map((tag) => (
                                  <span
                                    key={tag}
                                    className="text-[9px] px-1 py-0.5 rounded bg-slate-800 text-slate-400"
                                  >
                                    {tag}
                                  </span>
                                ))}
                              </div>
                            )}
                          </div>
                          {station.url && (
                            <a
                              href={station.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="shrink-0 ml-2"
                            >
                              <ExternalLink className="h-3 w-3 text-slate-500 hover:text-blue-400" />
                            </a>
                          )}
                        </div>
                      ))}
                      {onlineResults.length === 0 && !onlineLoading && (
                        <p className="text-sm text-slate-500 text-center py-8">
                          Search online radio database above
                        </p>
                      )}
                      {onlineLoading && (
                        <div className="flex items-center justify-center py-8">
                          <Loader2 className="h-5 w-5 animate-spin text-slate-400" />
                        </div>
                      )}
                    </div>
                  </ScrollArea>
                </div>
              </TabsContent>

              {/* Signal ID tab */}
              <TabsContent value="signal-id" className="mt-4">
                <div className="space-y-3">
                  <div className="flex gap-2">
                    <Input
                      className="bg-slate-900 border-slate-800 text-slate-100 flex-1 h-8 text-sm"
                      placeholder="e.g. AM, FM, DAB, QPSK, OFDM, CW..."
                      value={signalQuery}
                      onChange={(e) => setSignalQuery(e.target.value)}
                      onKeyDown={(e) => e.key === "Enter" && searchSignal()}
                    />
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={searchSignal}
                      disabled={signalLoading}
                      className="border-slate-700 text-slate-300 h-8"
                    >
                      {signalLoading ? (
                        <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      ) : (
                        <Search className="h-3.5 w-3.5" />
                      )}
                    </Button>
                  </div>
                  <p className="text-[10px] text-slate-600">
                    Powered by Signal Identification Wiki (sigidwiki.com)
                  </p>

                  {signalResult && (
                    <Card className="border-slate-700 bg-slate-900/50">
                      <CardContent className="p-3 space-y-2">
                        <div className="flex items-center gap-2">
                          <Radio className="h-4 w-4 text-emerald-500" />
                          <span className="text-sm font-medium text-slate-200">
                            {signalResult.title}
                          </span>
                        </div>
                        {signalResult.description && (
                          <p className="text-xs text-slate-400">
                            {signalResult.description.slice(0, 300)}
                          </p>
                        )}
                        <a
                          href={signalResult.page_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300"
                        >
                          View on SigID Wiki{" "}
                          <ExternalLink className="h-3 w-3" />
                        </a>
                      </CardContent>
                    </Card>
                  )}
                  {!signalResult && !signalLoading && (
                    <p className="text-sm text-slate-500 text-center py-8">
                      Search for a signal type to identify it
                    </p>
                  )}
                  {signalLoading && (
                    <div className="flex items-center justify-center py-8">
                      <Loader2 className="h-5 w-5 animate-spin text-slate-400" />
                    </div>
                  )}
                </div>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">
              Frequency Selector
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label htmlFor="manual-freq" className="text-xs text-slate-400">
                Enter frequency (MHz)
              </label>
              <div className="flex gap-2">
                <Input
                  id="manual-freq"
                  className="bg-slate-900 border-slate-800 text-slate-100 font-mono text-sm"
                  placeholder="e.g. 198.0"
                  value={manualFreq}
                  onChange={(e) => setManualFreq(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && openFrequency()}
                />
                <Button
                  size="sm"
                  variant="outline"
                  onClick={openFrequency}
                  className="border-slate-700 text-slate-300"
                >
                  <Radio className="h-3.5 w-3.5" />
                </Button>
              </div>
              <p className="text-[10px] text-slate-600">
                Opens WebSDR for this frequency
              </p>
            </div>

            <div className="space-y-2">
              <label className="text-xs text-slate-400">Quick Presets</label>
              <div className="grid grid-cols-2 gap-2">
                {PRESET_STATIONS.slice(0, 8).map((s) => (
                  <Button
                    key={s.callsign}
                    size="sm"
                    variant="outline"
                    className="text-xs border-slate-700 text-slate-400 hover:text-slate-200 h-auto py-1.5"
                    onClick={() =>
                      setManualFreq(
                        s.frequency_mhz < 1
                          ? (s.frequency_khz / 1000).toFixed(3)
                          : s.frequency_mhz.toFixed(1),
                      )
                    }
                  >
                    {s.callsign}
                  </Button>
                ))}
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-xs text-slate-400">
                Favorites ({favorites.length})
              </label>
              <div className="space-y-1">
                {favorites.length === 0 && (
                  <p className="text-xs text-slate-600">
                    Click the star on any station to add it here
                  </p>
                )}
                {favorites.map((callsign) => {
                  const station = PRESET_STATIONS.find(
                    (s) => s.callsign === callsign,
                  );
                  if (!station) return null;
                  return (
                    <div
                      key={callsign}
                      className="flex items-center justify-between p-2 rounded bg-slate-900/30 border border-slate-800"
                    >
                      <div>
                        <span className="text-xs text-slate-300">
                          {station.name}
                        </span>
                        <span className="text-xs text-slate-500 ml-2 font-mono">
                          {station.frequency_mhz < 1
                            ? `${station.frequency_khz} kHz`
                            : `${station.frequency_mhz} MHz`}
                        </span>
                      </div>
                      <Button
                        size="icon"
                        variant="ghost"
                        className="h-5 w-5"
                        onClick={() => toggleFavorite(callsign)}
                      >
                        <Star className="h-3 w-3 fill-yellow-500 text-yellow-500" />
                      </Button>
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="border-t border-slate-800 pt-3 mt-3">
              <p className="text-xs text-slate-500 mb-2">
                Online Frequency Databases
              </p>
              <div className="space-y-1">
                <a
                  href="https://shortwave.am"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block text-xs text-blue-400 hover:text-blue-300"
                >
                  Shortwave.am — SW broadcast schedules
                </a>
                <a
                  href="https://www.fmlist.org"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block text-xs text-blue-400 hover:text-blue-300"
                >
                  FMList — FM station database
                </a>
                <a
                  href="https://www.sigidwiki.com"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block text-xs text-blue-400 hover:text-blue-300"
                >
                  SigID Wiki — Signal identification
                </a>
                <a
                  href="https://de1.api.radio-browser.info"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block text-xs text-blue-400 hover:text-blue-300"
                >
                  radio-browser.info — Open station API
                </a>
                <a
                  href="http://websdr.org"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block text-xs text-blue-400 hover:text-blue-300"
                >
                  WebSDR — Remote SDR receivers
                </a>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
