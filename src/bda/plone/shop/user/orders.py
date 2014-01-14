from AccessControl import Unauthorized
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from bda.plone.orders import message_factory as _bpo
from bda.plone.orders.browser.views import OrdersTable
from bda.plone.orders.browser.views import TableData
from bda.plone.orders.browser.views import Translate
from bda.plone.shop import message_factory as _
from plone.api import user as apiuser
from repoze.catalog.query import Contains
from repoze.catalog.query import Eq
from yafowil.utils import Tag


class UserOrdersTable(OrdersTable):
    table_template = ViewPageTemplateFile('templates/table.pt')

    @property
    def current_user(self):
        user = apiuser.get_current()
        if not user:
            return None
        return user.getId()

    def _check_permission(self, perm, userid=None):
        perms = apiuser.get_permissions(obj=self.context, username=userid)
        return perm in perms and perms[perm] or False

    @property
    def allow_view_all_orders(self):
        return self._check_permission('bda.plone.shop: View all orders')

    @property
    def allow_view_vendor_orders(self):
        return self._check_permission('bda.plone.shop: View vendor orders')

    @property
    def allow_userfilter(self):
        return self.allow_view_vendor_orders or self.allow_view_all_orders

    @property
    def url(self):
        return self.request.getURL()

    @property
    def ajaxurl(self):
        userid = self.request.form.get('user')
        userid_qs = userid and '?userid=%s' % userid or ''
        return '%s/%s%s' % (
            self.context.absolute_url(), '@@ordersdata', userid_qs)

    @property
    def columns(self):
        if apiuser.is_anonymous():
            # don't allow this for anonymous users
            raise Unauthorized(
                _('unauthorized_orders_view',
                  default="You have to log in to access the orders view")
            )
        return [{
            'id': 'actions',
            'label': _bpo('actions', 'Actions'),
            'renderer': self.render_order_actions,
        }, {
            'id': 'created',
            'label': _bpo('date', 'Date'),
            'renderer': self.render_dt,
        }, {
            'id': 'personal_data.lastname',
            'label': _bpo('lastname', 'Last Name'),
        }, {
            'id': 'personal_data.firstname',
            'label': _bpo('firstname', 'First Name'),
        }, {
            'id': 'billing_address.city',
            'label': _bpo('city', 'City'),
        }, {
            'id': 'salaried',
            'label': _bpo('salaried', 'Salaried'),
            'renderer': self.render_salaried,
        }, {
            'id': 'state',
            'label': _bpo('state', 'State'),
            'renderer': self.render_state,
        }]

    def render_order_actions(self, colname, record):
        tag = Tag(Translate(self.request))
        target = '%s?uid=%s' % (self.context.absolute_url(),
                                str(record.attrs['uid']))
        link_attrs = {
            'ajax:bind': 'click',
            'ajax:target': target,
            'ajax:overlay': 'order',
            'class_': 'contenttype-document',
            'href': '',
            'title': _bpo('view_order', 'View Order'),
        }
        return tag('a', '&nbsp', **link_attrs)

    def render_salaried(self, colname, record):
        return record.attrs.get('salaried', 'no')

    def render_state(self, colname, record):
        return record.attrs['state']


class UserOrdersData(UserOrdersTable, TableData):
    soup_name = 'bda_plone_orders_orders'
    search_text_index = 'text'

    def query(self, soup):

        query = None
        if self.allow_view_all_orders or self.allow_view_vendor_orders:
            userid = self.request.form.get('userid')
        else:
            user = apiuser.get_current()
            userid = user.getId()
            if apiuser.is_anonymous() or not userid:
                # don't allow this for anonymous users
                raise Unauthorized(
                    _('unauthorized_orders_view',
                      default="You have to log in to access the orders view")
                )
        if userid:
            _query = Eq('creator', userid)
            query = query and query & _query or _query

        sort = self.sort()
        term = self.request.form['sSearch'].decode('utf-8')
        if term:
            _query = Contains(self.search_text_index, term)
            query = query and query & _query or _query

        if query:
            res = soup.lazy(query,
                            sort_index=sort['index'],
                            reverse=sort['reverse'],
                            with_size=True)
            length = res.next()
            return length, res
        else:
            return self.all(soup)
