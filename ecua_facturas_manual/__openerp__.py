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
    "name" : "Ecuadorian Invoice",
    "version" : "1.40",
    "author" : "Christopher Ormaza, Ecuadorenlinea.net",
    "website" : "http://www.ecuadorenlinea.net/",
    "category" : "Ecuadorian Regulations",
    "depends" : [
                 'base',
                 'account',
                 'account_voucher',
                 'sale',
                 'stock',
                 'purchase',
                 'report_aeroo',
                 'report_aeroo_ooo',
                 'ecua_verifica_ruc_cedula',
                 'l10n_ec_niif_minimal',
                 'ecua_autorizaciones_sri',
                 'account_cancel'
                 ],
    "description": """
    SRI is the regulator of the tax laws in Ecuador, 
    the agency issued permits for the printing of 
    bills for each company and each agency stated, 
    this data must be stored on invoices issued and 
    received for subsequent statement, 
    the module now only the model for manually register 
    and add a field agency for subsequent generation of invoice numbers
    """,
    "init_xml": [],
    "update_xml": [
                   'wizard/invoice_print_wizard.xml',
                   'security/ir.model.access.csv',
                   'report/factura_report.xml',
                   'views/account_invoice_view.xml',
                   'views/purchase_order_view.xml',
                   'views/sale_order_view.xml',
                   'views/account_invoice_line_view.xml',
                   'views/account_voucher.xml'
    ],
    "installable": True,
    "active": False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
