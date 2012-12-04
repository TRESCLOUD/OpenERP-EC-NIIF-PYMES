# -*- encoding: utf-8 -*-
########################################################################
#                                                                       
# @authors: Christopher                                                                           
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

{
    "name": "Posiciones Fiscales Ecuador",
    "version": "1.0",
    "depends": ['base',
                'account',
                'sale',
                'purchase',
                'l10n_ec_niif_minimal',
                'ecua_verifica_ruc_cedula',
                ],
    "author": "Christopher Ormaza",
    "website": "http://www.ecuadorenlinea.net",
    "category": "Partner",
    "description": """
    This module provide :
    
    """,
    "init_xml": [
                 
                 ],
    'update_xml': [
                   'data/fiscal_templates.xml',
                   'view/invoice_view.xml',
                   'view/purchase_view.xml',
                   'view/sale_order_view.xml',
                   'view/fiscal_position_view.xml',
                   ],
    'demo_xml': [],
    'installable': True,
    'active': False,
#    'certificate': 'certificate',
}