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
from osv import fields,osv
import decimal_precision as dp
from tools.translate import _

class account_remision(osv.osv):
    
    def unlink(self, cr, uid, ids, context=None):
        if not context:
            context = {}
        unlink_ids = []
        for r in self.browse(cr, uid, ids, context):
            if r.state != 'draft':
                raise osv.except_osv(_('Invalid action !'), _('Cannot delete delivery note(s) that are already Done !'))
        return super(account_remision, self).unlink(cr, uid, ids)
    
    def onchange_invoice(self, cr, uid, ids, invoice_id, context=None):
        return {}

    def onchange_picking(self, cr, uid, ids, picking_id, context=None):
        return {}

    def _get_automatic(self, cr, uid, ids, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        return user.company_id.generate_automatic
    
    _name = 'account.remision'

    _columns = {
        'automatic_number': fields.char ('number', size=17, readonly=True),
        'number': fields.char ('Number', size=17, required=False,readonly=True, states={'draft':[('readonly', False)]}),
        'number_in': fields.char ('Number', size=17, required=False,readonly=True, states={'draft':[('readonly', False)]}),
        'number_out': fields.char ('Number', size=17, required=False,readonly=True, states={'draft':[('readonly', False)]}),
        'transfer_date': fields.date('Transfer date' , required=True, readonly=True, states={'draft':[('readonly', False)]}),
        'delivery_date': fields.date('Delivery date', required=True, readonly=True, states={'draft':[('readonly', False)]}),
        'create_date': fields.date('Date', readonly=True),
        'motive': fields.text('Motive', required=True, readonly=True, states={'draft':[('readonly', False)]}),
        'motive_select':fields.selection([
            ('sale','Sale'),
            ('purchase','Purchase'),
            ('transformation','Transformation'),
            ('consignment','Consignment'),
            ('internal','Internal'),
            ('return','Return'),
            ('import','Import'),
            ('export','Export'),
            ('other','Other'),
             ],    'Motive Selection', select=True, readonly=False),
        'placa':fields.char('Placa', size=8, required=False, readonly=True, states={'draft':[('readonly', False)]}),
        'delivery_address': fields.many2one('res.partner.address', 'Address', readonly=True, states={'draft':[('readonly', False)]}),
        'number_import': fields.char('Number of import', size=20, states={'draft':[('readonly', False)]}),
        'authorizacion_id': fields.many2one('sri.authorization','Authorization', readonly=True, states={'draft':[('readonly', False)]}),
        'invoice_id': fields.many2one('account.invoice', 'Invoice', readonly=True, states={'draft':[('readonly', False)]}),
        'partner_id': fields.many2one('res.partner', 'Partner', readonly=True, states={'draft':[('readonly', False)]}),
        'stock_picking_id': fields.many2one('stock.picking', 'Picking', readonly=True, states={'draft':[('readonly', False)]}),
        'delivery_carrier': fields.many2one('delivery.carrier', 'Carrier', readonly=True, states={'draft':[('readonly', False)]}),
        'sale_order': fields.many2one('sale.order', 'Sale order'),
        'type':fields.selection([
            ('sales', 'Delivery for sale'),
            ('internal', 'Internal Delivery'),
            #('out', 'External Delivery'),
            ],  'type', readonly=True, states={'draft':[('readonly', False)]}),
        'remision_line': fields.one2many('account.remision.line', 'remision_id','Delivery note lines', readonly=True, states={'draft':[('readonly', False)]}),
        'state':fields.selection([
            ('draft','Draft'),
            ('waiting','Waiting'),
            ('done','Done'),
            ('canceled','Canceled'),
            ], 'state', required=True, readonly=True),
        'shop_id':fields.many2one('sale.shop', 'Shop', readonly=True, states={'draft':[('readonly',False)]}),
        'printer_id':fields.many2one('sri.printer.point', 'Printer Point', readonly=True, states={'draft':[('readonly',False)]}),
        'automatic':fields.boolean('Automatic', required=True),
        'company_id': fields.many2one('res.company', 'Company', required=True, change_default=True, readonly=True, states={'draft':[('readonly',False)]}),
    }
    
    _rec_name='number'
    
    _defaults = {
                 'state': lambda *a: 'draft',
                 'automatic': _get_automatic,
                 'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'account.remision', context=c),
                 }
    
    _sql_constraints = [('numbe_uniq','unique(number_out)', 'There is another delivery note generated with this number, please verify')]
    
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
    
    def action_confirm(self, cr, uid, ids, context=None):
        document_obj = self.pool.get('sri.type.document')
        for remision in self.browse(cr, uid, ids, context):
            if remision.type in ('sales', 'internal'):
                if not remision.automatic:
                    if not remision.number_out:
                        raise osv.except_osv(_('Invalid action!'), _('Not exist number for the document, please check'))
                    auth = self.pool.get('sri.authorization').get_auth(cr, uid, 'delivery_note', remision.company_id.id, remision.shop_id.id, remision.number_out, remision.printer_id.id, context)
                    if not auth['authorization']:
                        raise osv.except_osv(_('Invalid action!'), _('Do not exist authorization for this number of secuence, please check'))
                    doc_id = document_obj.search(cr, uid, [('name','=','delivery_note'),('printer_id','=',remision.printer_id.id),('shop_id','=',remision.shop_id.id),('sri_authorization_id','=',remision.authorizacion_id.id)])                                                
                    document_obj.add_document(cr, uid, doc_id, context)
                    self.write(cr, uid, [remision.id], {'state':'done'}, context)
                else:
                    if remision.number_out:
                        number = remision.number_out
                    auth = self.pool.get('sri.authorization').get_auth(cr, uid, 'delivery_note', remision.company_id.id, remision.shop_id.id, remision.number_out, remision.printer_id.id, context)
                    if not auth['authorization']:
                        raise osv.except_osv(_('Invalid action!'), _('Do not exist authorization for this number of secuence, please check'))
                    doc_id = document_obj.search(cr, uid, [('name','=','delivery_note'),('printer_id','=',remision.printer_id.id),('shop_id','=',remision.shop_id.id),('sri_authorization_id','=',remision.authorizacion_id.id)])                                                
                    document_obj.add_document(cr, uid, doc_id, context)
                    self.write(cr, uid, [remision.id], {'state':'done', 'number': number }, context)
            else:
                self.write(cr, uid, [remision.id], {'state':'done', 'number': remision.number_in }, context)
                    
    def action_cancel(self,cr,uid,ids,context=None):
        document_obj = self.pool.get('sri.type.document')
        remision = self.pool.get('account.remision').browse(cr, uid, ids, context)
        for rem in remision:
            if rem.state=='done':
                for doc in rem.authorizacion_id.type_document_ids:
                    if doc.name=='delivery_note':
                        document_obj.rest_document(cr, uid, [doc.id,])
            self.pool.get('account.remision').write(cr, uid, [rem.id, ], {'state':'canceled'}, context)
        return True
    
    def action_set_draft(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'draft'})
        return True
    
account_remision()

class account_remision_line(osv.osv):
    _name = 'account.remision.line'
    _columns = {
        'quantity': fields.float('Quantity', digits_compute=dp.get_precision('Account')),
        'product_id': fields.many2one('product.product', 'product'),
        'product_uom': fields.many2one('product.uom', 'Unit of Measure', ondelete='set null'),
        'prodlot_id': fields.many2one('stock.production.lot', 'Production Lot', states={'done': [('readonly', True)]}, select=True),
        'remision_id': fields.many2one('account.remision','Delivery note',ondelete='cascade')
    }
account_remision_line()

