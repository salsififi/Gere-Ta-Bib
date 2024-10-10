"""Models for transactions"""

from datetime import timedelta, date
from typing import NoReturn

from peewee import Model, DateField, IntegerField, CharField, BooleanField

from gere_ta_bib.models.copies import BookCopy, FilmCopy, MusicCopy, BaseCopy
from gere_ta_bib.models.users import User
from gere_ta_bib.utils.constants import MAX_NB_OF_RENEWALS, Periods, DB, RENEWAL_NB_OF_DAYS_ADDED_TO_TODAY, \
    MAX_NB_OF_LOANS
from gere_ta_bib.utils.exceptions import CopyBorrowedTodayError, MaxNbOfRenewalsError, UnkonowCopyBarcodeError, \
    MultipleCopyBarcodeError, \
    NotBorrowedCopyError, AlreadyBorrowedBySelfError, ReturnedTodayError, AlreadyBorrowedByOtherError, MaxNbOfLoansError


class AbstractTransaction(Model):
    card_number = CharField(max_length=9)

    class Meta:
        database = DB
        abstract = True

    @property
    def borrower(self) -> User:
        return User.get(User.card_number == self.card_number)


class Transaction(AbstractTransaction):
    """A transaction"""
    barcode = CharField(max_length=12)
    borrow_date = DateField()
    due_date = DateField()
    return_date = DateField(null=True)
    nb_of_renewals = IntegerField(default=0)
    overdue = BooleanField(default=False)

    class Meta:
        database = DB
        table_name = "Transactions"

    @property
    def copy(self) -> BaseCopy | NoReturn:
        book_copy_exists = BookCopy.select().where(BookCopy.barcode == self.barcode).exists()
        film_copy_exists = FilmCopy.select().where(FilmCopy.barcode == self.barcode).exists()
        music_copy_exists = MusicCopy.select().where(MusicCopy.barcode == self.barcode).exists()

        match (book_copy_exists, film_copy_exists, music_copy_exists):
            case (True, False, False):
                return BookCopy.get(BookCopy.barcode == self.barcode)
            case (False, True, False):
                return FilmCopy.get(FilmCopy.barcode == self.barcode)
            case (False, False, True):
                return MusicCopy.get(MusicCopy.barcode == self.barcode)
            case (False, False, False):
                raise UnkonowCopyBarcodeError()
            case _:
                raise MultipleCopyBarcodeError()

    def __str__(self) -> str:
        """Return transactions infos"""
        return f"User n°{self.borrower.card_number}, document n°{self.barcode}"

    @classmethod
    def borrow_copy(cls, card_number: str, barcode: str) -> None | NoReturn:
        """Create a new transaction if document is not already borrowed by user
        and if user didn't return it today"""
        current_borrower_card_number = cls.get_current_borrower(barcode)
        if current_borrower_card_number:
            if current_borrower_card_number == card_number:
                raise AlreadyBorrowedBySelfError()
            raise AlreadyBorrowedByOtherError
        else:
            if cls.has_returned_copy_today(card_number, barcode):
                raise ReturnedTodayError()
            if cls.has_maximal_nb_of_loans(card_number):
                raise MaxNbOfLoansError()

        cls.create(
            card_number=card_number,
            barcode=barcode,
        )

    @classmethod
    def get_current_borrower(cls, barcode: str) -> str | None:
        """
        Check if a document is already borrowed.
        If yes, return the current borrow user's card number.
        If not, return None.
        """
        current_borrow: cls = cls.select().where((cls.barcode == barcode)
                                                 & cls.return_date.is_null()).first()
        if current_borrow:
            return str(current_borrow.card_number)

    @classmethod
    def has_returned_copy_today(cls, card_number: str, barcode: str) -> bool:
        """True if user has returned the copy today, False otherwise"""
        return bool(cls.select().where(
            (cls.card_number == card_number) &
            (cls.barcode == barcode) &
            (cls.return_date == date.today())
        ))

    @classmethod
    def has_maximal_nb_of_loans(cls, card_number: str) -> bool:
        """True if user has the maximal number of borrowed documents, False otherwise"""
        return bool(cls.select().where(
            (cls.card_number == card_number) &
            (cls.return_date.is_null())
        ).count() >= MAX_NB_OF_LOANS)

    def renew_borrow(self) -> None | NoReturn:
        """Renew borrow if renewal is authorized, raise an error otherwise"""
        if self.borrow_date == date.today():
            raise CopyBorrowedTodayError()
        if self.nb_of_renewals >= MAX_NB_OF_RENEWALS:
            raise MaxNbOfRenewalsError()
        else:
            self.nb_of_renewals += 1
            self.due_date = date.today() + timedelta(days=RENEWAL_NB_OF_DAYS_ADDED_TO_TODAY)
            self.save()

    def return_copy(self) -> None | NoReturn:
        """Add a return_date to a transaction if not existing, raise an error otherwise"""
        if self.return_date:
            raise NotBorrowedCopyError()
        else:
            self.return_date = date.today()
            self.save()

    def save(self, *args, **kwargs):
        if not self.borrow_date:
            self.borrow_date = date.today()
            self.due_date = self.borrow_date + timedelta(
                days=Periods.STANDARD_USER_BORROW if not self.borrower.is_staff
                else Periods.STAFF_BORROW)
        self.set_overdue()
        return super().save(*args, **kwargs)

    def set_overdue(self) -> None:
        """Set overdue status"""
        self.overdue = (date.today() > self.due_date) if not self.return_date else False
