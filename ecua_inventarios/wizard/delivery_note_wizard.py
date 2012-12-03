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
import netsvc
from osv import osv
from osv import fields
from tools.translate import _
from lxml import etree
import time
import psycopg2
import re
from lxml import etree
import decimal_precision as dp

class delivery_note_wizard(osv.osv_memory):
    
    _name = "account.invoice.delivery.note.wizard"
    
    _columns = {
                'carrier_id': fields.many2one('delivery.carrier', 'Carrier', required=True),
                'placa':fields.char('Placa', size=8, required=False, readonly=False), 
                    }

    def onchange_carrier_id(self, cr, uid, ids, carrier_id, context=None):
        if not context:
            context={}
        value = {}
        domain = {}
        placa = None
        if carrier_id:
            placa = self.pool.get('delivery.carrier').browse(cr, uid, carrier_id).placa
        value['placa'] = placa
        return {'value': value, 'domain': domain }


    def create_delivery_note(self, cr, uid, ids, context=None):
        if not context:
            context = {}
        inv_obj = self.pool.get('account.invoice')
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        picking_obj = self.pool.get('stock.picking')
        stk_mov_obj = self.pool.get('stock.move')
        wf_service = netsvc.LocalService('workflow')
        del_not_obj = self.pool.get('account.remision')
        auth_obj = self.pool.get('sri.authorization')
        wizard = self.browse(cr, uid, ids[0])
        invoices = inv_obj.browse(cr, uid, context.get('active_ids', []), context)
        model_data_ids = mod_obj.search(cr,uid,[('model','=','ir.ui.view'),('name','=','view_picking_out_form')])
        resource_id = mod_obj.read(cr, uid, model_data_ids, fields=['res_id'])[0]['res_id']
        for invoice in invoices:
            picking_name = _("Sales - SI %s") % invoice.number
            if invoice.type == 'out_invoice':
                order_obj = self.pool.get('sale.order')
                order_id = None
                order_ids = order_obj.search(cr, uid, [('invoice_ids','in', (invoice.id,))])
                if order_ids:
                    order_id = order_ids[0]
                
                picking_id = None
                if order_id:
                    order = order_obj.browse(cr, uid, order_id, context)
                    for picking in order.picking_ids:
                        picking_id = picking.id
                        value_picking = {
                                         'origin': picking_name,
                                         'carrier_id': wizard.carrier_id.id,
                                         'placa': wizard.placa,
                                         'invoice_id': invoice.id,
                                         'invoice_state': 'invoiced',
                                         'delivery_note': True,
                                         }
                        picking_obj.write(cr, uid, [picking_id,], value_picking, context)
                    wf_service.trg_validate(uid, 'stock.picking', picking_id, 'button_confirm', cr)
                    picking_obj.force_assign(cr, uid, [picking_id,], context)
                    inv_obj.write(cr, uid, [invoice.id], {'delivery_note': True}, context)
                    wf_service.trg_validate(uid, 'account.invoice', invoice.id, 'invoice_open', cr)
                    for move_line in picking.move_lines:
                            #TODO buscar las lineas de facturas relacionadas con el picking actual y colocar los datos
                            #sale.order.line.invoice_lines
                            if move_line.sale_line_id:
                                invoice_line_id = None
                                for invoice_line in move_line.sale_line_id.invoice_lines:
                                    invoice_line_id = invoice_line.id
                                invoice_line = self.pool.get('account.invoice.line').browse(cr, uid, invoice_line_id, context)
                else:        
                    vals_picking = {
                                    'origin': picking_name,
                                    'address_id': invoice.address_invoice_id.id,
                                    'carrier_id': wizard.carrier_id.id,
                                    'placa': wizard.placa,
                                    'invoice_state': 'invoiced',
                                    'date': time.strftime('%Y-%m-%d %H:%M:%S'),
                                    'shop_id': invoice.shop_id.id,
                                    'printer_id': invoice.printer_id.id,
                                    'delivery_note': True,
                                    'type': 'out',
                                    'state': 'draft',
                                    'invoice_id': invoice.id,
                                    }
                    picking_id = picking_obj.create(cr, uid, vals_picking, context)        
                    
                    for line in invoice.invoice_line:
                        if line.product_id.type in ('product', 'consu'):
                            name = line.product_id.name
                            vals_stock_move = {
                                               'name': name,
                                               'invoice_line_id':line.id,
                                               'product_id': line.product_id.id,
                                               'prodlot_id': line.prodlot_id and line.prodlot_id.id,
                                               'product_qty': line.quantity,
                                               'product_uom': line.product_id.uom_id.id,
                                               'location_id': invoice.location_id.id,
                                               'location_dest_id': invoice.partner_id.property_stock_customer.id,
                                               'picking_id': picking_id,
                                               }
                            stk_mov_obj.create(cr, uid, vals_stock_move, context=None)
                    wf_service.trg_validate(uid, 'stock.picking', picking_id, 'button_confirm', cr)
                    picking_obj.force_assign(cr, uid, [picking_id,], context)
                    inv_obj.write(cr, uid, [invoice.id], {'delivery_note': True}, context)
                    wf_service.trg_validate(uid, 'account.invoice', invoice.id, 'invoice_open', cr)
                    #wf_service.trg_validate(uid, 'stock.picking', picking_id, 'button_done', cr)
                return {
                    'name': _('Out Picking'),
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'stock.picking',
                    'views': [(resource_id,'form')],
                    'type': 'ir.actions.act_window',
                    'target': 'current',
                    'res_id': [picking_id],
                    'context': context,
                }

delivery_note_wizard()
