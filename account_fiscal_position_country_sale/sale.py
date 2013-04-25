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

from osv import fields, osv

class sale_order(osv.osv):
    _inherit = "sale.order"

    def onchange_partner_id_fiscal_position(self, cr, uid, ids, partner_id):
        result = super(sale_order, self).onchange_partner_id(cr, uid, ids, partner_id)

        if not result['value']['fiscal_position']:
        	if partner_id:
	        	partner = self.pool.get('res.partner').browse(cr, uid, partner_id)
	        	addr = self.pool.get('res.partner').address_get(cr, uid, [partner_id])
	        	address = self.pool.get('res.partner.address').browse(cr, uid, addr['default'])
	        	result['value']['fiscal_position'] = address.country_id and address.country_id.property_account_position and address.country_id.property_account_position.id or False

        return result

sale_order()
