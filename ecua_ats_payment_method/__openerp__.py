# -*- coding: utf-8 -*-
########################################################################
#                                                                       
# @authors:TRESCLOUD Cia.Ltda                                                                           
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
{
   "name" : "Módulo para agregar formas de pago para (Cash y Bank and Cheques).",
   "author" : "TRESCLOUD Cia. Ltda.",
   "maintainer": 'TRESCLOUD Cia. Ltda.',
   "website": 'http://www.trescloud.com',
   'complexity': "easy",
   "description": """Sistema de gestión y control de las formas de pago. 
   
   Este sistema permite agregar las formas de pago a los tipo Cash y Bank and Cheques.
  
   Desarrollador:
   
   Carlos Yumbillo
   
   """,
   "category": "Contabilidad",
   "version" : "1.0",
   'depends': ['base','account',],
   'init_xml': [],
   'update_xml': [
       'security/ir.model.access.csv',
       'data/payment_method.xml',
       'ecua_ats_payment_method_view.xml',       
   ],
   'installable': True,
}