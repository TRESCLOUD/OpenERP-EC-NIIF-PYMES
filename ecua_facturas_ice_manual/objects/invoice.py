# -*- coding: UTF-8 -*- #
#########################################################################
# Copyright (C) 2011  Christopher Ormaza, Ecuadorenlinea.net            #
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

class account_invoice(osv.osv):

    _inherit = "account.invoice"

    def _amount_all_3(self, cr, uid, ids, name, args, context=None):
        res = {}
        for invoice in self.browse(cr, uid, ids, context=context):
            res[invoice.id] = {
                'total_sin_descuento':0.0,
                'amount_untaxed': 0.0,
                'base_iva': 0.0,
                'base_iva_0': 0.0,
                'amount_tax': 0.0,
                'amount_total': 0.0,
                'total_retencion': 0.0,
                'total_iva': 0.0,
                'total_ice': 0.0,
                'total_descuento': 0.0,
                'total_descuento_per': 0.0,
            }
            contador = 0;
            desc_per = 0.0
            for line in invoice.invoice_line:
                res[invoice.id]['amount_untaxed'] += line.price_subtotal
                res[invoice.id]['total_sin_descuento'] += line.price_unit * line.quantity
                res[invoice.id]['total_descuento'] += line.price_unit * line.quantity * line.discount * 0.01
                if line.discount != 0:
                    contador += 1
                    desc_per += line.discount
            for line in invoice.tax_line:
                    res[invoice.id]['amount_tax'] += line.amount
                    if line.amount > 0:
                        if line.type_ec == 'iva' and line.amount > 0:
                            res[invoice.id]['base_iva'] += line.base
                        if line.type_ec == 'ice':
                            res[invoice.id]['total_ice'] += line.amount
                        else:
                            res[invoice.id]['total_iva'] += line.amount           
                    else:
                        if line.type_ec == 'iva' and line.amount == 0:
                            res[invoice.id]['base_iva_0'] += line.base
                        res[invoice.id]['total_retencion'] += line.amount
            if contador != 0:
                res[invoice.id]['total_descuento_per'] = desc_per / contador
            res[invoice.id]['amount_total'] = res[invoice.id]['amount_tax'] + res[invoice.id]['amount_untaxed']
        return res

    def _get_invoice_tax(self, cr, uid, ids, context=None):
        result = {}
        for tax in self.pool.get('account.invoice.tax').browse(cr, uid, ids, context=context):
            result[tax.invoice_id.id] = True
        return result.keys()
    
    def _get_invoice_line(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('account.invoice.line').browse(cr, uid, ids, context=context):
            result[line.invoice_id.id] = True
        return result.keys()
    
    _columns = {
                'base_iva': fields.function(_amount_all_3, method=True, digits_compute=dp.get_precision('Account'), string='IVA Base',
                    store={
                        'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
                        'account.invoice.tax': (_get_invoice_tax, None, 20),
                        'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 20),
                    },
                    multi='all1'),
                'base_iva_0': fields.function(_amount_all_3, method=True, digits_compute=dp.get_precision('Account'), string='IVA 0 Base',
                    store={
                        'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
                        'account.invoice.tax': (_get_invoice_tax, None, 20),
                        'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 20),
                    },
                    multi='all1'),
                'total_retencion': fields.function(_amount_all_3, method=True, digits_compute=dp.get_precision('Account'), string='Total Retenido',
                    store={
                        'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
                        'account.invoice.tax': (_get_invoice_tax, None, 20),
                        'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 20),
                    },
                    multi='all1'),
                'total_iva': fields.function(_amount_all_3, method=True, digits_compute=dp.get_precision('Account'), string='Total IVA',
                    store={
                        'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
                        'account.invoice.tax': (_get_invoice_tax, None, 20),
                        'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 20),
                    },
                    multi='all1'),
                'total_descuento': fields.function(_amount_all_3, method=True, digits_compute=dp.get_precision('Account'), string='Descuento Total',
                    store={
                        'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
                        'account.invoice.tax': (_get_invoice_tax, None, 20),
                        'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 20),
                    },
                    multi='all1'),                
                'total_descuento_per': fields.function(_amount_all_3, method=True, digits_compute=dp.get_precision('Account'), string='Total',
                    store={
                        'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
                        'account.invoice.tax': (_get_invoice_tax, None, 20),
                        'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 20),
                    },
                    multi='all1'),  
                'total_ice': fields.function(_amount_all_3, method=True, digits_compute=dp.get_precision('Account'), string='ICE Total',
                    store={
                        'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
                        'account.invoice.tax': (_get_invoice_tax, None, 20),
                        'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 20),
                    },
                    multi='all1'),
                'total_sin_descuento': fields.function(_amount_all_3, method=True, digits_compute=dp.get_precision('Account'), string='Sub Total',
                    store={
                        'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
                        'account.invoice.tax': (_get_invoice_tax, None, 20),
                        'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 20),
                    },
                    multi='all1'),  

                    }
    
    def action_check_ice(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService("workflow")
        inv_obj = self.pool.get('account.invoice')
        invoices = inv_obj.browse(cr, uid, ids, context)
        if context is None: context = {}
        ice = False
        count_normal_product = 0
        for invoice in invoices:
            for line in invoice.invoice_line:
                normal_product = True
                for tax in line.invoice_line_tax_id:
                    if tax.type_ec == 'ice':
                        ice = True
                        normal_product = False
                if normal_product:
                    count_normal_product += 1
            if not ice or count_normal_product == 0:
                wf_service.trg_validate(uid, 'account.invoice', invoice.id, 'invoice_open', cr)
            else:
                wizard_id = self.pool.get("account.invoice.ice.wizard").create(cr, uid, {}, context=dict(context, active_ids=ids))
                return {
                    'name':_("Invoice Options"),
                    'view_mode': 'form',
                    'view_type': 'form',
                    'res_model': 'account.invoice.ice.wizard',
                    'res_id': wizard_id,
                    'type': 'ir.actions.act_window',
                    'nodestroy': True,
                    'target': 'new',
                    'domain': '[]',
                    'context': dict(context, active_ids=ids)
                }
        return True

account_invoice()

class account_invoice_tax(osv.osv):
    
    _inherit = "account.invoice.tax"

    def compute(self, cr, uid, invoice_id, context=None):
        if not context:
            context = {}
        tax_grouped = {}
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        inv = self.pool.get('account.invoice').browse(cr, uid, invoice_id, context=context)
        cur = inv.currency_id
        company_currency = inv.company_id.currency_id.id
        for line in inv.invoice_line:
            tax_iva = []
            taxes = []
            ice = False
            for tax in line.invoice_line_tax_id:
                if tax.type_ec == "ice":
                    ice = True
            for tax in line.invoice_line_tax_id:
                if tax.type_ec == "iva":
                    tax_iva.append(tax)
                else:
                    taxes.append(tax)
            #computo de ice
            if ice:
                for tax in tax_obj.compute_all(cr, uid, taxes, (line.price_unit* (1-(line.discount or 0.0)/100.0)), line.quantity, inv.address_invoice_id.id, line.product_id, inv.partner_id)['taxes']:
                    tax_browse = tax_obj.browse(cr, uid, tax['id'], context)
                    val={}
                    val['invoice_id'] = inv.id
                    val['name'] = tax['name']
                    val['amount'] = tax['amount']
                    val['manual'] = False
                    val['sequence'] = tax['sequence']
                    val['base'] = tax['price_unit'] * line['quantity']
    
                    if inv.type in ('out_invoice','in_invoice'):
                        val['base_code_id'] = tax['base_code_id']
                        val['tax_code_id'] = tax['tax_code_id']
                        val['base_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['base'] * tax['base_sign'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                        val['tax_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['amount'] * tax['tax_sign'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                        val['account_id'] = tax['account_collected_id'] or line.account_id.id
                        val['type_ec'] = tax_browse.type_ec
                        val['assets'] = tax_browse.assets
                        val['imports'] = tax_browse.imports
                        val['exports'] = tax_browse.exports
                    else:
                        val['base_code_id'] = tax['ref_base_code_id']
                        val['tax_code_id'] = tax['ref_tax_code_id']
                        val['base_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['base'] * tax['ref_base_sign'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                        val['tax_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['amount'] * tax['ref_tax_sign'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                        val['account_id'] = tax['account_paid_id'] or line.account_id.id
                        val['type_ec'] = tax_browse.type_ec
                        val['assets'] = tax_browse.assets
                        val['imports'] = tax_browse.imports
                        val['exports'] = tax_browse.exports
    
                    key = (val['tax_code_id'], val['base_code_id'], val['account_id'])
                    if not key in tax_grouped:
                        tax_grouped[key] = val
                    else:
                        tax_grouped[key]['amount'] += val['amount']
                        tax_grouped[key]['base'] += val['base']
                        tax_grouped[key]['base_amount'] += val['base_amount']
                        tax_grouped[key]['tax_amount'] += val['tax_amount']
    
                #computo del IVA
                ice_value = 1
                if line.product_id.ice_type_id:
                    ice_value = 1+line.product_id.ice_type_id.rate
                for tax in tax_obj.compute_all(cr, uid, tax_iva, (line.price_unit * (ice_value) * (1-(line.discount or 0.0)/100.0)), line.quantity, inv.address_invoice_id.id, line.product_id, inv.partner_id)['taxes']:
                    tax_browse = tax_obj.browse(cr, uid, tax['id'], context)
                    val={}
                    val['invoice_id'] = inv.id
                    val['name'] = tax['name']
                    val['amount'] = tax['amount']
                    val['manual'] = False
                    val['sequence'] = tax['sequence']
                    val['base'] = tax['price_unit'] * line['quantity']
    
                    if inv.type in ('out_invoice','in_invoice'):
                        val['base_code_id'] = tax['base_code_id']
                        val['tax_code_id'] = tax['tax_code_id']
                        val['base_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['base'] * tax['base_sign'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                        val['tax_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['amount'] * tax['tax_sign'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                        val['account_id'] = tax['account_collected_id'] or line.account_id.id
                        val['type_ec'] = tax_browse.type_ec
                        val['assets'] = tax_browse.assets
                        val['imports'] = tax_browse.imports
                        val['exports'] = tax_browse.exports
                    else:
                        val['base_code_id'] = tax['ref_base_code_id']
                        val['tax_code_id'] = tax['ref_tax_code_id']
                        val['base_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['base'] * tax['ref_base_sign'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                        val['tax_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['amount'] * tax['ref_tax_sign'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                        val['account_id'] = tax['account_paid_id'] or line.account_id.id
                        val['type_ec'] = tax_browse.type_ec
                        val['assets'] = tax_browse.assets
                        val['imports'] = tax_browse.imports
                        val['exports'] = tax_browse.exports
    
                    key = (val['tax_code_id'], val['base_code_id'], val['account_id'])
                    if not key in tax_grouped:
                        tax_grouped[key] = val
                    else:
                        tax_grouped[key]['amount'] += val['amount']
                        tax_grouped[key]['base'] += val['base']
                        tax_grouped[key]['base_amount'] += val['base_amount']
                        tax_grouped[key]['tax_amount'] += val['tax_amount']

            else:
                for tax in tax_obj.compute_all(cr, uid, line.invoice_line_tax_id, (line.price_unit* (1-(line.discount or 0.0)/100.0)), line.quantity, inv.address_invoice_id.id, line.product_id, inv.partner_id)['taxes']:
                    tax_browse = tax_obj.browse(cr, uid, tax['id'], context)
                    val={}
                    val['invoice_id'] = inv.id
                    val['name'] = tax['name']
                    val['amount'] = tax['amount']
                    val['manual'] = False
                    val['sequence'] = tax['sequence']
                    val['base'] = tax['price_unit'] * line['quantity']
    
                    if inv.type in ('out_invoice','in_invoice'):
                        val['base_code_id'] = tax['base_code_id']
                        val['tax_code_id'] = tax['tax_code_id']
                        val['base_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['base'] * tax['base_sign'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                        val['tax_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['amount'] * tax['tax_sign'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                        val['account_id'] = tax['account_collected_id'] or line.account_id.id
                        val['type_ec'] = tax_browse.type_ec
                        val['assets'] = tax_browse.assets
                        val['imports'] = tax_browse.imports
                        val['exports'] = tax_browse.exports
                    else:
                        val['base_code_id'] = tax['ref_base_code_id']
                        val['tax_code_id'] = tax['ref_tax_code_id']
                        val['base_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['base'] * tax['ref_base_sign'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                        val['tax_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['amount'] * tax['ref_tax_sign'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                        val['account_id'] = tax['account_paid_id'] or line.account_id.id
                        val['type_ec'] = tax_browse.type_ec
                        val['assets'] = tax_browse.assets
                        val['imports'] = tax_browse.imports
                        val['exports'] = tax_browse.exports
    
                    key = (val['tax_code_id'], val['base_code_id'], val['account_id'])
                    if not key in tax_grouped:
                        tax_grouped[key] = val
                    else:
                        tax_grouped[key]['amount'] += val['amount']
                        tax_grouped[key]['base'] += val['base']
                        tax_grouped[key]['base_amount'] += val['base_amount']
                        tax_grouped[key]['tax_amount'] += val['tax_amount']
        for t in tax_grouped.values():
            t['base'] = cur_obj.round(cr, uid, cur, t['base'])
            t['amount'] = cur_obj.round(cr, uid, cur, t['amount'])
            t['base_amount'] = cur_obj.round(cr, uid, cur, t['base_amount'])
            t['tax_amount'] = cur_obj.round(cr, uid, cur, t['tax_amount'])
        return tax_grouped
    
account_invoice_tax()