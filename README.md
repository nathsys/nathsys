<p align="center">
  <img src="banner.jpg" alt="Pixel-art retro computer on a dark background" width="736" />
</p>

<p align="center">
  <a href="https://www.linkedin.com/in/nathanael-mohanu-7a14b4183/"><img src="https://img.shields.io/badge/LINKEDIN-b8c2b9?style=for-the-badge&labelColor=382b26" alt="LinkedIn" /></a>
  <img src="https://img.shields.io/badge/TU%20DELFT-MSc%20Computer%20%26%20Embedded%20Systems-b8c2b9?style=for-the-badge&labelColor=382b26" alt="TU Delft, MSc Computer and Embedded Systems Engineering" />
  <img src="https://img.shields.io/badge/OPEN%20TO-INTERNSHIPS%20(NL)-b8c2b9?style=for-the-badge&labelColor=382b26" alt="Open to internships in the Netherlands" />
</p>

## $ whoami

```text
Nathanael (Nathan) Mohanu
MSc student, Computer & Embedded Systems Engineering, TU Delft

focus     embedded systems, hardware security, performance-focused code
looking   internships in the Netherlands (embedded, firmware, hardware security, software)
```

<p align="center">
  <img src="metrics.svg" alt="GitHub stats: stars, commits, streak and contribution average" width="560" />
</p>

## $ ls projects/

| Project | What it is |
|---|---|
| **[bootloader](https://github.com/nathsys/bootloader)** `Rust` `no_std` `STM32` | Slotted UART bootloader for STM32F4, under 16 KB. Validates an application's vector table, sets VTOR and jumps to it. Updates arrive as CRC-32 framed messages and go through a sector-guarded flash driver. Host-side unit tests for the CRC, parser and sector map. |
| **[pyke](https://github.com/nathsys/pyke)** `C++20` `BMI2` `AVX-512` | Single-threaded perft engine tuned purely for throughput: 2.4 billion positions/s on perft(7) without hashing (Ryzen 9 7900X). Templates, PEXT tables and AVX-512 counting. Exact counts through depth 9, plus the perftcheck corpus. |
| **[sunsnake](https://github.com/nathsys/sunsnake)** `C++20` `CMake` | Reusable chess move-generation library. About 500 million positions/s on perft(7) single-threaded, exact perft through depth 8, fuzzed against Stockfish, with CI. |

## $ cat thesis.txt

```text
Bachelor thesis, Leiden University (LIACS)
Side-channel analysis of the PROACT chip prototype

- 160,000 power traces from four crypto co-processors on an FPGA
  (two AES, Ascon, Xoodyak)
- C firmware and Python pipelines for capture, TVLA, SNR and CPA
- significant data-dependent leakage in all four co-processors
- full AES-128 key recovered from both AES cores (first-order CPA)
```

## $ ./skills --list

```text
languages   Rust, C, C++, Python, Java
embedded    ARM Cortex-M (STM32), RISC-V, FPGA (Artix-7), UART, ChipWhisperer
security    side-channel analysis (TVLA, SNR, CPA), power-trace capture
tools       Git, GitHub Actions, CMake, Linux, Cargo, probe-rs
```

## $ contact

[LinkedIn](https://www.linkedin.com/in/nathanael-mohanu-7a14b4183/)
