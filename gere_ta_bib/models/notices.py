"""Models for bibliographic notices"""
from abc import abstractmethod
from datetime import date

from peewee import Model, CharField, IntegerField, ManyToManyField, ForeignKeyField, DeferredThroughModel, DateField

from gere_ta_bib.models.contributors import Author, Publisher, Musician, Director
from gere_ta_bib.utils.constants import DB, GENRES_TO_REFS1, DOC_TYPES


# region Through differed models
BookAuthorThroughDeferred = DeferredThroughModel()
FilmDirectorThroughDeferred = DeferredThroughModel()
MusicMusicianThroughDeferred = DeferredThroughModel()
# endregion


# region Models
class BaseNotice(Model):
    ean = CharField(max_length=13, unique=True, )  # EAN: European Article Number
    title = CharField(max_length=255, )
    artists = None  # Implement here a ManyToManyField
    genre = CharField(max_length=50, null=True)
    ref1 = CharField(max_length=10, null=True)
    ref2 = CharField(max_length=10, null=True)
    ref3 = CharField(max_length=10, null=True)
    _created_at = DateField()
    updated_at = DateField()

    class Meta:
        database = DB
        abstract = True

    @property
    @abstractmethod
    def doc_type(self) -> str:
        """Document type (book, dvd, cd...)"""
        return ""

    def get_ref1(self) -> str | None:
        """Get the first mark of classification from genre"""
        return GENRES_TO_REFS1.get(self.genre)

    def get_ref2(self) -> str | None:
        """
        Get the second mark of classification from main artist name.
        DON'T CALL THIS FROM SAVE() METHOD,
        because 'artists' refers to a ManyToManyField that won't be resolved yet.
        """
        if self.artists:
            return self.artists[0].last_name.upper()[0:3]

    def save(self, *args, **kwargs) -> None:
        """
        To call when an instance is created or changed.
        Warning: field ref2 can't be completed from here because not resolved yet.
        """
        if not self._created_at:
            self._created_at = date.today()
            self.ref1 = self.get_ref1()
        self.updated_at = date.today()
        return super().save(*args, **kwargs)

    @staticmethod
    def withdraw_leading_article(text) -> str:
        """Withdraw leading articles from title"""
        articles = ("LE ", "LA ", "LES ", "UN ", "UNE ", "DE ", "L'", "DES ", "D'", "A ", "THE ", "AN ")
        text = text.upper()
        for article in articles:
            if text.startswith(article):
                return text[len(article):]
        return text


class BookNotice(BaseNotice):
    publisher = ForeignKeyField(Publisher, backref="books", null=True)
    series_name = CharField(max_length=255, null=True)
    series_volume = IntegerField(null=True)
    artists = ManyToManyField(Author, backref="books", through_model=BookAuthorThroughDeferred)
    genre = CharField(max_length=20, null=True)

    class Meta:
        table_name = "Livres - NOTICES"

    def __str__(self) -> str:
        """Return book title"""
        return f"{str(self.title)}, de {" et ".join(str(author) for author in self.artists)}"

    @property
    def doc_type(self) -> str:
        """Document type (book, dvd, cd...)"""
        return DOC_TYPES.get("book")

    def get_ref2(self) -> str | None:
        """
        Get the second mark of classification from main artist name or from title, based on ref1.
        DON'T CALL THIS FROM SAVE() METHOD,
        because 'artists' refers to a ManyToManyField that won't be resolved yet.
        """
        if self.ref1 in ("BD", "BDM", "BDC"):
            return (self.withdraw_leading_article(self.series_name)[0:3] if self.series_name
                    else self.withdraw_leading_article(self.title)[0:3])
        else:
            return super().get_ref2()


class FilmNotice(BaseNotice):
    series_name = CharField(max_length=255, null=True)
    series_volume = IntegerField(null=True)
    artists = ManyToManyField(Director, backref="films", through_model=FilmDirectorThroughDeferred)
    genre = CharField(max_length=20, null=True)

    class Meta:
        table_name = "Films - NOTICES"

    def __str__(self) -> str:
        """Return film title"""
        return f"{str(self.title)}, de {" et ".join(str(director) for director in self.artists)}"

    @property
    def doc_type(self) -> str:
        """Document type (book, dvd, cd...)"""
        return DOC_TYPES.get("film")


class MusicNotice(BaseNotice):
    artists = ManyToManyField(Musician, backref="films", through_model=MusicMusicianThroughDeferred)
    genre = CharField(max_length=20, null=True)

    class Meta:
        table_name = "Musique - NOTICES"

    def __str__(self) -> str:
        """Return music title"""
        return f"{str(self.title)}, de {" et ".join(str(musician) for musician in self.artists)}"

    @property
    def doc_type(self) -> str:
        """Document type (book, dvd, cd...)"""
        return DOC_TYPES.get("music")
# endregion


# region Through tables
class BookAuthorThrough(Model):
    book = ForeignKeyField(BookNotice, backref="book_authors", on_delete="CASCADE")
    author = ForeignKeyField(Author, backref="book_authors", on_delete="CASCADE")

    class Meta:
        database = DB
        table_name = "Livres_Auteurices"


class FilmDirectorThrough(Model):
    film = ForeignKeyField(FilmNotice, backref="film_directors", on_delete="CASCADE")
    director = ForeignKeyField(Director, backref="film_directors", on_delete="CASCADE")

    class Meta:
        database = DB
        table_name = "Films_Réalisateurices"


class MusicMusicianThrough(Model):
    music = ForeignKeyField(MusicNotice, backref="music_musicians", on_delete="CASCADE")
    musician = ForeignKeyField(Musician, backref="music_musicians", on_delete="CASCADE")

    class Meta:
        database = DB
        table_name = "Musique_Musicien·nes"
# endregion


BookAuthorThroughDeferred.set_model(BookAuthorThrough)
FilmDirectorThroughDeferred.set_model(FilmDirectorThrough)
MusicMusicianThroughDeferred.set_model(MusicMusicianThrough)

# NOTICES_MODELS = [BookNotice, FilmNotice, MusicNotice,]
NOTICES_MODELS = {
    BookNotice: DOC_TYPES.get("book"),
    FilmNotice: DOC_TYPES.get("film"),
    MusicNotice: DOC_TYPES.get("music"),
}
