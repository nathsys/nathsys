<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:0f2027,100:2c5364&height=180&section=header&text=Nathanael%20Mohanu&fontSize=44&fontColor=ffffff&fontAlignY=38&desc=Embedded%20%7C%20Hardware%20security%20%7C%20Performance&descSize=16&descAlignY=60" alt="Nathanael (Nathan) Mohanu: Embedded, hardware security, performance" />

<img src="https://readme-typing-svg.demolab.com?font=Fira+Code&weight=500&size=20&pause=1500&color=36BCF7&center=true&vCenter=true&width=600&lines=Embedded+systems;Hardware+security;Rust%2C+C+and+C%2B%2B" alt="Embedded systems, hardware security, Rust, C and C++" />

<br />

[![TU Delft](https://img.shields.io/badge/TU%20Delft-MSc%20Computer%20%26%20Embedded%20Systems-00A6D6?style=flat-square)](https://www.tudelft.nl)
[![Open to internships](https://img.shields.io/badge/Open%20to-internships%20(NL)-2ea44f?style=flat-square)](https://www.linkedin.com/in/nathanael-mohanu-7a14b4183/)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Nathanael%20Mohanu-0A66C2?style=flat-square&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/nathanael-mohanu-7a14b4183/)

</div>

MSc student in Computer & Embedded Systems Engineering at TU Delft. I work on embedded systems, hardware security and performance-focused systems code. Looking for internships in the Netherlands (embedded, firmware, hardware security and software).

## ⚙️ Projects

| Project | What it is |
|---|---|
| **[bootloader](https://github.com/nathsys/bootloader)** `Rust` `no_std` `STM32` | Slotted UART bootloader for STM32F4, under 16 KB. Validates an application's vector table, sets VTOR and jumps to it. Updates arrive as CRC-32 framed messages and go through a sector-guarded flash driver. Host-side unit tests for the CRC, parser and sector map. |
| **[pyke](https://github.com/nathsys/pyke)** `C++20` `BMI2` `AVX-512` | Single-threaded perft engine tuned purely for throughput: 2.4 billion positions/s on perft(7) without hashing (Ryzen 9 7900X). Templates, PEXT tables and AVX-512 counting. Exact counts through depth 9, plus the perftcheck corpus. |
| **[sunsnake](https://github.com/nathsys/sunsnake)** `C++20` `CMake` | Reusable chess move-generation library. About 500 million positions/s on perft(7) single-threaded, exact perft through depth 8, fuzzed against Stockfish, with CI. |

## 🔐 Research

**Bachelor thesis (Leiden University, LIACS): side-channel analysis of the PROACT chip prototype.**

<details>
<summary>What I did and found</summary>

- Captured 160,000 power traces from four cryptographic co-processors on an FPGA prototype (two AES, Ascon, Xoodyak).
- Wrote the C firmware and the Python pipelines for trace capture and for TVLA, SNR and CPA analysis.
- All four co-processors showed significant data-dependent leakage, and I recovered the full AES-128 key from both AES cores with first-order CPA.

</details>

## 🧰 Skills

<p>
<img src="https://skillicons.dev/icons?i=rust,c,cpp,python,java,linux,git,cmake,githubactions&perline=9" alt="Rust, C, C++, Python, Java, Linux, Git, CMake, GitHub Actions" />
</p>

**Embedded and hardware:** ARM Cortex-M (STM32), RISC-V, FPGA (Artix-7), UART, ChipWhisperer<br />
**Security and analysis:** side-channel analysis (TVLA, SNR, CPA), power-trace capture

<!--
Optional: animated contribution snake. Needs a GitHub Action (Platane/snk) in this repo; see its README.
-->

<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:0f2027,100:2c5364&height=100&section=footer" alt="" />

</div>
