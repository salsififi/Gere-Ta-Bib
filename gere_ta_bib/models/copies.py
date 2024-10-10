"""Models for copies (of books, films, etc.)"""
from datetime import date

from peewee import CharField, ForeignKeyField, Model, DateField

# from constants import NOTICE_TYPES
from gere_ta_bib.models.notices import BookNotice, FilmNotice, MusicNotice
from gere_ta_bib.utils.constants import DB


class BaseCopy(Model):
    """An abstract copy"""
    barcode = CharField(max_length=12, unique=True)
    parent_notice = None  # to be defined as ForeignKeyField in herited classes
    _created_at = DateField()
    updated_at = DateField()

    class Meta:
        database = DB
        abstract = True

    @staticmethod
    def generate_unique_barcode() -> str:
        """Generate a valid and unique barcode for a copy"""
        barcodes = []
        for model in COPIES_MODELS:
            model_barcodes = [copy.barcode for copy in model.select()]
            barcodes.extend(model_barcodes)
        highest = max([int(barcode) for barcode in barcodes]) if barcodes else 0
        return f"{(highest + 1):012d}"

    def save(self, *args, **kwargs) -> None:
        if not self._created_at:
            self._created_at = date.today()
            self.barcode = self.generate_unique_barcode()
        self.updated_at = date.today()
        return super().save(*args, **kwargs)


class BookCopy(BaseCopy):
    """A book copy"""
    parent_notice = ForeignKeyField(BookNotice, backref="book_copies")

    class Meta:
        table_name = "Livres - EXEMPLAIRES"

    def __str__(self) -> str:
        """Return book title and barcode"""
        return f"{str(self.parent_notice)} (n°{str(self.barcode)})"


class FilmCopy(BaseCopy):
    """A film copy"""
    parent_notice = ForeignKeyField(FilmNotice, backref="copies")

    class Meta:
        table_name = "Films - EXEMPLAIRES"

    def __str__(self) -> str:
        """Return film title and barcode"""
        return f"{str(self.parent_notice)} (n°{str(self.barcode)})"


class MusicCopy(BaseCopy):
    """A music copy"""
    parent_notice = ForeignKeyField(MusicNotice, backref="copies")

    class Meta:
        table_name = "Musique - EXEMPLAIRES"

    def __str__(self) -> str:
        """Return music title and barcode"""
        return f"{str(self.parent_notice)} (n°{str(self.barcode)})"


COPIES_MODELS = [BookCopy, FilmCopy, MusicCopy]
