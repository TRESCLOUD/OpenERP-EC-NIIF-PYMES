
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

class account_check(osv.osv):
    '''
    Open ERP Model
    '''
    _name = 'account.check'
    _description = 'account.check'

    _columns = {
            'number':fields.char('Name', size=255, required=False),
            'check_book_id':fields.many2one('account.check.book', 'Check Book', required=False),
            'payment_line_id':fields.many2one('account.payment.line', 'Payment Line', required=False),
            #'voucher_id':fields.many2one('account.voucher', 'Voucher', required=False),
            'third':fields.boolean('Third?', required=False),
            'partner_id':fields.many2one('res.partner', 'Partner', required=False),
            'bank_id':fields.many2one('res.partner.bank', 'Bank Account', required=False),
            'received_date': fields.date('Received Date'),
            'deposit_date': fields.date('Deposit Date'),
            'payment_date': fields.date('Payment Date'),
            'return_date': fields.date('Return Date'),
            'state':fields.selection([
                ('draft','Draft'),
                ('open','Open'),
                ('canceled','Canceled'),
                 ],    'State', select=True, readonly=True),
        }
    
    _rec_name = 'number'
    
    
account_check()