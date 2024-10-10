

class AlreadyBorrowedBySelfError(Exception):
    def __init__(self, message="Document déjà emprunté par cette personne."):
        self.message = message
        super().__init__(self.message)


class AlreadyBorrowedByOtherError(Exception):
    def __init__(self, message="Document actuellement emprunté par une autre personne."):
        self.message = message
        super().__init__(self.message)


class AlreadyReservedBySelfError(Exception):
    def __init__(self, message="Réservation déjà en cours sur cette notice pour cette personne."):
        self.message = message
        super().__init__(self.message)


class CopyBorrowedTodayError(Exception):
    def __init__(self, message="Document emprunté ce jour, prolongation impossible."):
        self.message = message
        super().__init__(self.message)


class ExitFunction(Exception):
    pass


class MaxNbOfLoansError(Exception):
    def __init__(self, message="Nombre maximal d'emprunts atteint."):
        self.message = message
        super().__init__(self.message)


class MaxNbOfReservationsError(Exception):
    def __init__(self, message="Nombre maximal de réservations atteint."):
        self.message = message
        super().__init__(self.message)


class MaxNbOfRenewalsError(Exception):
    def __init__(self, message="Nombre maximal de prolongations atteint."):
        self.message = message
        super().__init__(self.message)


class MultipleCopyBarcodeError(Exception):
    def __init__(self, message="Ce code-barres exemplaire est présent dans plusieurs tables."):
        self.message = message
        super().__init__(self.message)


class MultipleEANError(Exception):
    def __init__(self, message="Ce code-barres commercial (EAN) est présent dans plusieurs tables"):
        self.message = message
        super().__init__(self.message)


class NotBorrowedCopyError(Exception):
    def __init__(self, message="Ce document n'était pas emprunté."):
        self.message = message
        super().__init__(self.message)


class NotExistingFieldsError(Exception):
    def __init__(self, fields: list, message="Ces champs n'existent pas: {}"):
        self.message = message.format(
            s="s" if len(fields) > 1 else "",
            nt="nt" if len(fields) > 1 else "",
            fields=", ".join(f"'{field}'" for field in fields)
        )
        super().__init__(self.message)


class ReturnedTodayError(Exception):
    def __init__(self, message="Emprunt impossible car le document a été rendu aujourd'hui par cette personne."):
        self.message = message
        super().__init__(self.message)


class UnkonowCopyBarcodeError(Exception):
    def __init__(self, message="Code-barres exemplaire inconnu."):
        self.message = message
        super().__init__(self.message)


class UnkonowEANError(Exception):
    def __init__(self, message="Code-barres commercial (EAN) inconnu."):
        self.message = message
        super().__init__(self.message)


class ValidationError(Exception):
    pass


if __name__ == '__main__':
    pass
