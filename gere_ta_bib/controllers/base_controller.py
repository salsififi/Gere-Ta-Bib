"""Define the main controller"""
import random
from abc import ABC, abstractmethod
from datetime import date
from enum import Enum
from pprint import pprint
from typing import Callable

from gere_ta_bib.controllers.helpers import (get_reservations_from_card_number, get_borrowed_copies_dict,
                                             get_copy_from_barcode,
                                             is_valid_and_existing_copy_barcode, check_user_account,
                                             get_notices_from_keywords,
                                             check_numeric_choice, exit_func, NOTICES_MODELS, is_reserved,
                                             get_first_reservation_from_barcode, is_reserved_by_self)
from gere_ta_bib.models.copies import BaseCopy
from gere_ta_bib.models.notices import BaseNotice
from gere_ta_bib.models.reservation import Reservation
from gere_ta_bib.models.transaction import Transaction
from gere_ta_bib.models.users import User
from gere_ta_bib.utils.constants import NB_OF_RANDOM_NOTICES, QUIT_LETTER, ReservationStatuses, YES_NO
from gere_ta_bib.utils.exceptions import CopyBorrowedTodayError, MaxNbOfRenewalsError, AlreadyBorrowedByOtherError, \
    AlreadyBorrowedBySelfError, ReturnedTodayError, MaxNbOfReservationsError, AlreadyReservedBySelfError, \
    MaxNbOfLoansError
from gere_ta_bib.views.cli.base_cli_view import BaseCliView


class BaseController(ABC):
    """Abstract model for controllers"""

    @abstractmethod
    def __init__(self, view: BaseCliView):
        """Has a view and actions"""
        self.view = view
        self.actions = None  # To replace with USER_ACTIONS or STAFF_ACTIONS in inherited classes
        self.function_by_action = {}

    @check_user_account
    def borrow(self, **kwargs) -> None:
        """Borrow document(s)"""
        card_number = kwargs.get("card_number")
        while (barcode := self.view.prompt_copy_barcode().upper()) != QUIT_LETTER:
            if not is_valid_and_existing_copy_barcode(barcode):
                continue
            copy = get_copy_from_barcode(barcode)
            try:
                Transaction.borrow_copy(card_number, barcode)
                self.view.borrow_confirmed(copy)
                if is_reserved_by_self(barcode, card_number):
                    reservation: Reservation = Reservation.get((Reservation.ean == copy.parent_notice.ean)
                                                               & (Reservation.card_number == card_number))
                    reservation.pickup_date = date.today()
                    reservation.save()
            except AlreadyBorrowedByOtherError:
                current_borrow: Transaction = Transaction.select().where((Transaction.barcode == barcode)
                                                                         & (Transaction.return_date.is_null())).first()
                current_borrow.return_date = date.today()
                current_borrow.save()
                Transaction.borrow_copy(card_number, barcode)
                self.view.borrow_confirmed(copy)
            except AlreadyBorrowedBySelfError:
                self.view.already_borrowed_by_self(copy)
            except ReturnedTodayError:
                self.handle_returned_today(card_number, copy)
            except MaxNbOfLoansError:
                self.handle_max_nb_of_loans(card_number, copy)

    @check_user_account
    def check_account(self, **kwargs) -> None:
        """Check borrowed and reserved documents"""
        card_number = kwargs.get("card_number")
        borrowed = get_borrowed_copies_dict(card_number)
        reservations = get_reservations_from_card_number(card_number)
        self.view.info_account(borrowed, reservations)

    def choose_action(self) -> int:
        """Get the user's choice in the menu"""
        self.view.display_possible_actions()
        choice = self.view.prompt_choice()
        return check_numeric_choice(
            self.view, self.actions, choice, self.view.goodbye
        )

    @staticmethod
    def daily_routine() -> None:
        """Operations that must be done every day"""
        # Set transactions overdue statuses
        for transaction in Transaction.select().where(Transaction.return_date.is_null()):
            transaction.set_overdue()

        # Set reservations statuses
        for reservation in Reservation.select().where(
                Reservation.status.in_([ReservationStatuses.PENDING, ReservationStatuses.AVAILABLE])):
            reservation.set_status()

        # Set users is_active statuses
        for user in User.select():
            user.set_is_active_status()

    def get_function_from_choice(self, actions: dict, choice: int) -> Callable:
        """Get function associated to choice"""
        return self.function_by_action.get(actions.get(choice))

    def get_random_selection(self) -> None:
        """Get a random selection of notices"""
        all_notices = [notice for notice_model in NOTICES_MODELS for notice in notice_model.select()]
        nb_to_display = min(NB_OF_RANDOM_NOTICES, len(all_notices))
        random_notices = random.sample(all_notices, k=nb_to_display)
        self.view.random_selection(random_notices)
        self.view.prompt_press_enter()

    def handle_max_nb_of_loans(self, card_number: str, copy: BaseCopy) -> None:
        """Handle the MaxNbOfLoansError based on view"""
        pass

    def handle_max_nb_of_renewals(self, card_number: str, copy: BaseCopy) -> None:
        """Handle the MaxNbOfRenewalsError based on view"""
        pass

    @abstractmethod
    def handle_max_nb_of_reservations(self, card_number: str, notice: BaseNotice) -> None:
        """Handle the ReturnedTodayError based on view"""
        pass

    @abstractmethod
    def handle_returned_today(self, card_number: str, copy: BaseCopy) -> None:
        """Handle the ReturnedTodayError based on view"""
        pass

    @check_user_account
    def renew_borrows(self, **kwargs) -> None:
        """Renew loan(s)"""
        card_number = kwargs.get("card_number")
        borrowed = get_borrowed_copies_dict(card_number)
        if borrowed:
            self.view.borrowed_copies(borrowed)
            while (num := self.view.prompt_renew_loan()).upper() != QUIT_LETTER:
                try:
                    num = int(num)
                    if num not in range(1, len(borrowed) + 1):
                        self.view.invalid_choice()
                        continue
                except ValueError:
                    self.view.invalid_choice()
                    continue
                copy: BaseCopy = list(borrowed)[num - 1]
                transaction = Transaction.select().where((Transaction.barcode == copy.barcode)
                                                         & Transaction.return_date.is_null()).first()
                try:
                    transaction.renew_borrow()
                    self.view.renewal_confirmed(copy)
                except CopyBorrowedTodayError:
                    self.view.borrowed_today()
                except MaxNbOfRenewalsError:
                    self.handle_max_nb_of_renewals(card_number, copy)
        else:
            self.view.borrowed_copies(borrowed)
            self.view.prompt_press_enter()

    @check_user_account
    def reserve(self, **kwargs) -> None:
        """Make a reservation"""
        card_number = kwargs.get("card_number")
        while (query := self.view.prompt_search().upper()) != QUIT_LETTER:
            notices = get_notices_from_keywords(self.view, query)
            if notices:
                possible_choices = {num: notice for num, notice in enumerate(notices, 1)}
                choice = self.view.prompt_reserve()
                notice_nb = check_numeric_choice(self.view, possible_choices, choice, exit_func)
                if not notice_nb:
                    return
                notice = possible_choices.get(notice_nb)
                try:
                    Reservation.reserve(card_number, notice.ean)
                    self.view.reservation_confirmed(notice)
                except MaxNbOfReservationsError:
                    self.handle_max_nb_of_reservations(card_number, notice)
                except AlreadyReservedBySelfError:
                    self.view.already_reserved_by_self()

            if self.view.prompt_reserve_again().upper() == YES_NO["NO"]:
                return

    def return_copies(self) -> None:
        """Return document(s)"""
        while (barcode := self.view.prompt_copy_barcode().upper()) != QUIT_LETTER:
            if not is_valid_and_existing_copy_barcode(barcode):
                continue
            copy = get_copy_from_barcode(barcode)
            transaction: Transaction = Transaction.select().where((Transaction.barcode == barcode) &
                                                                  (Transaction.return_date.is_null(True))).first()
            if transaction:
                transaction.return_copy()
                self.view.return_confirmed(copy)
                if is_reserved(barcode):
                    reservation = get_first_reservation_from_barcode(barcode)
                    reservation.availability_date = date.today()
                    reservation.save()
                    self.view.returned_a_reserved_document(transaction.borrower)
            else:
                self.view.not_borrowed_copy(copy)
            continue

    def run(self) -> None:
        self.daily_routine()
        self.view.welcome()
        while True:
            action_num = self.choose_action()
            function = self.get_function_from_choice(self.actions, action_num)
            if function:
                self.view.display_short_separation()
                function()
                self.view.display_long_separation()

    def search(self) -> None:
        """Keyword search in the library catalog"""
        while (user_query := self.view.prompt_search().upper()) != QUIT_LETTER:
            get_notices_from_keywords(self.view, user_query)


if __name__ == '__main__':
    pass
