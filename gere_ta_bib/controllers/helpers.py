"""Helpers for controllers"""
import json
import logging
from datetime import date
from functools import wraps
from typing import Callable, NoReturn

import unicodedata
from peewee import ForeignKeyField, CharField

from gere_ta_bib.models.contributors import Publisher, Musician, Director, Author, BaseArtist
from gere_ta_bib.models.copies import BaseCopy, COPIES_MODELS, BookCopy, FilmCopy, MusicCopy
from gere_ta_bib.models.notices import BaseNotice, NOTICES_MODELS, MusicNotice, BookNotice, FilmNotice
from gere_ta_bib.models.reservation import Reservation
from gere_ta_bib.models.transaction import Transaction
from gere_ta_bib.models.users import User
from gere_ta_bib.utils.constants import ValidExpressions, ReservationStatuses, QUIT_LETTER, DOC_TYPES
from gere_ta_bib.utils.exceptions import ExitFunction
from gere_ta_bib.views.cli.base_cli_view import BaseCliView
from gere_ta_bib.views.cli.staff_cli_view import StaffCliView


def apply_ref2_to_notice(notice: BaseNotice) -> None:
    """Apply ref2 to a notice"""
    notice.ref2 = notice.get_ref2()
    notice.save()


def check_numeric_choice(view: BaseCliView, choices: dict, choice: str, exit_function: Callable) -> int | None:
    """Check if user input is a valid number, and return it if it is (or loop if it's not)."""

    def ask_once_again() -> str:
        """Called if input is invalid to ask for user's choice again"""
        view.invalid_choice()
        return view.prompt_choice()

    while not (isinstance(choice, int) and choice in choices):
        if choice.upper() == QUIT_LETTER:
            try:
                exit_function()
            except ExitFunction:
                return
        try:
            choice = int(choice)
            if choice not in choices:
                choice = ask_once_again()
        except ValueError:
            choice = ask_once_again()
    return choice


def check_user_account(func: Callable):
    """Decorator to check card number and if user is active."""

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        while not is_valid_and_existing_card_number(card_number := self.view.prompt_card_number()):
            if card_number.upper() == QUIT_LETTER:
                return
            continue
        user = get_user_from_card_number(card_number)
        self.view.info_connexion(user)
        if not user.is_active:
            self.view.not_active_user()
            self.view.prompt_press_enter()
            return
        kwargs["card_number"] = card_number
        return func(self, *args, **kwargs)

    return wrapper


def exit_func() -> NoReturn:
    """Raise a fake exception to simulate a return"""
    raise ExitFunction()


def extract_books_data(file: str) -> tuple[int, int, int]:
    """
    Extract books data from a json file and add them (if not already existing) in the database.
    :param file: a sting with the path of the json file
    :return: a tuple of integers (nb of new notices, nb of existing notices, nb of errors)
    """
    with open(file, "r", encoding="utf-8") as f:
        books_data = json.load(f)
        nb_new = nb_existing = nb_errors = 0
    for book_data in books_data:
        try:
            publisher = handle_publisher(book_data)
            authors = handle_artists(book_data, "authors", Author)
            new, existing = handle_book_notice(book_data, publisher, authors)
            nb_new += new
            nb_existing += existing
        except Exception as e:
            nb_errors += 1
            logging.error(e)
    return nb_new, nb_existing, nb_errors


def extract_films_data(file: str):
    """
    Extract films data from a json file and add them (if not already existing) in the database.
    :param file: a sting with the path of the json file
    :return: a tuple of integers (nb of new notices, nb of existing notices, nb of errors)
    """
    with open(file, "r", encoding="utf-8") as f:
        films_data = json.load(f)
        nb_new = nb_existing = nb_errors = 0
    for film_data in films_data:
        try:
            directors = handle_artists(film_data, "directors", Director)
            new, existing = handle_film_notice(film_data, directors)
            nb_new += new
            nb_existing += existing
        except Exception as e:
            nb_errors += 1
            logging.error(e)
    return nb_new, nb_existing, nb_errors


def extract_musics_data(file: str):
    """
    Extract musics data from a json file and add them (if not already existing) in the database.
    :param file: a sting with the path of the json file
    :return: a tuple of integers (nb of new notices, nb of existing notices, nb of errors)
    """
    with open(file, "r", encoding="utf-8") as f:
        musics_data = json.load(f)
        nb_new = nb_existing = nb_errors = 0
    for music_data in musics_data:
        try:
            musicians = handle_artists(music_data, "musicians", Musician)
            new, existing = handle_music_notice(music_data, musicians)
            nb_new += new
            nb_existing += existing
        except Exception as e:
            nb_errors += 1
            logging.error(e)
    return nb_new, nb_existing, nb_errors


def generate_unique_barcode() -> str:
    """Generate a valid and unique barcode for a copy"""
    barcodes = []
    for model in COPIES_MODELS:
        model_barcodes = [copy.barcode for copy in model.select()]
        barcodes.extend(model_barcodes)
    highest = max([int(barcode) for barcode in barcodes]) if barcodes else 0
    return f"{(highest + 1):012d}"


def get_borrowed_copies_dict(card_number: str) -> dict[BaseCopy, date]:
    """
    Get the list of all currently borrowed documents, and return_dates
    :param card_number: string with user's card number
    :return: dict of borrowed documents with document copies as keys,
    and return dates as values
    """
    borrowed = Transaction.select().where((Transaction.card_number == card_number)
                                          & (Transaction.return_date.is_null()))
    return {transaction.copy: transaction.due_date for transaction in borrowed}


def get_copy_from_barcode(barcode: str) -> BaseCopy | None:
    """Get a copy from a barcode"""
    for model in COPIES_MODELS:
        copy = model.select().where(model.barcode == barcode).first()
        if copy:
            return copy


def get_copy_model_from_notice(notice: BaseNotice) -> BaseCopy | None:
    """Get the copy model (BookCopy, FilmCopy or MusicCopy) from a notice"""
    doc_type = notice.doc_type
    if doc_type == DOC_TYPES.get("book"):
        return BookCopy
    elif doc_type == DOC_TYPES.get("film"):
        return FilmCopy
    elif doc_type == DOC_TYPES.get("music"):
        return MusicCopy


def get_first_reservation_from_barcode(barcode: str) -> Reservation | None:
    """Get the first pending reservation of a notice from a copy barcode"""
    notice = get_notice_from_barcode(barcode)
    first_reservation = Reservation.select().where(
        (Reservation.ean == notice.ean) & (Reservation.status == ReservationStatuses.PENDING)
    ).first()
    return first_reservation


def get_nb_of_overdues(card_number: str) -> int:
    """Get the number of overdue borrowed documents from a user card number"""
    return Transaction.select().where((Transaction.card_number == card_number)
                                      & Transaction.overdue).count()


def get_notice_from_ean(ean: str) -> BaseNotice | None:
    """Get a notice from an EAN"""
    for model in NOTICES_MODELS:
        for notice in model.select():
            if notice.ean == ean:
                return notice


def get_notice_from_barcode(barcode: str) -> BaseNotice:
    """Get the mother notice from a copy barcode"""
    return get_copy_from_barcode(barcode).parent_notice


def get_normalized_words(text: str) -> list:
    """
    Convert to lowercase, remove diacritical marks and replace punctuation marks by spaces,
    then return a list with normalized words.
    >>> get_normalized_words("L'école à la plage, c'est une bonne idée !")
    ['l', 'ecole', 'a', 'la', 'plage', 'c', 'est', 'une', 'bonne', 'idee']
    """
    text = remove_diacritical_marks(text.lower())
    return "".join(char if char.isalnum() else " " for char in text).split()


def get_notices_from_keywords(view, query: str) -> list[BaseNotice]:
    words = get_normalized_words(query)
    notices = []
    for model in NOTICES_MODELS:
        for notice in model.select():
            if word_is_in_charfields(words[0], notice):
                notices.append(notice)

    for word in words[1:]:
        for notice in notices[::-1]:
            word_found = False
            i = len(notices[::-1])
            while not word_found and i > 0:
                if word_is_in_charfields(word, notice):
                    word_found = True
                i -= 1
            if not word_found:
                notices.remove(notice)
    view.search_results(notices)
    return notices


def get_user_from_card_number(card_number: str) -> User:
    """Get a user from a card number"""
    return User.select().where(User.card_number == card_number).first()


def get_reservations_from_card_number(card_number: str) -> list[Reservation]:
    """Get pending and available reservations from a card number"""
    return list(Reservation.select().where(
        (Reservation.card_number == card_number) &
        (Reservation.status.in_([ReservationStatuses.PENDING, ReservationStatuses.AVAILABLE]))))


def handle_publisher(book_data: dict) -> Publisher:
    """Get publisher from book data, create it if not existing in database"""
    publisher_name = book_data.get("publisher")
    if not Publisher.select().where(Publisher.name == publisher_name).exists():
        publisher = Publisher.create(name=publisher_name)
    else:
        publisher = Publisher.select().where(Publisher.name == publisher_name).first()
    return publisher


def handle_artists(notice_data: dict, artist_type: str, model: BaseArtist) -> list[BaseArtist]:
    """Get artists from notice data, create them if not existing in database"""
    artists_data = notice_data.get(artist_type)
    artists = []
    for artist_data in artists_data:
        last_name = artist_data.get("last_name")
        first_name = artist_data.get("first_name")
        birth_year = artist_data.get("birth_year")
        death_year = artist_data.get("death_year")

        if not model.select().where(
                (model.last_name == last_name) &
                (model.first_name == first_name) &
                (model.birth_year == birth_year) &
                (model.death_year == death_year)
        ).exists():
            artist = model.create(
                last_name=last_name,
                first_name=first_name,
                birth_year=birth_year,
                death_year=death_year
            )
        else:
            artist = model.select().where(
                (model.last_name == last_name) &
                (model.first_name == first_name) &
                (model.birth_year == birth_year)
            )
        artists.append(artist)
        return artists


def handle_book_notice(book_data: dict, publisher: Publisher, authors: list[Author]) -> tuple[bool, bool] | None:
    """
    Create a notice with book data if a notice is not existing for this book in the database.
    If notice is already existing in the database, existing_notice will be True.
    If notice is new in the database, new_notice wille be True.
    :return: tuple of booleans(new_notice, existing_notice)
    """
    ean = book_data.get("ean")
    new_notice = existing_notice = False
    if not BookNotice.select().where(BookNotice.ean == ean).exists():
        title = book_data.get("title")
        series_name = book_data.get("series_name")
        series_volume = book_data.get("series_volume")
        genre = book_data.get("genre")
        book_notice: BookNotice = BookNotice.create(
            ean=ean,
            title=title,
            series_name=series_name,
            series_volume=series_volume,
            genre=genre,
            publisher=publisher,
        )
        for author in authors:
            book_notice.artists.add(author)
        book_notice.get_ref2()
        book_notice.save()
        new_notice = True
        logging.info(StaffCliView.InfoMessages.NOTICE_ADDED.format(
            notice_type="livre", notice=book_notice))
    else:
        existing_notice = True
        logging.info(StaffCliView.InfoMessages.ALREADY_EXISTING_NOTICE.format(
            notice_type="livre", notice=BookNotice.get(BookNotice.ean == ean)))
    return new_notice, existing_notice


def handle_film_notice(film_data: dict, directors: list[Director]) -> tuple[bool, bool] | None:
    """
    Create a notice with book data if a notice is not existing for this book in the database.
    If notice is already existing in the database, existing_notice will be True.
    If notice is new in the database, new_notice wille be True.
    :return: tuple of booleans(new_notice, existing_notice)
    """
    ean = film_data.get("ean")
    new_notice = existing_notice = False
    if not FilmNotice.select().where(FilmNotice.ean == ean).exists():
        title = film_data.get("title")
        series_name = film_data.get("series_name")
        series_volume = film_data.get("series_volume")
        genre = film_data.get("genre")
        film_notice: FilmNotice = FilmNotice.create(
            ean=ean,
            title=title,
            series_name=series_name,
            series_volume=series_volume,
            genre=genre,
        )
        for director in directors:
            film_notice.artists.add(director)
        film_notice.get_ref2()
        film_notice.save()
        new_notice = True
        logging.info(StaffCliView.InfoMessages.NOTICE_ADDED.format(
            notice_type="DVD", notice=film_notice))
    else:
        existing_notice = True
        logging.info(StaffCliView.InfoMessages.ALREADY_EXISTING_NOTICE.format(
            notice_type="DVD", notice=FilmNotice.get(FilmNotice.ean == ean)))
    return new_notice, existing_notice


def handle_music_notice(music_data: dict, musicians: list[Musician]) -> tuple[bool, bool] | None:
    """
    Create a notice with CD data if a notice is not existing for this CD in the database.
    If notice is already existing in the database, existing_notice will be True.
    If notice is new in the database, new_notice wille be True.
    :return: tuple of booleans(new_notice, existing_notice)
    """
    ean = music_data.get("ean")
    new_notice = existing_notice = False
    if not MusicNotice.select().where(MusicNotice.ean == ean).exists():
        title = music_data.get("title")
        genre = music_data.get("genre")
        music_notice: MusicNotice = MusicNotice.create(
            ean=ean,
            title=title,
            genre=genre,
        )
        for musician in musicians:
            music_notice.artists.add(musician)
        music_notice.get_ref2()
        music_notice.save()
        new_notice = True
        logging.info(StaffCliView.InfoMessages.NOTICE_ADDED.format(
            notice_type="CD", notice=music_notice))
    else:
        existing_notice = True
        logging.info(StaffCliView.InfoMessages.ALREADY_EXISTING_NOTICE.format(
            notice_type="CD", notice=MusicNotice.get(MusicNotice.ean == ean)))
    return new_notice, existing_notice


def is_existing_card_number(card_number: str) -> bool:
    """
    Check if card number exists in users table
    >>> is_existing_card_number("930999999")
    False
    >>> is_existing_card_number("930000001")
    True
    """
    return User.select().where(User.card_number == card_number).exists()


def is_existing_copy_barcode(barcode: str) -> bool:
    """
    Check if document barcode exists in tables BookCopies, FilmCopies or MusicCopies
    >>> is_existing_copy_barcode("000000000001")
    True
    >>> is_existing_copy_barcode("000009999999")
    False
    """
    for model in COPIES_MODELS:
        if model.select().where(model.barcode == barcode).exists():
            return True
    return False


def is_existing_ean(ean: str) -> bool:
    """
    Check if an EAN is existing in table BookNotice, FilmNotice or MusicNotice
    >>> is_existing_ean("9782211222396")
    True
    >>> is_existing_ean("9780000000000")
    False
    """
    for model in NOTICES_MODELS:
        if model.select().where(model.ean == ean).exists():
            return True
    return False


def is_overdue(barcode: str) -> bool:
    """True if copy is overdue, False otherwise"""
    transaction = Transaction.select().where((Transaction.barcode == barcode)
                                             & (Transaction.return_date.is_null()).first())
    return transaction.overdue


def is_reserved(barcode: str) -> bool:
    """True if mother notice is reserved, False otherwise"""
    notice = get_notice_from_barcode(barcode)
    return bool(Reservation.select().where((Reservation.ean == notice.ean)
                                           & (Reservation.status == ReservationStatuses.PENDING)))


def is_reserved_by(barcode: str) -> str | None:
    """If a notice is reserved, return the card number of the first user in the pending list"""
    ean = get_copy_from_barcode(barcode).parent_notice.ean
    reservation = Reservation.select().where((Reservation.ean == ean) &
                                             (Reservation.status == ReservationStatuses.PENDING)).first()
    if reservation:
        return reservation.borrower.card_number


def is_reserved_by_self(barcode: str, card_number: str) -> bool:
    """True if user has a pending or available reservation of the document"""
    reservations = get_reservations_from_card_number(card_number)
    for reservation in reservations:
        if reservation.notice == get_notice_from_barcode(barcode):
            return True
    return False


def is_valid_and_existing_card_number(card_number: str) -> bool:
    """Check if a card number is valid and existing"""
    if card_number.upper() == QUIT_LETTER:
        return False
    if not is_valid_card_number(card_number):
        BaseCliView.invalid_card_number()
        return False
    if not is_existing_card_number(card_number):
        BaseCliView.unknown_card_number()
        return False
    return True


def is_valid_and_existing_copy_barcode(barcode: str) -> bool:
    """Check if a document barcode is valid and existing in the datatbase"""
    if not is_valid_copy_barcode(barcode):
        BaseCliView.invalid_copy_barcode()
        return False
    if not is_existing_copy_barcode(barcode):
        BaseCliView.unknown_copy_barcode()
        return False
    return True


def is_valid_card_number(card_number: str) -> bool:
    """
    Check if library card number is valid (9-digits long string with leading 930)
    >>> is_valid_card_number("930000000")
    True
    >>> is_valid_card_number("93000000f")
    False
    >>> is_valid_card_number("93012121")
    False
    >>> is_valid_card_number("123456789")
    False
    """
    return ValidExpressions.CARD_NUMBER.match(card_number) is not None


def is_valid_copy_barcode(barcode: str) -> bool:
    """
    Check if document barcode is valid
    >>> is_valid_copy_barcode("000001234567")
    True
    >>> is_valid_copy_barcode("000012345678")
    False
    >>> is_valid_copy_barcode("00000123456789")
    False
    >>> is_valid_copy_barcode("00000123456")
    False
    """
    return ValidExpressions.COPY_BARCODE.match(barcode) is not None


def is_valid_ean(ean: str) -> bool:
    """
    Check if EAN is a valid
    >>> is_valid_ean("9780123456789")
    True
    >>> is_valid_ean("12345678")
    True
    >>> is_valid_ean("978012345678a")
    False
    >>> is_valid_ean("1234567890")
    False
    >>> is_valid_ean("1234567a")
    False
    """
    return ValidExpressions.EAN.match(ean) is not None


def is_valid_json_file(file: str) -> bool:
    """True if file is a valid json file, False otherwise"""
    try:
        with open(file, "r", encoding="utf-8") as f:
            json.load(f)
            return True
    except Exception as e:
        BaseCliView.display_exception_message(file, e)
        return False


def is_valid_name(name: str) -> bool:
    """
    Check if name is valid
    >>> is_valid_name("Marie")
    True
    >>> is_valid_name("pépé")
    True
    >>> is_valid_name("jean marc")
    True
    >>> is_valid_name("jean-marc")
    True
    >>> is_valid_name("Jean-Paul 2")
    False
    >>> is_valid_name("Marie123")
    False
    >>> is_valid_name("Marie ")
    False
    """
    return ValidExpressions.NAME.match(name) is not None


def remove_diacritical_marks(text: str) -> str:
    """
    Remove all diacritical marks from a string
    >>> remove_diacritical_marks("Éàçèï oôö")
    'Eacei ooo'
    """
    text = unicodedata.normalize("NFD", text)
    return "".join(char for char in text if unicodedata.category(char) != "Mn")


def word_is_in_charfields(word: str, instance: BaseNotice) -> bool:
    """Checks if a word is in the charfields of a model, or in the charfields of a related model"""
    for field_name, field_type in instance._meta.fields.items():
        if isinstance(field_type, CharField):
            field_value = getattr(instance, field_name)
            if field_value and word.lower() in get_normalized_words(field_value):
                return True
        if isinstance(field_type, ForeignKeyField):
            related_instance = getattr(instance, field_name)
            if related_instance and word_is_in_charfields(word, related_instance):
                return True
    if hasattr(instance, "artists"):
        for artist in instance.artists:
            if word_is_in_charfields(word, artist):
                return True
    return False
