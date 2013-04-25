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
   "name" : "Módulo de mejoras a partners para Ecuador",
   "author" : "TRESCloud Cia. Ltda.",
   "maintainer": 'TRESCloud Cia. Ltda.',
   "website": 'http://www.trescloud.com',
   'complexity': "easy",
   "description": """Sistema de mejoras a la vista de creación de PARTNERS
   
   Este sistema permite agregar mejoras a la vista de creación de partners, poniendo por defecto valores de Ecuador en el campo de localización, el nombre del vendedor y la fecha de creación.
     
   Desarrollador:
   
   Carlos Yumbillo
   
   """,
   "category": "Partners",
   "version" : "1.0",
   'depends': ['base','account'],
   'init_xml': [],
   'update_xml': [],
   'installable': True,
}