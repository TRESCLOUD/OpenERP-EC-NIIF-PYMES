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
from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
from operator import itemgetter
from itertools import groupby

from osv import fields, osv
from tools.translate import _
import netsvc
import tools
import decimal_precision as dp
import logging


class stock_move(osv.osv):
    _inherit = "stock.move"
    
    _columns = {
            'invoice_line_id':fields.many2one('account.invoice.line', 'Invoice Line', required=False), 
            'invoice_id': fields.related('invoice_line_id','invoice_id', type='many2one', relation='account.invoice', string='Invoice'),
                    }
    
    def action_done(self, cr, uid, ids, context=None):
        """ Makes the move done and if all moves are done, it will finish the picking.
        @return:
        """
        partial_datas=''
        picking_ids = []
        move_ids = []
        partial_obj=self.pool.get('stock.partial.picking')
        wf_service = netsvc.LocalService("workflow")
        partial_id=partial_obj.search(cr,uid,[])
        if partial_id:
            partial_datas = partial_obj.read(cr, uid, partial_id, context=context)[0]
        if context is None:
            context = {}

        todo = []
        for move in self.browse(cr, uid, ids, context=context):
            if move.state=="draft":
                todo.append(move.id)
        if todo:
            self.action_confirm(cr, uid, todo, context=context)
            todo = []

        product_obj = self.pool.get('product.product')
        location_obj = self.pool.get('stock.location')
        states=['done'] 
        what=('in', 'out')
        
        for move in self.browse(cr, uid, ids, context=context):
            
            if move.location_id.check_stock_out:
                context.update({
                    'states': states,
                    'what': what,
                    'location': move.location_id.id or []
                })
                
                available = product_obj.get_product_available(cr, uid, [move.product_id.id], context=context)
                available_qty = available[move.product_id.id]
                
                if move.product_qty > available_qty:
                    id_loc, location_name = location_obj.name_get(cr, uid, [move.location_id.id])[0]
                    id_prod, product_name = product_obj.name_get(cr, uid, [move.product_id.id])[0]
                    raise osv.except_osv(_('Stock Error!!!'),
                                         _("Available Real Stock in Location '%s' for product '%s' is %s %s, can't done move for %s %s") % (location_name, product_name, available_qty, move.product_uom.name, move.product_qty, move.product_uom.name))
                
            if move.state in ['done','cancel']:
                continue
            move_ids.append(move.id)

            if move.picking_id:
                picking_ids.append(move.picking_id.id)
            if move.move_dest_id.id and (move.state != 'done'):
                self.write(cr, uid, [move.id], {'move_history_ids': [(4, move.move_dest_id.id)]})
                #cr.execute('insert into stock_move_history_ids (parent_id,child_id) values (%s,%s)', (move.id, move.move_dest_id.id))
                if move.move_dest_id.state in ('waiting', 'confirmed'):
                    if move.prodlot_id.id and move.product_id.id == move.move_dest_id.product_id.id:
                        self.write(cr, uid, [move.move_dest_id.id], {'prodlot_id':move.prodlot_id.id})
                    self.force_assign(cr, uid, [move.move_dest_id.id], context=context)
                    if move.move_dest_id.picking_id:
                        wf_service.trg_write(uid, 'stock.picking', move.move_dest_id.picking_id.id, cr)
                    if move.move_dest_id.auto_validate:
                        self.action_done(cr, uid, [move.move_dest_id.id], context=context)

            self._create_product_valuation_moves(cr, uid, move, context=context)
            prodlot_id = partial_datas and partial_datas.get('move%s_prodlot_id' % (move.id), False)
            if prodlot_id:
                self.write(cr, uid, [move.id], {'prodlot_id': prodlot_id}, context=context)
            if move.state not in ('confirmed','done','assigned'):
                todo.append(move.id)

        if todo:
            self.action_confirm(cr, uid, todo, context=context)

        self.write(cr, uid, move_ids, {'state': 'done', 'date': time.strftime('%Y-%m-%d %H:%M:%S')}, context=context)
        for id in move_ids:
             wf_service.trg_trigger(uid, 'stock.move', id, cr)

        for pick_id in picking_ids:
            wf_service.trg_write(uid, 'stock.picking', pick_id, cr)

        return True
stock_move()