"""
Frequency Database and Program Schedule Management

Comprehensive database of radio stations, frequencies, and program schedules
to eliminate the historical challenge of finding and tracking stations.
"""

from dataclasses import dataclass
from datetime import datetime, time
from enum import Enum


class StationType(Enum):
    PUBLIC = "public"
    COMMERCIAL = "commercial"
    COMMUNITY = "community"
    RELIGIOUS = "religious"
    EDUCATIONAL = "educational"
    MILITARY = "military"
    INTERNATIONAL = "international"


class Band(Enum):
    LONGWAVE = "LW"
    MEDIUMWAVE = "MW"
    SHORTWAVE = "SW"
    VHF = "VHF"
    UHF = "UHF"


@dataclass
class ProgramSchedule:
    """Program schedule entry"""

    name: str
    description: str
    start_time: time
    end_time: time
    days: list[str]  # ['monday', 'tuesday', etc.]
    language: str = "English"
    genre: str = "General"


@dataclass
class RadioStation:
    """Complete radio station information"""

    name: str
    callsign: str
    frequency: float  # in Hz
    band: Band
    country: str
    city: str
    station_type: StationType
    power: int  # in kW
    language: str
    website: str | None = None
    description: str = ""
    programs: list[ProgramSchedule] = None

    def __post_init__(self):
        if self.programs is None:
            self.programs = []

    @property
    def frequency_mhz(self) -> float:
        """Frequency in MHz"""
        return self.frequency / 1e6

    @property
    def frequency_khz(self) -> float:
        """Frequency in kHz"""
        return self.frequency / 1e3


class FrequencyDatabase:
    """Comprehensive frequency database with program schedules"""

    def __init__(self):
        self.stations: dict[str, RadioStation] = {}
        self._load_database()

    def _load_database(self):
        """Load the comprehensive frequency database"""
        # Longwave stations (150-300 kHz)
        self._add_longwave_stations()

        # Medium wave stations (530-1700 kHz)
        self._add_mediumwave_stations()

        # Shortwave stations (3-30 MHz)
        self._add_shortwave_stations()

        # VHF FM stations (87.5-108 MHz) - major international broadcasters
        self._add_vhf_stations()

    def _add_longwave_stations(self):
        """Add European longwave stations with detailed schedules"""
        stations_data = [
            {
                "name": "BBC Radio 4",
                "callsign": "BBC LW",
                "frequency": 198000,  # 198 kHz
                "country": "United Kingdom",
                "city": "Droitwich",
                "station_type": StationType.PUBLIC,
                "power": 500,
                "language": "English",
                "description": "BBC's flagship speech radio station featuring news, drama, comedy, and cultural programming",
                "website": "https://www.bbc.co.uk/radio4",
                "programs": [
                    ProgramSchedule(
                        "Today",
                        "News and current affairs",
                        time(6, 0),
                        time(9, 0),
                        ["monday", "tuesday", "wednesday", "thursday", "friday"],
                    ),
                    ProgramSchedule(
                        "The World at One",
                        "Lunchtime news",
                        time(13, 0),
                        time(13, 45),
                        ["monday", "tuesday", "wednesday", "thursday", "friday"],
                    ),
                    ProgramSchedule(
                        "PM",
                        "Evening news and analysis",
                        time(17, 0),
                        time(18, 0),
                        ["monday", "tuesday", "wednesday", "thursday", "friday"],
                    ),
                    ProgramSchedule(
                        "The Archers",
                        "Long-running radio soap opera",
                        time(19, 15),
                        time(19, 45),
                        ["monday", "tuesday", "wednesday", "thursday", "friday"],
                    ),
                    ProgramSchedule(
                        "Book of the Week",
                        "Literary discussion",
                        time(9, 45),
                        time(10, 0),
                        ["monday", "tuesday", "wednesday", "thursday", "friday"],
                    ),
                ],
            },
            {
                "name": "ORF Radio Österreich 1",
                "callsign": "ORF LW",
                "frequency": 198000,  # 198 kHz
                "country": "Austria",
                "city": "Moosbrunn",
                "station_type": StationType.PUBLIC,
                "power": 100,
                "language": "German",
                "description": "ORF's flagship cultural and information station with classical music and comprehensive news",
                "website": "https://orf.at",
                "programs": [
                    ProgramSchedule(
                        "Ö1 Morgenjournal",
                        "Morning news",
                        time(5, 0),
                        time(9, 0),
                        ["monday", "tuesday", "wednesday", "thursday", "friday"],
                    ),
                    ProgramSchedule(
                        "Ö1 Mittagsjournal",
                        "Lunch news",
                        time(12, 0),
                        time(13, 0),
                        ["monday", "tuesday", "wednesday", "thursday", "friday"],
                    ),
                    ProgramSchedule(
                        "Ö1 Abendjournal",
                        "Evening news",
                        time(18, 30),
                        time(19, 30),
                        ["monday", "tuesday", "wednesday", "thursday", "friday"],
                    ),
                    ProgramSchedule(
                        "Klassik-Treffpunkt",
                        "Classical music program",
                        time(19, 30),
                        time(21, 0),
                        ["monday", "tuesday", "wednesday", "thursday", "friday"],
                    ),
                ],
            },
            {
                "name": "France Inter",
                "callsign": "France Inter LW",
                "frequency": 162000,  # 162 kHz
                "country": "France",
                "city": "Allouis",
                "station_type": StationType.PUBLIC,
                "power": 2000,
                "language": "French",
                "description": "France's main public radio station featuring news, culture, music, and intellectual programming",
                "website": "https://www.franceinter.fr",
                "programs": [
                    ProgramSchedule(
                        "Le Journal de 7h",
                        "Morning news",
                        time(7, 0),
                        time(9, 0),
                        ["monday", "tuesday", "wednesday", "thursday", "friday"],
                    ),
                    ProgramSchedule(
                        "Le Journal de 8h",
                        "News update",
                        time(8, 0),
                        time(8, 30),
                        ["monday", "tuesday", "wednesday", "thursday", "friday"],
                    ),
                    ProgramSchedule(
                        "Le Journal de 12h",
                        "Midday news",
                        time(12, 0),
                        time(12, 30),
                        ["monday", "tuesday", "wednesday", "thursday", "friday"],
                    ),
                    ProgramSchedule(
                        "Le Journal de 13h",
                        "Afternoon news",
                        time(13, 0),
                        time(13, 30),
                        ["monday", "tuesday", "wednesday", "thursday", "friday"],
                    ),
                    ProgramSchedule(
                        "Le Journal de 18h",
                        "Evening news",
                        time(18, 0),
                        time(18, 30),
                        ["monday", "tuesday", "wednesday", "thursday", "friday"],
                    ),
                ],
            },
            {
                "name": "RTL Radio",
                "callsign": "RTL LW",
                "frequency": 234000,  # 234 kHz
                "country": "Luxembourg",
                "city": "Junglinster",
                "station_type": StationType.COMMERCIAL,
                "power": 300,
                "language": "French",
                "description": "Popular commercial radio station broadcasting entertainment, music, and information across Europe",
                "website": "https://www.rtl.lu",
                "programs": [
                    ProgramSchedule(
                        "RTL Matin",
                        "Morning show",
                        time(6, 0),
                        time(9, 0),
                        ["monday", "tuesday", "wednesday", "thursday", "friday"],
                    ),
                    ProgramSchedule(
                        "RTL Soir",
                        "Evening entertainment",
                        time(16, 0),
                        time(19, 0),
                        ["monday", "tuesday", "wednesday", "thursday", "friday"],
                    ),
                ],
            },
        ]

        for station_data in stations_data:
            station = RadioStation(
                name=station_data["name"],
                callsign=station_data["callsign"],
                frequency=station_data["frequency"],
                band=Band.LONGWAVE,
                country=station_data["country"],
                city=station_data["city"],
                station_type=station_data["station_type"],
                power=station_data["power"],
                language=station_data["language"],
                website=station_data.get("website"),
                description=station_data["description"],
                programs=station_data["programs"],
            )
            self.stations[station.callsign] = station

    def _add_mediumwave_stations(self):
        """Add major medium wave stations"""
        mw_stations = [
            {
                "name": "BBC Radio 5 Live",
                "callsign": "BBC 5L",
                "frequency": 909000,  # 909 kHz
                "country": "United Kingdom",
                "city": "Wrotham",
                "station_type": StationType.PUBLIC,
                "power": 50,
                "language": "English",
                "description": "BBC's sports and live events station",
            },
            {
                "name": "France Info",
                "callsign": "France Info",
                "frequency": 837000,  # 837 kHz
                "country": "France",
                "city": "Paris",
                "station_type": StationType.PUBLIC,
                "power": 100,
                "language": "French",
                "description": "France's 24/7 news and information station",
            },
            {
                "name": "Deutsche Welle",
                "callsign": "DW",
                "frequency": 943000,  # 943 kHz
                "country": "Germany",
                "city": "Berlin",
                "station_type": StationType.INTERNATIONAL,
                "power": 150,
                "language": "German",
                "description": "Germany's international broadcaster",
            },
        ]

        for station_data in mw_stations:
            station = RadioStation(
                name=station_data["name"],
                callsign=station_data["callsign"],
                frequency=station_data["frequency"],
                band=Band.MEDIUMWAVE,
                country=station_data["country"],
                city=station_data["city"],
                station_type=station_data["station_type"],
                power=station_data["power"],
                language=station_data["language"],
                website=station_data.get("website"),
                description=station_data["description"],
            )
            self.stations[station.callsign] = station

    def _add_shortwave_stations(self):
        """Add major shortwave international broadcasters"""
        sw_stations = [
            {
                "name": "BBC World Service",
                "callsign": "BBC WS",
                "frequency": 5975000,  # 5.975 MHz
                "country": "United Kingdom",
                "city": "Woofferton",
                "station_type": StationType.INTERNATIONAL,
                "power": 250,
                "language": "English",
                "description": "BBC's international news and information service",
            },
            {
                "name": "Voice of America",
                "callsign": "VOA",
                "frequency": 5955000,  # 5.955 MHz
                "country": "United States",
                "city": "Delano",
                "station_type": StationType.INTERNATIONAL,
                "power": 250,
                "language": "English",
                "description": "US international broadcasting service",
            },
            {
                "name": "Radio France Internationale",
                "callsign": "RFI",
                "frequency": 6165000,  # 6.165 MHz
                "country": "France",
                "city": "Issoudun",
                "station_type": StationType.INTERNATIONAL,
                "power": 500,
                "language": "French",
                "description": "France's international radio service",
            },
        ]

        for station_data in sw_stations:
            station = RadioStation(
                name=station_data["name"],
                callsign=station_data["callsign"],
                frequency=station_data["frequency"],
                band=Band.SHORTWAVE,
                country=station_data["country"],
                city=station_data["city"],
                station_type=station_data["station_type"],
                power=station_data["power"],
                language=station_data["language"],
                website=station_data.get("website"),
                description=station_data["description"],
            )
            self.stations[station.callsign] = station

    def _add_vhf_stations(self):
        """Add major VHF FM international stations"""
        vhf_stations = [
            {
                "name": "BFBS Radio 1",
                "callsign": "BFBS 1",
                "frequency": 89000000,  # 89.0 MHz
                "country": "United Kingdom",
                "city": "Various (Europe)",
                "station_type": StationType.MILITARY,
                "power": 10,
                "language": "English",
                "description": "British Forces Broadcasting Service",
            }
        ]

        for station_data in vhf_stations:
            station = RadioStation(
                name=station_data["name"],
                callsign=station_data["callsign"],
                frequency=station_data["frequency"],
                band=Band.VHF,
                country=station_data["country"],
                city=station_data["city"],
                station_type=station_data["station_type"],
                power=station_data["power"],
                language=station_data["language"],
                website=station_data.get("website"),
                description=station_data["description"],
            )
            self.stations[station.callsign] = station

    def search_stations(self, query: str, band: Band | None = None, country: str | None = None) -> list[RadioStation]:
        """Search stations by name, callsign, or description"""
        query_lower = query.lower()
        results = []

        for station in self.stations.values():
            if band and station.band != band:
                continue
            if country and station.country.lower() != country.lower():
                continue

            if (
                query_lower in station.name.lower()
                or query_lower in station.callsign.lower()
                or query_lower in station.description.lower()
                or query_lower in station.country.lower()
            ):
                results.append(station)

        return results

    def get_stations_by_frequency_range(self, min_freq: float, max_freq: float) -> list[RadioStation]:
        """Get stations within frequency range (in Hz)"""
        return [s for s in self.stations.values() if min_freq <= s.frequency <= max_freq]

    def get_stations_by_band(self, band: Band) -> list[RadioStation]:
        """Get all stations on a specific band"""
        return [s for s in self.stations.values() if s.band == band]

    def get_stations_by_country(self, country: str) -> list[RadioStation]:
        """Get all stations from a specific country"""
        return [s for s in self.stations.values() if s.country.lower() == country.lower()]

    def get_current_program(self, station_callsign: str) -> ProgramSchedule | None:
        """Get the currently playing program for a station"""
        station = self.stations.get(station_callsign)
        if not station or not station.programs:
            return None

        now = datetime.now()
        current_time = now.time()
        current_day = now.strftime("%A").lower()

        for program in station.programs:
            if current_day in program.days:
                if program.start_time <= current_time <= program.end_time:
                    return program

        return None

    def get_program_schedule(self, station_callsign: str, day: str | None = None) -> list[ProgramSchedule]:
        """Get program schedule for a station on a specific day"""
        station = self.stations.get(station_callsign)
        if not station:
            return []

        if day:
            day_lower = day.lower()
            return [p for p in station.programs if day_lower in p.days]
        else:
            return station.programs.copy()

    def get_all_stations(self) -> list[RadioStation]:
        """Get all stations in the database"""
        return list(self.stations.values())

    def get_station_count(self) -> int:
        """Get total number of stations in database"""
        return len(self.stations)

    def get_stations_by_type(self, station_type: StationType) -> list[RadioStation]:
        """Get stations by type (public, commercial, etc.)"""
        return [s for s in self.stations.values() if s.station_type == station_type]


# Global frequency database instance
_frequency_db = None


def get_frequency_database() -> FrequencyDatabase:
    """Get or create the global frequency database instance"""
    global _frequency_db
    if _frequency_db is None:
        _frequency_db = FrequencyDatabase()
    return _frequency_db
