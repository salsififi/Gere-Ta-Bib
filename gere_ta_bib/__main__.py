"""
"Gère Ta Bib"
A library management software in commandline
Author: Simon Salvaing
Date: septembre 2024

Entry point
"""
import sys

import typer

from gere_ta_bib.controllers.staff_controller import StaffController
from gere_ta_bib.controllers.user_controller import UserController
from gere_ta_bib.views.cli.staff_cli_view import StaffCliView
from gere_ta_bib.views.cli.user_cli_view import UserCliView

app = typer.Typer()


@app.command("staff")
def launch_staff_controller() -> None:
    """Launch program for a staff member"""
    return StaffController(StaffCliView()).run()


@app.command("user")
def launch_user_controller() -> None:
    """Launch program for a standard user"""
    return UserController(UserCliView()).run()


def main() -> None:
    """Called if no command is given after python -m gere_ta_bib"""
    print("Pour accéder à la médiathèque, vous devez préciser un profil:\n"
          "Choisissez entre USER (utilisateurice standard) et STAFF (médiathécaires):", end=" ")
    while (choice := input()).lower() not in ("user", "staff"):
        print("Choix invalide. Saisissez USER ou STAFF, puis appuyez sur 'Entrée':", end=" ")
        continue
    sys.argv.append(choice.lower())


if __name__ == '__main__':
    if len(sys.argv) == 1:
        main()
    else:
        if sys.argv[-1] == "-h":
            sys.argv[-1] = "--help"
    app()

