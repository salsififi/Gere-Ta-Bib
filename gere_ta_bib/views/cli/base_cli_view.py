"""Contains the abstract view model"""
import datetime
import sys
from abc import ABC, abstractmethod
from locale import setlocale, LC_TIME
from random import randint

import typer

from gere_ta_bib.models.copies import BaseCopy
from gere_ta_bib.models.notices import BaseNotice
from gere_ta_bib.models.reservation import Reservation
from gere_ta_bib.models.users import User
from gere_ta_bib.utils.constants import ReservationStatuses, QUIT_LETTER, YES_NO

setlocale(LC_TIME, "fr_FR.UTF-8")


class BaseCliView(ABC):
    """The abstract model for all views"""

    choice_color = ""  # to change to a typer color in inherited classes
    quit_letter = QUIT_LETTER  # to change to typer stylised letter in inherited classes

    class ErrorMessages:
        """All error messages are here"""
        ALREADY_BORROWED_BY_SELF = ""
        ALREADY_RESERVED_BY_SELF = ""
        BORROWED_TODAY = "Le document ne peut pas être prolongé le même jour que son emprunt. "
        INVALID_CARD_NUMBER = "Ce numéro de carte est invalide."
        INVALID_CHOICE = "Choix invalide, choisissez un des nombres proposés."
        INVALID_DOC_BARCODE = "Ce code-barres est invalide."
        INVALID_EAN = "Code_barres commercial invalide."
        MAX_NB_OF_LOANS = ""
        MAX_NB_OF_RESERVATIONS = ""
        MULTIPLE_COPY_BARCODE = "Ce code-barres exemplaire apparaît dans plusieurs tables."
        MULTIPLE_EAN = "Cet EAN apparaît dans plusieurs tables."
        NOT_ACTIVE = ""
        NOT_BORROWED_COPY = "'{}' n'était pas emprunté."
        NOT_EXISTING_FIELDS_ERROR = ("Le{s} champ{s} suivant{s} n'existe{nt} pas: {fields}.\n"
                                     "La mise à jour n'a pas été effectuée.")
        MAX_NB_OF_RENEWALS = ""
        RETURNED_TODAY = ""
        UNKNOWN_CARD_NUMBER = "Ce numéro de carte n'est pas attribué."
        UNKNOWN_DOCUMENT_BARCODE = "Code-barres exemplaire inconnu."
        UNKNOWN_EAN = "Code-barres commercial inconnu."

    class InfoMessages:
        """All info messages are here"""
        ACTIONS = ""
        BORROW_CONFIRMATION = "Prêt de '{}' enregistré."
        BORROWED_COPY = "{num} - {copy}\n\t--> Date d'échéance: {due_date}{overdue}"
        BORROWED = ""
        CONNEXION_CONFIRMATION = ""
        NO_SEARCH_RESULTS = "Aucun résultat..."
        NO_BORROWED = ""
        NO_RESERVATIONS = ""
        RANDOM_NOTICE = "{num}: {notice}\n\t--> Emplacement: {ref1} {ref2}"
        RANDOM_NOTICES = "Et si vous essayiez un de ces documents ?"
        RENEW_CONFIRMATION = "Prolongation de '{}' effectuée."
        RESERVE_CONFIRMATION = "La réservation de '{}' est enregistrée !"
        RESERVED_NOTICE = "{num} - {notice}\n\t--> Statut: {status}"
        RESERVED_NOTICES = ""
        RETURN_CONFIRMATION = "Retour de '{}' enregistré."
        RETURN_A_RESERVED_DOCUMENT = ""
        SEARCH_RESULT = "{num} - {result}"
        SEARCH_RESULTS = "Voici les résultats de votre recherche:"
        USER_ACCOUNT = "Compte de {}."

    class PromptMessages:
        """All prompt messages are here"""
        BACK_TO_MENU = "('{}' pour revenir au menu)"
        BARCODE = f"{BACK_TO_MENU} Code-barres du document: "
        CARD_NUMBER = f"{BACK_TO_MENU} Numéro de la carte de médiathèque: "
        CHOICE = ""
        MAX_NB_OF_LOANS = ""
        MAX_NB_OF_RENEWALS = ""
        MAX_NB_OF_RESERVATIONS = ""
        PRESS_ENTER = "\n(Appuyez sur 'Entrée' pour revenir au menu.)"
        RENEW_LOAN = f"{BACK_TO_MENU} Quel document souhaitez-vous prolonger ? "
        RESERVE = f"{BACK_TO_MENU} Indiquez le numéro du document que vous souhaitez réserver: "
        RESERVE_AGAIN = ("Souhaitez-vous faire une autre recherche ? "
                         f"[{YES_NO["YES"].upper()}/{YES_NO["NO"].lower()}] ")
        RETURNED_TODAY = ""
        SEARCH = f"{BACK_TO_MENU} Que cherchez-vous ? "

    class ReceptionMessage:
        """All reception messages are here"""
        GOOD_BYE = ""
        WELCOME_STAFF = ""

    def already_borrowed_by_self(self, copy: BaseCopy) -> None:
        """Display a warning message when user tries to borrow a document he/she already owns"""
        print(self.ErrorMessages.ALREADY_BORROWED_BY_SELF.format(copy))

    def already_reserved_by_self(self) -> None:
        """Display a warning message when user tries to reserve a document
        for which he/she has already a reservation """
        print(self.ErrorMessages.ALREADY_BORROWED_BY_SELF)

    @staticmethod
    def borrow_confirmed(copy: BaseCopy) -> None:
        """Display a confirmation message for document return"""
        print(BaseCliView.InfoMessages.BORROW_CONFIRMATION.format(copy))

    def borrowed_copies(self, borrowed: dict[BaseCopy, datetime.date]) -> None:
        """Display a message with the list of all borrowed documents"""
        overdues = [copy for copy in borrowed if borrowed[copy] < datetime.date.today()]
        if borrowed:
            print(self.InfoMessages.BORROWED.format(f"{len(overdues)} en" if overdues else "aucun"))
            print("\n".join(BaseCliView.InfoMessages.BORROWED_COPY.format(
                num=typer.style(i, fg=self.choice_color), copy=str(copy), due_date=str(date),
                overdue=(" (EN RETARD)" if copy in overdues else ""))
                            for i, (copy, date) in enumerate(borrowed.items(), 1)))
        else:
            print(BaseCliView.InfoMessages.NO_BORROWED)

    @staticmethod
    def borrowed_today():
        """Display a message saying it's impossible to renew a document borrowed the same day"""
        print(BaseCliView.ErrorMessages.BORROWED_TODAY)

    def current_reservations(self, reservations: list[Reservation]) -> None:
        """Display a message with the list of all current reservations (pending or available)"""
        available_reservations = [reservation for reservation in reservations
                                  if reservation.status == ReservationStatuses.AVAILABLE]
        if reservations:
            print(self.InfoMessages.RESERVED_NOTICES.format(
                nb=str(len(available_reservations)), s=("" if len(available_reservations) < 2 else "s")))
            print("\n".join(BaseCliView.InfoMessages.RESERVED_NOTICE.format(
                num=typer.style(i, fg=self.choice_color), notice=reservation.notice, status=reservation.status)
                            for i, reservation in enumerate(reservations, 1)
                            ))
        else:
            print(BaseCliView.InfoMessages.NO_RESERVATIONS)

    def display_possible_actions(self):
        print(self.InfoMessages.ACTIONS)

    @staticmethod
    @abstractmethod
    def display_long_separation():
        """Display a long separation to improve readability"""
        pass

    @staticmethod
    def display_short_separation():
        """Display a short separation to improve readability"""
        print()

    @staticmethod
    def display_exception_message(file: str, e: Exception):
        """Display an error message from an exception"""
        print(f"Problème avec le fichier '{file}':\n{e}")

    def goodbye(self) -> None:
        """Display a goodbye message"""
        print(f"\n{self.ReceptionMessage.GOOD_BYE}")
        sys.exit()

    @abstractmethod
    def handle_welcome(self) -> None:
        """Handle welcom message display"""
        pass

    def info_account(self, borrowed: dict, reservations: list[Reservation]) -> None:
        """Display the list of all borrowed and reserved documents"""
        if borrowed:
            self.borrowed_copies(borrowed)
        else:
            self.no_borrowed_copies()
        print()
        if reservations:
            self.current_reservations(reservations)
        else:
            self.no_reservations()
        self.prompt_press_enter()

    @abstractmethod
    def info_connexion(self, user: User) -> None:
        """Display an info message to confirm the user account"""
        pass

    @staticmethod
    def invalid_card_number() -> None:
        """Display an error message for invalid card number problem"""
        print(BaseCliView.ErrorMessages.INVALID_CARD_NUMBER)

    @staticmethod
    def invalid_copy_barcode() -> None:
        """Display an error message for invalid document barcode problem"""
        print(BaseCliView.ErrorMessages.INVALID_DOC_BARCODE)

    @staticmethod
    def invalid_choice() -> None:
        """Display an error message for user invalid choice problem"""
        print(BaseCliView.ErrorMessages.INVALID_CHOICE)

    @staticmethod
    def invalid_ean() -> None:
        """Display an error message for invalid ean problem"""
        print(BaseCliView.ErrorMessages.INVALID_EAN)

    def max_number_of_loans(self) -> None:
        """Display a message when user tries to borrow while he/she already reached maximal number of loans"""
        print(self.ErrorMessages.MAX_NB_OF_LOANS)

    def max_number_of_renewals(self) -> None:
        """Display a message when user tries to renew loans
        while he/she already reached maximal number of loans for this document"""
        print(self.ErrorMessages.MAX_NB_OF_RENEWALS)

    def max_number_of_reservations(self) -> None:
        """Display a message when user tries to reserve while he/she already reached maximal number of reservations"""
        print(self.ErrorMessages.MAX_NB_OF_RESERVATIONS)

    def not_active_user(self) -> None:
        """Display a message to warn that user's account must be updated"""
        print(self.ErrorMessages.NOT_ACTIVE)

    def no_borrowed_copies(self) -> None:
        """Display a message to say that user has currently no documents borrowed"""
        print(self.InfoMessages.NO_BORROWED)

    def no_reservations(self) -> None:
        """Display a message to say that user has currently no reservations"""
        print(self.InfoMessages.NO_RESERVATIONS)

    @staticmethod
    def not_borrowed_copy(copy: BaseCopy) -> None:
        """Display a message for return of a not loaned document"""
        print(BaseCliView.ErrorMessages.NOT_BORROWED_COPY.format(copy))

    def prompt_copy_barcode(self) -> str:
        """Ask user the barcode of the document he/she wishes to act on"""
        return input(BaseCliView.PromptMessages.BARCODE.format(self.quit_letter))

    @staticmethod
    def prompt_press_enter() -> None:
        """Waits for user to press Enter"""
        input(BaseCliView.PromptMessages.PRESS_ENTER)

    def prompt_renew_loan(self) -> str:
        """Ask user the number of the document for which he/she wishes to renew the loan"""
        return input(BaseCliView.PromptMessages.RENEW_LOAN.format(self.quit_letter))

    def prompt_reserve(self) -> str:
        """Ask user the number of the document he/she wants to reserve"""
        return input(BaseCliView.PromptMessages.RESERVE.format(self.quit_letter))

    @staticmethod
    def prompt_reserve_again() -> str:
        """Ask user if he/she wants to search a new document for a reservation"""
        return input(BaseCliView.PromptMessages.RESERVE_AGAIN)

    def prompt_search(self) -> str:
        """Ask user for a query"""
        return input(BaseCliView.PromptMessages.SEARCH.format(self.quit_letter))

    def prompt_card_number(self) -> str:
        """Ask user his/her library card number"""
        return input(BaseCliView.PromptMessages.CARD_NUMBER.format(self.quit_letter))

    @abstractmethod
    def prompt_choice(self) -> str:
        """Ask user what he/she wants to do"""
        pass

    def random_selection(self, notices: list[BaseNotice]) -> None:
        """Display a random list of notices"""
        print(f"\n{BaseCliView.InfoMessages.RANDOM_NOTICES}")
        print("\n".join(BaseCliView.InfoMessages.RANDOM_NOTICE.format(
            num=typer.style(f"{i:>2}", fg=self.choice_color),
            notice=notice,
            ref1=notice.ref1,
            ref2=notice.ref2, ) for i, notice in enumerate(notices, 1)))

    @staticmethod
    def renewal_confirmed(copy: BaseCopy) -> None:
        """Display a confirmation message for document return"""
        print(BaseCliView.InfoMessages.RENEW_CONFIRMATION.format(copy))

    @staticmethod
    def reservation_confirmed(notice: BaseNotice) -> None:
        """Display a confirmation message for a reservation"""
        print(BaseCliView.InfoMessages.RESERVE_CONFIRMATION.format(notice))

    @staticmethod
    def return_confirmed(copy: BaseCopy) -> None:
        """Display a confirmation message for a document return"""
        print(BaseCliView.InfoMessages.RETURN_CONFIRMATION.format(copy))

    @abstractmethod
    def returned_a_reserved_document(self, borrower: User) -> None:
        """Display a warning when a reserved document is returned"""
        pass

    def returned_today(self) -> None:
        """Display a message when user tries to borrow a document he/she has returned the same day"""
        pass

    def search_results(self, results: list[BaseNotice]):
        """Display a message with search results"""
        if results:
            print(BaseCliView.InfoMessages.SEARCH_RESULTS)
            print("\n".join(BaseCliView.InfoMessages.SEARCH_RESULT.format(
                num=typer.style(i, fg=self.choice_color), result=str(result))
                            for i, result in enumerate(results, 1)))
        else:
            print(BaseCliView.InfoMessages.NO_SEARCH_RESULTS)

    @staticmethod
    def unknown_copy_barcode() -> None:
        """Display an error message for user unknown document barcode problem"""
        print(BaseCliView.ErrorMessages.UNKNOWN_DOCUMENT_BARCODE)

    @staticmethod
    def unknown_card_number() -> None:
        """Display an error message for user unknown user card number problem"""
        print(BaseCliView.ErrorMessages.UNKNOWN_CARD_NUMBER)

    @staticmethod
    def unknown_ean() -> None:
        """Display an error message for unknown ean problem"""
        print(BaseCliView.ErrorMessages.UNKNOWN_EAN)

    def welcome(self) -> None:
        """Display a welcome message"""
        self.display_long_separation()
        self.handle_welcome()
        self.display_long_separation()


def get_random_color() -> tuple:
    """
    Get a random RGB color
    :return: random tuple (r, g, b)
    """
    return tuple(randint(0, 255) for _ in range(3))
