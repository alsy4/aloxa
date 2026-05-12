from gpiozero import LED

from database import get_connection

COMPARTMENT_PINS = {"A": 5, "B": 6}

_leds: dict[str, LED] | None = None


def _init():
    global _leds
    if _leds is None:
        _leds = {c: LED(pin) for c, pin in COMPARTMENT_PINS.items()}


def refresh():
    """Light each compartment's LED iff it has a pending reminder."""
    _init()
    conn = get_connection()
    rows = conn.execute(
        "SELECT DISTINCT m.container FROM intake_log il "
        "JOIN medications m ON il.medication_id = m.id "
        "WHERE il.status = 'pending'"
    ).fetchall()
    conn.close()
    pending = {r["container"] for r in rows}
    for compartment, led in _leds.items():
        if compartment in pending:
            led.on()
        else:
            led.off()


def all_off():
    if _leds is None:
        return
    for led in _leds.values():
        led.off()
