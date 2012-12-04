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
from osv import fields,osv
import decimal_precision as dp
from tools.translate import _

class stock_move(osv.osv):
    _inherit = 'stock.move'

    def _get_reference_accounting_values_for_valuation(self, cr, uid, move, context=None):
        """
        Overrides the default stock valuation to take into account the currency that was specified
        on the purchase order in case the valuation data was not directly specified during picking
        confirmation.
        """
        product_uom_obj = self.pool.get('product.uom')
        default_uom = move.product_id.uom_id.id
        qty = product_uom_obj._compute_qty(cr, uid, move.product_uom.id, move.product_qty, default_uom)
        reference_amount, reference_currency_id = super(stock_move, self)._get_reference_accounting_values_for_valuation(cr, uid, move, context=context)
        if move.product_id.cost_method != 'average' or not move.price_unit:
            # no average price costing or cost not specified during picking validation, we will
            # plug the purchase line values if they are found.
            if move.purchase_line_id and move.picking_id.purchase_id.pricelist_id:
                reference_amount, reference_currency_id = move.purchase_line_id.price_unit * qty, move.picking_id.purchase_id.pricelist_id.currency_id.id

        if move.product_id.cost_method == 'average' and move.price_unit:
            reference_amount = qty * move.price_unit
            reference_currency_id = move.price_currency_id.id or reference_currency_id
        return reference_amount, reference_currency_id

stock_move()