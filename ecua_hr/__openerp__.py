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
   "name" : "Módulo para personalizar la vista de planilla de pagos de empleados",
   "author" : "TRESCloud Cia. Ltda.",
   "maintainer": 'TRESCloud Cia. Ltda.',
   "website": 'http://www.trescloud.com',
   'complexity': "easy",
   "description": """
      
   Este sistema permite agregar automaticamente lineas con valor cero a Dias trabajados (HORA_EXTRA_REGULAR Y HORA_EXTRA_EXTRAORDINARIA) y 
   Otros Ingresos (BONIFICACIÓN Y COMISIÓN).
       
   Desarrollador:
   
   Carlos Yumbillo
   
   """,
   "category": "Human Resources",
   "version" : "1.0",
   'depends': ['base','ecua_seguro_social'],
   'init_xml': [],
   'update_xml': [],
   'installable': True,
}