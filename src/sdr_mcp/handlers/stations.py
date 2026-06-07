"""Station database query handlers."""

from __future__ import annotations

import logging
from typing import Any

from ..frequency_db import Band, StationType, get_frequency_database
from .state import VALID_BANDS

logger = logging.getLogger(__name__)


async def search_stations(query: str, band: str | None = None, country: str | None = None) -> dict[str, Any]:
    """Search for radio stations by name, callsign, or description with intelligent matching."""
    try:
        db = get_frequency_database()

        band_enum = None
        if band:
            try:
                band_enum = Band(band.upper())
            except ValueError:
                pass

        results = db.search_stations(query, band_enum, country)

        if not results:
            return {
                "status": "no_results",
                "conversation": {
                    "message": f"No stations found matching '{query}'"
                    + (f" in {country}" if country else "")
                    + (f" on {band} band" if band else ""),
                    "suggestions": [
                        "Try broader search terms",
                        "Check spelling of station names",
                        "Search by country or region",
                        "Use frequency ranges instead: sdr_scan_frequencies()",
                    ],
                    "popular_searches": [
                        "BBC",
                        "France Inter",
                        "ORF",
                        "Voice of America",
                        "BBC World Service",
                        "Radio France Internationale",
                    ],
                },
            }

        by_band = {}
        for station in results:
            band_name = station.band.value
            if band_name not in by_band:
                by_band[band_name] = []
            by_band[band_name].append(station)

        total_found = len(results)
        bands_found = list(by_band.keys())
        top_recommendations = results[:3]

        return {
            "status": "found",
            "total_results": total_found,
            "bands": bands_found,
            "stations": [
                {
                    "name": s.name,
                    "callsign": s.callsign,
                    "frequency_mhz": s.frequency_mhz,
                    "frequency_khz": s.frequency_khz,
                    "band": s.band.value,
                    "country": s.country,
                    "city": s.city,
                    "type": s.station_type.value,
                    "language": s.language,
                    "description": s.description[:100] + "..." if len(s.description) > 100 else s.description,
                    "power_kw": s.power,
                    "website": s.website,
                }
                for s in results
            ],
            "conversation": {
                "message": f"Found {total_found} station(s) matching '{query}' across {len(bands_found)} band(s): {', '.join(bands_found)}",
                "top_recommendations": [
                    {
                        "name": s.name,
                        "callsign": s.callsign,
                        "frequency": f"{s.frequency_mhz:.1f} MHz ({s.frequency_khz:.0f} kHz)",
                        "reason": f"{'Strong signal' if s.power > 100 else 'Reliable'} {s.band.value} station from {s.country}",
                    }
                    for s in top_recommendations
                ],
                "next_steps": [
                    f"Tune to top result: sdr_tune_frequency({top_recommendations[0].frequency_mhz})"
                    if top_recommendations
                    else None,
                    "Get program schedule: sdr_get_program_schedule('"
                    + (top_recommendations[0].callsign if top_recommendations else "STATION")
                    + "')",
                    "Search by country: sdr_search_stations('', country='France')",
                    "Explore band: sdr_get_stations_by_band('LW')",
                ],
                "search_insights": {
                    "total_database_size": db.get_station_count(),
                    "bands_available": [b.value for b in Band],
                    "countries_covered": len(set(s.country for s in db.get_all_stations())),
                    "languages_supported": len(set(s.language for s in db.get_all_stations())),
                },
            },
        }

    except Exception as e:
        logger.error("Error searching stations: %s", e, exc_info=True)
        return {
            "status": "error",
            "conversation": {
                "message": f"Station search failed: {e}",
                "troubleshooting": [
                    "Check search query format",
                    "Try without filters first",
                    "Use simpler search terms",
                ],
            },
            "error": str(e),
        }


async def get_stations_by_band(band: str) -> dict[str, Any]:
    """Get all stations on a specific frequency band with detailed information."""
    try:
        band_upper = band.upper()
        if band_upper not in VALID_BANDS:
            return {
                "status": "invalid_band",
                "conversation": {
                    "message": f"'{band}' is not a valid band. Available bands: {', '.join(sorted(VALID_BANDS))}",
                    "band_guide": {
                        "LW": "Longwave (150-300 kHz) - BBC, ORF, France Inter",
                        "MW": "Medium Wave (530-1700 kHz) - Regional AM stations",
                        "SW": "Shortwave (3-30 MHz) - BBC World Service, VOA, RFI",
                        "VHF": "VHF (30-300 MHz) - FM radio, military communications",
                        "UHF": "UHF (300-3000 MHz) - Digital radio, satellite",
                    },
                },
            }

        db = get_frequency_database()
        band_enum = Band(band_upper)
        stations = db.get_stations_by_band(band_enum)

        if not stations:
            return {
                "status": "no_stations",
                "conversation": {
                    "message": f"No stations found on {band} band in our database.",
                    "band_info": {
                        "LW": "Longwave (150-300 kHz) - Long distance, stable signals",
                        "MW": "Medium Wave (530-1700 kHz) - Regional AM broadcasting",
                        "SW": "Shortwave (3-30 MHz) - International broadcasting",
                        "VHF": "VHF (30-300 MHz) - Local FM, aviation",
                        "UHF": "UHF (300-3000 MHz) - Digital, satellite",
                    },
                    "suggestions": [
                        "Try other bands: LW, MW, SW",
                        "Use general search: sdr_search_stations('')",
                        "Search by country: sdr_get_stations_by_country('France')",
                    ],
                },
            }

        by_country = {}
        for station in stations:
            if station.country not in by_country:
                by_country[station.country] = []
            by_country[station.country].append(station)

        sorted_countries = sorted(by_country.items(), key=lambda x: len(x[1]), reverse=True)

        return {
            "status": "success",
            "band": band.upper(),
            "total_stations": len(stations),
            "countries": len(by_country),
            "stations": [
                {
                    "name": s.name,
                    "callsign": s.callsign,
                    "frequency_mhz": s.frequency_mhz,
                    "frequency_khz": s.frequency_khz,
                    "country": s.country,
                    "city": s.city,
                    "type": s.station_type.value,
                    "power_kw": s.power,
                    "language": s.language,
                    "description": s.description,
                }
                for s in stations
            ],
            "conversation": {
                "message": f"Found {len(stations)} station(s) on {band.upper()} band across {len(by_country)} countries.",
                "band_characteristics": {
                    "LW": "Longwave stations provide extremely stable, long-distance signals perfect for news and cultural programming.",
                    "MW": "Medium wave offers regional coverage with AM broadcasting, great for local news and entertainment.",
                    "SW": "Shortwave enables international broadcasting, reaching across continents with high power transmitters.",
                    "VHF": "VHF band includes local FM stations and specialized communications.",
                    "UHF": "UHF covers modern digital broadcasting and satellite communications.",
                }.get(band.upper(), ""),
                "top_countries": [
                    {
                        "country": country,
                        "station_count": len(stations_list),
                        "examples": [s.name for s in stations_list[:2]],
                    }
                    for country, stations_list in sorted_countries[:3]
                ],
                "frequency_range": {
                    "LW": "150-300 kHz",
                    "MW": "530-1700 kHz",
                    "SW": "3-30 MHz",
                    "VHF": "30-300 MHz",
                    "UHF": "300-3000 MHz",
                }.get(band.upper(), ""),
                "recommended_stations": [
                    s.callsign for s in stations if s.station_type == StationType.INTERNATIONAL or s.power > 100
                ][:3],
            },
        }

    except ValueError:
        return {
            "status": "invalid_band",
            "conversation": {
                "message": f"'{band}' is not a valid band. Available bands: LW, MW, SW, VHF, UHF",
                "band_guide": {
                    "LW": "Longwave (150-300 kHz) - BBC, ORF, France Inter",
                    "MW": "Medium Wave (530-1700 kHz) - Regional AM stations",
                    "SW": "Shortwave (3-30 MHz) - BBC World Service, VOA, RFI",
                    "VHF": "VHF (30-300 MHz) - FM radio, military communications",
                    "UHF": "UHF (300-3000 MHz) - Digital radio, satellite",
                },
            },
        }
    except Exception as e:
        logger.error("Error getting stations by band: %s", e, exc_info=True)
        return {
            "status": "error",
            "conversation": {
                "message": f"Failed to retrieve {band} band stations: {e}",
                "fallback": "Try: sdr_search_stations('') for all available stations",
            },
            "error": str(e),
        }


async def get_program_schedule(station_callsign: str, day: str | None = None) -> dict[str, Any]:
    """Get program schedule for a specific radio station."""
    try:
        db = get_frequency_database()
        station = db.stations.get(station_callsign)

        if not station:
            possible_matches = [
                s
                for s in db.get_all_stations()
                if station_callsign.lower() in s.callsign.lower() or station_callsign.lower() in s.name.lower()
            ]

            return {
                "status": "station_not_found",
                "conversation": {
                    "message": f"Station '{station_callsign}' not found in database.",
                    "possible_matches": [
                        {"callsign": s.callsign, "name": s.name, "frequency": f"{s.frequency_mhz:.1f} MHz"}
                        for s in possible_matches[:3]
                    ]
                    if possible_matches
                    else [],
                    "suggestions": [
                        "Use: sdr_search_stations('BBC') to find BBC stations",
                        "Try: sdr_get_stations_by_band('LW') for longwave stations",
                        "Check callsign spelling",
                    ],
                },
            }

        current_program = db.get_current_program(station_callsign)
        schedule = db.get_program_schedule(station_callsign, day)

        schedule_by_day = {}
        for program in schedule:
            for day_name in program.days:
                if day_name not in schedule_by_day:
                    schedule_by_day[day_name] = []
                schedule_by_day[day_name].append(
                    {
                        "name": program.name,
                        "description": program.description,
                        "start_time": program.start_time.strftime("%H:%M"),
                        "end_time": program.end_time.strftime("%H:%M"),
                        "language": program.language,
                        "genre": program.genre,
                    }
                )

        for day_programs in schedule_by_day.values():
            day_programs.sort(key=lambda x: x["start_time"])

        return {
            "status": "success",
            "station": {
                "name": station.name,
                "callsign": station.callsign,
                "frequency_mhz": station.frequency_mhz,
                "frequency_khz": station.frequency_khz,
                "band": station.band.value,
                "country": station.country,
                "language": station.language,
                "description": station.description,
            },
            "current_program": {
                "name": current_program.name if current_program else "Off-air/Unknown",
                "description": current_program.description if current_program else "",
                "start_time": current_program.start_time.strftime("%H:%M") if current_program else "",
                "end_time": current_program.end_time.strftime("%H:%M") if current_program else "",
                "language": current_program.language if current_program else "",
                "genre": current_program.genre if current_program else "",
            }
            if current_program or schedule
            else None,
            "schedule": schedule_by_day,
            "conversation": {
                "message": f"Program schedule for {station.name} ({station.callsign})",
                "current_status": f"Currently playing: {current_program.name}"
                if current_program
                else "Current program information not available",
                "schedule_summary": {
                    "total_programs": len(schedule),
                    "days_scheduled": len(schedule_by_day),
                    "languages": list(set(p.language for p in schedule)) if schedule else [],
                    "genres": list(set(p.genre for p in schedule)) if schedule else [],
                },
                "next_steps": [
                    f"Listen now: sdr_tune_preset('{station.callsign.lower().replace(' ', '_')}')",
                    "Get real-time spectrum: sdr_get_spectrum()",
                    "Search similar stations: sdr_get_stations_by_country('" + station.country + "')",
                ],
                "schedule_note": "Times shown in UTC. Local time may vary. Program schedules are subject to change.",
            },
        }

    except Exception as e:
        logger.error("Error getting program schedule: %s", e, exc_info=True)
        return {
            "status": "error",
            "conversation": {
                "message": f"Failed to retrieve program schedule: {e}",
                "suggestions": [
                    "Check station callsign spelling",
                    "Try station search first: sdr_search_stations('')",
                    "Some stations may not have schedule data available",
                ],
            },
            "error": str(e),
        }


async def get_stations_by_country(country: str) -> dict[str, Any]:
    """Get all radio stations from a specific country."""
    try:
        db = get_frequency_database()
        stations = db.get_stations_by_country(country)

        if not stations:
            all_countries = list(set(s.country for s in db.get_all_stations()))
            similar_countries = [
                c
                for c in all_countries
                if country.lower() in c.lower() or any(word in c.lower() for word in country.lower().split())
            ]

            return {
                "status": "no_stations",
                "conversation": {
                    "message": f"No stations found for '{country}' in our database.",
                    "available_countries": all_countries[:10],
                    "similar_countries": similar_countries[:5] if similar_countries else [],
                    "suggestions": [
                        "Check country name spelling",
                        "Try major countries: France, Germany, United Kingdom",
                        "Use general search: sdr_search_stations('')",
                    ],
                },
            }

        by_band = {}
        for station in stations:
            band_name = station.band.value
            if band_name not in by_band:
                by_band[band_name] = []
            by_band[band_name].append(station)

        by_type = {}
        for station in stations:
            type_name = station.station_type.value
            if type_name not in by_type:
                by_type[type_name] = []
            by_type[type_name].append(station)

        sorted_stations = sorted(stations, key=lambda x: x.power, reverse=True)

        return {
            "status": "success",
            "country": country,
            "total_stations": len(stations),
            "bands": list(by_band.keys()),
            "station_types": list(by_type.keys()),
            "stations": [
                {
                    "name": s.name,
                    "callsign": s.callsign,
                    "frequency_mhz": s.frequency_mhz,
                    "frequency_khz": s.frequency_khz,
                    "band": s.band.value,
                    "city": s.city,
                    "type": s.station_type.value,
                    "power_kw": s.power,
                    "language": s.language,
                    "description": s.description[:150] + "..." if len(s.description) > 150 else s.description,
                }
                for s in stations
            ],
            "conversation": {
                "message": f"Found {len(stations)} station(s) broadcasting from {country} across {len(by_band)} frequency bands.",
                "band_breakdown": {band_name: len(lst) for band_name, lst in by_band.items()},
                "type_breakdown": {stype: len(lst) for stype, lst in by_type.items()},
                "top_stations": [
                    {
                        "name": s.name,
                        "callsign": s.callsign,
                        "band": s.band.value,
                        "power": f"{s.power} kW",
                        "reason": "High power international broadcaster"
                        if s.station_type == StationType.INTERNATIONAL
                        else "Major national station"
                        if s.power > 100
                        else "Regional broadcaster",
                    }
                    for s in sorted_stations[:3]
                ],
                "cultural_insights": {
                    "United Kingdom": "Home of the BBC, with extensive public broadcasting and international services.",
                    "France": "Strong public broadcasting tradition with cultural focus and international reach.",
                    "Germany": "Diverse broadcasting landscape with strong regional and international services.",
                    "Austria": "Rich cultural broadcasting with emphasis on classical music and public service.",
                }.get(country, f"{country} has a diverse broadcasting landscape with various station types."),
                "next_steps": [
                    "Tune to top station: sdr_tune_frequency(" + str(sorted_stations[0].frequency_mhz) + ")",
                    "Get program schedule: sdr_get_program_schedule('" + sorted_stations[0].callsign + "')",
                    "Explore by band: sdr_get_stations_by_band('LW')",
                    "Search within country: sdr_search_stations('', country='" + country + "')",
                ],
            },
        }

    except Exception as e:
        logger.error("Error getting stations by country: %s", e, exc_info=True)
        return {
            "status": "error",
            "conversation": {
                "message": f"Failed to retrieve stations for {country}: {e}",
                "fallback": "Try: sdr_search_stations('') for all available stations",
            },
            "error": str(e),
        }


async def get_frequency_database_stats() -> dict[str, Any]:
    """Get comprehensive statistics about the frequency database."""
    try:
        db = get_frequency_database()
        all_stations = db.get_all_stations()

        by_band = {}
        by_country = {}
        by_type = {}
        languages = set()
        total_power = 0

        for station in all_stations:
            band_name = station.band.value
            by_band[band_name] = by_band.get(band_name, 0) + 1
            by_country[station.country] = by_country.get(station.country, 0) + 1
            type_name = station.station_type.value
            by_type[type_name] = by_type.get(type_name, 0) + 1
            languages.add(station.language)
            total_power += station.power

        return {
            "status": "success",
            "database_stats": {
                "total_stations": len(all_stations),
                "countries_covered": len(by_country),
                "bands_covered": len(by_band),
                "station_types": len(by_type),
                "languages_supported": len(languages),
                "total_transmitter_power": total_power,
                "average_power_per_station": round(total_power / len(all_stations), 1) if all_stations else 0,
            },
            "breakdown": {
                "by_band": by_band,
                "by_country": dict(sorted(by_country.items(), key=lambda x: x[1], reverse=True)),
                "by_type": by_type,
                "languages": sorted(list(languages)),
            },
            "top_countries": [
                {"country": country_name, "stations": count}
                for country_name, count in sorted(by_country.items(), key=lambda x: x[1], reverse=True)[:5]
            ],
            "conversation": {
                "message": f"SDR Frequency Database contains {len(all_stations)} stations from {len(by_country)} countries.",
                "key_insights": [
                    f"Most active band: {max(by_band.items(), key=lambda x: x[1])[0]} with {max(by_band.items(), key=lambda x: x[1])[1]} stations",
                    f"Best represented country: {max(by_country.items(), key=lambda x: x[1])[0]} with {max(by_country.items(), key=lambda x: x[1])[1]} stations",
                    f"Total transmitter power: {total_power} kW across all stations",
                    f"Languages supported: {len(languages)} ({', '.join(sorted(list(languages))[:3])}...)",
                ],
                "historical_context": "This database eliminates the traditional SDR challenge of manually tracking frequencies and schedules.",
                "capabilities": [
                    "Real-time station lookup by name, frequency, or location",
                    "Program schedules with current playing information",
                    "Signal strength expectations and propagation guidance",
                    "Cultural and historical context for each station",
                ],
            },
        }

    except Exception as e:
        logger.error("Error getting database stats: %s", e, exc_info=True)
        return {
            "status": "error",
            "conversation": {
                "message": f"Failed to retrieve database statistics: {e}",
                "note": "The frequency database provides comprehensive station information.",
            },
            "error": str(e),
        }
