##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2011-2012 Ecuadorenlinea.net (http://www.ecuadorenlinea.net>). 
#    All Rights Reserved
#    
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time
import netsvc
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta

from osv import fields, osv
import decimal_precision as dp
from tools import config
from tools.translate import _

class sale_order(osv.osv):
    
    _inherit = 'sale.order'

    def _amount_line_tax(self, cr, uid, line, context=None):
        val = 0.0
        for c in self.pool.get('account.tax').compute_all(cr, uid, line.tax_id, line.price_unit * (1-(line.discount or 0.0)/100.0), line.product_uom_qty, line.order_id.partner_invoice_id.id, line.product_id, line.order_id.partner_id)['taxes']:#,{'skip_round':True})['taxes']:
            val += c.get('amount', 0.0)
        return val
    
    def _amount_all2(self, cr, uid, ids, field_name, arg, context=None):
        cur_obj = self.pool.get('res.currency')
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
                'base_iva_0': 0.0,
                'base_iva_12': 0.0,
                'iva': 0.0,
                'amount_untaxed': 0.0,
                'amount_tax': 0.0,
                'amount_total': 0.0,
            }
            val = val1 = 0.0
            cur = order.pricelist_id.currency_id
            for line in order.order_line:
                val1 += line.price_subtotal
                val += self._amount_line_tax(cr, uid, line, context=context)
                tax = self._amount_line_tax(cr, uid, line, context=context)
                if tax > 0.0:
                    res[order.id]['base_iva_12'] += cur_obj.round(cr, uid, cur, line.price_subtotal)
                    res[order.id]['iva'] += cur_obj.round(cr, uid, cur, tax)
                else:
                    res[order.id]['base_iva_0'] = cur_obj.round(cr, uid, cur, line.price_subtotal)
            res[order.id]['amount_tax'] = cur_obj.round(cr, uid, cur, val)
            res[order.id]['amount_untaxed'] = cur_obj.round(cr, uid, cur, val1)
            res[order.id]['amount_total'] = res[order.id]['amount_untaxed'] + res[order.id]['amount_tax']
        return res

    def _get_order(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('sale.order.line').browse(cr, uid, ids, context=context):
            result[line.order_id.id] = True
        return result.keys()

    _columns = {
        'base_iva_0': fields.function(_amount_all2, method=True, digits_compute= dp.get_precision('Account'), string='Base IVA 0',
            store = {
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums'),
        'base_iva_12': fields.function(_amount_all2, method=True, digits_compute= dp.get_precision('Account'), string='Base IVA 12',
            store = {
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums'),
        'iva': fields.function(_amount_all2, method=True, digits_compute= dp.get_precision('Account'), string='IVA',
            store = {
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums'),
        'amount_untaxed': fields.function(_amount_all2, method=True, digits_compute= dp.get_precision('Account'), string='Untaxed Amount',
            store = {
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums', help="The amount without tax."),
        'amount_tax': fields.function(_amount_all2, method=True, digits_compute= dp.get_precision('Account'), string='Taxes',
            store = {
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums', help="The tax amount."),
        'amount_total': fields.function(_amount_all2, method=True, digits_compute= dp.get_precision('Account'), string='Total',
            store = {
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums', help="The total amount."),
        }


    def manual_invoice(self, cr, uid, ids, context=None):
        mod_obj = self.pool.get('ir.model.data')
        wf_service = netsvc.LocalService("workflow")
        inv_ids = set()
        inv_ids1 = set()
        for id in ids:
            for record in self.pool.get('sale.order').browse(cr, uid, id).invoice_ids:
                inv_ids.add(record.id)
        # inv_ids would have old invoices if any
        for id in ids:
            wf_service.trg_validate(uid, 'sale.order', id, 'manual_invoice', cr)
            for record in self.pool.get('sale.order').browse(cr, uid, id).invoice_ids:
                inv_ids1.add(record.id)
        inv_ids = list(inv_ids1.difference(inv_ids))

        res = mod_obj.get_object_reference(cr, uid, 'ecua_facturas_manual', 'account_invoice_sales_form_view')
        res_id = res and res[1] or False,

        return {
            'name': _('Customer Invoices'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': [res_id],
            'res_model': 'account.invoice',
            'context': "{'type':'out_invoice'}",
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'res_id': inv_ids and inv_ids[0] or False,
        }

    def _get_automatic(self, cr, uid, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        return user.company_id.generate_automatic
        
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
        else:
            #Is useful in the case of there are not automatic, that happens when you choice generate_automatic 
            curr_shop = self.pool.get('sale.shop').browse(cr, uid, [order.shop_id.id], context)[0]
            printer_obj = self.pool.get('sri.printer.point')
            automatic_number =curr_shop.number + "-" + printer_obj.browse(cr, uid,order.printer_id.id, context).number + "-000000000"
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
            #'journal_id': journal_ids[0],
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