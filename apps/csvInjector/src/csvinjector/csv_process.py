import csv
from datetime import datetime
from futile.logging import LoggerMixin


class csvProcessor(LoggerMixin):
    def __init__(self,
                 path,
                 delim=",",
                 quotechar="|",
                 time_format="%d/%m/%Y-%H:%M",
                 duration=0,
                 date_classifier="date"):
        with open(path, 'rb') as csvfile:
            self.csv_data = list(csv.DictReader(csvfile))
        self.time_format = time_format
        self.duration = duration
        self.date_classifier = date_classifier

        # Date Processing
        if isinstance(self.date_classifier, list):
            self._join_multiple_timestamps()
        self._date_string_to_date_object()
        self.csv_data = sorted(
            self.csv_data, key=lambda k: k[self.date_classifier])
        self._date_to_seconds_since_first()
        self._scale_to_duration()

    def _join_multiple_timestamps(self):
        for entry in self.csv_data:
            entry["timestamp_schedule"] = "-".join([entry[k] for k in self.date_classifier])
            for date_c in self.date_classifier:
                entry.pop(date_c, None)
        self.date_classifier = "timestamp_schedule"
        self.time_format = "-".join(self.time_format)

    def _date_string_to_date_object(self):
        for entry in self.csv_data:
            entry[self.date_classifier] = datetime.strptime(
                entry[self.date_classifier], self.time_format)

    def _date_to_seconds_since_first(self):
        for entry in self.csv_data:
            if 'first' in locals():
                entry[self.date_classifier] = (
                    entry[self.date_classifier] - first).total_seconds()
            else:
                first = entry[self.date_classifier]
                entry[self.date_classifier] = 0.0

    def _scale_to_duration(self):
        if self.duration <= 0:
            return
        scaling_factor = self.duration / self.csv_data[-1][
            self.date_classifier]
        self.logger.debug("Set scaling factor to {}".format(scaling_factor))
        for entry in self.csv_data:
            entry[self.date_classifier] = entry[
                self.date_classifier] * scaling_factor

    def getList(self):
        return self.csv_data


if __name__ == "__main__":
    p = csvProcessor("example.csv", duration=300)
    for e in p.csv_data:
        print(e)
