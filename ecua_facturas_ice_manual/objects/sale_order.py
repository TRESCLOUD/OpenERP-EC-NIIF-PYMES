##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2011-2012 Christopher Ormaza (http://www.ecuadorenlinea.net>). 
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
    
    
    def _amount_line_tax(self, cr, uid, line, context=None):
        val = 0.0
        ice = False
        tax_iva = []
        taxes = []
        for tax in line.tax_id:
            if tax.type_ec == 'ice':
                ice = True
        for tax in line.tax_id:
            if tax.type_ec == 'iva':
                tax_iva.append(tax)
            else:
                taxes.append(tax)
        ice_value = 1
        if line.product_id.ice_type_id:
            ice_value = 1+line.product_id.ice_type_id.rate
        if ice:
            for c in self.pool.get('account.tax').compute_all(cr, uid, taxes, line.price_unit * (1-(line.discount or 0.0)/100.0), line.product_uom_qty, line.order_id.partner_invoice_id.id, line.product_id, line.order_id.partner_id)['taxes']:
                val += c.get('amount', 0.0)
            for c in self.pool.get('account.tax').compute_all(cr, uid, tax_iva, line.price_unit * ice_value * (1-(line.discount or 0.0)/100.0), line.product_uom_qty, line.order_id.partner_invoice_id.id, line.product_id, line.order_id.partner_id)['taxes']:
                val += c.get('amount', 0.0)        
        else:
            for c in self.pool.get('account.tax').compute_all(cr, uid, line.tax_id, line.price_unit * (1-(line.discount or 0.0)/100.0), line.product_uom_qty, line.order_id.partner_invoice_id.id, line.product_id, line.order_id.partner_id)['taxes']:
                val += c.get('amount', 0.0)
            
        return val

    def _amount_all_3(self, cr, uid, ids, field_name, arg, context=None):
        cur_obj = self.pool.get('res.currency')
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
                'amount_untaxed': 0.0,
                'amount_tax': 0.0,
                'amount_total': 0.0,
                'total_descuento': 0.0,
                'total_descuento_per': 0.0,
                'total_ice': 0.0,
                'base_iva': 0.0,
                'total_iva': 0.0,
            }
            val = val1 = 0.0
            cur = order.pricelist_id.currency_id
            for line in order.order_line:
                val1 += line.price_subtotal
                val += self._amount_line_tax(cr, uid, line, context=context)
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
                'amount_untaxed': fields.function(_amount_all_3, method=True, digits_compute= dp.get_precision('Sale Price'), string='Untaxed Amount',
                    store = {
                        'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                        'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
                    },
                    multi='sums', help="The amount without tax."),
                'amount_tax': fields.function(_amount_all_3, method=True, digits_compute= dp.get_precision('Sale Price'), string='Taxes',
                    store = {
                        'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                        'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
                    },
                    multi='sums', help="The tax amount."),
                'amount_total': fields.function(_amount_all_3, method=True, digits_compute= dp.get_precision('Sale Price'), string='Total',
                    store = {
                        'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                        'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
                    },
                    multi='sums', help="The total amount."),
                'total_descuento': fields.function(_amount_all_3, method=True, digits_compute=dp.get_precision('Account'), string='Descuento Total',
                    store={
                        'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                        'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
                    },
                    multi='sums'),                
                'total_descuento_per': fields.function(_amount_all_3, method=True, digits_compute=dp.get_precision('Account'), string='Total',
                    store={
                        'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                        'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
                    },
                    multi='sums'),  
                'total_ice': fields.function(_amount_all_3, method=True, digits_compute=dp.get_precision('Account'), string='ICE Total',
                    store={
                        'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                        'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
                    },
                    multi='sums'),                
                'base_iva': fields.function(_amount_all_3, method=True, digits_compute=dp.get_precision('Account'), string='IVA Base',
                    store={
                        'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                        'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
                    },
                    multi='sums'),
                'total_iva': fields.function(_amount_all_3, method=True, digits_compute=dp.get_precision('Account'), string='Total IVA',
                    store={
                        'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                        'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
                    },
                    multi='sums'),
                }

    def action_check_ice(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService("workflow")
        sale_order_obj = self.pool.get('sale.order')
        sale_orders = sale_order_obj.browse(cr, uid, ids, context)
        if context is None: context = {}
        ice = False
        count_normal_product = 0
        for order in sale_orders:
            for line in order.order_line:
                normal_product = True
                for tax in line.tax_id:
                    if tax.type_ec == 'ice':
                        ice = True
                        normal_product = False
                if normal_product:
                    count_normal_product += 1
            if not ice or count_normal_product == 0:
                wf_service.trg_validate(uid, 'sale.order', order.id, 'order_confirm', cr)
            else:
                wizard_id = self.pool.get("sale.order.ice.wizard").create(cr, uid, {}, context=dict(context, active_ids=ids))
                return {
                    'name':_("Sale Order Options"),
                    'view_mode': 'form',
                    'view_type': 'form',
                    'res_model': 'sale.order.ice.wizard',
                    'res_id': wizard_id,
                    'type': 'ir.actions.act_window',
                    'nodestroy': True,
                    'target': 'new',
                    'domain': '[]',
                    'context': dict(context, active_ids=ids)
                }
        return True
sale_order()