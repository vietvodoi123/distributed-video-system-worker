import subprocess

subprocess.run([
    "ffprobe",
    "-hide_banner",
    str(r"tmp\8c271a8f-9d53-4114-8537-8f13f0c3ef7e\downloads\batches\91406729-a795-4040-b1f6-e5086d684014\chapters\1\video\layers\mc_loop.mp4")
])