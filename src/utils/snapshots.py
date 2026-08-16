import shutil
from datetime import datetime
from pathlib import Path


class SnapshotManager:
    def __init__(self, working_directory):
        self.working_directory = Path(working_directory)
        self.snapshot_dir = self.working_directory / ".snapshots"
        self.snapshot_dir.mkdir(exist_ok=True)
        # Instance attribute, NOT a class attribute — a function stored on the
        # class would be bound as a method and receive `self` as an extra arg.
        self.ignore = shutil.ignore_patterns(
            ".snapshots", ".git", "venv", "__pycache__", "*.pyc"
        )

    def create_snapshot(self, label):
        """Copy the current working directory into a timestamped snapshot folder."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        snapshot_id = f"{timestamp}_{label}"
        destination = self.snapshot_dir / snapshot_id
        shutil.copytree(self.working_directory, destination, ignore=self.ignore)
        return snapshot_id

    def list_snapshots(self):
        snapshots = []
        for path in self.snapshot_dir.iterdir():
            if path.is_dir():
                snapshots.append({"id": path.name})
        return snapshots

    def restore_snapshot(self, snapshot_id):
        source = self.snapshot_dir / snapshot_id
        if not source.is_dir():
            return {"success": False, "error": f"Snapshot not found: {snapshot_id}"}
        shutil.copytree(source, self.working_directory, dirs_exist_ok=True)
        return {"success": True, "result": f"Restored snapshot {snapshot_id}"}

if __name__ == "__main__":
    sm = SnapshotManager(".")
    snap_id = sm.create_snapshot("test")
    print("created:", snap_id)
    print("copied files:", sorted(p.name for p in (sm.snapshot_dir / snap_id).iterdir()))
    print("snapshots:", sm.list_snapshots())
    print("restore:", sm.restore_snapshot(snap_id))
    print("restore bad id:", sm.restore_snapshot("does not exist"))