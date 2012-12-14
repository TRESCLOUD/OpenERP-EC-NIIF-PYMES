
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

class account_payment_mode(osv.osv):
    
    _name = 'account.payment.modes'
    
    _columns = {
                'name':fields.char('Name', size=255, required=True, readonly=False),
                'journal_id':fields.many2one('account.journal', 'Journal', required=True),
                'application':fields.selection([
                    ('customer','Customers'),
                    ('supplier','Suppliers'),
                    ('both','Both'),
                     ], 'Application', select=True, readonly=False, required=True),
                'active':fields.boolean('Active?', required=False),
                'type':fields.selection([
                    ('cash','Cash'),
                    ('bank','Bank'),
                    ('credit_card','Credit Card'),
                     ], 'Type', select=True, required=True),
                'is_check':fields.boolean('is Check?', required=False),
                'bank_id':fields.many2one('res.partner.bank', 'Bank Account', required=False),
                'postdated_account_id':fields.many2one('account.account', 'Postdated Account', required=False),
                'rejected_account_id':fields.many2one('account.account', 'Rejected Account', required=False),
                    }
    
    _defaults = {  
        'application': 'both',
        'active': True,
        }

account_payment_mode()
