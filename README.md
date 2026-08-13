<h1 align="center">🤖 WeCoder.AI</h1>

<p align="center">
  <strong>An offline-first, multi-AI collaborative framework for local software development and automation.</strong>
</p>

<p align="center">
  <a href="#"><img src="https://img.shields.io/badge/Python-3.11+-blue?style=flat-square&logo=python" alt="Python"></a>
  <a href="#"><img src="https://img.shields.io/badge/License-MIT-green?style=flat-square" alt="License"></a>
</p>

---

## ✨ Overview

**WeCoder.AI** is an innovative, offline-first framework designed to orchestrate **dual-agent reasoning** for local software development. By combining the architectural vision of one AI with the execution capabilities of another (e.g., *Qwen2.5-Coder* and *Gemini*), WeCoder enables models to debate, design, and write highly optimized code—all without relying on constant cloud connectivity.

Built for **low-resource environments**, it ensures that powerful, multi-agent AI coding assistance is accessible, private, and exceptionally efficient.

---

## 🚀 Key Features

- 🧠 **Dual-Agent Reasoning:** Separates logic into an *Architect* (System Design) and a *Lead Developer* (Code Implementation) for robust, debate-driven problem solving.
- 📴 **Offline-First Architecture:** Run local models entirely on your machine. No data leaves your network, ensuring maximum privacy and zero latency.
- ⚡ **Low-Resource Efficiency:** Optimized context management and model quantization allow heavy reasoning on consumer-grade hardware.
- 🔄 **Automated Code Refinement:** The Architect critiques the Lead Developer's code in real-time, reducing bugs and improving architecture adherence.
- 🧩 **Multi-Model Support:** Mix and match local models (Ollama, LM Studio) and cloud APIs based on your hardware capabilities.

---

## ⚙️ How It Works

WeCoder.AI utilizes a continuous feedback loop between two distinct AI personas:

> **Status:** The capabilities described above are **planned**, not yet
> implemented. The repository currently contains the Phase 01 engineering
> foundation described below.
>
> **Implemented:** installable Python 3.11+ package, the `wecoder` CLI
> (`--help`, `--version`, `init`, `status`, `models list`, `models ping`), typed
> configuration (TOML + `WECODER_*` env + defaults), structured logging, an
> error hierarchy, and a vendor-neutral model boundary with Ollama and
> OpenAI-compatible HTTP adapters.
>
> **Planned (future phases):** tools, the coding agent, multi-agent
> collaboration, memory, and everything else in the vision above.

---

## 🛠 Development

Requires Python 3.11+. Phase 02 adds the model boundary: configure `ollama` or `openai_compat`, inspect adapters with `wecoder models list`, and explicitly check connectivity with `wecoder models ping`. The latter may contact a provider (and cloud usage may cost money). Tools and the agent are not implemented.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

wecoder --help
wecoder status        # print version, config source, python version
wecoder init          # write a default project config to .wecoder/config.toml
```

Run checks:

```bash
pytest          # test suite
ruff check .    # lint
mypy wecoder    # type check
```

Configuration precedence (highest last wins): built-in defaults → `~/.wecoder/config.toml`
→ `<cwd>/.wecoder/config.toml` → `WECODER_*` environment variables → CLI flags.
