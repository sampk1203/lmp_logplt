import sys
import numpy as np


def moving_average(arr: np.ndarray, window: int) -> np.ndarray:
    """Simple centered rolling mean. Shrinks window at edges (no NaN padding)."""
    if window <= 1:
        return arr
    kernel = np.ones(window) / window
    # 'same' mode + edge correction via counting overlapping kernel weight
    smoothed = np.convolve(arr, kernel, mode="same")
    counts = np.convolve(np.ones_like(arr), kernel, mode="same")
    return smoothed / counts


def get_color(block_index: int, total_blocks: int):
    import matplotlib as mpl

    if total_blocks <= 20:
        cmap = mpl.colormaps["tab20"]
        return cmap(block_index % 20)
    cmap = mpl.colormaps["hsv"]
    return cmap((block_index / max(total_blocks, 1)) % 1.0)


def build_series(blocks, x_name, y_name, z_name, every, smooth):
    """For each block, extract (x, y[, z]) if columns present.
    Returns list of dicts: {index, x, y, z, y_smooth, z_smooth}
    Warns to stderr when a requested column is missing in a block.
    """
    total = len(blocks)
    series = []
    for b in blocks:
        missing = [c for c in (x_name, y_name, z_name) if c and c not in b.columns]
        if missing:
            print(
                f"warn: block {b.index} (lines {b.start_line}-{b.end_line}): "
                f"thermo style changed, missing column(s): {', '.join(missing)}",
                file=sys.stderr,
            )
            continue
        x = b.data[x_name][::every]
        y = b.data[y_name][::every]
        entry = {"index": b.index, "x": x, "y": y}
        if smooth > 1:
            entry["y_smooth"] = moving_average(y, smooth)
        if z_name:
            z = b.data[z_name][::every]
            entry["z"] = z
            if smooth > 1:
                entry["z_smooth"] = moving_average(z, smooth)
        series.append(entry)
    return series, total


def plot(series, total_blocks, x_name, y_name, z_name, markersize, linewidth, smooth):
    import matplotlib.pyplot as plt

    plt.rcParams["path.simplify"] = True
    plt.rcParams["path.simplify_threshold"] = 1.0
    plt.rcParams["agg.path.chunksize"] = 20000

    fig = plt.figure()
    if z_name:
        from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

        ax = fig.add_subplot(111, projection="3d")
        # mplot3d recomputes per-artist depth sorting on every redraw;
        # this is the main source of interactive lag. Turning it off
        # draws artists in call order instead (fine for a single
        # continuous trajectory) and is a large speedup.
        ax.computed_zorder = False
    else:
        ax = fig.add_subplot(111)

    # markers are the other big lag source in 3D (mplot3d has no fast
    # marker path for point clouds); skip them there, keep for 2D.
    use_markers = z_name is None

    for entry in series:
        color = get_color(entry["index"], total_blocks)
        if z_name:
            ax.plot(
                entry["x"], entry["y"], entry["z"],
                color=color, linewidth=linewidth,
                antialiased=False,
            )
            if smooth > 1:
                ax.plot(
                    entry["x"], entry["y_smooth"], entry["z_smooth"],
                    color=color, linewidth=linewidth * 2.5, alpha=0.9,
                    antialiased=False,
                )
        else:
            ax.plot(
                entry["x"], entry["y"],
                color=color, linewidth=linewidth,
                marker="o" if use_markers else None,
                markersize=markersize,
            )
            if smooth > 1:
                ax.plot(
                    entry["x"], entry["y_smooth"],
                    color=color, linewidth=linewidth * 2.5, alpha=0.9,
                )

    ax.set_xlabel(x_name)
    ax.set_ylabel(y_name)
    if z_name:
        ax.set_zlabel(z_name)
    fig.tight_layout()
    return fig
