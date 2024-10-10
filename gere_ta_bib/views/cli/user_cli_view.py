"""Cmmand line interface view for standard users"""
from datetime import date

import typer

from gere_ta_bib.models.users import User
from gere_ta_bib.utils.constants import LINE_LENGTH, DECORATION_CHAR, QUIT_LETTER, USER_ACTIONS, \
    MAX_NB_OF_RESERVATIONS, MAX_NB_OF_LOANS, MAX_NB_OF_RENEWALS, USER_CHOICE_COLOR
from gere_ta_bib.views.cli.base_cli_view import BaseCliView, get_random_color


class UserCliView(BaseCliView):
    """A view for self-checkout kiosks"""

    choice_color = USER_CHOICE_COLOR
    quit_letter = typer.style(QUIT_LETTER, fg=choice_color)

    class ErrorMessages:
        """All error messages are here"""
        ALREADY_BORROWED_BY_SELF = "Ce document est déjà enregistré dans vos emprunts."
        ALREADY_RESERVED_BY_SELF = "Vous avez déjà une réservation en cours pour ce document."
        MAX_NB_OF_LOANS = f"Vous avez déjà atteint le nombre maximal d'emprunts ({MAX_NB_OF_LOANS})."
        MAX_NB_OF_RENEWALS = (f"Vous avez déjà atteint le nombre maximal de prolongations ({MAX_NB_OF_RENEWALS}) "
                              "pour ce document.")
        MAX_NB_OF_RESERVATIONS = (f"Vous avez déjà atteint le nombre maximal "
                                  f"de réservations ({MAX_NB_OF_RESERVATIONS}).")
        NOT_ACTIVE = "Votre abonnement est arrivé à échéance, adressez-vous à un·e bibliothécaire."
        RETURNED_TODAY = ("Emprunt impossible, car vous avez rendu ce document aujourd'hui.\n"
                          "Adressez-vous à un·e bibliothécaire.")

    class InfoMessages:
        """All info messages are here"""
        ACTIONS = "\n".join(
            f"{typer.style(num, fg=USER_CHOICE_COLOR)}: {action}" for num, action in USER_ACTIONS.items())
        BORROWED = "Liste de vos emprunts actuels ({} retard):"
        CONNEXION_CONFIRMATION = "Bonjour {} !"
        NO_BORROWED = "Vous n'avez actuellement aucun document emprunté."
        NO_RESERVATIONS = "Vous n'avez aucune réservation en cours."
        RESERVED_NOTICES = "Liste de vos réservations en cours (dont {nb} disponible{s}):"
        RETURN_A_RESERVED_DOCUMENT = "Ce document est réservé. Merci de le remettre à un·e bibliothécaire."

    class PromptMessages:
        """All prompt messages are here"""
        CHOICE = f"('{typer.style(QUIT_LETTER, fg=USER_CHOICE_COLOR)}' pour quitter) Votre choix ? "

    class ReceptionMessage:
        """All reception messages are here"""
        GOOD_BYE = "Merci et à bientôt !"
        WELCOME = ("Bienvenue dans votre médiathèque !\n"
                   "(C'est gratuit, c'est pour tout le monde !)\n"
                   f"{date.today().strftime('%A %e %B %Y').capitalize()}")

    @staticmethod
    def display_long_separation():
        """Display a separation to improve readability between operations"""
        print("".join(typer.style(DECORATION_CHAR, fg=get_random_color()) for _ in range(LINE_LENGTH)))

    def info_connexion(self, user: User) -> None:
        """Display a personnalized welcome when user is connecting"""
        print(f"\n{self.InfoMessages.CONNEXION_CONFIRMATION.format(user.first_name)}")

    def returned_today(self) -> None:
        """Display a message when user tries to borrow a document he/she has returned the same day"""
        print(self.ErrorMessages.RETURNED_TODAY)

    def prompt_choice(self) -> str:
        """Ask user what he/she wants to do"""
        return input(self.PromptMessages.CHOICE)

    def returned_a_reserved_document(self, borrower: User) -> None:
        """Display a warning when a reserved document is returned"""
        print(self.InfoMessages.RETURN_A_RESERVED_DOCUMENT)

    def handle_welcome(self) -> None:
        """Display a welcome message"""
        char = typer.style(DECORATION_CHAR, fg=get_random_color())
        for line in self.ReceptionMessage.WELCOME.split("\n"):
            print(char, line.center(LINE_LENGTH - 4), char)
