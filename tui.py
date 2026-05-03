"""Textual TUI for Aloxa.

Standalone tool. The primary front-end is the Flask web UI launched via
`python3 web.py`. `main.py` keeps the original interactive menu. Run this
file directly (`python3 tui.py`) for the Textual terminal UI. Reuses
MedicationManager so data + scheduler logic are shared.
"""
from datetime import datetime

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    Static,
)

from database import init_db
from medication import MedicationManager
from medication.scheduler import ReminderScheduler


class ContainerPanel(Static):
    """One panel per container: header + DataTable of its medications (max 3 shown)."""

    MAX_VISIBLE = 3

    def __init__(self, container: str, **kw):
        super().__init__(**kw)
        self.container = container

    def compose(self) -> ComposeResult:
        yield Label(f"[b]Container {self.container}[/b]", id=f"title-{self.container}", classes="panel-title")
        yield DataTable(id=f"table-{self.container}", zebra_stripes=True)
        yield Label("", id=f"overflow-{self.container}", classes="overflow-note")

    def on_mount(self):
        table = self.query_one(DataTable)
        table.add_columns("ID", "Name", "Dosage", "Times", "Info")

    def refresh_rows(self, meds):
        table = self.query_one(DataTable)
        table.clear()

        in_container = [m for m in meds if m.container == self.container]
        visible = in_container[: self.MAX_VISIBLE]
        hidden = len(in_container) - len(visible)

        for med in visible:
            table.add_row(
                str(med.id),
                med.name,
                med.dosage,
                ", ".join(med.scheduled_times) or "—",
                med.information or "",
            )

        title = self.query_one(f"#title-{self.container}", Label)
        title.update(
            f"[b]Container {self.container}[/b]  [dim]({len(in_container)}/{self.MAX_VISIBLE})[/dim]"
        )
        overflow = self.query_one(f"#overflow-{self.container}", Label)
        overflow.update(
            f"[yellow]+{hidden} more not shown (container over capacity)[/yellow]" if hidden > 0 else ""
        )


class AddMedicationScreen(ModalScreen[dict | None]):
    """Modal dialog for adding a medication. Returns a dict or None on cancel."""

    CSS = """
    AddMedicationScreen { align: center middle; }
    #dialog { width: 60; height: auto; padding: 1 2; background: $panel; border: thick $primary; }
    Input { margin-bottom: 1; }
    #buttons { height: 3; align: right middle; }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label("[b]Add Medication[/b]")
            yield Input(placeholder="Name", id="name")
            yield Input(placeholder="Dosage (e.g. 500mg)", id="dosage")
            yield Input(placeholder="Info (optional)", id="info")
            yield Input(placeholder="Times, comma-separated (08:00,22:00)", id="times")
            yield Input(placeholder="Container (A or B)", id="container")
            with Horizontal(id="buttons"):
                yield Button("Cancel", id="cancel")
                yield Button("Add", id="add", variant="primary")

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "cancel":
            self.dismiss(None)
            return
        if event.button.id != "add":
            return

        name = self.query_one("#name", Input).value.strip()
        dosage = self.query_one("#dosage", Input).value.strip()
        info = self.query_one("#info", Input).value.strip()
        raw_times = self.query_one("#times", Input).value.strip()
        container = self.query_one("#container", Input).value.strip().upper()

        if not name or not dosage or container not in ("A", "B"):
            self.app.bell()
            return
        times = [t.strip() for t in raw_times.split(",") if t.strip()]

        self.dismiss({
            "name": name, "dosage": dosage, "information": info,
            "times": times, "container": container,
        })


class ConfirmDeleteScreen(ModalScreen[bool]):
    """Yes/No confirmation for deleting a medication."""

    CSS = """
    ConfirmDeleteScreen { align: center middle; }
    #dialog { width: 60; height: auto; padding: 1 2; background: $panel; border: thick $error; }
    #buttons { height: 3; align: right middle; margin-top: 1; }
    """

    def __init__(self, med_id: int, med_name: str):
        super().__init__()
        self.med_id = med_id
        self.med_name = med_name

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label("[b]Delete Medication[/b]")
            yield Label(f"Delete [{self.med_id}] {self.med_name}?")
            yield Label("[dim]This also removes its scheduled times and intake history.[/dim]")
            with Horizontal(id="buttons"):
                yield Button("Cancel", id="cancel")
                yield Button("Delete", id="confirm", variant="error")

    def on_button_pressed(self, event: Button.Pressed):
        self.dismiss(event.button.id == "confirm")


class DeleteByIdScreen(ModalScreen[int | None]):
    """Prompt for a medication ID when no row is selected."""

    CSS = """
    DeleteByIdScreen { align: center middle; }
    #dialog { width: 60; height: auto; padding: 1 2; background: $panel; border: thick $primary; }
    #buttons { height: 3; align: right middle; margin-top: 1; }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label("[b]Delete Medication[/b]")
            yield Label("[dim]Tip: focus a row in a container and press 'd' to skip this prompt.[/dim]")
            yield Input(placeholder="Medication ID", id="med_id")
            with Horizontal(id="buttons"):
                yield Button("Cancel", id="cancel")
                yield Button("Next", id="next", variant="primary")

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "cancel":
            self.dismiss(None)
            return
        raw = self.query_one("#med_id", Input).value.strip()
        if not raw.isdigit():
            self.app.bell()
            return
        self.dismiss(int(raw))


class AloxaTUI(App):
    CSS = """
    #clock { dock: top; height: 1; padding: 0 1; background: $boost; }
    #panels { height: 1fr; }
    ContainerPanel { width: 1fr; padding: 1; border: round $primary; margin: 1; }
    .panel-title { margin-bottom: 1; }
    .overflow-note { margin-top: 1; }
    #pending-title { margin: 0 1; }
    #pending { height: 10; border: round $warning; margin: 0 1 1 1; padding: 0 1; }
    """

    BINDINGS = [
        ("a", "add_medication", "Add"),
        ("d", "delete_medication", "Delete"),
        ("t", "mark_taken", "Taken"),
        ("m", "mark_missed", "Missed"),
        ("r", "refresh", "Refresh"),
        ("q", "quit", "Quit"),
    ]

    clock_text = reactive("")

    def __init__(self, manager: MedicationManager, scheduler: "ReminderScheduler | None" = None):
        super().__init__()
        self.manager = manager
        self.scheduler = scheduler
        if scheduler is not None:
            scheduler.on_alert = self._on_alert

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        yield Static(id="clock")
        with Horizontal(id="panels"):
            yield ContainerPanel("A")
            yield ContainerPanel("B")
        yield Label("[b]Pending reminders[/b]", id="pending-title")
        yield DataTable(id="pending", zebra_stripes=True)
        yield Footer()

    def on_mount(self):
        pending = self.query_one("#pending", DataTable)
        pending.add_columns("Reminder", "Med", "Scheduled", "Since", "Status")
        self._tick_clock()
        self.set_interval(1.0, self._tick_clock)
        self.set_interval(5.0, self.action_refresh)
        self.action_refresh()

    def _tick_clock(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.query_one("#clock", Static).update(f"🕒 {now}")

    def action_refresh(self):
        meds = self.manager.get_all_medications()
        for panel in self.query(ContainerPanel):
            panel.refresh_rows(meds)

        pending_table = self.query_one("#pending", DataTable)
        pending_table.clear()
        now = datetime.now().strftime("%H:%M")
        for r in self.manager.get_pending_reminders():
            due_marker = "🔔" if r["scheduled_time"] <= now else "⏳"
            alerts = r.get("alert_count", 0) or 0
            pending_table.add_row(
                str(r["id"]),
                r["name"],
                r["scheduled_time"],
                str(r["reminded_at"]),
                f"{due_marker} {r['status']} (x{alerts})",
            )

        header_label = self.query_one("#pending-title", Label)
        header_label.update(
            f"[b]Pending reminders[/b]  [dim]({pending_table.row_count} active)[/dim]"
        )

    def action_add_medication(self):
        def handle(result):
            if result:
                self.manager.add_medication(**result)
                self.action_refresh()
        self.push_screen(AddMedicationScreen(), handle)

    def action_delete_medication(self):
        med_id, med_name = self._focused_row()
        if med_id is not None:
            self._confirm_delete(med_id, med_name)
            return

        def got_id(entered):
            if entered is None:
                return
            med = self.manager.get_medication(entered)
            if med is None:
                self.notify(f"No medication with id {entered}.", severity="error")
                return
            self._confirm_delete(med.id, med.name)

        self.push_screen(DeleteByIdScreen(), got_id)

    def _focused_row(self) -> tuple[int | None, str]:
        """If a ContainerPanel's DataTable is focused with a valid cursor row, return its med id+name."""
        focused = self.focused
        if not isinstance(focused, DataTable) or focused.id not in ("table-A", "table-B"):
            return None, ""
        if focused.row_count == 0 or focused.cursor_row < 0:
            return None, ""
        try:
            row = focused.get_row_at(focused.cursor_row)
        except Exception:
            return None, ""
        return int(row[0]), str(row[1])

    def _on_alert(self, reminder: dict, alert_count: int):
        """Scheduler callback — runs on the scheduler thread, so marshal to the UI thread."""
        ordinal = "Reminder" if alert_count == 1 else f"Repeat #{alert_count - 1}"
        message = (
            f"{ordinal}: take {reminder['name']} {reminder['dosage']} "
            f"(scheduled {reminder['scheduled_time']})"
        )
        severity = "warning" if alert_count == 1 else "error"
        self.call_from_thread(self._show_alert, message, severity)

    def _show_alert(self, message: str, severity: str):
        self.notify(message, severity=severity, timeout=10)
        self.action_refresh()

    def action_mark_taken(self):
        self._respond_to_focused_reminder("taken")

    def action_mark_missed(self):
        self._respond_to_focused_reminder("missed")

    def _respond_to_focused_reminder(self, status: str):
        pending = self.query_one("#pending", DataTable)
        if self.focused is not pending:
            self.notify(
                "Focus the pending reminders table first (click it or Tab to it).",
                severity="warning",
            )
            return
        if pending.row_count == 0 or pending.cursor_row < 0:
            self.bell()
            return
        try:
            row = pending.get_row_at(pending.cursor_row)
        except Exception:
            self.bell()
            return

        log_id = int(row[0])
        med_name = str(row[1])
        if status == "taken":
            self.manager.mark_taken(log_id)
        else:
            self.manager.mark_missed(log_id)
        self.notify(f"Marked '{med_name}' as {status}.")
        self.action_refresh()

    def _confirm_delete(self, med_id: int, med_name: str):
        def handle(confirmed):
            if not confirmed:
                return
            if self.manager.delete_medication(med_id):
                self.notify(f"Deleted '{med_name}'.")
            else:
                self.notify(f"Medication {med_id} not found.", severity="error")
            self.action_refresh()
        self.push_screen(ConfirmDeleteScreen(med_id, med_name), handle)


def main():
    init_db()
    manager = MedicationManager()

    scheduler = ReminderScheduler(manager)
    app = AloxaTUI(manager, scheduler)
    scheduler.start()
    try:
        app.run()
    finally:
        scheduler.stop()


if __name__ == "__main__":
    main()
