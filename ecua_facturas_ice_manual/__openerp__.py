#########################################################################
# Copyright (C) 2011  Christopher Ormaza, Ecuadorenlinea.net	        #
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
    "name" : "Ecuadorian ICE Invoices",
    "version" : "1.0",
    "author" : "Christopher Ormaza, Ecuadorenlinea.net",
    "website" : "http://www.ecuadorenlinea.net/",
    "category" : "Ecuadorian Regulations",
    "depends" : ['base',
                 'report_aeroo_ooo',
                 'account',
                 'sale',
                 'purchase',
                 'product',
                 'ecua_verifica_ruc_cedula',
                 'ecua_facturas_manual',
                 'ecua_autorizaciones_sri',
                 'account_cancel'],
    "description": """Add support to unique invoice type to ICE products

    """,
    "init_xml": [],
    "update_xml": [
                   'data/ice_codes.xml',
                   'data/ice_tax.xml',
                   'security/ir.model.access.csv',
                   'report/factura_ice_report.xml',
                   'views/account_invoice_view.xml',
                   'views/product_view.xml',
                   'views/purchase_order_view.xml',
                   'views/sale_order_view.xml',
                   'wizard/wizard_invoice_ice.xml',
                   'wizard/wizard_sale_order_ice.xml',
    ],
    "installable": True,
    "active": False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
