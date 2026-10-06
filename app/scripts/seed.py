import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import Task, create_app, db  # noqa: E402

SAMPLES = [
    ("Write Terraform code", "high"),
    ("Set up VMware network", "medium"),
    ("Create automation user", "medium"),
    ("Install Ansible", "low"),
    ("Write prepare-nodes playbook", "medium"),
    ("Bootstrap Kubernetes cluster", "high"),
    ("Apply Calico CNI", "high"),
    ("Build Docker image", "medium"),
    ("Configure GitHub Actions", "medium"),
    ("Deploy app on Kubernetes", "high"),
]


def main():
    app = create_app()
    with app.app_context():
        db.create_all()
        added = 0
        for title, priority in SAMPLES:
            if not Task.query.filter_by(title=title).first():
                db.session.add(Task(title=title, priority=priority))
                added += 1
        db.session.commit()
        print(f"Seeded {added} new tasks, total: {Task.query.count()}")


if __name__ == "__main__":
    main()
