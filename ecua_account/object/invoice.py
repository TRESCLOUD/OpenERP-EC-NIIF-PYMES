
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

class account_invoice(osv.osv):
    '''
    Open ERP Model
    '''
    _inherit = 'account.invoice'

    _columns = {
        }
    
    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        types = {
                'out_invoice': 'FACT-CLI: ',
                'in_invoice': 'FACT-PROV: ',
                'out_refund': 'NC-CLI: ',
                'in_refund': 'NC-PROV: ',
                'liquidation': 'LIQ-COMP: ',
                }
        res = []
        for r in self.read(cr, uid, ids, ['type', 'number', 'invoice_number_out', 'invoice_number_in', 'number_credit_note_in', 'number_credit_note_out','number_liquidation','name', 'liquidation'], context, load='_classic_write'):
            name = r['number'] or types[r['type']]  or ''
            if r['type'] == 'out_invoice':
                name = r['invoice_number_out'] or types[r['type']] or ''
            if r['type'] == 'in_invoice':
                name = r['invoice_number_in'] or types[r['type']] or ''
            if r['type'] == 'out_refund':
                name = r['number_credit_note_out'] or types[r['type']] or ''
            if r['type'] == 'in_refund':
                name = r['number_credit_note_in'] or types[r['type']] or ''
            if r['liquidation']:
                name = r['number_liquidation'] or types['liquidation']  or ''
            res.append((r['id'], name ))
        return res

account_invoice()