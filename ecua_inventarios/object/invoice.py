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

class account_invoice(osv.osv):

    def _delivered(self, cursor, user, ids, name, arg, context=None):
        res = {}
        for invoice in self.browse(cursor, user, ids, context=context):
            res[invoice.id] = True
            for picking in invoice.picking_ids:
                if picking.state != 'done':
                    res[invoice.id] = False
                    break
            if not invoice.picking_ids:
                res[invoice.id] = False
        return res

    def _get_invoice_piking(self, cr, uid, ids, context=None):
        result = {}
        for picking in self.pool.get('stock.picking').browse(cr, uid, ids, context=context):
            if picking.invoice_id:
                result[picking.invoice_id.id] = True
        return result.keys()
    
    _inherit = 'account.invoice' 

    _columns = {
                'delivered': fields.function(_delivered, method=True, string='Delivered',
                   type='boolean', help="It indicates that an invoice has been delivered.", 
                   store={
                       'stock.picking': (_get_invoice_piking, ['state','invoice_id'], 1),
                       'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['picking_ids'], 2),}),
                'picking_ids':fields.one2many('stock.picking', 'invoice_id', 'Pickings', required=False), 
                'remision_ids':fields.one2many('account.remision', 'invoice_id', 'Remisions', required=False), 
                'remision_id': fields.related('remision_ids', 'number', type='char', string='Remision Number'),
                'delivery_note':fields.boolean('Delivery Note', required=False),
                'warehouse_id': fields.related('shop_id','warehouse_id', type='many2one', relation='stock.warehouse', string='Warehouse'),
                'location_id': fields.related('warehouse_id','lot_stock_id', type='many2one', relation='stock.location', string='Location', store=True),
                    }
    
    def copy(self, cr, uid, id, default=None, context=None):
        if not context:
            context = {}
        default.update({
                        'delivery_note': False,
                        'picking_ids': [],
                        'remision_ids':[],
                        })
        res_id = super(account_invoice, self).copy(cr, uid, id, default, context)
        return res_id 

    def check_stock_move(self, cr, uid, ids, context=None):
        inv_obj = self.pool.get('account.invoice')
        picking_obj = self.pool.get('stock.picking')
        remision_obj = self.pool.get('account.remision')
        sale_obj = self.pool.get('sale.order')
        for invoice in self.browse(cr, uid, ids, context):
            sale_ids = sale_obj.search(cr, uid, [('invoice_ids', 'in', (invoice.id,))])
            for sale_id in sale_ids:
                order = sale_obj.browse(cr, uid, sale_id, context)
                for picking in order.picking_ids:
                    if not picking.invoice_id:
                        picking_obj.write(cr, uid, [picking.id],{'invoice_id': invoice.id}, context)
                for remision in order.remision_ids:
                    if not remision.invoice_id:
                        remision_obj.write(cr, uid, [remision.id],{'invoice_id': invoice.id}, context)
        return True

    def write_stock_move(self, cr, uid, ids, context=None):
        inv_obj = self.pool.get('account.invoice')
        picking_obj = self.pool.get('stock.picking')
        stk_mov_obj = self.pool.get('stock.move')
        wf_service = netsvc.LocalService('workflow')
        for invoice in self.browse(cr, uid, ids, context):
            dest_location = None
            source_location = None
            picking_name = None
            type_picking = 'in'
            if invoice.type == 'out_invoice':
                continue
            if invoice.type == 'in_refund':
                picking_name = _("Purchase Refund - RP %s") % invoice.number
                source_location = invoice.location_id.id,
                dest_location = invoice.partner_id.property_stock_supplier.id,
                type_picking = 'out'
            if invoice.type == 'out_refund':
                picking_name = _("Sales Refund - RS %s") % invoice.number
                dest_location = invoice.location_id.id,
                source_location = invoice.partner_id.property_stock_customer.id,
                type_picking = 'in'
            if invoice.type == 'in_invoice':
                picking_name = _("Purchase Input - SI %s") % invoice.number
                dest_location = invoice.location_id.id,
                source_location = invoice.partner_id.property_stock_supplier.id,
                type_picking = 'in'

            vals_picking = {
                            'origin': picking_name,
                            'address_id': invoice.address_invoice_id.id,
                            'invoice_state': 'invoiced',
                            'date': time.strftime('%Y-%m-%d %H:%M:%S'),
                            'delivery_note': False,
                            'type': type_picking,
                            'state': 'draft',
                            'invoice_id': invoice.id,
                            }
            picking_id = picking_obj.create(cr, uid, vals_picking, context)        
            
            for line in invoice.invoice_line:
                if line.product_id.type in ('product', 'consu'):
                    name = line.product_id.name
                    price_unit = line.price_unit
                    vals_stock_move = {
                                       'name': name,
                                       'product_id': line.product_id.id,
                                       'prodlot_id': line.prodlot_id and line.prodlot_id.id,
                                       'invoice_line_id': line.id,
                                       'product_qty': line.quantity,
                                       'product_uom': line.uos_id.id,
                                       'location_dest_id': dest_location,
                                       'location_id': source_location,
                                       'picking_id': picking_id,
                                       'price_unit': price_unit
                                       }
                    stk_mov_obj.create(cr, uid, vals_stock_move, context=None)
            wf_service.trg_validate(uid, 'stock.picking', picking_id, 'button_confirm', cr)
            picking_obj.force_assign(cr, uid, [picking_id,], context)
            inv_obj.write(cr, uid, [invoice.id], {'delivery_note': True}, context)
            wf_service.trg_validate(uid, 'stock.picking', picking_id, 'button_done', cr)
        return True

    def _refund_cleanup_lines(self, cr, uid, lines):
        for line in lines:
            del line['id']
            del line['invoice_id']
            del line['move_ids']
            for field in ('company_id', 'partner_id', 'account_id', 'product_id', 'prodlot_id', 'location_id',
                          'uos_id', 'account_analytic_id', 'tax_code_id', 'base_code_id'):
                line[field] = line.get(field, False) and line[field][0]
            if 'invoice_line_tax_id' in line:
                line['invoice_line_tax_id'] = [(6,0, line.get('invoice_line_tax_id', [])) ]
        return map(lambda x: (0,0,x), lines)


    def action_cancel(self, cr, uid, ids, context=None):
        if not context:
            context = {}
        picking_obj = self.pool.get('stock.picking')
        remision_obj = self.pool.get('account.remision')
        move_obj = self.pool.get('stock.move')
        for invoice in self.browse(cr, uid, ids, context):
            for picking in invoice.picking_ids:
                for move in picking.move_lines:
                    move_obj.write(cr, uid, [move.id], {'state':'draft'})
                    move_obj.unlink(cr, uid, [move.id])
                picking_obj.action_cancel(cr, uid, [picking.id])
                picking_obj.write(cr, uid, [picking.id], {'state':'draft'})
                picking_obj.unlink(cr, uid, [picking.id])
            for remision in invoice.remision_ids:
                remision_obj.action_cancel(cr, uid, [remision.id], context)
                remision_obj.action_set_draft(cr, uid, [remision.id], context)
                remision_obj.unlink(cr, uid, [remision.id])
        self.write(cr, uid, ids, {'delivery_note':False})
        res = super(account_invoice, self).action_cancel(cr, uid, ids, context)
        return res

account_invoice()

class account_invoice_line(osv.osv):
    
    _inherit = 'account.invoice.line'
    
    _columns = {
                'prodlot_id':fields.many2one('stock.production.lot', 'Lote', required=False),
                'move_ids':fields.one2many('stock.move', 'invoice_line_id', 'Stock Moves', required=False),
                'location_id':fields.many2one('stock.location', 'Location', required=False),
                'lot_required':fields.boolean('Lot Required', required=False),
                    }

    def default_get(self, cr, uid, fields_list, context=None):
        if not context:
            context={}
        values = super(account_invoice_line, self).default_get(cr, uid, fields_list, context)
        shop = self.pool.get('sale.shop').browse(cr, uid, context.get('shop_id', None), context=context)
        values['location_id'] = shop and shop.warehouse_id and shop.warehouse_id.lot_stock_id and shop.warehouse_id.lot_stock_id.id or None
        return values

    def product_id_change(self, cr, uid, ids, product, uom, qty=0, name='', type='out_invoice', partner_id=False, fposition_id=False, price_unit=False, address_invoice_id=False, currency_id=False, context=None, shop_id=None):
        if context is None:
            context = {}
        company_id = context.get('company_id',False)
        if not partner_id:
            raise osv.except_osv(_('No ha seleccionado a la Empresa !'),_("Debe seleccionar a la empresa primero !") )
        if not product:
            return {'value': {'price_unit': 0.0, 'categ_id': False}, 'domain':{'product_uom':[]}}
        part = self.pool.get('res.partner').browse(cr, uid, partner_id, context=context)
        fpos_obj = self.pool.get('account.fiscal.position')
        fpos = fposition_id and fpos_obj.browse(cr, uid, fposition_id, context=context) or False
        
        if part.lang:
            context.update({'lang': part.lang})
        result = {}
        res = self.pool.get('product.product').browse(cr, uid, product, context=context)
        if shop_id:
            shop = self.pool.get('sale.shop').browse(cr, uid, shop_id, context=context)
            result['location_id'] = shop.warehouse_id and shop.warehouse_id.lot_stock_id and shop.warehouse_id.lot_stock_id.id or None
        if res and (type in ('out_invoice', 'out_refund') and res.track_outgoing) or (type in ('in_invoice', 'in_refund') and res.track_incoming):
            result['lot_required'] = True
        if type in ('out_invoice','out_refund'):
            a = res.product_tmpl_id.property_account_income.id
            if not a:
                a = res.categ_id.property_account_income_categ.id
        else:
            a = res.product_tmpl_id.property_account_expense.id
            if not a:
                a = res.categ_id.property_account_expense_categ.id
        a = fpos_obj.map_account(cr, uid, fpos, a)
        if a:
            result['account_id'] = a

        if type in ('out_invoice', 'out_refund'):
            taxes = res.taxes_id and res.taxes_id or (a and self.pool.get('account.account').browse(cr, uid, a, context=context).tax_ids or False)
        else:
            taxes = res.supplier_taxes_id and res.supplier_taxes_id or (a and self.pool.get('account.account').browse(cr, uid, a, context=context).tax_ids or False)
        tax_id = fpos_obj.map_tax(cr, uid, fpos, taxes)

        if type in ('in_invoice', 'in_refund'):
            result.update( {'price_unit': price_unit or res.standard_price,'invoice_line_tax_id': tax_id} )
        else:
            result.update({'price_unit': res.list_price, 'invoice_line_tax_id': tax_id})
        result['name'] = res.partner_ref

        domain = {}
        result['uos_id'] = res.uom_id.id or uom or False
        result['note'] = res.description
        if result['uos_id']:
            res2 = res.uom_id.category_id.id
            if res2:
                domain = {'uos_id':[('category_id','=',res2 )]}

        result['categ_id'] = res.categ_id.id
        res_final = {'value':result, 'domain':domain}

        if not company_id or not currency_id:
            return res_final

        company = self.pool.get('res.company').browse(cr, uid, company_id, context=context)
        currency = self.pool.get('res.currency').browse(cr, uid, currency_id, context=context)

        if company.currency_id.id != currency.id:
            new_price = res_final['value']['price_unit'] * currency.rate
            res_final['value']['price_unit'] = new_price

        if uom:
            uom = self.pool.get('product.uom').browse(cr, uid, uom, context=context)
            if res.uom_id.category_id.id == uom.category_id.id:
                new_price = res_final['value']['price_unit'] * uom.factor_inv
                res_final['value']['price_unit'] = new_price
        return res_final
account_invoice_line()