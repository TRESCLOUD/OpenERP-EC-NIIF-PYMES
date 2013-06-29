# -*- coding: UTF-8 -*- #
#########################################################################
# Copyright (C) 2012  Christopher Ormaza                                #
# Ecuadorenlinea.net                                                    #
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

import time
import datetime
from dateutil.relativedelta import relativedelta
from os.path import join as opj
from operator import itemgetter

from tools.translate import _
from osv import fields, osv
import netsvc
import tools

class auth_wizard(osv.osv_memory):
    
    def _default_company(self, cr, uid, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        return user.company_id and user.company_id.id or False
    
    _name = 'auth.wizard'
    _columns = {
                'auto_printer':fields.boolean('Auto Printer?',), 
                'number':fields.char('Authorization Number', size=37, required=True, readonly=False),
                'start_date': fields.date('Start Date'),
                'expiration_date': fields.date('Expiration Date'),
                'company_id': fields.many2one('res.company', 'Company', required=True),
                'type_document_wizard_ids':fields.one2many('auth.wizard.line', 'auth_wizard_id', 'Document Description', required=True),
               }
    
    _defaults={'company_id':_default_company,
               'auto_printer': lambda *a: False
               }
    
    def crear_sufijo(self, cadena):
        entero = int(cadena)
        retorno = ""
        if entero < 10:
            retorno = "00" + str(entero)
        elif entero < 100:
            retorno = "0" + str(entero)
        else:
            retorno = str(entero)
        return retorno
    
    def button_execute(self, cr, uid, ids, context=None):
        dtw_obj = self.pool.get('auth.wizard.line')
        seq_obj = self.pool.get('ir.sequence')
        comp_obj = self.pool.get('res.company')
        journal_obj = self.pool.get('account.journal')
        aut_obj = self.pool.get('sri.authorization')
        dt_obj = self.pool.get('sri.type.document')
        shop_obj = self.pool.get('sale.shop')
        printer_obj = self.pool.get('sri.printer.point')
        
        for res in self.browse(cr, uid, ids, context=context):
            if not res.type_document_wizard_ids:
                raise osv.except_osv(_(u'You must input almost one type of document to continue'))
            if not aut_obj.search(cr, uid, [('number','=',res['number']),]):
                #create authorization
                vals_aut={'number':res['number'],
                          'start_date':res['start_date'],
                          'expiration_date':res['expiration_date'],
                          'company_id':res['company_id']['id'],
                          'auto_printer': res['auto_printer']
                          }
                aut_id = aut_obj.create(cr, uid, vals_aut, context=context)                
                #assing authorization to company
                agency = 1
                for dt in res['type_document_wizard_ids']:
                    code= ''
                    #verify the number of agency or shop
                    shop = shop_obj.read(cr, uid, dt['shop_id']['id'], context=context)
                    if not shop['number']:
                        vals_shop={'number':self.crear_sufijo(agency)
                                   }
                        shop_obj.write(cr, uid, [shop['id']] ,vals_shop, context=context)
                        agency=agency+1
                    printer = printer_obj.read(cr, uid, dt['printer_id']['id'], context=context)
                    if not printer['number']:
                        number_print=0
                        for shop in shop_obj.browse(cr, uid, [dt.shop_id.id,], context):
                            if shop.printer_point_ids:
                                for printer_point in shop.printer_point_ids:
                                    if printer_point.number:
                                        if int(printer_point.number) > number_print:
                                            number_print = int(printer_point.number)
                        vals_printer={'number':self.crear_sufijo(number_print+1)
                                   }
                        printer_obj.write(cr, uid, [printer['id']] ,vals_printer, context=context)
                        
                    if dt['name']=='invoice':
                        if not dt['shop_id']['sales_journal_id']:
                            raise osv.except_osv(_('Error!!'), _('You must asign a Sales Journal for de shop %s') % dt['shop_id']['name'])
                        code= 'account.invoice.out_invoice'
                    elif dt['name']=='withholding':
                        code= 'ret_seq'
                    elif dt['name']=='delivery_note':
                        code= 'rem_seq'
                    elif dt['name']=='liquidation':
                        if not dt['shop_id']['liquidation_journal_id']:
                            raise osv.except_osv(_('Error!!'), _('You must asign a Liquidation of Purchases Journal for de shop %s') % dt['shop_id']['name'])
                        code= 'liq_seq'
                    elif dt['name']=='credit_note':
                        if not dt['shop_id']['credit_note_purchase_journal_id']:
                            raise osv.except_osv(_('Error!!'), _('You must asign a Credit Note Purchases Journal for shop %s') % dt['shop_id']['name'])
                        if not dt['shop_id']['credit_note_sale_journal_id']:
                            raise osv.except_osv(_('Error!!'), _('You must asign a Credit Note Sales Journal for shop %s') % dt['shop_id']['name'])
                        code= 'account.invoice.out_refund'
                    elif dt['name']=='debit_note':
                        if not dt['shop_id']['debit_note_journal_id']:
                            raise osv.except_osv(_('Error!!'), _('You must asign a Sales Journal for shop %s') % dt['shop_id']['name'])
                        code= 'deb_seq'
                        
                    cadena = shop_obj.read(cr, uid, dt['shop_id']['id'], context=context)['number'] + '-' + printer_obj.read(cr, uid, dt['printer_id']['id'], context=context)['number'] + "-"
                    vals_seq = {
                        'name': 'Diario de '+ dt['name'] + ' - '+ res['number'],
                        'code': code,
                        'prefix': cadena,
                        'company_id': res['company_id']['id'],
                        'padding': 9,
                        'number_next': dt['first_secuence'],
                        'number_increment':1
                        }
                    seq_id = seq_obj.create(cr, uid, vals_seq, context=context)
                    #create object for reports
                    vals_doc_type={
                                  'name':dt['name'],
                                  'first_secuence': dt['first_secuence'],
                                  'last_secuence': dt['last_secuence'],
                                  'shop_id':dt['shop_id']['id'],
                                  'printer_id':dt['printer_id']['id'],
                                  'sri_authorization_id':aut_id,
                                  'sequence_id':seq_id,
                                  'padding': dt.padding,
                                  'automatic':dt['automatic'],
                                  'expired':dt['expired']
                                  }
                    #print vals_doc_type
                    id = dt_obj.create(cr, uid, vals_doc_type, context=context)
                    dt_obj.write(cr, uid, id ,{}, context=context)
                    #aut_obj.write(cr, uid, aut_id ,{}, context=context)
            else:
                #obtengo la id de la autorizacion existente para agregarle las lineas de autorizacion
                aut_id = aut_obj.search(cr, uid, [('number','=',res['number']),])[0]
                #assing authorization to company
                agency = 1
                for dt in res['type_document_wizard_ids']:
                    code= ''
                    #verify the number of agency or shop
                    shop = shop_obj.read(cr, uid, dt['shop_id']['id'], context=context)
                    if not shop['number']:
                        vals_shop={'number':self.crear_sufijo(agency)
                                   }
                        shop_obj.write(cr, uid, [shop['id']] ,vals_shop, context=context)
                        agency=agency+1
                        
                    printer = printer_obj.read(cr, uid, dt['printer_id']['id'], context=context)
                    if not printer['number']:
                        number_print=0
                        for shop in shop_obj.browse(cr, uid, [dt.shop_id.id,], context):
                            if shop.printer_point_ids:
                                for printer_point in shop.printer_point_ids:
                                    if printer_point.number:
                                        if int(printer_point.number) > number_print:
                                            number_print = int(printer_point.number)
                        vals_printer={'number':self.crear_sufijo(number_print+1)
                                   }
                        printer_obj.write(cr, uid, [printer['id']] ,vals_printer, context=context)
                        if dt['name']=='invoice':
                            if not dt['shop_id']['sales_journal_id']:
                                raise osv.except_osv(_('Error!!'), _('You must asign a Sales Journal for de shop %s') % dt['shop_id']['name'])
                            code= 'account.invoice.out_invoice'
                        elif dt['name']=='withholding':
                            code= 'ret_seq'
                        elif dt['name']=='delivery_note':
                            code= 'rem_seq'
                        elif dt['name']=='liquidation':
                            if not dt['shop_id']['liquidation_journal_id']:
                                raise osv.except_osv(_('Error!!'), _('You must asign a Liquidation of Purchases Journal for de shop %s') % dt['shop_id']['name'])
                            code= 'liq_seq'
                        elif dt['name']=='credit_note':
                            if not dt['shop_id']['credit_note_purchase_journal_id']:
                                raise osv.except_osv(_('Error!!'), _('You must asign a Credit Note Purchases Journal for shop %s') % dt['shop_id']['name'])
                            if not dt['shop_id']['credit_note_sale_journal_id']:
                                raise osv.except_osv(_('Error!!'), _('You must asign a Credit Note Sales Journal for shop %s') % dt['shop_id']['name'])
                            code= 'account.invoice.out_refund'
                        elif dt['name']=='debit_note':
                            if not dt['shop_id']['debit_note_journal_id']:
                                raise osv.except_osv(_('Error!!'), _('You must asign a Sales Journal for de shop %s') % dt['shop_id']['name'])
                            code= 'deb_seq'
                    
                    cadena = shop_obj.read(cr, uid, dt['shop_id']['id'], context=context)['number'] + '-' + printer_obj.read(cr, uid, dt['printer_id']['id'], context=context)['number']+"-"
                    vals_seq = {
                        'name': 'Diario de '+ dt['name'] + ' - '+ res['number'],
                        'code': code,
                        'prefix': cadena,
                        'company_id': res['company_id']['id'],
                        'padding': 9,
                        'number_next': dt['first_secuence'],
                        'number_increment':1
                        }
                    seq_id = seq_obj.create(cr, uid, vals_seq, context=context)
                    #create object for reports
                    vals_doc_type={
                                  'name':dt['name'],
                                  'first_secuence': dt['first_secuence'],
                                  'last_secuence': dt['last_secuence'],
                                  'printer_id':dt['printer_id']['id'],
                                  'shop_id':dt['shop_id']['id'],
                                  'sri_authorization_id':aut_id,
                                  'sequence_id':seq_id,
                                  'padding': dt.padding,
                                  'automatic':dt['automatic'],
                                  'expired':dt['expired']
                                  }
                    id = dt_obj.create(cr, uid, vals_doc_type, context=context)
                    dt_obj.write(cr, uid, id ,{}, context=context)
                    #aut_obj.write(cr, uid, aut_id ,{}, context=context)
        return {'type':'ir.actions.act_window_close' }
    
auth_wizard()

class auth_wizard_line(osv.osv_memory):
    
    def _get_name(self, cr, uid, context=None):
        output = []
        module_ids = self.pool.get('ir.module.module').search(cr, uid, [('name','like','ecua')])
        module = self.pool.get('ir.module.module').browse(cr, uid, module_ids, context)
        for mod in module:
            if mod['state']=='installed':
                if mod['name'] == 'ecua_facturas_manual':
                    output.append(('invoice',_('Invoice')))
                if mod['name']== 'ecua_remision':
                    output.append(('delivery_note',_('Delivery note')))
                if mod['name'] == 'ecua_retenciones_manual':
                    output.append(('withholding',_('Withholding')))
                if mod['name']== 'ecua_liquidacion_compras':
                    output.append(('liquidation',_('Liquidation of Purchases')))
                if mod['name']== 'ecua_notas_credito_manual':
                    output.append(('credit_note',_('Credit Note')))
                if mod['name']== 'ecua_notas_debito_manual':
                    output.append(('debit_note',_('Debit Note')))
        return output
    
    def onchange_name(self, cr, uid, ids, name, shop, printer, automatic, context=None):
        result = {}
        primera=0
        ultima=0
        range_default=99
        result['automatic'] = automatic
        if (not name) or (not shop) or (not printer):
            return {'value':result}
        dt_obj = self.pool.get('sri.type.document')
        if automatic:
            dt_ant_aut_act_ids = dt_obj.search(cr, uid, [('name','=', name ),('state','=',True), ('shop_id','=',shop),('printer_id','=',printer), ('automatic','=',True)])
            if not dt_ant_aut_act_ids:
                
                dt_ant_aut_ids = dt_obj.search(cr, uid, [('name','=', name ), ('shop_id','=',shop),('printer_id','=',printer), ('automatic','=',True)])
                if dt_ant_aut_ids:
                    primera=dt_obj.browse(cr, uid, dt_ant_aut_ids, context)[-1].last_secuence + 1
                else:
                    primera = 1
                result['last_secuence'] = primera
            else:
                result['expired']=True
        else:
            #Obtengo la ultima secuencia del documento anterior para asignar la siguiente por defecto
            dt_ant_ids = dt_obj.search(cr, uid, [('name','=', name ),('state','=',True), ('shop_id','=',shop),('printer_id','=',printer), ('automatic','=',False)])
            if not dt_ant_ids:
                primera=1
            else:
                for dt in dt_obj.browse(cr, uid, dt_ant_ids , context=context):
                    primera=dt['last_secuence']+1
            ultima=primera + range_default
            result['last_secuence'] = ultima
        result['state'] = name
        result['first_secuence'] = primera
        value = {'value':result}
        return value
    
    def onchange_number(self, cr, uid, ids, first_secuence, automatic, context=None):
        result = {}
        if automatic:
            result['last_secuence'] = first_secuence
        value = {'value':result}
        return value
    
    def _check_sequence(self,cr,uid,ids):
        for std in self.browse(cr, uid, ids):
            if (std['last_secuence'] < 0 or std['first_secuence'] < 0):
                return False
            else:
                return True
    def _check_padding(self, cr, uid, ids, context=None):
        for auth in self.browse(cr, uid, ids):
            if auth.padding >= 0 and auth.padding <= 9:
                return True
            else:
                return False
        
    _name = 'auth.wizard.line'
    _columns={
              'name':fields.selection(_get_name, 'Name'),
              'first_secuence': fields.integer('Inicial Secuence'),
              'last_secuence': fields.integer('Last Secuence'),
              'shop_id':fields.many2one('sale.shop', 'Agency', required=True),
              'printer_id':fields.many2one('sri.printer.point', 'Printer Point', required=True,),
              'auth_wizard_id':fields.many2one('auth.wizard', 'Installer'),
              'state':fields.selection(_get_name,  'state', required=True, readonly=True),
              'automatic':fields.boolean('automatic?', required=False),
              'expired':fields.boolean('expired', required=False),
              'padding': fields.integer('Padding'),
              }
    
    _constraints = [
                    (_check_sequence,_('Sequence number must be a positive number'),['first_secuence', 'last_secuence']),
                    (_check_padding, _('Error: Padding must be a number between 0 - 9'), ['padding']),
                    ]

    _defaults = {  
        'padding': 9,
        }

    def default_get(self, cr, uid, fields_list, context=None):
        if not context:
            context={}
        shop_id = None
        company_id = context.get('company_id', False)
        if company_id:
            for shop in self.pool.get('res.company').browse(cr, uid, company_id, context).shop_ids:
                shop_id = shop.id
                break
        values = super(auth_wizard_line, self).default_get(cr, uid, fields_list, context)
        values['shop_id'] = shop_id
        return values
    
auth_wizard_line()