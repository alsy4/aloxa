import json
import queue

from flask import (
    Blueprint,
    Response,
    abort,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    stream_with_context,
    url_for,
)

from medication.cli import load_mock_data
from webapp.forms import MedicationForm, parse_times

bp = Blueprint("main", __name__)


def _manager():
    return current_app.config["MANAGER"]


@bp.route("/")
def index():
    m = _manager()
    return render_template(
        "index.html",
        pending=m.get_pending_reminders(),
        recent=m.get_all_intake_history()[:5],
        med_count=len(m.get_all_medications()),
    )


# ── Medications ───────────────────────────────────────────────

@bp.route("/medications")
def medications_list():
    return render_template(
        "medications/list.html",
        meds=_manager().get_all_medications(),
    )


@bp.route("/medications/new", methods=["GET", "POST"])
def medications_new():
    form = MedicationForm()
    if form.validate_on_submit():
        _manager().add_medication(
            form.name.data.strip(),
            form.dosage.data.strip(),
            (form.information.data or "").strip(),
            parse_times(form.times.data),
            container=form.container.data,
        )
        flash(f"Added '{form.name.data.strip()}'.", "success")
        return redirect(url_for("main.medications_list"))
    return render_template("medications/form.html", form=form, mode="new", med=None)


@bp.route("/medications/<int:med_id>/edit", methods=["GET", "POST"])
def medications_edit(med_id):
    med = _manager().get_medication(med_id)
    if not med:
        abort(404)
    form = MedicationForm()
    if request.method == "GET":
        form.name.data = med.name
        form.dosage.data = med.dosage
        form.information.data = med.information
        form.container.data = med.container
        form.times.data = ", ".join(med.scheduled_times)
    if form.validate_on_submit():
        _manager().update_medication(
            med_id,
            name=form.name.data.strip(),
            dosage=form.dosage.data.strip(),
            information=(form.information.data or "").strip(),
            container=form.container.data,
            times=parse_times(form.times.data),
        )
        flash(f"Updated '{form.name.data.strip()}'.", "success")
        return redirect(url_for("main.medications_list"))
    return render_template("medications/form.html", form=form, mode="edit", med=med)


@bp.route("/medications/<int:med_id>/delete", methods=["POST"])
def medications_delete(med_id):
    if _manager().delete_medication(med_id):
        flash("Medication deleted.", "success")
    else:
        flash("Medication not found.", "error")
    return redirect(url_for("main.medications_list"))


# ── Intake / pending ─────────────────────────────────────────

@bp.route("/pending")
def pending_list():
    return render_template(
        "pending.html",
        pending=_manager().get_pending_reminders(),
    )


@bp.route("/intake/<int:log_id>/taken", methods=["POST"])
def intake_taken(log_id):
    _manager().mark_taken(log_id)
    flash("Marked as taken.", "success")
    return redirect(request.referrer or url_for("main.pending_list"))


@bp.route("/intake/<int:log_id>/missed", methods=["POST"])
def intake_missed(log_id):
    _manager().mark_missed(log_id)
    flash("Marked as missed.", "success")
    return redirect(request.referrer or url_for("main.pending_list"))


# ── History ──────────────────────────────────────────────────

@bp.route("/history")
def history():
    m = _manager()
    med_filter = request.args.get("med", type=int)
    date_filter = (request.args.get("date") or "").strip() or None

    if med_filter:
        med = m.get_medication(med_filter)
        if not med:
            abort(404)
        entries = m.get_intake_history(med_filter, date_filter)
        for e in entries:
            e["name"] = med.name
            e["dosage"] = med.dosage
        entries.reverse()  # newest first, matching get_all_intake_history
    else:
        entries = m.get_all_intake_history()
        if date_filter:
            entries = [
                e for e in entries
                if (e.get("reminded_at") or "").startswith(date_filter)
            ]

    return render_template(
        "history.html",
        entries=entries,
        meds=m.get_all_medications(),
        med_filter=med_filter,
        date_filter=date_filter,
    )


# ── Admin ────────────────────────────────────────────────────

@bp.route("/admin/reset", methods=["POST"])
def admin_reset():
    _manager().reset_all()
    flash("All medications and intake history have been reset.", "success")
    return redirect(url_for("main.index"))


@bp.route("/admin/mock-data", methods=["POST"])
def admin_mock_data():
    load_mock_data(_manager())
    flash("Mock data loaded — alerts will fire shortly.", "success")
    return redirect(url_for("main.index"))


# ── Live updates ─────────────────────────────────────────────

@bp.route("/api/pending")
def api_pending():
    """Snapshot of pending reminders as JSON for client-side refresh."""
    return jsonify({"pending": _manager().get_pending_reminders()})


@bp.route("/events")
def events():
    """Server-Sent Events stream. Yields alert events as the scheduler fires them."""
    broker = current_app.config["BROKER"]
    q = broker.subscribe()

    def stream():
        try:
            yield "event: connected\ndata: {}\n\n"
            while True:
                try:
                    event = q.get(timeout=15)
                except queue.Empty:
                    yield ": heartbeat\n\n"
                    continue
                yield (
                    f"event: {event['type']}\n"
                    f"data: {json.dumps(event)}\n\n"
                )
        finally:
            broker.unsubscribe(q)

    return Response(
        stream_with_context(stream()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
