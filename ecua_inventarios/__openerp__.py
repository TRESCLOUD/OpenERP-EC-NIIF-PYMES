# -*- coding: UTF-8 -*- #
#########################################################################
# Copyright (C) 2012  Christopher Ormaza, Ecuadorenlinea.net            #
#                                                                       #
#This program is free software: you can redistribute it and/or modify   #
#it under the terms of the GNU General Public License as published by   #
#the Free Software Foundation, either version 3 of the License, or      #
#(at your option) any later version.                                    #
#                                                                       #
#This program is distributed in the hope that it will be useful,        #
#but WITHOUT ANY WARRANTY; without even the implied warranty of         #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the          #
#GNU General Public License for more details.                           #
#                                                                       #
#You should have received a copy of the GNU General Public License      #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.  #
#########################################################################

{
    "name" : "Stock Control",
    "version" : "1.8",
    "author" : "Christopher Ormaza, Ecuadorenlinea.net",
    "website" : "http://www.ecuadorenlinea.net/",
    "category" : "Stock",
    "depends" : ['base',
                 'account',
                 'sale',
                 'ecua_facturas_manual',
                 'ecua_remision',
                 'ecua_liquidacion_compras',
                 'ecua_notas_credito_manual',
                 'stock',
                 ],
    "description": """
    Control of stock moves, can't change state of a stock move without disponibility
    """,
    "init_xml": [],
    "update_xml": [
                   'data/location_data.xml',
                   'wizard/delivery_note_wizard.xml',
                   'views/location_view.xml',
                   'views/invoice_view.xml',
                   'workflow/invoice_workflow.xml',
    ],
    "installable": True,
    "active": False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
