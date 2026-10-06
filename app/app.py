import logging
import os

from flask import Flask, jsonify, redirect, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

db = SQLAlchemy()
PRIORITIES = ("low", "medium", "high")


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    done = db.Column(db.Boolean, default=False, nullable=False)
    priority = db.Column(db.String(10), default="medium", nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "done": self.done,
            "priority": self.priority,
        }


def create_app(config=None):
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL", "sqlite:///tasks.db"
    )
    app.config["APP_VERSION"] = os.environ.get("APP_VERSION", "dev")
    if config:
        app.config.update(config)
    db.init_app(app)

    try:
        with app.app_context():
            db.create_all()
    except Exception as exc:  # the database may not be reachable yet
        logging.warning("Database not ready at startup: %s", exc)

    @app.get("/health")
    def health():
        return jsonify(status="ok", version=app.config["APP_VERSION"])

    @app.get("/ready")
    def ready():
        try:
            db.session.execute(text("SELECT 1"))
            db.create_all()
        except Exception:
            db.session.rollback()
            return jsonify(status="not ready"), 503
        return jsonify(status="ready")

    @app.get("/")
    def index():
        tasks = Task.query.order_by(Task.id.desc()).all()
        return render_template(
            "index.html",
            tasks=tasks,
            priorities=PRIORITIES,
            version=app.config["APP_VERSION"],
        )

    @app.post("/tasks")
    def create_task_form():
        title = request.form.get("title", "").strip()
        priority = request.form.get("priority", "medium")
        if title and priority in PRIORITIES:
            db.session.add(Task(title=title, priority=priority))
            db.session.commit()
        return redirect(url_for("index"))

    @app.post("/tasks/<int:task_id>/toggle")
    def toggle_task(task_id):
        task = db.get_or_404(Task, task_id)
        task.done = not task.done
        db.session.commit()
        return redirect(url_for("index"))

    @app.post("/tasks/<int:task_id>/delete")
    def delete_task(task_id):
        task = db.get_or_404(Task, task_id)
        db.session.delete(task)
        db.session.commit()
        return redirect(url_for("index"))

    @app.get("/api/tasks")
    def list_tasks():
        tasks = Task.query.order_by(Task.id).all()
        return jsonify([t.to_dict() for t in tasks])

    @app.post("/api/tasks")
    def create_task():
        data = request.get_json(silent=True) or {}
        title = str(data.get("title", "")).strip()
        priority = data.get("priority", "medium")
        if not title:
            return jsonify(error="title is required"), 400
        if priority not in PRIORITIES:
            return jsonify(error="priority must be low, medium or high"), 400
        task = Task(title=title, priority=priority)
        db.session.add(task)
        db.session.commit()
        return jsonify(task.to_dict()), 201

    return app
