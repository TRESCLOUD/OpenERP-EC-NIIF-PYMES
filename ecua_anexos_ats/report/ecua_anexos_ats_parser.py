# -*- coding: utf-8 -*-
########################################################################
#                                                                       
#@authors:TRESCLOUD Cia.Ltda                                                                          
# Copyright (C) 2013                     
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
#ice
########################################################################

from report import report_sxw

class Parser(report_sxw.rml_parse):
    
    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context)
        self.cr = cr
        self.uid = uid
        self.localcontext.update({
            'get_total':self._get_sum_account_total
        })
        
    def _get_sum_account_total(self, period, type):
        total = 0.00
        obj_invoice = self.pool.get('account.invoice')
        invoice_id_list = obj_invoice.search(self.cr, self.uid,[('period_id','=',period),('type','=',type),('state','in',('open','paid')),])
        
        if invoice_id_list:
            invoices = obj_invoice.browse(self.cr, self.uid, invoice_id_list)           
            for lines in invoices:            
              total = total + lines.amount_total

        return {'total':total}
    