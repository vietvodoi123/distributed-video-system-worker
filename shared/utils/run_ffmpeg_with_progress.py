import subprocess
import time

def run_ffmpeg_with_progress(cmd):
    process = subprocess.Popen(
        cmd,
        stderr=subprocess.PIPE,
        stdout=subprocess.DEVNULL,  # 🔥 không in stdout
        text=True
    )

    _, stderr = process.communicate()

    if process.returncode != 0:
        print("❌ FFmpeg error:")
        print(stderr)
        raise RuntimeError("FFmpeg failed")




def run_ffmpeg_safe(cmd, max_idle=900):

    process = subprocess.Popen(
        cmd,
        stderr=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        text=True,
        bufsize=1,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
    )

    last_output = time.time()

    try:
        for line in process.stderr:
            # Nếu có bất kỳ output nào thì cập nhật thời gian
            last_output = time.time()

            # Chỉ in khi là lỗi thực sự
            if "error" in line.lower() or "failed" in line.lower():
                print("FFmpeg ERROR:", line.strip())

            if time.time() - last_output > max_idle:
                process.kill()
                raise RuntimeError("FFmpeg bị treo (idle timeout)")

        process.wait()

    finally:
        if process.poll() is None:
            process.kill()

    if process.returncode != 0:
        raise RuntimeError("FFmpeg failed")

    print("✅ FFmpeg hoàn thành")
