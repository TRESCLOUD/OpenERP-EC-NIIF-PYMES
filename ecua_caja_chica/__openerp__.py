
# -*- encoding: utf-8 -*-
########################################################################
#                                                                       
# @authors: Christopher Ormaza                                                                           
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
    "name": "Account Pretty Cash Replenishment",
    "version": "1.0",
    "depends": ["base",
                "account",
                "ecua_account",
                ],
    "author": "Christopher Ormaza",
    "website": "https://www.openerpecuador.org",
    "category": "Account",
    "description": """
    This module provide :
    
    """,
    "init_xml": [],
    'update_xml': [
                   "report/petty_cash_replenishment_report.xml",
                   "views/pretty_cash_replenishment_view.xml",
                   "views/journal_view.xml"
                   ],
    'demo_xml': [],
    'installable': True,
    'active': False,
}