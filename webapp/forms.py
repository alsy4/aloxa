import re

from flask_wtf import FlaskForm
from wtforms import PasswordField, RadioField, StringField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, ValidationError

_TIME_RE = re.compile(r"^(\d{2}):(\d{2})$")


def parse_times(raw: str) -> list[str]:
    """Split a comma- or newline-separated string into HH:MM tokens."""
    return [t.strip() for t in re.split(r"[,\n]", raw or "") if t.strip()]


def _validate_times(form, field):
    times = parse_times(field.data)
    if not times:
        raise ValidationError("At least one scheduled time is required.")
    for t in times:
        match = _TIME_RE.match(t)
        if not match:
            raise ValidationError(f"Invalid time format: '{t}'. Use HH:MM.")
        hh, mm = int(match.group(1)), int(match.group(2))
        if not (0 <= hh < 24 and 0 <= mm < 60):
            raise ValidationError(f"Invalid time: '{t}'.")


class LoginForm(FlaskForm):
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Log in")


class MedicationForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=100)])
    dosage = StringField("Dosage", validators=[DataRequired(), Length(max=50)])
    information = StringField("Info (optional)", validators=[Optional(), Length(max=255)])
    container = RadioField(
        "Container",
        choices=[("A", "A"), ("B", "B")],
        default="A",
        validators=[DataRequired()],
    )
    times = StringField(
        "Scheduled times",
        validators=[DataRequired(), _validate_times],
        description="Comma-separated HH:MM, e.g. 08:00, 22:00",
    )
    submit = SubmitField("Save")
