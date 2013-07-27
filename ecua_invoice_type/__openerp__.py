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
   "name" : "Módulo de facturación a proveedores/clientes para Ecuador",
   "author" : "TRESCLOUD Cia. Ltda.",
   "maintainer": 'TRESCLOUD Cia. Ltda.',
   "website": 'http://www.trescloud.com',
   'complexity': "easy",
   "description": """Sistema de gestión y control de compras y ventas 
   
   Este sistema permite el control del tipo de documento autorizado a emitir al momento de realizar una compra o venta, por ejemplo (Factura, nota de venta, liquidación de compra, etc).
   Nota:
   Si no se va a utilizar el módulo de contabilidad ecuatoriana "ecua_facturas_manual", borrarla de depends, descomentar las lineas (101 a la 116) y comentar (83 a la 100) del archivo ecua_invoice_type.xml 
     
   Desarrolladores:
   
   Carlos Yumbillo,
   Andrea Garcia
   
   """,
   "category": "Contabilidad",
   "version" : "1.0",
   'depends': [
               'base',
               'account',
               'ecua_autorizaciones_sri'
               ],
   'init_xml': [],
   'update_xml': [
       'security/ir.model.access.csv',
       'report/report.xml',
       'data/document_type.xml',
       'ecua_invoice_type_view.xml', 
       'ecua_autorization_view.xml',      
       'ecua_reembolso_view.xml', 
   ],
   'installable': True,
}
