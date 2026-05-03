import hmac
from functools import wraps
from urllib.parse import urlparse

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from config import WEB_PASSWORD
from webapp.forms import LoginForm

bp = Blueprint("auth", __name__)

SESSION_KEY = "authenticated"


def is_authenticated() -> bool:
    return bool(session.get(SESSION_KEY))


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not is_authenticated():
            return redirect(url_for("auth.login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


@bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        if hmac.compare_digest(form.password.data or "", WEB_PASSWORD):
            session.clear()
            session[SESSION_KEY] = True
            target = request.args.get("next") or url_for("main.index")
            parsed = urlparse(target)
            if parsed.netloc or parsed.scheme or not target.startswith("/"):
                target = url_for("main.index")
            return redirect(target)
        flash("Incorrect password.", "error")
    return render_template("login.html", form=form)


@bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
