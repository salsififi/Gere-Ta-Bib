"""Controller for staff users"""
import logging
from datetime import date, timedelta, datetime
from pathlib import Path

from gere_ta_bib.controllers.base_controller import BaseController
from gere_ta_bib.controllers.helpers import check_numeric_choice, exit_func, is_valid_name, check_user_account, \
    get_user_from_card_number, is_valid_ean, is_existing_ean, get_notice_from_ean, get_copy_model_from_notice, \
    is_valid_and_existing_copy_barcode, get_copy_from_barcode, extract_books_data, extract_films_data, \
    extract_musics_data, is_valid_json_file
from gere_ta_bib.models.copies import BaseCopy, COPIES_MODELS
from gere_ta_bib.models.notices import BaseNotice, NOTICES_MODELS, BookNotice, FilmNotice
from gere_ta_bib.models.reservation import Reservation
from gere_ta_bib.models.transaction import Transaction
from gere_ta_bib.models.users import User
from gere_ta_bib.utils.constants import STAFF_ACTIONS, YES_NO, StaffActionsNames, RENEWAL_NB_OF_DAYS_ADDED_TO_TODAY, \
    STAFF_OTHER_ACTIONS, StaffOtherActionsNames, QUIT_LETTER, DOC_TYPES_NAMES, LOGS_FOLDER_PATH, LOG_FORMAT
from gere_ta_bib.views.cli.staff_cli_view import StaffCliView


class StaffController(BaseController):
    """A controller for staff users"""

    def __init__(self, view: StaffCliView):
        self.view = view
        self.actions = STAFF_ACTIONS
        self.other_actions = STAFF_OTHER_ACTIONS
        self.function_by_action = {
            StaffActionsNames.ACCOUNT.value: self.check_account,
            StaffActionsNames.BORROW.value: self.borrow,
            StaffActionsNames.RETURN.value: self.return_copies,
            StaffActionsNames.RENEW.value: self.renew_borrows,
            StaffActionsNames.RESERVE.value: self.reserve,
            StaffActionsNames.SEARCH.value: self.search,
            StaffActionsNames.OTHER.value: self.run_secondary_menu,
            StaffOtherActionsNames.ADD_USER.value: self.add_new_user,
            StaffOtherActionsNames.RENEW_USER.value: self.update_user_account,
            StaffOtherActionsNames.ADD_COPY.value: self.create_new_copy,
            StaffOtherActionsNames.DELETE_COPY.value: self.delete_copy,
            StaffOtherActionsNames.ADD_NOTICES.value: self.add_notices,
            StaffOtherActionsNames.STATS.value: self.show_statistics,
        }

    def add_new_user(self) -> None:
        """Register a new user in the database"""
        while not is_valid_name(last_name := self.view.prompt_user_last_name()):
            self.view.invalid_name()
        if last_name.upper() == QUIT_LETTER:
            return

        while not is_valid_name(first_name := self.view.prompt_user_first_name()):
            self.view.invalid_name()
        if last_name.upper() == QUIT_LETTER:
            return

        last_name = last_name.upper()
        first_name = first_name.title()
        existing_user = User.select().where(
            (User.last_name == last_name) &
            (User.first_name == first_name)
        ).first()
        if existing_user:
            self.view.already_existing_user(existing_user)
        else:
            new_user = User.create(
                last_name=last_name,
                first_name=first_name
            )
            self.view.new_user_created(new_user)

    def add_notices(self) -> None:
        """Add notices from json files"""

        # region Notice type choice
        self.view.notices_to_add_info()
        type_choice = self.view.prompt_notices_type()
        types_choices = {i: doc_type for i, doc_type in enumerate(DOC_TYPES_NAMES, 1)}
        choice = check_numeric_choice(view=self.view,
                                      choices=types_choices,
                                      choice=type_choice,
                                      exit_function=exit_func)
        if not choice:
            return
        doc_type = DOC_TYPES_NAMES[choice - 1]
        notice_model_by_name = {name: notice for notice, name in NOTICES_MODELS.items()}
        notice_model = notice_model_by_name[doc_type]
        # endregion

        # region Path checking of the json file or folder
        while True:
            notices_path = self.view.prompt_notices_path()
            if notices_path.upper() == QUIT_LETTER:
                return
            if not Path(notices_path).exists():
                self.view.not_existing_path(notices_path)
                continue
            if Path(notices_path).is_dir() and not list(Path(notices_path).rglob("*.json")):
                self.view.not_json_folder(str(notices_path))
                continue
            if Path(notices_path).is_file() and not Path(notices_path).suffix == ".json":
                self.view.not_json_file(str(notices_path))
                continue
            if Path(notices_path).is_file() and not is_valid_json_file(notices_path):
                continue
            if Path(notices_path).is_dir():
                nb_errors = 0
                for file in Path(notices_path).rglob("*.json"):
                    if not is_valid_json_file(str(file)):
                        nb_errors += 1
                if nb_errors > 0:
                    continue
            break
        # endregion

        # region Logger
        logging.basicConfig(encoding="utf-8",
                            filename=str(LOGS_FOLDER_PATH / f"{datetime.now().strftime('%y%m%d_%Hh%Mm%Ss')}.log"),
                            level=logging.INFO,
                            format=LOG_FORMAT, )
        # endregion

        # region Notices handling
        if notice_model == BookNotice:
            nb_new, nb_existing, nb_errors = extract_books_data(notices_path)
        elif notice_model == FilmNotice:
            nb_new, nb_existing, nb_errors = extract_films_data(notices_path)
        else:  # notice_model == MusicNotice:
            nb_new, nb_existing, nb_errors = extract_musics_data(notices_path)
        # endregion

        self.view.notices_added_end(nb_new, nb_existing, nb_errors)

    def choose_other_action(self) -> int | None:
        """Display a new menu with other librarian actions, and return choice"""
        self.view.display_other_actions()
        choice = self.view.prompt_choice_other()
        return check_numeric_choice(
            self.view, self.other_actions, choice, exit_func
        )

    def create_new_copy(self) -> None:
        """Create a new copy of a notice"""
        ean = self.view.prompt_new_copy_ean()
        while not (is_valid_ean(ean) and is_existing_ean(ean)):
            if ean.upper() == QUIT_LETTER:
                return
            if not is_valid_ean(ean):
                self.view.invalid_ean()
            elif not is_existing_ean(ean):
                self.view.unknown_ean()
            ean = self.view.prompt_new_copy_ean()
        notice = get_notice_from_ean(ean)
        choice = self.view.prompt_new_copy_confirm(notice)
        if choice.upper() == YES_NO["NO"]:
            return
        copy_model = get_copy_model_from_notice(notice)
        if copy_model:
            new_copy = copy_model.create(
                parent_notice=notice
            )
            self.view.new_copy_created(notice=notice, barcode=new_copy.barcode)

    def delete_copy(self) -> None:
        """Delete a copy of a notice"""
        while not is_valid_and_existing_copy_barcode(barcode := self.view.prompt_delete_copy()):
            continue
        copy = get_copy_from_barcode(barcode)
        copy_deletion_choice = self.view.prompt_delete_copy_confirm(copy)
        if copy_deletion_choice.upper() == YES_NO["YES"]:
            notice: BaseNotice = copy.parent_notice
            model = get_copy_model_from_notice(copy.parent_notice)
            copy.delete_instance()
            self.view.delete_copy_confirm(copy)
            other_existing_copies = model.select().where(
                model.parent_notice == notice).exists()
            if not other_existing_copies:
                notice_deletion_choice = self.view.prompt_delete_notice(notice)
                if notice_deletion_choice.upper() == YES_NO["YES"]:
                    notice.delete_instance()
                    self.view.delete_notice_confirm(notice)

    def handle_returned_today(self, card_number: str, copy: BaseCopy) -> None:
        """Librarian has to decide to accept loan or not"""
        decision = self.view.prompt_return_today()
        if decision.upper() == YES_NO["YES"]:
            Transaction.create(
                card_number=card_number,
                barcode=copy.barcode,
            )
            self.view.borrow_confirmed(copy)

    def handle_max_nb_of_loans(self, card_number: str, copy: BaseCopy) -> None:
        """Librarian has to decide to accept loan or not"""
        decision = self.view.prompt_max_nb_of_loans()
        if decision.upper() == YES_NO["YES"]:
            Transaction.create(
                card_number=card_number,
                barcode=copy.barcode,
            )
            self.view.borrow_confirmed(copy)

    def handle_max_nb_of_renewals(self, card_number: str, copy: BaseCopy) -> None:
        """Librarian has to decide to accept renewal or not"""
        decision = self.view.prompt_max_nb_of_renewals()
        if decision.upper() == YES_NO["YES"]:
            transaction = Transaction.select().where((Transaction.barcode == copy.barcode)
                                                     & Transaction.return_date.is_null()).first()
            transaction.nb_of_renewals += 1
            transaction.due_date = date.today() + timedelta(days=RENEWAL_NB_OF_DAYS_ADDED_TO_TODAY)
            transaction.save()
            self.view.renewal_confirmed(copy)

    def handle_max_nb_of_reservations(self, card_number: str, notice: BaseNotice) -> None:
        """Librarian has to decide to accept reservation or not"""
        decision = self.view.prompt_max_nb_of_reservations()
        if decision.upper() == YES_NO["YES"]:
            Reservation.create(
                card_number=card_number,
                ean=notice.ean,
            )
            self.view.reservation_confirmed(notice)

    @check_user_account
    def update_user_account(self, **kwargs) -> None:
        """Update a user account to set is_active status to True"""
        card_number = kwargs.get("card_number")
        user = get_user_from_card_number(card_number)
        choice = self.view.prompt_update_user_account(user)
        if choice.upper() == YES_NO["NO"]:
            return
        user.updated_at = date.today()
        user.save()
        self.view.user_account_updated(user)

    def run_secondary_menu(self):
        """Run action from the staff secondary menu"""
        while True:
            other_action_num = self.choose_other_action()
            if not other_action_num:
                return
            function = self.get_function_from_choice(actions=self.other_actions,
                                                     choice=other_action_num)
            if function:
                self.view.display_short_separation()
                function()

    def show_statistics(self) -> None:
        """
        Produce statistics:
        - current nb of active users
        - current nb of copies
        - current nb of linked notices
        - nb of loans in the given year
        - nb of new user registrations in the given year
        """
        while True:
            year = self.view.prompt_year()
            if year.upper() == QUIT_LETTER:
                return
            try:
                year = int(year)
            except ValueError:
                self.view.invalid_year()
                continue
            if year < 2000 or year > date.today().year:
                self.view.invalid_year()
                continue
            break
        nb_active_users = User.select().where(User.is_active).count()
        nb_copies = sum(model.select().count() for model in COPIES_MODELS)
        nb_linked_notices = sum(model.select(model.parent_notice).distinct().count() for model in COPIES_MODELS)
        nb_loans = Transaction.select().where(Transaction.borrow_date.year == year).count()
        nb_new_users = User.select().where(User._created_at.year == year).count()
        self.view.statistics(nb_active_users=nb_active_users,
                             nb_copies=nb_copies,
                             nb_linked_notices=nb_linked_notices,
                             nb_loans=nb_loans,
                             nb_new_users=nb_new_users,
                             year=year)


if __name__ == '__main__':
    StaffController(StaffCliView()).run()
