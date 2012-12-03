# -*- coding: UTF-8 -*- #
#########################################################################
# Copyright (C) 2012  Christopher Ormaza, Ecuadorenlinea.net            #
#                                                                       #
#This program is free software: you can redistribute it and/or modify   #
#it under the terms of the GNU General Public License as published by   #
#the Free Software Foundation, either version 3 of the License, or      #
#(at your option) any later version.                                    #
#                                                                       #
#This program is distributed in the hope that it will be useful,        #
#but WITHOUT ANY WARRANTY; without even the implied warranty of         #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the          #
#GNU General Public License for more details.                           #
#                                                                       #
#You should have received a copy of the GNU General Public License      #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.  #
#########################################################################
import netsvc
from osv import osv
from osv import fields
from tools.translate import _
from lxml import etree
import time
import psycopg2
import re
from lxml import etree
import decimal_precision as dp

class sale_order(osv.osv):
    
    _inherit = 'sale.order'
    
    _columns = {
                'product_description': fields.char('Product Description', size=255, readonly=True, states={'draft':[('readonly',False)]}, help="Nombre del Producto Diseñado por ArtFlex"),
                }

    def _make_invoice(self, cr, uid, order, lines, context=None):
        journal_obj = self.pool.get('account.journal')
        inv_obj = self.pool.get('account.invoice')
        obj_invoice_line = self.pool.get('account.invoice.line')
        auth_obj=self.pool.get('sri.authorization')
        doc_obj=self.pool.get('sri.type.document')
        if context is None:
            context = {}
        if not order.shop_id.sales_journal_id:
            raise osv.except_osv(_('Error !'),
                _('There is no sales journal defined for this Agency: "%s" (id:%d)') % (order.shop_id.name, order.shop_id.id))
        a = order.partner_id.property_account_receivable.id
        pay_term = order.payment_term and order.payment_term.id or False
        invoiced_sale_line_ids = self.pool.get('sale.order.line').search(cr, uid, [('order_id', '=', order.id), ('invoiced', '=', True)], context=context)
        from_line_invoice_ids = []
        for invoiced_sale_line_id in self.pool.get('sale.order.line').browse(cr, uid, invoiced_sale_line_ids, context=context):
            for invoice_line_id in invoiced_sale_line_id.invoice_lines:
                if invoice_line_id.invoice_id.id not in from_line_invoice_ids:
                    from_line_invoice_ids.append(invoice_line_id.invoice_id.id)
        for preinv in order.invoice_ids:
            if preinv.state not in ('cancel',) and preinv.id not in from_line_invoice_ids:
                for preline in preinv.invoice_line:
                    inv_line_id = obj_invoice_line.copy(cr, uid, preline.id, {'invoice_id': False, 'price_unit': -preline.price_unit})
                    lines.append(inv_line_id)
        auth_line_id = doc_obj.search(cr, uid, [('name','=','invoice'), ('printer_id','=',order.printer_id.id), ('shop_id','=',order.shop_id.id), ('state','=',True),])
        if not auth_line_id:
            raise osv.except_osv(_('Error !'),
                _('There is no active authorization for create invoice in this Agency: "%s"') % order.shop_id.name)
        authorization_sales = doc_obj.browse(cr, uid, auth_line_id[0],context).sri_authorization_id
        automatic = self._get_automatic(cr, uid, context)
        automatic_number = False
        invoice_number_out = False
        date_invoice = False
        if automatic:
            automatic_number = doc_obj.get_next_value_secuence(cr, uid, 'invoice', False, order.company_id.id, order.shop_id.id, order.printer_id.id, 'account.invoice', 'invoice_number_out', context)
            invoice_number_out = automatic_number
            date_invoice = time.strftime('%Y-%m-%d')
        inv = {
            'name': order.client_order_ref or '',
            'origin': order.name,
            'type': 'out_invoice',
            'reference': order.client_order_ref or order.name,
            'account_id': a,
            'partner_id': order.partner_id.id,
            'automatic_number':automatic_number or False,
            'invoice_number_out':invoice_number_out or False,
            'date_invoice':context.get('date_invoice',False) or date_invoice,
            'product_description': order.product_description,
            'journal_id': order.shop_id.sales_journal_id.id,
            'shop_id': order.shop_id.id,
            'printer_id':order.printer_id.id,
            'authorization_sales': authorization_sales.id,
            'authorization': authorization_sales.number,
            'address_invoice_id': order.partner_invoice_id.id,
            'address_contact_id': order.partner_order_id.id,
            'invoice_line': [(6, 0, lines)],
            'currency_id': order.pricelist_id.currency_id.id,
            'comment': order.note,
            'payment_term': pay_term,
            'fiscal_position': order.fiscal_position.id or order.partner_id.property_account_position.id,
            'company_id': order.company_id.id,
            'user_id': order.user_id and order.user_id.id or False
        }
        inv.update(self._inv_get(cr, uid, order))
        inv_id = inv_obj.create(cr, uid, inv, context=context)
        data = inv_obj.onchange_payment_term_date_invoice(cr, uid, [inv_id], pay_term, time.strftime('%Y-%m-%d'))
        if data.get('value', False):
            inv_obj.write(cr, uid, [inv_id], data['value'], context=context)
        inv_obj.button_compute(cr, uid, [inv_id])
        return inv_id

sale_order()

class sale_order_line(osv.osv):
    
    _inherit = 'sale.order.line'

sale_order_line()