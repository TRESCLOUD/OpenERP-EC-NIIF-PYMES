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

class account_fiscal_position(osv.osv):
    
    _inherit = 'account.fiscal.position'
 
    _columns = {
                'no_iva':fields.boolean('No Aplica Retenciones de IVA', required=False),
                'no_renta':fields.boolean('No Aplica Retenciones de Renta', required=False),
                'iva_bienes_tax_id':fields.many2one('account.tax', 'Retención IVA Bienes', ondelete="restrict", required=False),
                'iva_servicios_tax_id':fields.many2one('account.tax', 'Retención IVA Servicios', ondelete="restrict", required=False),
                'line_renta_ids':fields.one2many('account.fiscal.position.line', 'fiscal_position_id', 'Renta Lines', required=False, domain=[('type','=','renta')], context={'default_type':'renta'}), 
                'line_iva_ids':fields.one2many('account.fiscal.position.line', 'fiscal_position_id', 'IVA Lines', required=False, domain=[('type','=','iva')], context={'default_type':'iva'}), 
        }
    
    def map_tax(self, cr, uid, fposition_id, taxes, context=None):
        if not taxes:
            return []
        if not fposition_id:
            return map(lambda x: x.id, taxes)
        result = []
        for t in taxes:
            ok = False
            for tax in fposition_id.tax_ids:
                if tax.tax_src_id.id == t.id:
                    if tax.tax_dest_id:
                        result.append(tax.tax_dest_id.id)
                    ok=True
            if not ok:
                result.append(t.id)
        return result

account_fiscal_position()

class account_fiscal_position_line(osv.osv):
    
    _name = 'account.fiscal.position.line'
 
    _columns = {
                'fiscal_position_id':fields.many2one('account.fiscal.position', 'Fiscal Position Parent', required=True),
                'fiscal_position_dest_id':fields.many2one('account.fiscal.position', 'Fiscal Position Destination', required=True),
                'type':fields.selection([
                    ('iva','IVA'),
                    ('renta','Renta'),
                     ],    'Type', select=True),
                'usage':fields.selection([
                    ('bienes','Bienes'),
                    ('servicios','Servicios'),
                     ],    'Type', select=True),
                'tax_id':fields.many2one('account.tax', 'Tax', ondelete="restrict", required=True),
        }
    
    def _get_type(self, cr, uid, context=None):
        if not context:
            context = {}
        return context.get('type', 'iva')
    
    _defaults = {  
        'type': _get_type,
        }
account_fiscal_position_line()
