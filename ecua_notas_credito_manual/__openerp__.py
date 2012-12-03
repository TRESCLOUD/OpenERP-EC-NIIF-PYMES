##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2011-2012 Christopher Ormaza - Ecuadorenlinea.net. All Rights Reserved
#
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see http://www.gnu.org/licenses/.
#
##############################################################################

{
    "name": "Credit Note - Ecuador",
    "version": "1.43",
    "depends": ["base",
                "account",
                "account_voucher",
                "ecua_autorizaciones_sri",
                "ecua_facturas_manual",
                "ecua_retenciones_manual",
                "report_aeroo_ooo"],
    "author": "Christopher Ormaza - Ecuadorenlinea.net",
    "website" : "http://www.ecuadorenlinea.net",
    "category": "Ecuadorian Legislation",
    "description": """
    This module provide : Support for credit notes on Ecuadorian Legislation
    """,
    "init_xml": ["data/data_init.xml"],
    'update_xml': [
                   "data/data.xml",
                   "report/credit_note_report.xml",
                   "wizard/wizard_credit_note_view.xml",
                   "workflow/invoice_workflow.xml",
                   "views/invoice_view.xml",
                   "views/invoice_refund_view.xml",
                   "views/shop_view.xml",
                   ],
    'demo_xml': [],
    'installable': True,
    'active': False,
#    'certificate': 'certificate',
}
