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
from tools.translate import _ 
import time
import netsvc
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta

class stock_picking(osv.osv):

    _inherit = 'stock.picking' 
 
    _columns = {
            'remision_ids': fields.one2many('account.remision', 'stock_picking_id', 'Delivery Notes'),
            'delivery_note':fields.boolean('Delivery Note?', required=False, states={'draft':[('readonly',False)]}), 
            'shop_id':fields.many2one('sale.shop', 'Shop', readonly=True, states={'draft':[('readonly',False)]}), 
            'printer_id':fields.many2one('sri.printer.point', 'Printer Point', readonly=True, states={'draft':[('readonly',False)]}),
            'invoice_id':fields.many2one('account.invoice', 'Invoice', required=False), 
            'placa':fields.char('Placa', size=8, required=False, readonly=False), 
    }
    
    def _get_delivery_note_defaults(self, cr, uid, ids, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        return user.company_id.delivery_note_defaults
    
    _defaults = {  
        'delivery_note': _get_delivery_note_defaults,
        }
    
    def copy(self, cr, uid, id, default={}, context=None):
        if context is None:
            context = {}
        default.update({
            'remision_ids':[],
        })
        return super(stock_picking, self).copy(cr, uid, id, default, context)
    
    def action_process(self, cr, uid, ids, context=None):
        if context is None: context = {}
        partial_id = self.pool.get("stock.partial.picking").create(
            cr, uid, {}, context=dict(context, active_ids=ids))
        return {
            'name':_("Products to Process"),
            'view_mode': 'form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'stock.partial.picking',
            'res_id': partial_id,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            'context': dict(context, active_ids=ids)
        }

    def action_cancel(self, cr, uid, ids, context=None):
        for pick in self.browse(cr, uid, ids, context=context):
            if pick.remision_ids:
                for remision in pick.remision_ids:
                    self.pool.get('account.remision').action_cancel(cr, uid, [remision.id,], context)
            return super(stock_picking, self).action_cancel(cr, uid, ids, context)


stock_picking()