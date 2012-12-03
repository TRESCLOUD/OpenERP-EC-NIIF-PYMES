#########################################################################
# Copyright (C) 2010  Christopher Ormaza, Ecuadorenlinea.net            #
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
        "name" : "Ecuadorian Retentions",
        "version" : "1.28",
        "author" : "Christopher Ormaza, Ecuadorenlinea.net",
        "website" : "http://www.ecuadorenlinea.net/",
        "category" : "Ecuadorian Legislation",
        "description": """ This module provide a data structure to store withholdings of VAT and 
        Source Withholding
        """,
        "depends" : ['base', 'report_aeroo_ooo', 'account','account_voucher','product','ecua_facturas_manual','l10n_ec_niif_minimal'],
        "init_xml" : [ ],
        "demo_xml" : [ ],
        "update_xml" : ['workflow/retention_workflow.xml',
                        'wizard/retention_wizard_view.xml',
                        'wizard/cancel_retentions_wizard.xml',
                        'report/retention_report.xml',
                        'views/shop.xml',
                        'data/data.xml',
                        'views/retenciones_view.xml',
                        'views/invoice_view.xml',
                        'views/company_view.xml',
                        'security/ir.model.access.csv'
                        ],
        "installable": True
}