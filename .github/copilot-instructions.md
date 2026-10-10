# Copilot instructions (SDR-MCP)

You have Software Defined Radio tools: RTL-SDR device control, spectrum analysis, station databases, GNU Radio demod.

Before starting work: `sdr_device(operation="health")`, `sdr_device(operation="list")`, `sdr_spectrum(operation="spectrum")`.
At end of work: `sdr_gnuradio(operation="stop")` if the sidecar runs.
