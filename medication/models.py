from dataclasses import dataclass, field


@dataclass
class Medication:
    id: int | None
    name: str
    dosage: str
    information: str
    scheduled_times: list[str] = field(default_factory=list)  # ["08:00", "22:00"]
