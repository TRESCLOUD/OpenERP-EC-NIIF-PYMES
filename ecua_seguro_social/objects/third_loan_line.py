
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

from time import strftime
import time

import netsvc
from osv import osv, fields
import decimal_precision as dp
from tools.translate import _

class account_hr_third_loan_line(osv.osv):
    
    _name = "account.hr.third.loan.line"
    
    _columns = {
                'loan_id':fields.many2one('account.hr.third.loan', 'Loan', required=False), 
                'amount':fields.float('Amount', digits_compute=dp.get_precision('Account')),
                'period_id': fields.many2one('account.period','Period',
                                             required=True),
                'date_to_pay': fields.date('Date to Pay'),
                'date_policy':fields.selection([
                    ('date','By Date'),
                    ('period','By Period'),
                     ], 'Date Policy', select=False),
                'rule_id':fields.many2one('hr.extra.input.output', 'Rule', required=False),
                    }
    
    _defaults = {  
        'date_policy': 'period',  
        }
    
account_hr_third_loan_line()