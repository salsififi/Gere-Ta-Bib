"""Constants"""
import re
from enum import Enum
from pathlib import Path

import typer
from peewee import SqliteDatabase
from typer.colors import YELLOW, MAGENTA

# region Database
DB_NAME = "database.db"
DB = SqliteDatabase(DB_NAME)


# endregion


# region Actions
class StaffActionsNames(Enum):
    BORROW = "Prêt"
    RETURN = "Retour"
    RENEW = "Prolongation"
    RESERVE = "Réservation"
    ACCOUNT = "Consultation d'un compte"
    SEARCH = "Recherche dans le catalogue"
    OTHER = "Autres actions..."


class StaffOtherActionsNames(Enum):
    ADD_USER = "Ajouter un·e utilisateurice"
    RENEW_USER = "Renouveler l'abonnement d'un·e utilisateurice"
    ADD_COPY = "Ajouter un exemplaire"
    DELETE_COPY = "Supprimer un exemplaire"
    ADD_NOTICES = "Ajouter des notices bibliographiques"
    STATS = "Consulter des statistiques"


STAFF_ACTIONS = {i: action.value for i, action in enumerate(StaffActionsNames, 1)}
STAFF_OTHER_ACTIONS = {i: action.value for i, action in enumerate(StaffOtherActionsNames, 1)}


class UserActionNames(Enum):
    BORROW = "Emprunter"
    RETURN = "Rendre"
    RENEW = "Prolonger un document"
    RESERVE = "Réserver un document"
    ACCOUNT = "Consulter mon compte"
    SEARCH = "Faire une recherche"
    SELECTION = "Donnez-moi des idées..."


USER_ACTIONS = {i: action.value for i, action in enumerate(UserActionNames, 1)}


# endregion


# region Library rules and practices
class Periods:
    """Periods defined in the library rules"""
    MEMBERSHIP = 365
    STANDARD_USER_BORROW = 28
    STAFF_BORROW = 60
    RESERVATION_VALDITY = 180
    RESERVATION_PICKUP = 14


class ReservationStatuses:
    """All reservation statuses are here"""
    PENDING = "En traitement"
    AVAILABLE = "Disponible"
    SATISFIED = "Satisfaite"
    EXPIRED = "Expirée"
    UNCLAIMED = "Non retirée"


class ValidExpressions:
    """All regex needed are here"""
    CARD_NUMBER = re.compile(r"^93\d{7}$")
    EAN = re.compile(r"^\d{13}$|^\d{8}$")
    COPY_BARCODE = re.compile(r"^00000\d{7}$")
    NAME = re.compile(r"[a-zA-Zéèëê]+([ -][a-zA-Zéèëê]+)*$")


DOC_TYPES = {
    "book": "LIV",
    "film": "DVD",
    "music": "CD",
}
DOC_TYPES_NAMES = list(DOC_TYPES.values())

GENRES_TO_REFS1 = {
    "BD": "BD", "Manga": "BDM", "Comics": "BDC", "One shot": "BDO",

    "Album": "A", "Conte": "C",

    "Roman": "R", "Roman policier": "RP", "Roman SF": "RSF", "Roman ados": "R ado",

    "Drame": "F dra", "Comédie": "F com", "Série TV": "F tv", "Film SF": "F sf",
    "Film policier": "F pol", "Aventure": "F ave", "Anime": "F man", "Animation": "F ani",

    "Classique": "M cla", "Rock": "M roc", "Blues": "M blu", "Jazz": "M jaz", "Reggae": "M reg",
    "Europe": "M eur", "BO": "M bof", "Amérique": "M ame", "Afrique": "M afr", "Asie": "M asi",
    "Ambiance": "M amb", "Chanson française": "M fra", "Rap": "M rap", "Pop": "M pop",
}

MAX_NB_OF_LOANS = 30
MAX_NB_OF_RENEWALS = 1
MAX_NB_OF_RESERVATIONS = 5
MINIMAL_CARD_NUMBER = 930000000
RENEWAL_NB_OF_DAYS_ADDED_TO_TODAY = 28
# endregion


# region Program settings
DECORATION_CHAR = "*"
EXAMPLES_NOTICES_FOLDER = "gere_ta_bib/utils/EXAMPLES_notices_to_import"
LINE_LENGTH = 75
LOG_FORMAT = "%(levelname)s: %(message)s"
LOGS_FOLDER_PATH = Path(__file__).parent.parent / "logs"
NB_OF_RANDOM_NOTICES = 10
QUIT_LETTER = "Q"
YES_NO = {"YES": "O", "NO": "N"}
USER_CHOICE_COLOR = YELLOW
STAFF_CHOICE_COLOR = MAGENTA
# endregion


if __name__ == '__main__':
    pass
