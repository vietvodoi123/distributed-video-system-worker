import psutil

from shared.scheduling.resource_profile import (
    ResourceProfile
)
import subprocess

class WorkerResourceProfiler:

    @classmethod
    def detect(cls) -> ResourceProfile:

        # =========================
        # CPU
        # =========================

        cpu = psutil.cpu_count(
            logical=True
        ) or 1

        # =========================
        # RAM (GB)
        # =========================

        ram_gb = (

            psutil
            .virtual_memory()
            .total

            / 1024 ** 3
        )

        # =========================
        # NETWORK
        # =========================

        network = 20

        # =========================
        # DISK
        # =========================

        disk_io = 20

        # =========================
        # GPU
        # =========================

        gpu = cls.detect_gpu_score()

        return ResourceProfile(

            cpu=round(cpu),

            ram=round(ram_gb),

            gpu=gpu,

            network=network,

            disk_io=disk_io
        )



    @staticmethod
    def detect_gpu_score():

        try:

            result = subprocess.run(

                [
                    "nvidia-smi",
                    "--query-gpu=name",
                    "--format=csv,noheader"
                ],

                capture_output=True,

                text=True,

                timeout=5
            )

            if result.returncode != 0:
                return 0

            gpu_name = result.stdout.strip()

            print(
                "[WorkerProfiler] GPU:",
                gpu_name
            )

            return 40

        except Exception:

            return 0