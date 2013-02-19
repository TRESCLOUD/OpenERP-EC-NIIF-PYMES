
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

class account_payment_line(osv.osv):
    
    def _check_amount(self, cr, uid, ids, context=None):
        res = True
        for payment in self.browse(cr, uid, ids):
            if payment.amount <= 0:
                res = False
        return res

    _name = "account.payment.line"
    
    _columns = {
                'name':fields.char('Reference/Number', size=255, required=False, readonly=False),
                'authorization':fields.char('Credit Card Authorization', size=255, required=False, readonly=False),
                'beneficiary':fields.char('Beneficiary', size=255, required=False, readonly=False),
                'voucher_id':fields.many2one('account.voucher', 'Voucher', required=False),
                'mode_id':fields.many2one('account.payment.modes', 'Mode', required=True),
                'amount': fields.float('Amount', digits_compute=dp.get_precision('Account')),
                'move_line_id':fields.many2one('account.move.line', 'Move Line', required=False),
                'type':fields.selection([
                    ('receipt', 'Receipt'),
                    ('payment', 'Payment'),
                     ], 'Type', select=True, readonly=False),
                'state':fields.selection([
                    ('draft', 'Draft'),
                    ('pending', 'Pending'),
                    ('done', 'Done'),
                    ('cancel', 'Cancel'),
                     ], 'State', select=True, readonly=True),
                'check_type':fields.selection([
                    ('today', 'Today'),
                    ('postdated', 'Postdated'),
                     ], 'Check Type', select=True, readonly=False),
                'deposit_id':fields.many2one('account.deposit.slip', 'Deposit Slip', required=False),
                'is_cash':fields.boolean('is Cash?', required=False),
                'is_check':fields.boolean('is Check?', required=False),
                'is_credit_card':fields.boolean('is Credit Card?', required=False),
                'bank_id':fields.many2one('res.partner.bank', 'Bank Account', required=False),
                'received_date': fields.date('Received Date'),
                'deposit_date': fields.date('Deposit Date'),
                'payment_date': fields.date('Payment Date'),
                'return_date': fields.date('Return Date'),
    }

    _defaults = {
               'state': 'draft',
               'check_type': 'today',
    }
        
    def default_get(self, cr, uid, fields_list, context=None):
        if not context:
            context = {}
        values = super(account_payment_line, self).default_get(cr, uid, fields_list, context)
        if 'type' in fields_list:
            values['type'] = context.get('type_payment', 'receipt')
        return values
    
    def onchange_mode_id(self, cr, uid, ids, mode_id, partner_id=None, context=None):
        if not context:
            context = {}
        value = {}
        domain = {}
        mode_obj = self.pool.get('account.payment.modes')
        if mode_id:
            mode = mode_obj.browse(cr, uid, mode_id)
            if mode.type == 'cash':
                value.update({
                             'is_check': False,
                             'is_credit_card': False,
                             'name': _(u'EFECTIVO'),
                             })
            if mode.type == 'credit_card':
                value.update({
                             'is_check': False,
                             'is_credit_card': True,
                             })
            if mode.type == 'bank':
                if partner_id:
                    domain.update({
                                   'bank_id': [('partner_id','=', partner_id)]
                                   })
                value.update({
                             'is_check': mode.is_check,
                             'is_credit_card': False,
                             })
        return {'value': value, 'domain': domain }
    
    _constraints = [(_check_amount, _('Amount must be bigger than 0!'), ['amount'])]

    def _check_deposit_date(self, cr, uid, ids, context=None): 
        if not context:
            context = {}
        now = time.strftime('%Y-%m-%d')
        for line in self.browse(cr, uid, ids):
            if line.type == 'receipt' and line.is_check and line.check_type == 'postdated':
                if line.deposit_date <= time.strftime('%Y-%m-%d'):
                    return False
        return True
    _constraints = [(_check_deposit_date, _('Error: You must select a date after today to check postdated'), ['deposit_date']), ] 

account_payment_line()
