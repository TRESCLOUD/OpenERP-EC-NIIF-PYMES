# -*- coding: utf-8 -*-
########################################################################
#                                                                       
# @authors:TRESCLOUD Cia.Ltda                                                                           
# Copyright (C) 2012                                  
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
{
   "name" : "Módulo de cheques para Ecuador",
   "author" : "TRESCloud Cia. Ltda.",
   "maintainer": 'TRESCloud Cia. Ltda.',
   "website": 'http://www.trescloud.com',
   'complexity': "easy",
   "description": """Sistema gestión y control de CHEQUES
   
   Este sistema permite la impresión de los cheques y conocer el estado de los mismos.
     
   Desarrollador:
   
   Andrea García,
   Carlos Yumbillo
   
   """,
   "category": "Tesoreria",
   "version" : "1.0",
   'depends': ['base','account','account_payment'],
   'init_xml': [],
   'update_xml': [
       'security/ir.model.access.csv',        
       'trescloud_cheques_view.xml',
       'workflow/check_wkf.xml',
       'account_voucher_view.xml',
       'account_view.xml',
       'report/report_data.xml',
   ],
   'installable': True,
}