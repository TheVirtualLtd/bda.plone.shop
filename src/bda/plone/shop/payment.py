from decimal import Decimal
from bda.plone.cart import CURRENCY_LITERALS
from bda.plone.payment.interfaces import IPaymentSettings
from bda.plone.payment.cash_on_delivery import ICashOnDeliverySettings
from bda.plone.payment.interfaces import ISurcharge
from bda.plone.shop.utils import format_amount
from bda.plone.shop.utils import get_shop_settings
from bda.plone.shop.utils import get_shop_payment_settings
from zope.component import adapter
from zope.interface import implementer
from zope.interface import Interface


@implementer(IPaymentSettings)
@adapter(Interface)
class PaymentSettings(object):

    def __init__(self, context):
        self.context = context

    @property
    def available(self):
        settings = get_shop_payment_settings()
        return settings.available_payment_methods

    @property
    def default(self):
        settings = get_shop_payment_settings()
        return settings.payment_method


@implementer(ICashOnDeliverySettings)
@adapter(Interface)
class CashOnDeliverySettings(object):

    def __init__(self, context):
        self.context = context

    @property
    def currency(self):
        settings = get_shop_settings()
        currency = settings.currency
        show_currency = settings.show_currency
        if show_currency == 'symbol':
            currency = CURRENCY_LITERALS[currency]
        return currency

    @property
    def costs(self):
        try:
            settings = get_shop_payment_settings()
        except KeyError:
            # happens GS profile application if registry entries not present
            # yet
            return Decimal('0')
        costs = settings.cash_on_delivery_costs
        if costs:
            costs = Decimal(str(costs))
        else:
            costs = Decimal('0')
        return format_amount(costs)


@implementer(ISurcharge)
@adapter(Interface)
class Surcharge(object):
    label = None
    description = None

    def __init__(self, context):
        self.context = context

    @property
    def payment_method_surchargeable(self):
        settings = get_shop_payment_settings()
        return settings.surchargeable_payment_methods

    @property
    def currency(self):
        settings = get_shop_settings()
        currency = settings.currency
        show_currency = settings.show_currency
        if show_currency == 'symbol':
            currency = CURRENCY_LITERALS[currency]
        return currency

    @property
    def percent_surcharge(self):
        try:
            settings = get_shop_payment_settings()
        except KeyError:
            # happens GS profile application if registry entries not present
            # yet
            return Decimal('0')
        surcharge = settings.percent_surcharge
        if surcharge:
            return format_amount(Decimal(str(surcharge)))
        else:
            return ''

    @property
    def fixed_surcharge(self):
        try:
            settings = get_shop_payment_settings()
        except KeyError:
            # happens GS profile application if registry entries not present
            # yet
            return Decimal('0')
        surcharge = settings.fixed_surcharge
        if surcharge:
            return format_amount(Decimal(str(surcharge)))
        else:
            return ''

    def surcharge(self, total):
        try:
            settings = get_shop_payment_settings()
        except KeyError:
            # happens GS profile application if registry entries not present
            # yet
            return Decimal('0')
        fixed = (Decimal(str(settings.fixed_surcharge)) if
                 settings.fixed_surcharge else Decimal('0'))
        percent = (Decimal(str(settings.percent_surcharge)) if
                   settings.percent_surcharge else Decimal('0'))
        return (total * percent) / Decimal('100') + fixed
