"""Model for reservations"""

from datetime import date, timedelta
from typing import NoReturn

from peewee import CharField, DateField

from gere_ta_bib.models.notices import BaseNotice, BookNotice, FilmNotice, MusicNotice
from gere_ta_bib.models.transaction import AbstractTransaction
from gere_ta_bib.utils.constants import ReservationStatuses, Periods, MAX_NB_OF_RESERVATIONS
from gere_ta_bib.utils.exceptions import UnkonowEANError, MultipleEANError, AlreadyReservedBySelfError, \
    MaxNbOfReservationsError


class Reservation(AbstractTransaction):
    """A document reservation"""
    ean = CharField(max_length=13)
    creation_date = DateField()
    expiration_date = DateField()
    availability_date = DateField(null=True)
    pickup_date = DateField(null=True)
    status = CharField(max_length=25, default=ReservationStatuses.PENDING)

    class Meta:
        table_name = "Réservations"

    @property
    def notice(self) -> BaseNotice | NoReturn:
        book_notice_exists = BookNotice.select().where(BookNotice.ean == self.ean).exists()
        film_notice_exists = FilmNotice.select().where(FilmNotice.ean == self.ean).exists()
        music_notice_exists = MusicNotice.select().where(MusicNotice.ean == self.ean).exists()

        match (book_notice_exists, film_notice_exists, music_notice_exists):
            case (True, False, False):
                return BookNotice.get(BookNotice.ean == self.ean)
            case (False, True, False):
                return FilmNotice.get(FilmNotice.ean == self.ean)
            case (False, False, True):
                return MusicNotice.get(MusicNotice.ean == self.ean)
            case (False, False, False):
                raise UnkonowEANError()
            case _:
                raise MultipleEANError()

    @classmethod
    def has_already_a_current_reservation_of_this(cls, card_number: str, ean: str) -> bool:
        """True if user has already a pending or available reservation of this notice, False otherwise"""
        return bool(Reservation.select().where(
            (Reservation.card_number == card_number) &
            (Reservation.ean == ean) &
            (Reservation.status.in_([ReservationStatuses.PENDING, ReservationStatuses.AVAILABLE, ]))
        ))

    @classmethod
    def has_maximal_number_of_reservations(cls, card_number: str) -> bool:
        """True if user has already the maximal number of reservations, False otherwise"""
        return bool(cls.select().where(
            (cls.card_number == card_number) &
            (cls.status.in_([ReservationStatuses.PENDING, ReservationStatuses.AVAILABLE]))
        ).count() >= MAX_NB_OF_RESERVATIONS)

    @classmethod
    def reserve(cls, card_number: str, ean: str) -> None | NoReturn:
        """Create a reservation if authorized, alse raise an error"""
        if cls.has_already_a_current_reservation_of_this(card_number, ean):
            raise AlreadyReservedBySelfError()
        if cls.has_maximal_number_of_reservations(card_number):
            raise MaxNbOfReservationsError()

        cls.create(
            card_number=card_number,
            ean=ean,
        )

    def save(self, *args, **kwargs):
        if not self.creation_date:
            self.creation_date = date.today()
            self.expiration_date = self.creation_date + timedelta(days=Periods.RESERVATION_VALDITY)
        self.set_status()
        return super().save(*args, **kwargs)

    def set_status(self):
        """Set reservation status based on dates"""
        if self.pickup_date:
            self.status = ReservationStatuses.SATISFIED
        elif self.availability_date:
            self.status = (ReservationStatuses.UNCLAIMED
                           if date.today() - self.availability_date > timedelta(days=Periods.RESERVATION_PICKUP)
                           else ReservationStatuses.AVAILABLE)
        else:
            self.status = (ReservationStatuses.EXPIRED
                           if date.today() > self.expiration_date
                           else ReservationStatuses.PENDING)
