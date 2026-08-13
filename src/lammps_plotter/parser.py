"""Parse LAMMPS log files into thermo blocks.

A block = one header line (whitespace-separated column names, all
non-numeric tokens) followed by contiguous numeric rows. Block ends at
the first line that doesn't parse as len(header) floats (blank line,
"Loop time of ...", a new header, etc).
"""

from dataclasses import dataclass
import numpy as np


@dataclass
class Block:
    index: int
    columns: list[str]
    data: dict[str, np.ndarray]  # column name -> float array
    start_line: int
    end_line: int


def _is_float(tok: str) -> bool:
    try:
        float(tok)
        return True
    except ValueError:
        return False


def _is_header(tokens: list[str]) -> bool:
    return len(tokens) >= 2 and all(not _is_float(t) for t in tokens)


def _is_noise(line: str) -> bool:
    # LAMMPS interleaves these into the thermo stream mid-run (e.g. the
    # "too many warnings" message can land right after a header, before
    # any data row). Skip them without ending the block.
    s = line.lstrip()
    return s.startswith("WARNING:") or s.startswith("ERROR:")


def parse_log(path: str) -> list[Block]:
    with open(path, "r", errors="replace") as f:
        lines = f.readlines()

    blocks: list[Block] = []
    i = 0
    n = len(lines)
    block_idx = 0

    while i < n:
        tokens = lines[i].split()
        if _is_header(tokens):
            ncols = len(tokens)
            header = tokens
            rows: list[list[float]] = []
            start_line = i + 1
            j = i + 1
            while j < n:
                row_tokens = lines[j].split()
                if len(row_tokens) == ncols and all(_is_float(t) for t in row_tokens):
                    rows.append([float(t) for t in row_tokens])
                    j += 1
                elif _is_noise(lines[j]):
                    j += 1
                else:
                    break
            if rows:
                arr = np.array(rows, dtype=float)
                data = {header[k]: arr[:, k] for k in range(ncols)}
                blocks.append(
                    Block(
                        index=block_idx,
                        columns=header,
                        data=data,
                        start_line=start_line,
                        end_line=j,
                    )
                )
                block_idx += 1
            i = j
        else:
            i += 1

    return blocks
