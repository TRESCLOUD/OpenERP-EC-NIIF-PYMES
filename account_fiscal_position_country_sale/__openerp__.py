# -*- coding: utf-8 -*-
##############################################################################
#    
#    Copyright (C) 2011 Agile Business Group sagl (<http://www.agilebg.com>)
#    Copyright (C) 2011 Domsense srl (<http://www.domsense.com>)
#    All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Fiscal Position by country, sales',
    'version': '0.2',
    'category': 'Generic Modules/Accounting',
    'description': """A rule to select automatically the fiscal position in a sale order
    This module extends the account_fiscal_position_country_sale to sale orders. The modules are
    kept separate to reduce dependencies
    """,
    'author': 'Agile Business Group & Domsense',
    'website': 'http://www.agilebg.com',
    'license': 'AGPL-3',

    'depends': ['account_fiscal_position_country','sale'],
    'init_xml': [],
    'update_xml': 
                [
                'sale_view.xml',
                ],
    'demo_xml': [],
    'active': False,

    'installable': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
