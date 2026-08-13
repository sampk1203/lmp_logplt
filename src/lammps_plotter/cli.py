import argparse
import sys


def main():
    p = argparse.ArgumentParser(
        prog="lammps-plot",
        description="Fast LAMMPS log plotter. Autodetects thermo columns per block, "
        "one color per thermo block, warns on thermo-style discontinuities.",
    )
    p.add_argument("logfile", help="path to LAMMPS log file")
    p.add_argument("-x", required=True, help="x column name (e.g. Step)")
    p.add_argument("-y", required=True, help="y column name (e.g. TotEng)")
    p.add_argument("-z", default=None, help="z column name (optional, makes 3D plot)")
    p.add_argument("--every", type=int, default=1, help="plot every Nth point (default 1)")
    p.add_argument(
        "--smooth", type=int, default=0,
        help="rolling-mean window size overlaid on raw data (0 = off)",
    )
    p.add_argument("--save", default=None, help="save to file instead of showing interactively")
    p.add_argument("--dpi", type=int, default=150, help="dpi for --save (default 150)")
    p.add_argument("--markersize", type=float, default=1.5, help="marker size (default 1.5)")
    p.add_argument("--linewidth", type=float, default=0.8, help="line width (default 0.8)")
    args = p.parse_args()

    import matplotlib
    if args.save:
        matplotlib.use("Agg")
    # else: leave default backend for interactive show()

    from .parser import parse_log
    from .plotting import build_series, plot

    blocks = parse_log(args.logfile)
    if not blocks:
        print("error: no thermo blocks found in log file", file=sys.stderr)
        sys.exit(1)

    series, total = build_series(blocks, args.x, args.y, args.z, args.every, args.smooth)
    if not series:
        print("error: requested column(s) never present together in any block", file=sys.stderr)
        sys.exit(1)

    fig = plot(series, total, args.x, args.y, args.z, args.markersize, args.linewidth, args.smooth)

    if args.save:
        fig.savefig(args.save, dpi=args.dpi)
        print(f"saved: {args.save}")
    else:
        import matplotlib.pyplot as plt
        plt.show()


if __name__ == "__main__":
    main()
