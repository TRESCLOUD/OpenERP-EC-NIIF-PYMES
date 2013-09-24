
# -*- encoding: utf-8 -*-
########################################################################
#                                                                       
# @authors: Christopher Ormaza, Patricio Rangles                                                                           
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
    "name": "Ecuadorian Accounting",
    "version": "1.0",
    "depends": ["base",
                "account",
                "product",
                "stock",
                "account_voucher",
                "ecua_facturas_manual",
                "ecua_liquidacion_compras",
                "ecua_notas_credito_manual",
                "ecua_retenciones_manual",
                "ecua_facturas_ice_manual",
                ],
    "author": "TRESCLOUD Cia Ltda",
    "website": "www.trescloud.com",
    "category": "Account",
    "description": """
    This module install some common caracteristics for ecuadorian account
    
    Authors:
    Christopher Ormaza
    Patricio Rangles
    Carlos Yumbillo
    
    """,
    "init_xml": [],
    'update_xml': [
                   "report/report_data.xml",
                   "data/data.xml",
                   ],
    'demo_xml': [],
    'installable': True,
    'active': False,
}