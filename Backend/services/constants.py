from services.formatters import formatMoney

def textLastDebtorQuestion(user: str, remainingAmount: float) -> str:
    return f'@{user} должен {formatMoney(remainingAmount)}?'

def textLastDebtorApprove(fromUser: str, remainingAmount: float) -> str:
    return f'@{fromUser} согласился взять остаток {formatMoney(remainingAmount)}'

def textLastDebtorPapikApprove(fromUser: str, debtor: str, remainingAmount: float) -> str:
    return f'@{fromUser} определил долю @{debtor} в {formatMoney(remainingAmount)}'
