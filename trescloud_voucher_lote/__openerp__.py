# -*- encoding: utf-8 -*-
########################################################################
#                                                                       
# @authors: Patricio Rangles                                                                          
# Copyright (C) 2012  TRESCloud Cia. Ltda.                                 
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
{
    "name" : "Registro del Numero de Lote de Vouchers",
    "version" : "1.0",
    "author" : "Patricio Rangles",
    "website": "http://www.trescloud.com",
    "category" : "Lote de Vouchers",
    "description": """Ingreso del numero de lote para los vouchers que son cobrados a los clientes
    Debe configurarse un diario (Journal) para cada institucion que emite la tarjeta con la cual se 
    efectua el pago""",
    "depends": ['base','account_voucher'],
    "init_xml": [],
    "update_xml": [
        'views/trescloud_voucher_lote_view.xml',
    ],
    "installable": True,
    "active": False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


