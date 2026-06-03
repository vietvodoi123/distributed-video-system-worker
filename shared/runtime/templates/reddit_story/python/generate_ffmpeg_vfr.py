import os

# Đường dẫn đến file concat.txt
concat_file = "concat.txt"

with open(concat_file, "r", encoding="utf-8") as f:
    lines = f.readlines()

entries = []
current_file = None

for line in lines:
    line = line.strip()
    if line.startswith("file"):
        current_file = line.split("file")[1].strip().strip("'").strip('"')
    elif line.startswith("duration") and current_file:
        duration = float(line.split("duration")[1].strip())
        entries.append((current_file, duration))
        current_file = None

# Bắt đầu sinh filter_complex và input
inputs = []
filters = []
concat_labels = []

for idx, (filename, duration) in enumerate(entries):
    label = f"[v{idx}]"
    # Add input
    inputs.append(f"-loop 1 -t {duration:.3f} -i \"{filename}\"")
    # Filter để set pts
    filters.append(f"[{idx}:v]setpts=PTS-STARTPTS,format=yuva420p{label}")
    concat_labels.append(label)

# Ghép filter
filter_complex = "; ".join(filters) + f"; {''.join(concat_labels)}concat=n={len(entries)}:v=1:a=0[outv]"

# Build ffmpeg command
cmd = f"ffmpeg {' '.join(inputs)} -filter_complex \"{filter_complex}\" -map \"[outv]\" -vsync vfr -pix_fmt yuv420p output.mp4"

print("Lệnh FFmpeg:")
print(cmd)
