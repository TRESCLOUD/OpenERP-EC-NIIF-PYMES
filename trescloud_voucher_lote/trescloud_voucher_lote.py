
# -*- encoding: utf-8 -*-
########################################################################
#                                                                       
# @authors: Patricio Rangles                                                                           
# Copyright (C) 2012  TRESCLOUD Cia Ltda.                                 
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
#from tools.translate import _

class account_voucher(osv.osv):
    
    _inherit = 'account.voucher'
    _name = 'account.voucher'
    
    _columns = {
        'reference': fields.char('No. Referencia', size=64, required=True, readonly=True, states={'draft':[('readonly',False)]}, help="Puede anotarse la siguiente informacion: No. de Deposito, No. de Voucher, otras referencias"),
                }
    
    _defaults = {  
        'reference': 'Efectivo',
        }
    
account_voucher()


#class account_journal(osv.osv):
#    
#    _inherit = 'account.journal'
#    _name = 'account.journal'
#    
#    _columns = {
#        'imprimir_cheque': fields.boolean('Habilitar para generar la impresion de cheques desde egresos (Pagos)'),
#        'ingresar_voucher': fields.boolean('Habilitar para ingresar la informacion de vouchers desde ingresos (Cobros)'),
#                }
#    
#    _defaults = {  
#        'imprimir_cheque': False,
#        'ingresar_voucher': False,
#        }
#    
#account_journal()

 
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: