import time


class UsageLogger:

    def start(self):
        return time.perf_counter()

    def end(self, start_time):
        elapsed = time.perf_counter() - start_time

        print(
            f"Processing Time: {elapsed * 1000:.2f} ms"
        )


usage_logger = UsageLogger()