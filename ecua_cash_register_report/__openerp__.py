
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
    "name" : "Reporte para Control de Registro de Caja",
    "version" : "1.0",
    "author" : "TRESCloud Cia. Ltda.",
    "website": "http://www.trescloud.com",
    "category" : "Reportes",
    "description": """Reporte para Control de Registro de Caja
    Permite generar un reporte imprimible de los movimientos realizados por cada usuario
    en la fecha indicada. Este reporte es unico por que captura el estado actual de las 
    facturas, ordenes de venta movimiento de diarios entre otros.
    
    Autor:
    Patricio Rangles
    """,
    "depends": ['base',
                'ecua_autorizaciones_sri',
                ],
    "init_xml": [],
    "update_xml": [
        'report/report_data.xml',
        'view/ecua_cash_register_report_view.xml',
    ],
    "installable": True,
    "active": False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


