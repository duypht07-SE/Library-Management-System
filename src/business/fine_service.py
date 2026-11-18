"""Fine calculations and cash payment workflow (FR-RDR-08, FR-LIB-09:13)."""
from datetime import datetime

from common.exceptions import ValidationError
from data.repositories import FineRepository
from models import Fine, FineReason, Librarian, Reader


class FineService:
    """Applies fine rules and persists fine/payment records."""

    def __init__(self, fines: FineRepository) -> None:
        self.fines = fines

    @staticmethod
    def calculate_late_amount(days_late: int, daily_rate: int) -> int:
        if days_late < 0 or daily_rate < 0:
            raise ValueError("Days late and daily rate cannot be negative.")
        return days_late * daily_rate

    def view_fines(self, reader: Reader) -> list[Fine]:
        if reader.user_id is None:
            return []
        return reader.view_fines(self.fines.find_for_reader(reader.user_id))

    def all_fines(self) -> list[dict]:
        """Return counter records for the Librarian payment screen."""
        return self.fines.find_all()

    def record_fine(self, librarian: Librarian, borrow_id: int,
                    reason: str, amount: int) -> Fine:
        if amount < 1:
            raise ValidationError("Fine amount must be greater than 0 VND.")
        if not self.fines.loan_exists(borrow_id):
            raise ValidationError("Borrowing record was not found.")
        try:
            fine = librarian.record_fine(borrow_id, FineReason(reason), amount)
            return self.fines.save(fine)
        except ValueError as error:
            raise ValidationError(str(error)) from error

    def record_payment(self, librarian: Librarian, fine_id: int,
                       at: datetime) -> Fine:
        fine = self.fines.find_by_id(fine_id)
        if fine is None:
            raise ValidationError("Fine was not found.")
        try:
            librarian.record_payment(fine, at)
        except ValueError as error:
            raise ValidationError(str(error)) from error
        if not self.fines.mark_paid(fine_id, at.isoformat(sep=" ")):
            raise ValidationError("This fine has already been paid.")
        return fine

    def create_return_fines(self, borrow_id: int, days_late: int,
                            daily_rate: int, condition: str,
                            damage_amount: int | None = None) -> list[Fine]:
        """Create separate late and damaged/lost fines for the 0.4.0 flow."""
        if not self.fines.loan_exists(borrow_id):
            raise ValidationError("Borrowing record was not found.")
        reasons = []
        late_amount = self.calculate_late_amount(days_late, daily_rate)
        if late_amount:
            reasons.append(Fine(None, borrow_id, FineReason.LATE_RETURN,
                                late_amount))
        if condition in {"DAMAGED", "LOST"}:
            if not damage_amount or damage_amount < 1:
                raise ValidationError(
                    "Enter a fine amount greater than 0 VND for a damaged "
                    "or lost book.")
            reasons.append(Fine(None, borrow_id, FineReason(condition),
                                damage_amount))
        elif condition != "INTACT":
            raise ValidationError("Choose a valid book condition.")
        return self.fines.save_many(reasons) if reasons else []
