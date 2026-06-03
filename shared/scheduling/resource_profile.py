from dataclasses import dataclass


@dataclass
class ResourceProfile:

    cpu: float = 0

    ram: float = 0

    gpu: float = 0

    network: float = 0

    disk_io: float = 0

    queue_pressure: float = 0

    CPU_WEIGHT: float = 1
    RAM_WEIGHT: float = 1
    GPU_WEIGHT: float = 4
    NETWORK_WEIGHT: float = 1
    DISK_WEIGHT: float = 1
    QUEUE_WEIGHT: float = 1

    # =====================================
    # HELPERS
    # =====================================


    def total_cost(self) -> float:
        return (

                self.cpu * self.CPU_WEIGHT +

                self.ram * self.RAM_WEIGHT +

                self.gpu * self.GPU_WEIGHT +

                self.network * self.NETWORK_WEIGHT +

                self.disk_io * self.DISK_WEIGHT +

                self.queue_pressure * self.QUEUE_WEIGHT
        )

    def to_dict(self) -> dict:

        return {

            "cpu": self.cpu,

            "ram": self.ram,

            "gpu": self.gpu,

            "network": self.network,

            "disk_io": self.disk_io,

            "queue_pressure": self.queue_pressure,
        }

    @classmethod
    def from_dict(
        cls,
        data: dict | None
    ):

        if not data:

            return cls()

        return cls(

            cpu=data.get("cpu", 0),

            ram=data.get("ram", 0),

            gpu=data.get("gpu", 0),

            network=data.get(
                "network",
                0
            ),

            disk_io=data.get(
                "disk_io",
                0
            ),

            queue_pressure=data.get(
                "queue_pressure",
                0
            ),
        )