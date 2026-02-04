"""Scheduler module for periodic execution."""
import time
from datetime import datetime


class Scheduler:
    def __init__(self, interval_hours: int):
        self.interval_seconds = interval_hours * 3600

    def run(self, callback):
        """Run callback periodically."""
        print(f"Scheduler started. Interval: {self.interval_seconds // 3600} hours")
        print(f"Next run at: {self._get_next_run_time()}")

        while True:
            try:
                callback()
                print(f"Completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"Next run at: {self._get_next_run_time()}")
                time.sleep(self.interval_seconds)
            except KeyboardInterrupt:
                print("\nScheduler stopped by user")
                break
            except Exception as e:
                print(f"Error in scheduler: {e}")
                print(f"Retrying in {self.interval_seconds} seconds...")
                time.sleep(self.interval_seconds)

    def _get_next_run_time(self) -> str:
        """Calculate next run time."""
        next_time = datetime.now().fromtimestamp(
            time.time() + self.interval_seconds
        )
        return next_time.strftime('%Y-%m-%d %H:%M:%S')
