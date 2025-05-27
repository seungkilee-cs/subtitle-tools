import re
import argparse
from datetime import datetime, timedelta


def parse_srt_time(timestr):
    return datetime.strptime(timestr, "%H:%M:%S,%f")


def format_srt_time(dt):
    return dt.strftime("%H:%M:%S,%f")[:-3]


def split_text(text, n):
    # Split by sentences (periods), fallback to lines if not enough
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    if len(sentences) < n:
        # Fallback: split by lines
        lines = text.strip().split("\n")
        if len(lines) < n:
            # Fallback: split by words
            words = text.strip().split()
            avg = len(words) // n
            return [" ".join(words[i * avg : (i + 1) * avg]) for i in range(n - 1)] + [
                " ".join(words[(n - 1) * avg :])
            ]
        avg = len(lines) // n
        return [" ".join(lines[i * avg : (i + 1) * avg]) for i in range(n - 1)] + [
            " ".join(lines[(n - 1) * avg :])
        ]
    avg = len(sentences) // n
    return [" ".join(sentences[i * avg : (i + 1) * avg]) for i in range(n - 1)] + [
        " ".join(sentences[(n - 1) * avg :])
    ]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--line", type=int, required=True, help="SRT line number to split"
    )
    parser.add_argument("--split", type=int, required=True, help="Number of splits")
    parser.add_argument("input", help="Input SRT file")
    parser.add_argument("output", help="Output SRT file")
    args = parser.parse_args()

    # Read and parse SRT blocks
    with open(args.input, encoding="utf-8") as f:
        content = f.read()
    blocks = re.split(r"\n{2,}", content.strip())

    # Find the block to split
    idx = args.line - 1
    block = blocks[idx]
    lines = block.strip().split("\n")
    time_line = lines[1]
    text = " ".join(lines[2:]).replace("\n", " ")

    start_str, end_str = re.match(r"(.+) --> (.+)", time_line).groups()
    start = parse_srt_time(start_str)
    end = parse_srt_time(end_str)
    total_duration = end - start
    part_duration = total_duration / args.split

    # Split text
    text_parts = split_text(text, args.split)
    # Build new blocks
    new_blocks = []
    for i in range(args.split):
        part_start = start + i * part_duration
        part_end = part_start + part_duration
        if i == args.split - 1:
            part_end = end  # Ensure last part ends exactly at the original end
        new_blocks.append(
            [
                "",  # Placeholder for line number
                f"{format_srt_time(part_start)} --> {format_srt_time(part_end)}",
                text_parts[i],
            ]
        )

    # Replace original block with new blocks, renumber
    new_blocks_str = []
    for i, nb in enumerate(new_blocks):
        new_blocks_str.append("\n".join([str(args.line + i), nb[1], nb[2]]))
    # Insert new blocks and update following block numbers
    blocks = blocks[:idx] + new_blocks_str + blocks[idx + 1 :]
    # Renumber all blocks
    final_blocks = []
    for i, b in enumerate(blocks):
        blines = b.strip().split("\n")
        blines[0] = str(i + 1)
        final_blocks.append("\n".join(blines))

    # Write output
    with open(args.output, "w", encoding="utf-8") as f:
        f.write("\n\n".join(final_blocks) + "\n")


if __name__ == "__main__":
    main()
