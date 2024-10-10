"""Cmmand line interface view for staff users"""
from datetime import date

import typer
from typer.colors import RED

from gere_ta_bib.models.copies import BaseCopy
from gere_ta_bib.models.notices import BaseNotice
from gere_ta_bib.models.users import User
from gere_ta_bib.utils.constants import (DECORATION_CHAR, LINE_LENGTH, YES_NO, QUIT_LETTER,
                                         STAFF_ACTIONS, STAFF_CHOICE_COLOR, STAFF_OTHER_ACTIONS,
                                         EXAMPLES_NOTICES_FOLDER, DOC_TYPES_NAMES)
from gere_ta_bib.views.cli.base_cli_view import BaseCliView


class StaffCliView(BaseCliView):
    """A view for self-checkout kiosks"""

    choice_color = STAFF_CHOICE_COLOR
    quit_letter = typer.style(QUIT_LETTER, fg=choice_color)

    class ErrorMessages:
        """All error messages are here"""
        ALREADY_BORROWED_BY_SELF = "Ce document est déjà emprunté par la personne."
        ALREADY_RESERVED_BY_SELF = "Cette personne a déjà une réservation en cours pour ce document."
        INVALID_NAME = "Saisie invalide: seules les lettres, l'espace et le tiret '-' sont valides."
        INVALID_YEAR = ("Saisie invalide: écrivez l'année de votre choix "
                        "entre 2000 et aujourd'hui au format: 20XX.")
        MAX_NB_OF_RESERVATIONS = "Nombre maximal de réservations atteint."
        NOT_ACTIVE_USER = "Abonnement arrivé à échéance."
        NOT_EXISTING_PATH = "Le chemin '{}' n'existe pas."
        NOT_JSON_FILE = "Ce fichier n'est pas un fichier json..."
        NOT_JSON_FOLDER = "Ce dossier ne contient aucun fichier json..."

    class InfoMessages:
        """All info messages are here"""
        STATISTICS = ("Actuellement:\n"
                      "- Utisateurices: {nb_active_users} usagères et usagers actif·ves\n"
                      "- Taille de la collection: {nb_copies} exemplaires, pour {nb_linked_notices} "
                      "notices non orphelines\n\n"
                      "Au cours de l'année {year}:\n"
                      "- Prêts: {nb_loans} prêts réalisés\n"
                      "- Inscriptions: {nb_new_users} nouvelles inscriptions réalisées")
        ACTIONS = "\n".join(
            f"{typer.style(num, fg=STAFF_CHOICE_COLOR)}: {action}" for num, action in STAFF_ACTIONS.items())
        ACTIONS_OTHER = "\n".join(
            f"{typer.style(num, fg=STAFF_CHOICE_COLOR)}: {action}" for num, action in STAFF_OTHER_ACTIONS.items())
        ALREADY_EXISTING_USER = "{user} est déjà inscrit, son numéro de carte est: {card_number}."
        ALREADY_EXISTING_NOTICE = "Le {notice_type} '{notice}' existe déjà dans la base."
        BORROWED = "Emprunts actuels ({} retard):"
        CONNEXION_CONFIRMATION = "Compte de {}"
        DELETE_COPY_CONFIRMATION = "L'exemplaire '{copy}' a bien été supprimé."
        DELETE_NOTICE_CONFIRMATION = "La notice '{notice}' a bien été supprimée."
        NOTICE_ADDED = "Ajout du {notice_type} '{notice}'."
        NOTICES_ADDED_END = ("Fin de l'opération de récupération des notices:\n"
                             "-> {nb_new_notices} ajoutée{s1}\n"
                             "-> {nb_existing_notices} existai{ent} déjà\n"
                             "-> {nb_errors} erreurs rencontrée{s2} pendant l'exécution\n"
                             "Pour plus de détails, voir le fichier de log, qui sera généré "
                             f"{typer.style("à l'arrêt du programme", fg="yellow")} "
                             "dans le dossier geretabib/logs.")
        NEW_COPY_CREATED_CONFIRMATION = ("Un nouvel exemplaire de {notice} a été créé.\n"
                                         "Son code-barres ewxemplaire est: {barcode}.")
        NEW_USER_CREATED_CONFIRMATION = ("L'inscriuption de {first_name} {last_name} a bien été réalisée!\n"
                                         "Son numéro de carte est: {card_number}.")
        NO_BORROWED = "Aucun document actuellement emprunté."
        NO_RESERVATIONS = "Aucune réservation en cours."
        NO_USER_FOUND = "Personne ne correspond à cette recherche..."
        NOTICES_TO_ADD = ("Pour importer des notices, vous devez fournir un fichier (ou un dossier de fichiers) \n"
                          "au format json, contruit comme dans les modèles à cet emplacement:\n"
                          f"'{EXAMPLES_NOTICES_FOLDER}'.")
        RESERVED_NOTICES = "Réservations en cours (dont {nb} disponible{s}):"
        RETURN_A_RESERVED_DOCUMENT = "Ce document est réservé par {}."
        USER_FOUND = "{num}: {user}"
        USERS_FOUND = "Les personnes inscrites correspondant à votre recherche sont:"
        USER_UPDATED_CONFIRMATION = ("Le compte de {user} a été mis à jour.\n"
                                     "Son  abonnement est désormais valable jusqu'au {date}.")

    class PromptMessages:
        """All prompt messages are here"""
        BACK_TO_MENU = f"('{typer.style(QUIT_LETTER, fg=STAFF_CHOICE_COLOR)}' pour revenir au menu)"
        YEAR_OF_STATITICS = f"{BACK_TO_MENU} Pour quelle année souhaitez-vous afficher des statistiques ? "
        BACK_TO_MAIN_MENU = f"('{typer.style(QUIT_LETTER, fg=STAFF_CHOICE_COLOR)}' pour revenir au menu principal)"
        CHOICE = f"('{typer.style(QUIT_LETTER, fg=STAFF_CHOICE_COLOR)}' pour quitter) Votre choix ? "
        CHOICE_OTHER = f"{BACK_TO_MAIN_MENU} Votre choix ? "
        DELETE_COPY = f"{BACK_TO_MENU} Code-barres de l'exemplaire à supprimer: "
        DELETE_COPY_CONFIRM = ("Vous allez supprimer {copy}.\n"
                               f"Confirmez-vous la suppression ? [{YES_NO["YES"].lower()}/{YES_NO["NO"].upper()}] ")
        DELETE_NOTICE = ("Vous venez de supprimer le dernier exemplaire de {notice}.\n"
                         "Voulez-vous supprimer la notice bibliographoique associée ? "
                         f"[{YES_NO["YES"].lower()}/{YES_NO["NO"].upper()}] ")
        MAX_NB_OF_LOANS = ("Cette personne a déjà atteint le nombre maximal d'emprunts.\n"
                           "Faire tout de même le prêt ?"
                           f"[{YES_NO["YES"].lower()}/{YES_NO["NO"].upper()}] ")
        MAX_NB_OF_RENEWALS = ("Cette personne a déjà atteint le nombre maximal de prolongations pour ce document.\n"
                              "Faire tout de même une nouvelle prolongation ?"
                              f"[{YES_NO["YES"].lower()}/{YES_NO["NO"].upper()}] ")
        MAX_NB_OF_RESERVATIONS = ("Cette personne a déjà atteint le nombre maximal de réservations.\n"
                                  "Faire tout de même une nouvelle réservation ?"
                                  f"[{YES_NO["YES"].lower()}/{YES_NO["NO"].upper()}] ")
        NEW_COPY_EAN = f"{BACK_TO_MENU}\nSaisissez l'EAN du document dont vous voulez créer un exemplaire: "
        NEW_COPY_CONFIRM = ("Vous allez créer un nouvel exemplaire de: {notice}.\n"
                            f"Confirmez-vous ? [{YES_NO["YES"].upper()}/{YES_NO["NO"].lower()}] ")
        NEW_USER_FIRST_NAME = f"{BACK_TO_MENU} Prénom: "
        NEW_USER_LAST_NAME = f"{BACK_TO_MENU} Nom de famille: "
        NOTICES_FILE_PATH = (f"{BACK_TO_MENU}\nIndiquez l'emplacement absolu du fichier json "
                             "(ou du dossier contenant des fichiers json):\n")
        NOTICES_TYPE_TO_ADD = (f"{BACK_TO_MENU} Quel type de notices voulez-vous ajouter ?\n"
                               f"{'\n'.join(f"{typer.style(i, fg=STAFF_CHOICE_COLOR)}: {type}"
                                            for i, type in enumerate(DOC_TYPES_NAMES, 1))}\n"
                               "Votre choix ? ")
        RETURNED_TODAY = ("Document rendu ce jour par la personne.\n"
                          "Faire tout de même un nouvel emprunt ? "
                          f"[{YES_NO["YES"].lower()}/{YES_NO["NO"].upper()}] ")
        UPDATE_USER = ("Voulez-vous mettre à jour le dossier de {} ? "
                       f"[{YES_NO["YES"].upper()}/{YES_NO["NO"].lower()}] ")
        USER_SEARCH = f"{BACK_TO_MENU} Qui cherchez-vous ? "

    class ReceptionMessage:
        """All reception messages are here"""
        GOOD_BYE = "À demain (si vous le voulez bien 😜) !"
        WELCOME = f"Bienvenue !\n{date.today().strftime('%A %e %B %Y').capitalize()}"

    def already_existing_user(self, user: User) -> None:
        """Display a message to say that a user is already existing ion the database"""
        print(self.InfoMessages.ALREADY_EXISTING_USER.format(user=user, card_number=user.card_number))

    def delete_copy_confirm(self, copy: BaseCopy) -> None:
        """Display a message to confirm that a copy was deleted"""
        print(self.InfoMessages.DELETE_COPY_CONFIRMATION.format(copy=copy))

    def delete_notice_confirm(self, notice: BaseNotice) -> None:
        """Display a message to confirm that a copy was deleted"""
        print(self.InfoMessages.DELETE_NOTICE_CONFIRMATION.format(notice=notice))

    @staticmethod
    def display_long_separation():
        """Display a separation to improve readability between operations"""
        print("".join(typer.style(DECORATION_CHAR, fg=RED) for _ in range(LINE_LENGTH)))

    def display_other_actions(self) -> None:
        """Display a secondary menu with staff other actions"""
        self.display_long_separation()
        print(self.InfoMessages.ACTIONS_OTHER)

    def handle_welcome(self) -> None:
        """Display a welcome message"""
        char = typer.style(DECORATION_CHAR, fg=RED)
        for line in self.ReceptionMessage.WELCOME.split("\n"):
            print(char, line.center(LINE_LENGTH - 4), char)

    def info_connexion(self, user: User) -> None:
        """Display a personnalized welcome when user is connecting"""
        print(f"\n{self.InfoMessages.CONNEXION_CONFIRMATION.format(user)}")

    def invalid_name(self) -> None:
        """Display a message sayong that name input is not valid"""
        print(self.ErrorMessages.INVALID_NAME)

    def invalid_year(self) -> None:
        """Display a message sayong that year input is not valid"""
        print(self.ErrorMessages.INVALID_YEAR)

    def notices_added_end(self, nb_new_notices: int, nb_existing_notices: int, nb_errors: int) -> None:
        """Confirm that new notices were correctly added"""
        print(self.InfoMessages.NOTICES_ADDED_END.format(nb_new_notices=nb_new_notices,
                                                         s1="s" if nb_new_notices > 1 else "",
                                                         nb_existing_notices=nb_existing_notices,
                                                         ent="ent" if nb_existing_notices > 1 else "t",
                                                         nb_errors=nb_errors,
                                                         s2="s" if nb_errors > 1 else ""))

    def notices_to_add_info(self) -> None:
        """Say where to find example json notices files to import"""
        print(typer.style(self.InfoMessages.NOTICES_TO_ADD, fg="yellow"))

    def new_copy_created(self, notice: BaseNotice, barcode: str) -> None:
        """Display a message to confirm that a new copy of a notice has been created"""
        print(self.InfoMessages.NEW_COPY_CREATED_CONFIRMATION.format(notice=notice, barcode=barcode))

    def new_user_created(self, user: User) -> None:
        """Display a message to confirm the registration of a new user, and giving the card number"""
        print(self.InfoMessages.NEW_USER_CREATED_CONFIRMATION.format(
            last_name=user.last_name,
            first_name=user.first_name,
            card_number=user.card_number
        ))

    def not_existing_path(self, path: str) -> None:
        """Display a message when a path given by user doesn't exist"""
        print(self.ErrorMessages.NOT_EXISTING_PATH.format(path))

    def not_json_file(self, file_path: str) -> None:
        """Display a message if file is not a json file"""
        print(self.ErrorMessages.NOT_JSON_FILE)

    def not_json_folder(self, folder_path: str) -> None:
        """Display a message if folder doesn't contain any json file"""
        print(self.ErrorMessages.NOT_JSON_FOLDER)

    def prompt_choice(self) -> str:
        """Ask staff memeber what he/she wants to do in the main menu"""
        return input(self.PromptMessages.CHOICE)

    def prompt_choice_other(self) -> str:
        """Ask staff member what he/she wants to do in the secondary menu"""
        return input(self.PromptMessages.CHOICE_OTHER)

    def prompt_delete_copy(self) -> str:
        """Ask the barcode of the copy to delete"""
        return input(self.PromptMessages.DELETE_COPY)

    def prompt_delete_copy_confirm(self, copy: BaseCopy) -> str:
        """Ask to confirm a copy deletion"""
        return input(self.PromptMessages.DELETE_COPY_CONFIRM.format(copy=copy))

    def prompt_delete_notice(self, notice: BaseNotice) -> str:
        """Ask if staff member wants to delete a notice without copies"""
        return input(self.PromptMessages.DELETE_NOTICE.format(notice=notice))

    def prompt_max_nb_of_loans(self) -> str:
        """Ask librarian if a loan must be done when user has already the maximal number of loans"""
        return input(self.PromptMessages.MAX_NB_OF_LOANS)

    def prompt_max_nb_of_renewals(self) -> str:
        """Ask librarian if the renewal of a document already renewed the maximal number of times can be accepted"""
        return input(self.PromptMessages.MAX_NB_OF_RENEWALS)

    def prompt_max_nb_of_reservations(self) -> str:
        """Ask librarian if the loan of a document returned by the same user the same day can be accepted"""
        return input(self.PromptMessages.MAX_NB_OF_RESERVATIONS)

    def prompt_new_copy_confirm(self, notice: BaseNotice) -> str:
        """Ask to confirm the creation of a new copy"""
        return input(self.PromptMessages.NEW_COPY_CONFIRM.format(notice=notice))

    def prompt_new_copy_ean(self) -> str:
        """Ask the EAN of the notice to create a new copy"""
        return input(self.PromptMessages.NEW_COPY_EAN)

    def prompt_notices_path(self) -> str:
        """Ask for the path of the file (or folder) with notices json data to add"""
        return input(self.PromptMessages.NOTICES_FILE_PATH)

    def prompt_notices_type(self) -> str:
        """Ask for the type of the notices to add"""
        return input(self.PromptMessages.NOTICES_TYPE_TO_ADD)

    def prompt_update_user_account(self, user: User) -> str:
        """Ask staff member to update or not a user account"""
        return input(self.PromptMessages.UPDATE_USER.format(user))

    def prompt_search_user(self) -> str:
        """Ask words to search for a user in the database"""
        return input(self.PromptMessages.USER_SEARCH)

    def prompt_return_today(self) -> str:
        """Ask librarian if the loan of a document returned by the same user the same day can be accepted"""
        return input(self.PromptMessages.RETURNED_TODAY)

    def prompt_user_first_name(self) -> str:
        """Ask staff member the first namme of the user to register"""
        return input(self.PromptMessages.NEW_USER_FIRST_NAME)

    def prompt_user_last_name(self) -> str:
        """Ask staff member the last namme of the user to register"""
        return input(self.PromptMessages.NEW_USER_LAST_NAME)

    def prompt_year(self) -> str:
        """Ask staff member on which year he/she wants to produce statistics"""
        return input(self.PromptMessages.YEAR_OF_STATITICS)

    def returned_a_reserved_document(self, borrower: User) -> None:
        """Display a warning when a reserved document is returned"""
        print(self.InfoMessages.RETURN_A_RESERVED_DOCUMENT.format(borrower))

    def user_account_updated(self, user: User) -> None:
        """Display a message to confirm that user account has been updated,
        and to give the new date of membership ending"""
        print(self.InfoMessages.USER_UPDATED_CONFIRMATION.format(user=user,
                                                                 date=user.membership_end.strftime("%e %B %Y")))

    def statistics(self, **kwargs) -> None:
        """
        Produce statistics:
        - current nb of active users
        - current nb of copies
        - current nb of notices
        - nb of loans in the given year
        - nb of new users registrations in the given year
        """
        self.display_short_separation()
        print(self.InfoMessages.STATISTICS.format(
            year=kwargs.get("year"),
            nb_active_users=kwargs.get("nb_active_users"),
            nb_copies=kwargs.get("nb_copies"),
            nb_linked_notices=kwargs.get("nb_linked_notices"),
            nb_loans=kwargs.get("nb_loans"),
            nb_new_users=kwargs.get("nb_new_users")
        ))
        self.prompt_press_enter()


if __name__ == '__main__':
    print(StaffCliView.PromptMessages.NOTICES_TYPE_TO_ADD)
