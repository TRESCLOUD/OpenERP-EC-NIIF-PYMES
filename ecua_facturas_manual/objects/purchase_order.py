
# -*- encoding: utf-8 -*-
########################################################################
#                                                                       
# @authors: Christopher Ormaza                                                                           
# Copyright (C) 2012  Construteam S.A.                                 
#                                                                       
#This program is free software: you can redistribute it and/or modify   
#it under the terms of the GNU General Public License as published by   
#the Free Software Foundation, either version 3 of the License, or      
#(at your option) any later version.                                    
#
# This module is GPLv3 or newer and incompatible
# with OpenERP SA "AGPL + Private Use License"!
#                                                                       
#This program is distributed in the hope that it will be useful,        
#but WITHOUT ANY WARRANTY; without even the implied warranty of         
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the          
#GNU General Public License for more details.                           
#                                                                       
#You should have received a copy of the GNU General Public License      
#along with this program.  If not, see http://www.gnu.org/licenses.
########################################################################

from osv import osv
from osv import fields
import decimal_precision as dp
from tools.translate import _

class purchase_order(osv.osv):
    
    
    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        cur_obj=self.pool.get('res.currency')
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
                'base_iva_0': 0.0,
                'base_iva_12': 0.0,
                'iva': 0.0,
                'withhold': 0.0,
                'withhold_iva': 0.0,
                'amount_untaxed': 0.0,
                'amount_tax': 0.0,
                'amount_total': 0.0,
                'amount_total_wr': 0.0,
            }
            val = val1 = base_iva_0 = base_iva_12 = iva= 0.0
            cur = order.pricelist_id.currency_id
            for line in order.order_line:
                val1 += line.price_subtotal
                for c in self.pool.get('account.tax').compute_all(cr, uid, line.taxes_id, line.price_unit, line.product_qty, order.partner_address_id.id, line.product_id.id, order.partner_id)['taxes']:#, context={'skip_round':True})['taxes']:
                    tax = c.get('amount', 0.0)
                    val += c.get('amount', 0.0)
                    if tax == 0.0 and c.get('type_ec', False) == 'iva':
                        base_iva_0 += cur_obj.round(cr, uid, cur, line.price_subtotal)
                    elif tax > 0 and c.get('type_ec', False) == 'iva':
                        iva +=  c.get('amount', 0.0)
                        base_iva_12 += cur_obj.round(cr, uid, cur, line.price_subtotal)
                    if tax < 0 and c.get('type_ec', False) == 'renta':
                        res[order.id]['withhold'] += tax
                    if tax < 0 and c.get('type_ec', False) == 'iva':
                        res[order.id]['withhold_iva'] += tax
                res[order.id]['base_iva_0'] = base_iva_0
                res[order.id]['iva'] = cur_obj.round(cr, uid, cur, iva)
                res[order.id]['base_iva_12'] = base_iva_12
                res[order.id]['amount_tax']=cur_obj.round(cr, uid, cur, val)
                res[order.id]['amount_untaxed']=cur_obj.round(cr, uid, cur, val1)
                res[order.id]['amount_total']=res[order.id]['amount_untaxed'] + res[order.id]['amount_tax']
                res[order.id]['amount_total_wr']=res[order.id]['amount_untaxed'] + res[order.id]['iva']
            return res
        
    def _get_order(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('purchase.order.line').browse(cr, uid, ids, context=context):
            result[line.order_id.id] = True
        return result.keys()

    _inherit = 'purchase.order'

    _columns = {
        'base_iva_0': fields.function(_amount_all, method=True, digits_compute= dp.get_precision('Account'), string='Base IVA 0',
            store={
                'purchase.order.line': (_get_order, None, 10),
            }, multi="sums"),
        'base_iva_12': fields.function(_amount_all, method=True, digits_compute= dp.get_precision('Account'), string='Base IVA 12',
            store={
                'purchase.order.line': (_get_order, None, 10),
            }, multi="sums"),
        'iva': fields.function(_amount_all, method=True, digits_compute= dp.get_precision('Account'), string='IVA',
            store={
                'purchase.order.line': (_get_order, None, 10),
            }, multi="sums"),
        'withhold': fields.function(_amount_all, method=True, digits_compute= dp.get_precision('Account'), string='Retención',
            store={
                'purchase.order.line': (_get_order, None, 10),
            }, multi="sums"),
        'withhold_iva': fields.function(_amount_all, method=True, digits_compute= dp.get_precision('Account'), string='Retención IVA',
            store={
                'purchase.order.line': (_get_order, None, 10),
            }, multi="sums"),
        'amount_untaxed': fields.function(_amount_all, method=True, digits_compute= dp.get_precision('Account'), string='Untaxed Amount',
            store={
                'purchase.order.line': (_get_order, None, 10),
            }, multi="sums", help="The amount without tax"),
        'amount_tax': fields.function(_amount_all, method=True, digits_compute= dp.get_precision('Account'), string='Taxes',
            store={
                'purchase.order.line': (_get_order, None, 10),
            }, multi="sums",),
        'amount_total': fields.function(_amount_all, method=True, digits_compute= dp.get_precision('Account'), string='Total - Retención',
            store={
                'purchase.order.line': (_get_order, None, 10),
            }, multi="sums",help="The total amount"),
        'amount_total_wr': fields.function(_amount_all, method=True, digits_compute= dp.get_precision('Account'), string='Total',
            store={
                'purchase.order.line': (_get_order, None, 10),
            }, multi="sums"),
        }
purchase_order()
