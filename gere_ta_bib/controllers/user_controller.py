"""Controller for library standard users"""

from gere_ta_bib.controllers.base_controller import BaseController
from gere_ta_bib.models.copies import BaseCopy
from gere_ta_bib.utils.constants import USER_ACTIONS, UserActionNames
from gere_ta_bib.views.cli.user_cli_view import UserCliView


class UserController(BaseController):
    """A controller for library standard users"""

    def __init__(self, view: UserCliView):
        self.view = view
        self.actions = USER_ACTIONS
        self.function_by_action = {
            UserActionNames.ACCOUNT.value: self.check_account,
            UserActionNames.BORROW.value: self.borrow,
            UserActionNames.RETURN.value: self.return_copies,
            UserActionNames.RENEW.value: self.renew_borrows,
            UserActionNames.RESERVE.value: self.reserve,
            UserActionNames.SELECTION.value: self.get_random_selection,
            UserActionNames.SEARCH.value: self.search,
        }

    def handle_max_nb_of_loans(self, card_number: str, copy: BaseCopy) -> None:
        """Display a message saying that maximal number of loans was reached"""
        self.view.max_number_of_loans()

    def handle_max_nb_of_renewals(self, card_number: str, copy: BaseCopy) -> None:
        """Display a message saying that maximal number of reservations was reached"""
        self.view.max_number_of_renewals()

    def handle_max_nb_of_reservations(self, card_number: str, notice: str) -> None:
        """Display a message saying that maximal number of reservations was reached"""
        self.view.max_number_of_reservations()

    def handle_returned_today(self, card_number: str, copy: BaseCopy) -> None:
        """Display a message saying that document was returned today so can't be borrowed"""
        self.view.returned_today()


if __name__ == '__main__':
    UserController(UserCliView()).run()
