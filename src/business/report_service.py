"""Administrator reports (FR-ADM-05)."""
from datetime import datetime

from common.exceptions import ValidationError
from data.repositories import ReportRepository
from models import Administrator


class ReportService:
    """Builds month or year summaries from stored library records."""

    def __init__(self, reports: ReportRepository) -> None:
        self.reports = reports

    def view_reports(self, admin: Administrator, period: str,
                     value: str) -> dict:
        if period == "month":
            try:
                start_date = datetime.strptime(value, "%Y-%m")
            except ValueError as error:
                raise ValidationError("Choose a valid month.") from error
            end_date = (datetime(start_date.year + 1, 1, 1)
                        if start_date.month == 12 else
                        datetime(start_date.year, start_date.month + 1, 1))
            label = start_date.strftime("%B %Y")
        elif period == "year":
            try:
                year = int(value)
                if year < 2000 or year > 2200:
                    raise ValueError
            except (TypeError, ValueError) as error:
                raise ValidationError("Choose a valid year.") from error
            start_date = datetime(year, 1, 1)
            end_date = datetime(year + 1, 1, 1)
            label = str(year)
        else:
            raise ValidationError("Choose a month or year report.")
        data = self.reports.monthly(start_date.isoformat(sep=" "),
                                    end_date.isoformat(sep=" "))
        return admin.view_reports({"period": period, "value": value,
                                   "label": label, **data})
