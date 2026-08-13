# lammps-plotter

Fast CLI plotter for LAMMPS log files. Autodetects thermo columns, colors
each thermo block separately, warns when the thermo style changes
mid-log instead of silently dropping data.

Built because `matplotlib`-from-a-notebook is slow to iterate on for
multi-stage runs (minimize → heat → melt → quench → equilibrate), each
stage often with a different `thermo_style`.

## Install

Requires [uv](https://docs.astral.sh/uv/).

```
git clone <this-repo>
cd lammps-plotter
uv sync
```

Run without installing:
```
uv run lammps-plot run.log -x Step -y TotEng
```

Or install as a standalone command available from anywhere:
```
uv tool install --editable .
lammps-plot run.log -x Step -y TotEng
```
`--editable` means edits to the source take effect immediately, no reinstall.

## Usage

```
lammps-plot LOGFILE -x COL -y COL [-z COL] [options]

-x, -y, -z      column names, exact header text (e.g. Step, Temp, TotEng)
                -z is optional; passing it makes a 3D plot
--every N       plot every Nth point, downsamples dense runs (default 1)
--smooth N      rolling-mean overlay window, 0 = off (default 0)
--save PATH     save to file instead of opening an interactive window
--dpi N         dpi for --save (default 150)
--markersize N  marker size, 2D only (default 1.5)
--linewidth N   line width (default 0.8)
```

Examples:
```
lammps-plot run.log -x Step -y TotEng
lammps-plot run.log -x Step -y Temp --every 5 --smooth 20
lammps-plot run.log -x Step -y Temp -z TotEng --every 10 --save traj.png
```

## How it works

**Block detection.** A block is a header line (whitespace-separated,
all non-numeric tokens) followed by contiguous numeric rows. A block
ends at the first line that doesn't parse as `len(header)` floats —
blank line, `Loop time of ...`, a new header, etc. Each `run` /
`minimize` command in a LAMMPS input typically produces one block.

**Coloring.** Each block gets its own color from a fixed cycle, no
legend. A color change always means either a thermo-style change or a
break in logging (new `run` command) — never a mid-block gradient, so
you can visually spot restarts and stage boundaries at a glance.

**Missing columns.** If the requested `-x`/`-y`/`-z` column isn't in a
block (thermo_style changed for that stage), the tool warns to stderr
with the block index and line range, and skips that block — leaving a
visible gap rather than fabricating a connection across it. If the
column reappears in a later block, that block still gets a new color
(the block/color counter keeps advancing across skipped blocks), so a
break followed by a resume is visually distinguishable from one
continuous run.

**Interleaved noise.** LAMMPS sometimes writes `WARNING:`/`ERROR:`
lines directly into the thermo stream mid-run (e.g. the "too many
warnings, further warnings suppressed" message). These are skipped as
noise inside a block rather than terminating it — otherwise a single
stray warning line silently drops the rest of that run's data.

**Smoothing.** `--smooth N` overlays a plain centered rolling mean
(`numpy.convolve`), not a Kalman filter — no process/measurement noise
model to tune, just a moving average on top of the raw jittery line.

## Performance notes

- 2D: markers + line, fine up to the tens of thousands of points; use
  `--every` for anything denser.
- 3D: markers are dropped automatically (mplot3d has no fast path for
  per-point marker rendering) and `ax.computed_zorder` is disabled
  (skips mplot3d's expensive per-artist depth sort on every
  rotate/redraw). Still not GPU-accelerated — for very dense 3D
  trajectories, push `--every` harder.
