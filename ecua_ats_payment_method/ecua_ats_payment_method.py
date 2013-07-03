# -*- encoding: utf-8 -*-
########################################################################
#                                                                       
# @authors: Carlos Yumbillo                                                                           
# Copyright (C) 2013  TRESCLOUD Cia Ltda.                                 
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

from osv import fields,osv

class payment_method(osv.osv):
     """ Payment method """
     _name = 'account.journal.payment.method' 
     _order = 'code'
    
     _columns = {
         'code':fields.char('Code', size=2, required=True,),
         'name':fields.char('Name', size=255, required=True,),            
      }

payment_method()

class account_journal(osv.osv):
    
     _inherit = "account.journal"
     _description = "Journal"
     
     _columns = {
        'payment_method_id': fields.many2one('account.journal.payment.method', 'Payment Method', required=False, help='Field used to select the method of payment when the journal type is cash or (bank and checks).')
     }
          
account_journal()