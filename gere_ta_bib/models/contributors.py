"""Models for artists"""

from datetime import datetime

from peewee import Model, CharField, IntegerField

from gere_ta_bib.utils.constants import DB
from gere_ta_bib.utils.exceptions import ValidationError


class BaseArtist(Model):
    """Abstract models for all artists: authors, illustrators, filmmakers etc"""
    last_name = CharField(max_length=50)
    first_name = CharField(max_length=50, null=True)
    birth_year = IntegerField(column_name="Année de naissance", null=True)
    death_year = IntegerField(null=True,
                              column_name="Année de décès", )

    class Meta:
        database = DB
        abstract = True

    def save(self, *args, **kwargs):
        # Dates checking
        current_year = datetime.now().year
        if self.death_year:
            if self.death_year > current_year:
                raise ValidationError(f"La date de décès de {self.first_name} {self.last_name} "
                                      f"est supérieure à {current_year}...")
            elif self.birth_year > self.death_year:
                raise ValidationError(f"{self.birth_year}-{self.death_year}: "
                                      f"{self.first_name} {self.last_name} meurt avant de naître...")
        if self.birth_year and self.birth_year > current_year:
            raise ValidationError(f"La date de naissance de {self.first_name} {self.last_name} "
                                  f"est supérieure à {current_year}...")
        # Name formatting
        self.last_name = str(self.last_name).upper()
        if self.first_name:
            self.first_name = str(self.first_name).title()
        return super().save(*args, **kwargs)


class Author(BaseArtist):
    """Model for books authors"""

    class Meta:
        table_name = "Auteurices"

    def __str__(self) -> str:
        """Returns author's complete name"""
        return f"{str(self.first_name)} {str(self.last_name)}"


class Director(BaseArtist):
    """Model for film directors"""

    class Meta:
        table_name = "Réalisateurices"

    def __str__(self) -> str:
        """Returns film director's complete name"""
        return f"{str(self.first_name)} {str(self.last_name)}"


class Musician(BaseArtist):
    """Model for musicians"""

    class Meta:
        table_name = "Musicien·nes"

    def __str__(self) -> str:
        """Returns musician's complete name"""
        return f"{str(self.first_name)} {str(self.last_name)}"


class Publisher(Model):
    """Model for books publishers"""
    name = CharField(max_length=255, unique=True)

    class Meta:
        database = DB
        table_name = "Maisons d'éditions"

    def __str__(self) -> str:
        """Returns publisher's name"""
        return str(self.name)


CONTRIBUTORS_MODELS = [Author, Director, Musician, Publisher]
