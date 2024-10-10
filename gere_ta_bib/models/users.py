"""Models related ro users"""
from datetime import timedelta, date
from typing import NoReturn

from peewee import Model, CharField, BooleanField, DateTimeField, DateField

from gere_ta_bib.utils.constants import Periods, DB, MINIMAL_CARD_NUMBER
from gere_ta_bib.utils.exceptions import NotExistingFieldsError


class User(Model):
    card_number = CharField(max_length=9, unique=True)
    last_name = CharField(max_length=50)
    first_name = CharField(max_length=50)
    is_staff = BooleanField(default=False)
    is_active = BooleanField(default=True)
    membership_end = DateTimeField()
    _created_at = DateField()
    updated_at = DateField()

    class Meta:
        database = DB
        table_name = "Utilisateurices"

    def __str__(self) -> str:
        """Return card number and name"""
        return f"{self.first_name} {self.last_name} ({self.card_number})"

    @classmethod
    def generate_unique_card_number(cls) -> str:
        """Generate a valid and unique user card number"""
        card_numbers = [user.card_number for user in cls.select()]
        highest = max([int(card_number) for card_number in card_numbers]) if card_numbers else MINIMAL_CARD_NUMBER
        return str(highest + 1)

    def save(self, *args, **kwargs) -> None:
        if not self._created_at:
            self._created_at = date.today()
            self.card_number = self.generate_unique_card_number()
            self.membership_end = self._created_at + timedelta(days=Periods.MEMBERSHIP)
            self.updated_at = date.today()
        self.last_name = str(self.last_name).upper()
        if self.first_name:
            self.first_name = str(self.first_name).title()
        self.set_is_active_status()
        return super().save(*args, **kwargs)

    def set_is_active_status(self) -> None:
        """Set to False if account has not been updated in the membership period"""
        if date.today() - self.updated_at > timedelta(days=Periods.MEMBERSHIP):
            self.is_active = False
        else:
            self.is_active = True

    def update_user(self, **new_infos) -> None | NoReturn:
        """Update user with new infos"""
        not_existing_fields = []
        for key, value in new_infos.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                not_existing_fields.append(key)
        if not_existing_fields:
            raise NotExistingFieldsError(not_existing_fields)
        self.save()
