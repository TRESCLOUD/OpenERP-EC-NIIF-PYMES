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
import netsvc
from osv import osv
from osv import fields
from tools.translate import _
import time
import psycopg2
import re
from lxml import etree
import decimal_precision as dp

class account_invoice(osv.osv):

    _inherit = "account.invoice"

    def _amount_all_2(self, cr, uid, ids, name, args, context=None):
        res = {}
        for invoice in self.browse(cr, uid, ids, context=context):
            res[invoice.id] = {
                'total_sin_descuento':0.0,
                'amount_untaxed': 0.0,
                'amount_tax': 0.0,
                'amount_total': 0.0,
                'total_retencion': 0.0,
                'total_iva': 0.0,
                'total_descuento': 0.0,
                'total_descuento_per': 0.0,
            }
            contador = 0;
            desc_per = 0.0
            for line in invoice.invoice_line:
                res[invoice.id]['amount_untaxed'] += line.price_subtotal
                res[invoice.id]['total_sin_descuento'] += line.price_unit * line.quantity
                res[invoice.id]['total_descuento'] += line.price_unit * line.quantity * line.discount * 0.01
                if line.discount != 0:
                    contador += 1
                    desc_per += line.discount
            for line in invoice.tax_line:
                res[invoice.id]['amount_tax'] += line.amount
                if line.amount > 0:
                    res[invoice.id]['total_iva'] += line.amount
                else:
                    res[invoice.id]['total_retencion'] += line.amount
            if contador != 0:
                res[invoice.id]['total_descuento_per'] = desc_per / contador
            res[invoice.id]['amount_total'] = res[invoice.id]['amount_tax'] + res[invoice.id]['amount_untaxed']
        return res

    def _get_invoice_tax(self, cr, uid, ids, context=None):
        result = {}
        for tax in self.pool.get('account.invoice.tax').browse(cr, uid, ids, context=context):
            result[tax.invoice_id.id] = True
        return result.keys()
    
    def _get_invoice_line(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('account.invoice.line').browse(cr, uid, ids, context=context):
            result[line.invoice_id.id] = True
        return result.keys()
    
    def _number(self, cr, uid, ids, name, args, context=None):
        result = {}
        for invoice in self.browse(cr, uid, ids, args):
            result[invoice.id] = invoice.invoice_number
        return result

    def onchange_data_in(self, cr, uid, ids, invoice_number=None, type="in_invoice", partner_id=None, date_invoice=None, context=None):
        if not context: context={}
        auth_types = {
                 'in_invoice': 'invoice',
                 'in_refund': 'credit_note',
                 'debit_note': 'debit_note',
                 }
        field_number_types = {
                 'in_invoice': 'invoice_number_in',
                 'in_refund': 'number_credit_note_in',
                 'debit_note': 'number_debit_note_in',
                 }
        field_auth_types = {
                 'in_invoice': 'authorization_supplier_purchase_id',
                 'in_refund': 'authorization_credit_note_purchase_id',
                 'debit_note': 'authorization_debit_note_purchase_id',
                 }
        values = {}
        domain = {}
        warning = {}
        auth_supplier_obj = self.pool.get('sri.authorization.supplier')
        if not date_invoice:
            date_invoice = time.strftime('%Y-%m-%d')
        if not invoice_number and partner_id and type:
            values = {
                     field_number_types[type] : ""
                     }
            warning = {
                       'title': _(u'Advertencia!!!'),
                       'message':_(u'Usted debe seleccionar primero la empresa para proceder con esta acción'),
                       }
            return {'value': values, 'domain':domain, 'warning': warning}
        auth_data = auth_supplier_obj.get_supplier_authorizations(cr, uid, invoice_number, auth_types[type], partner_id, date_invoice)
        if not auth_data.get('auth_ids', []):
            warning = {
                       'title': _(u'Advertencia!!!'),
                       'message':auth_data.get('message',''),
                       }
            return {'value': values, 'domain':domain, 'warning': warning}
        domain = {
                  field_auth_types[type]:[('id','in',auth_data.get('auth_ids', []))]
                  }
        if auth_data.get('multi_auth', False):
            values = {
                     field_number_types[type] : ""
                     }
            warning = {
                       'title': _(u'Advertencia!!!'),
                       'message':auth_data.get('message',''),
                       }
            return {'value': values, 'domain':domain, 'warning': warning}
        else:
            auth_id = auth_data.get('auth_ids', []) and auth_data.get('auth_ids', [])[0] or None
            if auth_id:
                values = {
                         field_number_types[type] : auth_data.get('res_number', ''),
                         field_auth_types[type]: auth_id,
                         }
            
        return {'value': values, 'domain':domain, 'warning': warning}

    
    def onchange_data(self, cr, uid, ids, automatic=False, company_id=None, shop_id=None, type=None, printer_id=None, date=None, context=None):
        printer_obj = self.pool.get('sri.printer.point')
        doc_obj=self.pool.get('sri.type.document')
        values = {}
        if context is None:
            context = {}
        if not company_id:
            company_id = self.pool.get('res.company')._company_default_get(cr, uid, 'account.invoice', context=context)
        manual = context.get('manual',False)
        shop_ids = []
        curr_user = False
        curr_shop = False
        if shop_id:
            curr_shop = self.pool.get('sale.shop').browse(cr, uid, [shop_id,], context)[0]
        curr_user = self.pool.get('res.users').browse(cr, uid, [uid, ], context)[0]
        if curr_user:
            for s in curr_user.shop_ids:
                shop_ids.append(s.id)
        if curr_shop:
            if type:
                if type == 'out_invoice':
                    values['journal_id'] = curr_shop.sales_journal_id.id
                    if printer_id:
                        auth_line_id = doc_obj.search(cr, uid, [('name','=','invoice'), ('printer_id','=',printer_id), ('shop_id','=',curr_shop.id), ('state','=',True)])
                        if auth_line_id:
                            values['authorization'] = doc_obj.browse(cr, uid, auth_line_id[0],context).sri_authorization_id.number
                            values['authorization_sales'] = doc_obj.browse(cr, uid, auth_line_id[0],context).sri_authorization_id.id
                            if automatic:
                                values['automatic_number'] = doc_obj.get_next_value_secuence(cr, uid, 'invoice', False, company_id, curr_shop.id, printer_id, 'account.invoice', 'invoice_number_out', context)
                                values['invoice_number_out'] = values['automatic_number']
                                values['date_invoice'] = time.strftime('%Y-%m-%d')
                            else:
                                values['invoice_number_out'] = curr_shop.number + "-" + printer_obj.browse(cr, uid, printer_id, context).number + "-"
                        else:
                            values['authorization'] = None
                            values['authorization_sales'] = None
                            values['automatic'] = False
                            values['date_invoice'] = None
        return {'value': values, 'domain':{'shop_id':[('id','in', shop_ids)]}}
    
    def _get_shop(self, cr, uid, ids, context=None):
        curr_user = self.pool.get('res.users').browse(cr, uid, [uid, ], context)[0]
        shop_id = None
        if curr_user:
            if not curr_user.shop_ids:
                if uid != 1:
                    raise osv.except_osv('Error!', _("Your User doesn't have shops assigned"))
            for shop in curr_user.shop_ids:
                shop_id = shop.id
                continue
        return shop_id
    
    def _get_printer(self, cr, uid, ids, context=None):
        curr_user = self.pool.get('res.users').browse(cr, uid, [uid, ], context)[0]
        printer_id = None
        if curr_user:
            if not curr_user.shop_ids:
                if uid != 1:
                    raise osv.except_osv('Error!', _("Your User doesn't have shops assigned"))
            for shop in curr_user.shop_ids:
                printer_id = shop.printer_point_ids[0].id
                continue
        return printer_id

    def copy(self, cr, uid, id, default={}, context=None):
        inv_obj = self.pool.get('account.invoice')
        doc_obj=self.pool.get('sri.type.document')
        original_invoice = inv_obj.browse(cr, uid, id, context)
        new_number = False
        autorization_number = False
        authorization_id = False
        if original_invoice:
            if original_invoice.shop_id:
                if original_invoice.printer_id:
                    if original_invoice.company_id:
                        if original_invoice.type == "out_invoice":
                            new_number = doc_obj.get_next_value_secuence(cr, uid, 'invoice', False, original_invoice.company_id.id, original_invoice.shop_id.id, original_invoice.printer_id.id, 'account.invoice', 'invoice_number_out', context)
                            authorization_id = original_invoice.authorization_sales.id
                            autorization_number = original_invoice.authorization_sales.number
        if context is None:
            context = {}
        default.update({
            'state':'draft',
            'number':False,
            'move_id':False,
            'move_name':False,
            'internal_number': False,
            'invoice_number_in': False,
            'automatic_number': new_number,
            'invoice_number_out': new_number,
            'invoice_number': False,
            'authorization_purchase': False,
            'authorization_sales': authorization_id,
            'authorization': autorization_number,
        })
        if 'date_invoice' not in default:
            default.update({
                'date_invoice':False
            })
        if 'date_due' not in default:
            default.update({
                'date_due':False
            })
        return super(account_invoice, self).copy(cr, uid, id, default, context)


    def onchange_authorization_supplier(self, cr, uid, ids, authorization, number, context=None):
        if not context:
            context={}
        value = {}
        domain = {}
        if authorization:
            auth = self.pool.get('sri.authorization.supplier').browse(cr, uid, authorization, context)
            number = auth and auth.agency + "-" + auth.printer_point+"-"
            value['invoice_number_in'] = number or ''
        return {'value': value, 'domain': domain }

    def fields_view_get(self, cr, uid, view_id=None, view_type=False, context=None, toolbar=False, submenu=False):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        res = super(account_invoice,self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
        type = context.get('type', 'out_invoice')
        client = context.get('client','gtk')
        liquidation = context.get('liquidation',False)
        if view_type == 'search':
            doc = etree.XML(res['arch'])
            for field in res['fields']:
                if field == 'number':
                    nodes = doc.xpath("//field[@name='number']")
                    for node in nodes:
                        node.set('invisible', type and not liquidation and "1" or "0")
                        if type and client == 'web' and not liquidation:
                            node.getparent().remove(node)
                if field == 'invoice_number_out':
                    nodes = doc.xpath("//field[@name='invoice_number_out']")
                    for node in nodes:
                        node.set('invisible', type == 'out_invoice' and "0" or "1")
                        if type != 'out_invoice' and client == 'web':
                            node.getparent().remove(node)
                if field == 'invoice_number_in':
                    nodes = doc.xpath("//field[@name='invoice_number_in']")
                    for node in nodes:
                        node.set('invisible', type == 'in_invoice' and not liquidation and "0" or "1")
                        if type != 'in_invoice' and client == 'web' and not liquidation:
                            node.getparent().remove(node)
            res['arch'] = etree.tostring(doc)
        if view_type == 'tree':
            for field in res['fields']:
                if type == 'out_invoice':
                    if field == 'number':
                        doc = etree.XML(res['arch'])
                        nodes = doc.xpath("//field[@name='number']")
                        for node in nodes:
                            node.set('invisible', "1")
                        res['arch'] = etree.tostring(doc)
                    if field == 'invoice_number_out':
                        doc = etree.XML(res['arch'])
                        nodes = doc.xpath("//field[@name='invoice_number_out']")
                        for node in nodes:
                            node.set('invisible', "0")
                        res['arch'] = etree.tostring(doc)
                    if field == 'invoice_number_in':
                        doc = etree.XML(res['arch'])
                        nodes = doc.xpath("//field[@name='invoice_number_in']")
                        for node in nodes:
                            node.set('invisible', "1")
                        res['arch'] = etree.tostring(doc)
                else:
                    if type == 'in_invoice':
                        if field == 'number':
                            doc = etree.XML(res['arch'])
                            nodes = doc.xpath("//field[@name='number']")
                            for node in nodes:
                                node.set('invisible', "1")
                            res['arch'] = etree.tostring(doc)
                        if field == 'invoice_number_out':
                            doc = etree.XML(res['arch'])
                            nodes = doc.xpath("//field[@name='invoice_number_out']")
                            for node in nodes:
                                node.set('invisible', "1")
                            res['arch'] = etree.tostring(doc)
                        if field == 'invoice_number_in':
                            doc = etree.XML(res['arch'])
                            nodes = doc.xpath("//field[@name='invoice_number_in']")
                            for node in nodes:
                                node.set('invisible', "0")
                            res['arch'] = etree.tostring(doc)
                    else:
                        if field == 'number':
                            doc = etree.XML(res['arch'])
                            nodes = doc.xpath("//field[@name='number']")
                            for node in nodes:
                                node.set('invisible', "0")
                            res['arch'] = etree.tostring(doc)
                        if field == 'invoice_number_out':
                            doc = etree.XML(res['arch'])
                            nodes = doc.xpath("//field[@name='invoice_number_out']")
                            for node in nodes:
                                node.set('invisible', "1")
                            res['arch'] = etree.tostring(doc)
                        if field == 'invoice_number_in':
                            doc = etree.XML(res['arch'])
                            nodes = doc.xpath("//field[@name='invoice_number_in']")
                            for node in nodes:
                                node.set('invisible', "1")
                            res['arch'] = etree.tostring(doc)
                    
        if view_type == 'form':
            for field in res['fields']:
                if user.company_id.generate_automatic:
                    if field == 'automatic_number':
                        doc = etree.XML(res['arch'])
                        nodes = doc.xpath("//field[@name='automatic_number']")
                        for node in nodes:
                            node.set('invisible', "0")
                        res['arch'] = etree.tostring(doc)
                    if field == 'invoice_number_out':
                        doc = etree.XML(res['arch'])
                        nodes = doc.xpath("//field[@name='invoice_number_out']")
                        for node in nodes:
                            node.set('invisible', "1")
                        res['arch'] = etree.tostring(doc)
                else:
                    if field == 'automatic_number':
                        doc = etree.XML(res['arch'])
                        nodes = doc.xpath("//field[@name='automatic_number']")
                        for node in nodes:
                            node.set('invisible', "1")
                        res['arch'] = etree.tostring(doc)
                    if field == 'invoice_number_out':
                        doc = etree.XML(res['arch'])
                        nodes = doc.xpath("//field[@name='invoice_number_out']")
                        for node in nodes:
                            node.set('invisible', "0")
                        res['arch'] = etree.tostring(doc)
        return res
    
    def _get_automatic(self, cr, uid, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid, context)
        return user.company_id.generate_automatic
    
    def create(self, cr, uid, vals, context=None):
        auth_obj = self.pool.get('sri.authorization')
        doc_obj=self.pool.get('sri.type.document')
        company_id = vals.get('company_id', False)
        if not context:
            context = {}
        if vals.get('invoice_number_out', False):
            if context.get('type', False) == 'out_invoice':
                number_out = vals.get('invoice_number_out', False)
                company_id = vals.get('company_id', False)
                doc_obj.validate_unique_value_document(cr, uid, number_out, company_id, 'account.invoice', 'invoice_number_out', 'Factura', context)
                vals['automatic_number'] = vals.get('invoice_number_out', False)
                if vals.get('authorization_sales', False):
                    vals['authorization'] = auth_obj.browse(cr, uid, vals['authorization_sales'], context).number
        res = super(account_invoice, self).create(cr, uid, vals, context)
        return res
    
    def write(self, cr, uid, ids, vals, context=None):
        doc_obj = self.pool.get('sri.type.document')
        inv_obj = self.pool.get('account.invoice')
        if not context:
            context={}
        for invoice in inv_obj.browse(cr, uid, ids, context):
            if vals.get('invoice_number_out', False):
                if context.get('type', False) == 'out_invoice':
                    number_out = vals.get('invoice_number_out', False)
                    company_id = vals.get('company_id', False)
                    if not company_id:
                        company_id = invoice.company_id.id
                    doc_obj.validate_unique_value_document(cr, uid, number_out, company_id, 'account.invoice', 'invoice_number_out', 'Factura', context)
        res = super(account_invoice, self).write(cr, uid, ids, vals, context)
        return res 
     
    def button_reset_taxes(self, cr, uid, ids, context=None):
        for inv in self.browse(cr, uid, ids, context):
            if inv.type == "out_invoice":
                vals = {'automatic_number':inv.invoice_number_out}
                if inv.authorization_sales:
                    vals['authorization'] = inv.authorization_sales.number
                self.write(cr, uid, [inv.id], vals)
        return super(account_invoice, self).button_reset_taxes(cr, uid, ids, context)
        
    _columns = {
                'automatic_number': fields.char('Number', size=17, readonly=True,),
                'create_date': fields.date('Creation date', readonly=True),
                'authorization_sales':fields.many2one('sri.authorization', 'Authorization', required=False),
                'authorization':fields.char('Authorization', size=10, readonly=True),
                'authorization_supplier_purchase_id':fields.many2one('sri.authorization.supplier', 'Authorization', readonly=True, states={'draft':[('readonly',False)]}), 
                'authorization_purchase':fields.char('Authorization', size = 10, required=False, readonly=True, states={'draft':[('readonly',False)]}, help='This Number is necesary for SRI reports'),
                'number': fields.function(_number, method=True, type='char', size=17, string='Invoice Number', store=True, help='Unique number of the invoice, computed automatically when the invoice is created in Sales.'),
                'invoice_number': fields.char('Invoice Number', size=17, readonly=True, help="Unique number of the invoice, computed automatically when the invoice is created."),
                'invoice_number_in': fields.char('Invoice Number', size=17, required=False, readonly=True, states={'draft':[('readonly',False)]}, help="Unique number of the invoice."),
                'invoice_number_out': fields.char('Invoice Number', size=17, required=False, readonly=True, states={'draft':[('readonly',False)]}, help="Unique number of the invoice."),
                'prints_number': fields.integer('Prints Number', help = "You can't reprint a invoice twice or more times"),
                'automatic':fields.boolean('Automatic?',),
                'flag':fields.boolean('Flag',),
                'shop_id':fields.many2one('sale.shop', 'Shop', readonly=True, states={'draft':[('readonly',False)]}),
                'printer_id':fields.many2one('sri.printer.point', 'Printer Point', readonly=True, states={'draft':[('readonly',False)]}),
                'total_retencion': fields.function(_amount_all_2, method=True, digits_compute=dp.get_precision('Account'), string='Total Retenido',
                    store={
                        'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
                        'account.invoice.tax': (_get_invoice_tax, None, 20),
                        'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 20),
                    },
                    multi='all1'),
                'total_iva': fields.function(_amount_all_2, method=True, digits_compute=dp.get_precision('Account'), string='Total IVA',
                    store={
                        'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
                        'account.invoice.tax': (_get_invoice_tax, None, 20),
                        'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 20),
                    },
                    multi='all1'),                
                'total_descuento': fields.function(_amount_all_2, method=True, digits_compute=dp.get_precision('Account'), string='Descuento Total',
                    store={
                        'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
                        'account.invoice.tax': (_get_invoice_tax, None, 20),
                        'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 20),
                    },
                    multi='all1'),
                'total_descuento_per': fields.function(_amount_all_2, method=True, digits_compute=dp.get_precision('Account'), string='Total',
                    store={
                        'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
                        'account.invoice.tax': (_get_invoice_tax, None, 20),
                        'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 20),
                    },
                    multi='all1'),  
                'total_sin_descuento': fields.function(_amount_all_2, method=True, digits_compute=dp.get_precision('Account'), string='Sub Total',
                    store={
                        'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
                        'account.invoice.tax': (_get_invoice_tax, None, 20),
                        'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 20),
                    },
                    multi='all1'),
                'foreign': fields.related('partner_id','foreing', type='boolean', relation='res.partner', string='Foreing?'),
                
               }
    
    _defaults = {
                 'shop_id':_get_shop,
                 'printer_id': _get_printer,
                 'prints_number': lambda *a: 0,
                 'automatic': _get_automatic,
                 'flag': lambda *a: False,
                 }

    def action_number(self, cr, uid, ids, context=None):
        if not context:
            context = {}
        inv_obj = self.pool.get('account.invoice')
        auth_s_obj = self.pool.get('sri.authorization.supplier')
        document_obj = self.pool.get('sri.type.document')
        for invoice in self.browse(cr, uid, ids, context):
            context['automatic'] = invoice.automatic
            if not invoice.partner_id.foreing and not invoice.partner_id.ref:
                raise osv.except_osv(_('Error!'), _("Partner %s doesn't have CEDULA/RUC, you must input for validate.") % invoice.partner_id.name)
            if invoice.type=='out_invoice':
                if not invoice.authorization_sales:
                    raise osv.except_osv(_('Invalid action!'), _('Not exist authorization for the document, please check'))
                if not invoice.automatic:
                    if not invoice.invoice_number_out:
                        raise osv.except_osv(_('Invalid action!'), _('Not exist number for the document, please check'))
                    shop = invoice.shop_id.id
                    auth = self.pool.get('sri.authorization').get_auth(cr, uid, 'invoice', invoice.company_id.id, shop, invoice.invoice_number_out, invoice.printer_id.id, context)
                    if not auth['authorization']:
                        raise osv.except_osv(_('Invalid action!'), _('Do not exist authorization for this number of secuence, please check'))
                    doc_id = document_obj.search(cr, uid, [('name','=','invoice'),('printer_id','=',invoice.printer_id.id),('shop_id','=',invoice.shop_id.id),('sri_authorization_id','=',invoice.authorization_sales.id)])
                    document_obj.add_document(cr, uid, doc_id, context)
                    self.write(cr, uid, [invoice.id], {'invoice_number': invoice.invoice_number_out, 'flag': True, 'authorization':invoice.authorization_sales.number}, context)
                else:
                    if not invoice.invoice_number_out:
                        b = True
                        vals_aut = self.pool.get('sri.authorization').get_auth_secuence(cr, uid, 'invoice', invoice.company_id.id, invoice.shop_id.id, invoice.printer_id.id)
                        while b :
                            number_out = self.pool.get('ir.sequence').get_id(cr, uid, vals_aut['sequence'])
                            if not self.pool.get('account.invoice').search(cr, uid, [('type','=','out_invoice'),('invoice_number','=',number_out), ('automatic','=',True),('id','not in',tuple(ids))],):
                                b=False
                    else:
                        number_out = invoice.invoice_number_out
                    doc_id = document_obj.search(cr, uid, [('name','=','invoice'),('printer_id','=',invoice.printer_id.id),('shop_id','=',invoice.shop_id.id),('sri_authorization_id','=',invoice.authorization_sales.id)])                            
                    document_obj.add_document(cr, uid, doc_id, context)
                    self.write(cr, uid, [invoice.id], {'invoice_number': number_out,'invoice_number_out': number_out,'automatic_number': number_out, 'flag': True, 'authorization':invoice.authorization_sales.number}, context)
            elif invoice.type=='in_invoice':
                if invoice.invoice_number_in:
                    auth_s_obj.check_number_document(cr, uid, invoice.invoice_number_in, invoice.authorization_supplier_purchase_id, invoice.date_invoice, 'account.invoice', 'invoice_number_in', _('Invoice'), context, invoice.id, invoice.foreign)
                    if not invoice.foreign:
                        self.write(cr, uid, [invoice.id], {'invoice_number': invoice.invoice_number_in,'authorization_purchase': invoice.authorization_supplier_purchase_id.number}, context)
                    else:
                        self.write(cr, uid, [invoice.id], {'invoice_number': invoice.invoice_number_in}, context)
        result = super(account_invoice, self).action_number(cr, uid, ids, context)
        self.write(cr, uid, ids, {'internal_number': False,}, context)
        return result
    
    def action_cancel_draft(self, cr, uid, ids, *args):
        document_obj = self.pool.get('sri.type.document')
        for invoice in self.browse(cr, uid, ids):
            if invoice.type=='out_invoice':
                if invoice.flag:
                    for doc in invoice.authorization_sales.type_document_ids:
                        if doc.name=='invoice':
                            document_obj.rest_document(cr, uid, [doc.id,])
                    self.write(cr, uid, [invoice.id], {'flag': False}, context=None)
            return super(account_invoice, self).action_cancel_draft(cr, uid, ids)

    def split_invoice(self, cr, uid, ids):
        '''
        Split the invoice when the lines exceed the maximum set for the company
        '''
        for inv in self.browse(cr, uid, ids):
            inv_id =False
            if inv.type in ["out_invoice","out_refund"]:
                if len(inv.invoice_line)> inv.company_id.lines_invoice:
                    lst = []
                    invoice = self.read(cr, uid, inv.id, ['name', 'type', 'number', 'reference', 'comment', 'date_due', 'partner_id', 'address_contact_id', 'address_invoice_id', 'partner_contact', 'partner_insite', 'partner_ref', 'payment_term', 'account_id', 'currency_id', 'invoice_line', 'tax_line', 'journal_id', 'period_id'])
                    invoice.update({
                        'state': 'draft',
                        'number': False,
                        'invoice_line': [],
                        'tax_line': []
                    })
                    # take the id part of the tuple returned for many2one fields
                    for field in ('address_contact_id', 'address_invoice_id', 'partner_id',
                            'account_id', 'currency_id', 'payment_term', 'journal_id', 'period_id'):
                        invoice[field] = invoice[field] and invoice[field][0]

                    inv_id = self.create(cr, uid, invoice)
                    cont = 0
                    lst = inv.invoice_line
                    while cont < inv.company_id.lines_invoice:
                        lst.pop(0)
                        cont += 1
                    for il in lst:
                        self.pool.get('account.invoice.line').write(cr,uid,il.id,{'invoice_id':inv_id})
                    self.button_compute(cr, uid, [inv.id], set_total=True)
        
            if inv_id:
                wf_service = netsvc.LocalService("workflow")
                self.button_compute(cr, uid, [inv_id], set_total=True)
#                wf_service.trg_validate(uid, 'account.invoice', inv_id, 'invoice_open', cr)
        return True
    
    def action_date_assign(self, cr, uid, ids, *args):
        auth_obj = self.pool.get('sri.authorization')
        date=False
#        self.split_invoice(cr,uid,ids)
        res = super(account_invoice, self).action_date_assign(cr, uid, ids, args)
        for inv in self.browse(cr, uid, ids):
            if inv.type=='out_invoice':
                if not auth_obj.check_date_document(cr, uid, inv.date_invoice or time.strftime('%Y-%m-%d'), inv.authorization_sales.start_date, inv.authorization_sales.expiration_date):
                   raise osv.except_osv(_('Invalid action!'), _('The date entered is not valid for the authorization')) 
        return res
    
    def onchange_number(self, cr, uid, ids, number, automatic, company, shop=None, printer_id=None, context=None):
        result = {}
        if context is None:
            context = {}
        if shop==None:
            shop = self.pool.get('sale.shop').search(cr, uid,[])[0]
        if not number:
            return {'value': {'invoice_number_out': ''}}
        if not automatic:
            auth = self.pool.get('sri.authorization').get_auth(cr, uid, 'invoice', company, shop, number, printer_id, context)
            if not auth['authorization']:
                raise osv.except_osv(_('Invalid action!'), _('Do not exist authorization for this number of secuence, please check!'))
            result['authorization_sales'] = auth['authorization']
        res_final = {'value':result}
        return res_final
    
    def _check_number_invoice(self,cr,uid,ids):
        res = True
        for invoice in self.browse(cr, uid, ids):
            cadena='(\d{3})+\-(\d{3})+\-(\d{9})'
            ref = invoice.invoice_number_out
            if invoice.invoice_number_out:
                if re.match(cadena, ref):
                    res = True
                else:
                    res = False
            cadena='(\d{3})+\-(\d{3})+\-(\d{1,9})'
            ref = invoice.invoice_number_in
            if invoice.invoice_number_in and not invoice.foreign:
                if re.match(cadena, ref):
                    res = True
                else:
                    res = False
            return res
    
    def unlink(self, cr, uid, ids, context=None):
        invoices = self.read(cr, uid, ids, ['state'], context=context)
        unlink_ids = []
        for inv in invoices:
            if inv['state'] == 'draft':
                unlink_ids.append(inv['id'])
            else:
                raise osv.except_osv(_('Invalid action!'), _('You can delete Invoice in state Draft'))
        return super(account_invoice, self).unlink(cr, uid, unlink_ids, context)


    _constraints = [(_check_number_invoice,_('The number of Invoice is incorrect, it must be like 00X-00X-000XXXXXX, X is a number'),['invoice_number_out','invoice_number_in'])]
    
    def default_get(self, cr, uid, fields_list, context=None):
        """
        Returns default values for fields
        @param fields_list: list of fields, for which default values are required to be read
        @param context: context arguments, like lang, time zone

        @return: Returns a dict that contains default values for fields
        """
        if context is None:
            context = {}
        printer_obj = self.pool.get('sri.printer.point')
        doc_obj=self.pool.get('sri.type.document')
        values = super(account_invoice, self).default_get(cr, uid, fields_list, context=context)
        if not values:
            values={}
        shop_id = values.get('shop_id', False)
        printer_id = values.get('printer_id', False)
        company_id = values.get('company_id', False)
        automatic = values.get('automatic', False)
        type = values.get('type', False)
        if not company_id:
            company_id = self.pool.get('res.company')._company_default_get(cr, uid, 'account.invoice', context=context)
        manual = context.get('manual',False)
        shop_ids = []
        curr_user = False
        curr_shop = False
        if shop_id:
            curr_shop = self.pool.get('sale.shop').browse(cr, uid, [shop_id,], context)[0]
        curr_user = self.pool.get('res.users').browse(cr, uid, [uid, ], context)[0]
        if curr_user:
            for s in curr_user.shop_ids:
                shop_ids.append(s.id)
        if curr_shop:
            if type:
                if type == 'out_invoice' and ('invoice_number_out', 'automatic_number') in fields_list:
                    values['journal_id'] = curr_shop.sales_journal_id.id
                    if printer_id:
                        auth_line_id = doc_obj.search(cr, uid, [('name','=','invoice'), ('printer_id','=',printer_id), ('shop_id','=',curr_shop.id), ('state','=',True)])
                        if auth_line_id:
                            values['authorization'] = doc_obj.browse(cr, uid, auth_line_id[0],context).sri_authorization_id.number
                            values['authorization_sales'] = doc_obj.browse(cr, uid, auth_line_id[0],context).sri_authorization_id.id
                            if automatic:
                                values['automatic_number'] = doc_obj.get_next_value_secuence(cr, uid, 'invoice', False, company_id, curr_shop.id, printer_id, 'account.invoice', 'invoice_number_out', context)
                                values['invoice_number_out'] = values['automatic_number']
                                values['date_invoice'] = time.strftime('%Y-%m-%d')
                        else:
                            values['authorization'] = None
                            values['authorization_sales'] = None
                            values['automatic'] = False
                            values['date_invoice'] = None
        return values

    def onchange_partner_id(self, cr, uid, ids, type, partner_id, date_invoice=False, payment_term=False, partner_bank_id=False, company_id=False):
        partner_obj = self.pool.get('res.partner')
        res = super(account_invoice, self).onchange_partner_id(cr, uid, ids, type, partner_id, date_invoice, payment_term, partner_bank_id, company_id)
        foreing = False
        if partner_id:
            partner = partner_obj.browse(cr, uid, partner_id)
            foreing = partner and partner.foreing or False
        res['value']['foreign'] = foreing
        return res
    
account_invoice()