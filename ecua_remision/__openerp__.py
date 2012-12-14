# -*- coding: UTF-8 -*- #
#########################################################################
# Copyright (C) 2011  Christopher Ormaza, Ecuadorenlinea.net            #
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
        "name" : "Ecuadorian Delivery Note",
        "version" : "1.20",
        "author" :  "Christopher Ormaza, Ecuadorenlinea.net",
        "website" : "http://www.ecuadorenlinea.net/",
        "category" : "Ecuadorian Legislation",
        "description": """ Delivery notes in ecuador has a authorized document by SRI,
        These have sequence by authorization.
         """,
        "depends" : ['base',
                     'product',
                     'account',
                     'ecua_autorizaciones_sri',
                     'report_aeroo_ooo', 
                     'stock',
                     'delivery',
                     'sale'],
        "init_xml" : [ ],
        "demo_xml" : [ ],
        "update_xml" : [
                        'data/data.xml',
                        'report/delivery_note_report.xml',
                        'views/company_view.xml',
                        'views/carrier_view.xml',
                        'views/picking_view.xml',
                        'views/delivery_note_view.xml',
                        'views/sale_order_view.xml',
                        'wizard/stock_partial_picking_wizard.xml',
                        'wizard/cancel_delivery_notes_wizard.xml',
                        'views/partner_view.xml',
                        #'workflow/delivery_note_workflow.xml',
                        'security/ir.model.access.csv'],
        "installable": True
}
