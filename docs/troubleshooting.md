---
title: Troubleshooting
subtitle: Technical Notes Writer (tnw)
---

# Troubleshooting

## Mermaid diagram rendering fails (Puppeteer sandbox error)

### Problem

When building the book with `tnw build_book html book.yaml`, the Mermaid filter fails with an error similar to:

```
Error: Failed to launch the browser process: 
[...]:FATAL:content/browser/zygote_host/zygote_host_impl_linux.cc:130] 
No usable sandbox! If you are running on Ubuntu 23.10+ or another Linux distro 
that has disabled unprivileged user namespaces with AppArmor, [...]
```

The build aborts with `pandoc failed with exit code 83` and `*.html was not built`.

### Cause

The `mermaid-cli` (`mmdc`) uses Puppeteer to launch Chromium in headless mode to render Mermaid diagrams as SVG. In some Linux environments (containers, VMs, or systems with AppArmor/restricted user namespaces), Chromium's sandbox cannot start, causing Puppeteer to fail.

### Solution

Create a Puppeteer configuration to disable the sandbox and wrap `mmdc` so it uses it.

#### 1) Create a Puppeteer config file

Create `puppeteer-config.json` at the root of the project (or in a `scripts/` directory):

```json
{
  "args": [
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-dev-shm-usage",
    "--disable-accelerated-2d-canvas",
    "--disable-gpu"
  ]
}
```

#### 2) Create an `mmdc` wrapper

Replace or wrap the existing `mmdc` binary so it passes the config. For example, in `~/.local/bin/mmdc`:

```bash
#!/bin/bash
exec node /home/dieesrod/.local/lib/node_modules/@mermaid-js/mermaid-cli/src/cli.js -p /path/to/your/project/puppeteer-config.json "$@"
```

Make it executable:

```bash
chmod +x ~/.local/bin/mmdc
```

#### 3) Rebuild

```bash
cd report
tnw build_book html book.yaml
```

### Notes

- This is an environment workaround, not a bug in `tnw`. `tnw` just calls `mmdc` from `PATH`.
- Disabling the sandbox reduces Chromium's security isolation. Only use this in trusted local environments (dev/CI in controlled contexts).
- For portability, commit `puppeteer-config.json` and a project-local wrapper (e.g., `scripts/mmdc`) and document adding it to `PATH` when building.
