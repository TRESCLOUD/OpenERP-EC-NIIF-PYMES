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
import re

class stock_partial_picking(osv.osv_memory):
    
    def _check_number(self,cr,uid,ids):
        cadena='(\d{3})+\-(\d{3})+\-(\d{9})'
        for obj in self.browse(cr, uid, ids):
            ref = obj['number']
            if obj['number']:
                if re.match(cadena, ref):
                    return True
                else:
                    return False
            else:
                return True
            
    def _get_automatic(self, cr, uid, ids, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        return user.company_id.generate_automatic
    
    _inherit = 'stock.partial.picking'
    _columns = {
                'delivery_note':fields.boolean('Make Delivery Note'),
                'carrier_id': fields.many2one('delivery.carrier', 'Carrier'),
                'placa':fields.char('Placa', size=8, required=False, readonly=False),
                'number': fields.char ('Number', size=17, required=False),
                'automatic':fields.boolean('Automatic?', required=False),
                'automatic_number': fields.char ('Number', size=17, readonly="2"),
                'shop_id':fields.many2one('sale.shop', 'Shop'),
                'printer_id':fields.many2one('sri.printer.point', 'Printer Point',),
                }
    
    _defaults = {
                 'delivery_note': False,
                 'automatic': _get_automatic,
                 }
    
    _constraints = [(_check_number,'The number is incorrect, it must be like 001-00X-000XXXXXX, X is a number',['number'])]

    def get_picking_type(self, cr, uid, picking, context=None):
        picking_type = picking.type
        for move in picking.move_lines:
            if picking.type == 'in' and move.product_id.cost_method == 'average':
                picking_type = 'in'
                break
            else:
                picking_type = 'out'
        return picking_type

    def __create_partial_picking_memory(self, move, pick_type):
        move_memory = {
            'product_id' : move.product_id.id,
            'quantity' : move.product_qty,
            'product_uom' : move.product_uom.id,
            'prodlot_id' : move.prodlot_id.id,
            'move_id' : move.id,
        }

        if pick_type == 'in':
            move_memory.update({
                'cost' : move.product_id.standard_price,
                'currency' : move.product_id.company_id and move.product_id.company_id.currency_id.id or False,
            })
        return move_memory
    
    def defined_type_remision(self, dato):
        if (dato=='out'):
            return 'sales'
        else:
            return 'internal'
        
    def do_partial(self, cr, uid, ids, context=None):
        pick_obj = self.pool.get('stock.picking')
        move_obj = self.pool.get('stock.move')
        location_obj = self.pool.get('stock.location')
        
        picking_ids = context.get('active_ids', False)
        partial = self.browse(cr, uid, ids[0], context=context)
        partial_datas = {
            'delivery_date' : partial.date
        }

        for pick in pick_obj.browse(cr, uid, picking_ids, context=context):
            picking_type = self.get_picking_type(cr, uid, pick, context=context)
            moves_list = picking_type == 'in' and partial.product_moves_in or partial.product_moves_out

            for move in moves_list:
                partial_datas['move%s' % (move.move_id.id)] = {
                    'product_id': move.id, 
                    'product_qty': move.quantity, 
                    'product_uom': move.product_uom.id, 
                    'prodlot_id': move.prodlot_id.id, 
                }
                if (move.product_id.cost_method == 'average'):
                    partial_datas['move%s' % (move.move_id.id)].update({
                                                    'product_price' : move.cost, 
                                                    'product_currency': move.currency.id, 
                                                    })
        pick_obj.do_partial(cr, uid, picking_ids, partial_datas, context=context)
        
        #Method for creation of delivery note
        stock_picking_obj = self.pool.get('stock.picking')
        remision_obj = self.pool.get('account.remision')
        remision_line_obj = self.pool.get('account.remision.line')
        seq_obj = self.pool.get('ir.sequence')
        vals_aut=self.pool.get('sri.authorization').get_auth_secuence(cr, uid, 'delivery_note')
        bool=False
        remision_id=False
        for object in self.browse(cr, uid, ids, context=context):
            if (object.delivery_note):
                user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
                bool = user.company_id.generate_automatic
                stock_picking=stock_picking_obj.browse(cr, uid, picking_ids, context)
                for picking in stock_picking:
                    if  picking['state']=='done':
                        if bool:
                            b = True
                            vals_aut = self.pool.get('sri.authorization').get_auth_secuence(cr, uid, 'delivery_note')
                            while b :
                                number = self.pool.get('ir.sequence').get_id(cr, uid, vals_aut['sequence'])
                                if not self.pool.get('account.remision').search(cr, uid, [('number','=',number),('id','not in',tuple(ids))],):
                                    b=False
                            autorizacion = vals_aut['authorization']
                        else:
                            shop = self.pool.get('sale.shop').search(cr, uid,[])[0]
                            company = self.pool.get('res.company').search(cr, uid,[])[0]
                            number = object['number']
                            auth = self.pool.get('sri.authorization').get_auth(cr, uid, 'delivery_note', company, object.shop_id.id, number,object.printer_id.id ,context)
                            if not auth['authorization']:
                                raise osv.except_osv(_('Invalid action!'), _('Do not exist authorization for this number of secuence, please check'))
                            else:
                                autorizacion = auth['authorization']
                        if picking['type']=='out':
                            placa = ''
                            if picking['carrier_id']:
                                carrier= picking['carrier_id']['id']
                                placa = picking.carrier_id and picking.carrier_id.placa
                            else:
                                carrier= object['carrier_id']['id']
                                placa = object.carrier_id and picking.carrier_id.placa
                            vals_remi= {
                                        'number': number,
                                        'number_out': number,
                                        'authorizacion_id': autorizacion,
                                        'transfer_date': time.strftime('%Y-%m-%d'),
                                        'delivery_date': picking['min_date'],
                                        'motive': _("Generated by the picking # %s" % picking['name']) ,
                                        'delivery_address': picking['address_id']['id'],
                                        'partner_id': picking ['partner_id']['id'],
                                        'stock_picking_id': picking['id'],
                                        'delivery_carrier': carrier,
                                        'placa': placa,
                                        'shop_id':picking['shop_id']['id'],
                                        'printer_id':picking['printer_id']['id'],
                                        'sale_order':picking['sale_id']['id'],
                                        'invoice_id':picking.invoice_id.id or None,
                                        'type': self.defined_type_remision(picking['type']),
                                        'automatic': object.automatic,
                                        }
                            remision_id = remision_obj.create(cr, uid, vals_remi, context)
                            for line in picking.move_lines:
                                vals_remi_line= {
                                                 'quantity': line['product_qty'],
                                                 'product_id': line['product_id']['id'],
                                                 'uom_id': line['product_uom']['id'],
                                                 'remision_id': remision_id,
                                                 }
                                remision_line_id = remision_line_obj.create(cr, uid, vals_remi_line, context)
                        elif (picking['type']=='internal'):
                            vals_remi= {
                                        'number': number,
                                        'number_out': number,
                                        'authorizacion_id': autorizacion,
                                        'partner_id': picking ['address_id']['partner_id']['id'],
                                        'transfer_date': time.strftime('%Y-%m-%d'),
                                        'delivery_date': picking['min_date'],
                                        'delivery_address': picking['address_id']['id'],
                                        'stock_picking_id': picking['id'],
                                        'shop_id':picking['shop_id']['id'],
                                        'printer_id':picking['printer_id']['id'],
                                        'invoice_id':picking.invoice_id.id or None,
                                        'type': self.defined_type_remision(picking['type']),
                                        'automatic': object.automatic,
                                        }
                            remision_id = remision_obj.create(cr, uid, vals_remi, context)
                            for line in picking.move_lines:
                                vals_remi_line= {
                                                 'quantity': line['product_qty'],
                                                 'product_id': line['product_id']['id'],
                                                 'product_uom': line['product_uom']['id'],
                                                 'remision_id': remision_id,
                                                 }
                                remision_line_id = remision_line_obj.create(cr, uid, vals_remi_line, context)
                        remision_obj.action_confirm(cr, uid, [remision_id,], context)
                    elif picking['state']=='assigned':
                        if picking['backorder_id']['id']:
                            picking=stock_picking_obj.browse(cr, uid, picking['backorder_id']['id'], context)
                            if bool:
                                number = self.pool.get('ir.sequence').get_id(cr, uid, vals_aut['sequence'])
                                autorizacion = vals_aut['authorization']
                            else:
                                shop = self.pool.get('sale.shop').search(cr, uid,[])[0]
                                company = self.pool.get('res.company').search(cr, uid,[])[0]
                                number = object['number']
                                auth = self.pool.get('sri.authorization').get_auth(cr, uid, 'delivery_note', company, shop, number, context)
                                if not auth['authorization']:
                                    raise osv.except_osv(_('Invalid action!'), _('Do not exist authorization for this number of secuence, please check'))
                                else:
                                    autorizacion = auth['authorization']
                            if picking['type']=='out':
                                placa = ''
                                if picking['carrier_id']:
                                    carrier= picking['carrier_id']['id']
                                    placa = picking.carrier_id and picking.carrier_id.placa
                                else:
                                    carrier= object['carrier_id']['id']
                                    placa = object.carrier_id and picking.carrier_id.placa
                                vals_remi= {
                                            'number': number,
                                            'number_out': number,
                                            'authorizacion_id': autorizacion,
                                            'transfer_date': time.strftime('%Y-%m-%d'),
                                            'delivery_date': picking['min_date'],
                                            'motive': _("Generated by the picking # %s" % picking['name']),
                                            'delivery_address': picking['address_id']['id'],
                                            'partner_id': picking ['partner_id']['id'],
                                            'stock_picking_id': picking['id'],
                                            'delivery_carrier': carrier,
                                            'placa': placa,
                                            'shop_id':picking['shop_id']['id'],
                                            'printer_id':picking['printer_id']['id'],
                                            'invoice_id':picking.invoice_id.id or None,
                                            'sale_order':picking['sale_id']['id'],
                                            'type': self.defined_type_remision(picking['type']),
                                            'automatic': object.automatic,
                                            }
                                remision_id = remision_obj.create(cr, uid, vals_remi, context)
                                for line in picking.move_lines:
                                    vals_remi_line= {
                                                 'quantity': line['product_qty'],
                                                 'product_id': line['product_id']['id'],
                                                 'product_uom': line['product_uom']['id'],
                                                 'remision_id': remision_id,
                                                 }
                                    remision_line_id = remision_line_obj.create(cr, uid, vals_remi_line, context)
                            elif (picking['type']=='internal'):
                                vals_remi= {
                                            'number': number,
                                            'number_out': number,
                                            'authorizacion_id': autorizacion,
                                            'partner_id': picking ['address_id']['partner_id']['id'],
                                            'transfer_date': time.strftime('%Y-%m-%d'),
                                            'delivery_date': picking['min_date'],
                                            'delivery_address': picking['address_id']['id'],
                                            'stock_picking_id': picking['id'],
                                            'shop_id':picking['shop_id']['id'],
                                            'invoice_id':picking.invoice_id.id or None,
                                            'printer_id':picking['printer_id']['id'],
                                            'type': self.defined_type_remision(picking['type']),
                                            'automatic': object.automatic,
                                            }
                                remision_id = remision_obj.create(cr, uid, vals_remi, context)
                                for line in picking.move_lines:
                                    vals_remi_line= {
                                             'quantity': line['product_qty'],
                                             'product_id': line['product_id']['id'],
                                             'product_uom': line['product_uom']['id'],
                                             'remision_id': remision_id,
                                             }
                                    remision_line_id = remision_line_obj.create(cr, uid, vals_remi_line, context)
                            remision_obj.action_confirm(cr, uid, [remision_id,], context)

        act_obj = self.pool.get('ir.actions.act_window')
        mod_obj = self.pool.get('ir.model.data')

        model_data_ids = mod_obj.search(cr,uid,[('model','=','ir.ui.view'),('name','=','view_account_remision_form')])
        resource_id = mod_obj.read(cr, uid, model_data_ids, fields=['res_id'])[0]['res_id']
        
        if remision_id:
            return {
                'name': _('Delivery Note'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'account.remision',
                'views': [(resource_id,'form')],
                'type': 'ir.actions.act_window',
                'target': 'current',
                'res_id': [remision_id],
                'context': context,
            }
        else:
            return {'type': 'ir.actions.act_window_close'}

    def _get_automatic(self, cr, uid, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        return user.company_id.generate_automatic

    def default_get(self, cr, uid, fields, context=None):
        doc_obj = self.pool.get('sri.type.document')
        if context is None:
            context = {}
        values = {}
        pick_obj = self.pool.get('stock.picking')
        res = super(stock_partial_picking, self).default_get(cr, uid, fields, context)
        picking_ids = context.get('active_ids', [])
        if not picking_ids:
            return res
        objs = pick_obj.browse(cr , uid, picking_ids)
        company_id = self.pool.get('res.company')._company_default_get(cr, uid, 'stock.picking', context=context)
        automatic = self._get_automatic(cr, uid, context)
        for obj in objs:
            if obj.type in ('out', 'internal'):
                if 'automatic_number' in fields and 'number' in fields:
                    auth_line_id = doc_obj.search(cr, uid, [('name','=','delivery_note'), ('printer_id','=',obj.printer_id.id), ('shop_id','=',obj.shop_id.id), ('state','=',True),])
                    if auth_line_id:
                        if automatic:
                            automatic_number = doc_obj.get_next_value_secuence(cr, uid, 'delivery_note', False, company_id, obj.shop_id.id, obj.printer_id.id, 'account.remision', 'number_out', context)
                            res.update({'automatic_number': automatic_number})
                            res.update({'number': automatic_number})
                if 'carrier_id' in fields:
                    placa = obj.placa or obj.carrier_id.placa
                    res.update({'carrier_id': obj.carrier_id.id, 'placa': placa})                
                if 'delivery_note' in fields:
                    res.update({'delivery_note': obj.delivery_note})
                if 'shop_id' in fields:
                    res.update({'shop_id': obj.shop_id.id})
                if 'printer_id' in fields:
                    res.update({'printer_id': obj.printer_id.id})
        return res

    def onchange_data(self, cr, uid, ids, automatic, shop_id=None, printer_id=None, context=None):
        doc_obj = self.pool.get('sri.type.document')
        values = {}
        if context is None:
            context = {}
        company_id = self.pool.get('res.company')._company_default_get(cr, uid, 'stock.picking', context=context)
        shop_ids = []
        curr_shop = False
        if shop_id:
            curr_shop = self.pool.get('sale.shop').browse(cr, uid, [shop_id, ], context)[0]
        curr_user = self.pool.get('res.users').browse(cr, uid, [uid, ], context)[0]
        if curr_shop:
            if printer_id:
                auth_line_id = doc_obj.search(cr, uid, [('name','=','delivery_note'), ('printer_id','=',printer_id), ('shop_id','=',curr_shop.id), ('state','=',True),])
                if auth_line_id:
                    if automatic:
                        values['automatic_number'] = doc_obj.get_next_value_secuence(cr, uid, 'delivery_note', False, company_id, curr_shop.id, printer_id, 'account.remision', 'number_out', context)
                        values['number'] = values['automatic_number']
                        values['date'] = time.strftime('%Y-%m-%d')
                else:
                    values['automatic'] = False
                    values['date'] = None
        return {'value': values, }

    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        result = super(stock_partial_picking, self).fields_view_get(cr, uid, view_id, view_type, context, toolbar, submenu)
        trans = False
        pick_obj = self.pool.get('stock.picking')
        picking_ids = context.get('active_ids', False)

        if not picking_ids:
            return result
        for pick in pick_obj.browse(cr, uid, picking_ids, context=context):
            if pick.carrier_id:
                trans = True
            picking_type = self.get_picking_type(cr, uid, pick, context=context)
            if pick['type']=='in':
                return super(stock_partial_picking, self).fields_view_get(cr, uid, view_id, view_type, context, toolbar, submenu)
        _moves_arch_lst = """<form string="%s">
                        <field name="date" invisible="1"/>
                        <group height="400" width="600">
                            <separator colspan="4" string="%s"/>
                            <field name="%s" colspan="4" nolabel="1" mode="tree,form" height="200" ></field>
                            <separator string="%s" colspan="4" />
                            <group colspan="4" attrs="{'invisible':[('delivery_note','=',False)]}">
                                <field name="automatic" invisible="1"/>
                                <field name="shop_id" invisible="1" on_change="onchange_data(automatic, shop_id, printer_id)"/>
                                <field name="printer_id" invisible="1" on_change="onchange_data(automatic, shop_id, printer_id)"/>
                                <field name="automatic_number" attrs="{'invisible':[('automatic','!=',True)]}" />
                                <field name="number" attrs="{'invisible':[('automatic','=',True)],'required':[('automatic','=',False),('delivery_note','=',True)]}"/>
                        """ % (_('Process Document'), _('Products'), "product_moves_" + picking_type, _("Options"))
        _moves_fields = result['fields']

        _moves_fields.update({
                            'product_moves_' + picking_type: {'relation': 'stock.move.memory.'+picking_type, 'type' : 'one2many', 'string' : _('Product Moves')}, 
                            })
        if trans:
            _moves_arch_lst += """
                        </group>"""
        else:
            _moves_arch_lst += """
                    <field name="carrier_id" attrs="{'required':[('delivery_note','=',True)]}"/>
                    <field name="placa" attrs="{'required':[('delivery_note','=',True)]}"/>
                </group>"""
        
        _moves_arch_lst += """
                    <group colspan="4" col="6">
                            <field name="delivery_note"/>
                            <button icon='gtk-cancel' special="cancel"
                                string="_Cancel" />
                            <button name="do_partial" string="_Validate"
                                type="object" icon="gtk-go-forward" />
                        </group>
                    </group>
            </form>"""
        result['arch'] = _moves_arch_lst
        result['fields'] = _moves_fields
        return result

stock_partial_picking()
