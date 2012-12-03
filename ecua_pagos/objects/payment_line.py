
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
        res=True
        for payment in self.browse(cr, uid, ids):
            if payment.amount <= 0:
                res=False
        return res

    _name="account.payment.line"
    
    _columns={
              'name':fields.char('Reference/Number', size=255, required=False, readonly=False),
              'authorization':fields.char('Authorization', size=255, required=False, readonly=False),
              'beneficiary':fields.char('Beneficiary', size=255, required=False, readonly=False),
              'voucher_id':fields.many2one('account.voucher', 'Voucher', required=False),
              'mode_id':fields.many2one('account.payment.modes', 'Mode', required=False),
              'amount': fields.float('Amount', digits_compute=dp.get_precision('Account')),
              'move_line_id':fields.many2one('account.move.line', 'Move Line', required=False),
              'type':fields.selection([
                  ('receipt','Receipt'),
                  ('payment','Payment'),
                   ],    'Type', select=True, readonly=True),
              'state':fields.selection([
                  ('draft','Draft'),
                  ('done','Done'),
                   ], 'State', select=True, readonly=True),
    }

    _defaults={
               'state': 'draft',
    }
    
    def default_get(self, cr, uid, fields_list, context=None):
        if not context:
            context={}
        values = super(account_payment_line, self).default_get(cr, uid, fields_list, context)
        if 'type' in fields_list:
            values['type'] = context.get('type_payment', 'receipt')
        return values
    
    def onchange_payment_line(self, cr, uid, ids, payment_line, context=None):
        if not context:
            context={}
        value = {}
        domain = {}
        
        return {'value': value, 'domain': domain }
    
    _constraints = [(_check_amount,_('Amount must be bigger than 0!'),['amount'])]

account_payment_line()
