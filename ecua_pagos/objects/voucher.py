
# -*- encoding: utf-8 -*-
########################################################################
#                                                                       
# @authors: Christopher Ormaza                                                                           
# Copyright (C) 2012  Ecuadorenlinea.net                                 
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

class account_voucher(osv.osv):
    
    _inherit = 'account.voucher'
    
    def _total_payments(self, cr, uid, ids, name, args, context=None):
        if not context:
            context = {}
        res = {}
        for voucher in self.browse(cr, uid, ids, context):
            res[voucher.id] = 0
        return res

    _columns = {
            'payment_ids':fields.one2many('account.payment.line', 'voucher_id', 'Payments', required=False),
            'total_payments': fields.function(_total_payments, method=True, type='float', string='Total Payments', store=True),
        }

    def onchange_partner_id_multi(self, cr, uid, ids, partner_id, journal_id, price, currency_id, ttype, date, context=None):
        if not context:
            context = {}
        res = self.onchange_partner_id(cr, uid, ids, partner_id, journal_id, price, currency_id, ttype, date, context)
        return res
    
    def onchange_date_multi(self, cr, uid, ids, partner_id, journal_id, price, currency_id, ttype, date, context=None):
        if not context:
            context = {}
        res = self.onchange_date(cr, uid, ids, partner_id, journal_id, price, currency_id, ttype, date, context)
        return res
    
    def onchange_payment_line(self, cr, uid, ids, payment_ids, partner_id, date, line_dr_ids, line_cr_ids, context=None):
        if not context:
            context={}
        value = {}
        domain = {}
        return {'value': value, 'domain': domain }
    
account_voucher()

class account_voucher_line(osv.osv):
    
    _inherit = 'account.voucher.line' 
    
    _columns = {
                'reconcile':fields.boolean('Full Reconcile'),
                    }
    
    def onchange_reconcile(self, cr, uid, ids, reconcile, amount, amount_unreconciled, context=None):
        vals = { 'amount': 0.0}
        if reconcile:
            vals = { 'amount': amount_unreconciled}
        return {'value': vals}

    def onchange_amount(self, cr, uid, ids, amount, amount_unreconciled, context=None):
        vals = {}
        if amount:
            vals['reconcile'] = (amount == amount_unreconciled)
        return {'value': vals}

account_voucher_line()