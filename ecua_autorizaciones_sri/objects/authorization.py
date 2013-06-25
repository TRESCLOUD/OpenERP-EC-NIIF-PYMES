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
from osv import osv, fields, orm
import time
from tools.translate import _
import re


class sri_type_document(osv.osv):
    
    
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
    
    def _get_range(self, cr, uid, ids, name, args, context=None):
        result = {}
        for document in self.browse(cr, uid, ids, args):
            result[document.id] = document.last_secuence - document.first_secuence
        return result
    
    _name = 'sri.type.document'
    _columns = {'name':fields.selection(_get_name, 'Name', size=32), 
                'first_secuence': fields.integer('Inicial Secuence'),
                'last_secuence': fields.integer('Last Secuence'),
                'counter': fields.integer('counter'),
                'range': fields.function(_get_range, method=True, type='integer',string='range', store=True),
                }
    
    _defaults = {
                 'counter': lambda *a: 0
                 }
    
    def add_document(self,cr, uid, ids, context=None):
        seq_obj = self.pool.get('ir.sequence')
        if not context:
            context = {}
        for document in self.browse(cr, uid, ids, context=context):
            if document.sri_authorization_id.auto_printer:
                self.write(cr, uid, [document.id,],{'last_secuence': document.last_secuence+1, 'counter': document.counter+1}, context=context )
            else:
                if context.get('automatic', False):
                    seq_obj.get_id(cr, uid, document.sequence_id.id)
                self.write(cr, uid, [document.id,],{'counter': document.counter+1}, context=context)
            
    def rest_document(self,cr, uid, ids, context=None):
        seq_obj = self.pool.get('ir.sequence')
        if not context:
            context = {}
        for document in self.browse(cr, uid, ids, context=context):
            if document.sri_authorization_id.auto_printer:
                self.write(cr, uid, [document.id,],{'last_secuence': document.last_secuence-1, 'counter': document.counter-1}, context=context )
            else:
                if context.get('automatic', False):
                    seq_obj.write(cr, uid, document.sequence_id.id, {'next_number':document.sequence_id - 1})
                self.write(cr, uid, [document.id,],{'counter': document.counter-1}, context=context )
    
    def _check_sequence(self,cr,uid,ids):
        range = 0
        for std in self.browse(cr, uid, ids):
            range = std['last_secuence'] - std['first_secuence']
            if (std['last_secuence'] < 0 or std['first_secuence'] < 0):
                return False
            if (range < 0):
                return False
            else:
                return True
            
    _constraints = [(_check_sequence,_('Sequence number must be a positive number'),['first_secuence', 'last_secuence'])]
sri_type_document()

class sri_authorization(osv.osv):
    
    def _get_authorization(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('sri.type.document').browse(cr, uid, ids, context=context):
            result[line.sri_authorization_id.id] = True
        return result.keys()

    def _verify_state(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for auth in self.browse(cr, uid, ids, context=context):
            res[auth.id]=False            
            for line in auth.type_document_ids:
                if line.state == True:
                    res[auth.id]=True
        return res
        
        
    _name = 'sri.authorization'
    _columns = {
                'auto_printer':fields.boolean('Auto Printer?',), 
                'number':fields.char('Authorization Number', size=37, required=True, readonly=False),
                'creation_date': fields.date('Creation Date'),
                'start_date': fields.date('Start Date'),
                'expiration_date': fields.date('Expiration Date'),
                'company_id':fields.many2one('res.company', 'Company', required=True),
                'type_document_ids':fields.one2many('sri.type.document', 'sri_authorization_id', 'Documents Types', required=True),
                'state': fields.function(_verify_state, method=True, type='boolean', string='Active',
                                        store={  'sri.authorization': (lambda self, cr, uid, ids, c={}: ids, ['type_document_ids'], 10),
                                                 'sri.type.document': (_get_authorization , ['state','count'], 9)}), 
               }
    
    _sql_constraints = [('number_uniq','unique(number)', _('The number of authorization must be unique'))]
    
    def find(self, cr, uid, dt=None, context=None):
        if not dt:
            dt = time.strftime('%Y-%m-%d')
        ids = self.search(cr, uid, [('expiration_date','>=',dt)])
        return ids
    
    #TODO:Funcion que valida la fecha del documento con la fecha de la autorizacion
    def check_date_document(self, cr, uid, date_document=None, date_auth_start=None, date_auth_expired=None, context=None):
        try:
            if (date_document >= date_auth_start) and (date_document <= date_auth_expired):
                return True
            else:
                return False
        except:
            return False
    
    
    def check_if_seq_exist(self, cr, uid, type='invoice', secuence=None, printer_id=None, date_document=None, context=None):
        if not context: context = {}
        name_type = {
                    'invoice':_('Invoice'),
                    'delivery_note':_('Delivery note'),
                    'withholding':_('Withholding'),
                    'credit_note':_('Credit Note'),
                    'liquidation':_('Liquidation of Purchases'),
                    'debit_note':_('Debit Note')
                     }
        if not date_document: date_document = time.strftime('%Y-%m-%d')
        res = {
               'authorization' : None,
               'document_type_id': None,
               }
        number = None
        printer = None
        #Se verifica que el número tenga el formato correcto
        seq_number = ''
        agency_number = None
        printer_number = None
        has_form = False
        cadena = '(\d{3})+\-(\d{3})+\-(\d{9})'
        if re.match(cadena, secuence):
            has_form = True
        try:
            if has_form:
                number = secuence.split('-')
                agency_number = number[0]
                printer_number = number[1]
                seq_number = number[2]
            else:
                seq_number = secuence
        except:
            return res
        line_auth_obj = self.pool.get('sri.type.document')
        printer_obj = self.pool.get('sri.printer.point')
        if printer_id:
            printer = printer_obj.browse(cr, uid, printer_id, context)
        if not printer:
            return res
        #Se verifica que exista alguna línea de autorización que cumpla con este criterio
        line_auth_ids = line_auth_obj.search(cr, uid, [('name','=',type), ('printer_id','=',printer.id)])
        for document in line_auth_obj.browse(cr, uid, line_auth_ids, context):
            if not document.sri_authorization_id.auto_printer:
                #Se verifica que el número este dentro de las secuencias de la autorización
                if (int(seq_number)>= document.first_secuence and int(seq_number)<= document.last_secuence):
                    res['authorization'] = document.sri_authorization_id.id
                    res['document_type_id'] = document.id
                    if not self.check_date_document(cr, uid, date_document, document.sri_authorization_id.start_date, document.sri_authorization_id.expiration_date, context):
                        raise osv.except_osv(_('Error!!!'),('There\'s not authorization for this document %s with number %s in this date %s') % (name_type.get(type, _('Invoice')), secuence, date_document))
                    break
        #Se verifica que el número de la agencia sea el mismo que la primera secuencia
        if agency_number and not printer.shop_id.number == agency_number:
            res['authorization'] = None
            res['document_type_id'] = None
        #Se verifica que el número del punto de emisión sea el mismo que el de la secuencia
        if printer_number and not printer.number == printer_number:
            res['authorization'] = None
            res['document_type_id'] = None
        if not res['authorization'] or not res['document_type_id']:
            raise osv.except_osv(_('Error!!!'),('There\'s not authorization for this document %s with number %s') % (name_type.get(type, _('Invoice')), secuence))       
        return res

    def get_auth_only(self, cr, uid, type, company_id=None, shop_id=None, printer_id=None, date_document=None, context=None):
        manual = False
        if context == None:
            context = {}
        manual = context.get('manual', False)
        if date_document == None:
            date_document = time.strftime('%Y-%m-%d')
        auth_obj = self.pool.get('sri.authorization')
        line_auth_obj = self.pool.get('sri.type.document')
        if shop_id==None:
                shop_id = self.pool.get('sale.shop').search(cr, uid,[])[0]
        if company_id==None:
                company_id = self.pool.get('res.company').search(cr, uid,[])[0]
        if printer_id==None:
            printer_id = self.pool.get('sri.printer.point').search(cr, uid, [('shop_id.id','=',shop_id)])[0]
        line_auth_ids = None
        if manual:
            line_auth_ids = line_auth_obj.search(cr, uid, [('name','=',type),('shop_id','=',shop_id), ('printer_id','=',printer_id), ('state', '=',True )])
        else:
            line_auth_ids = line_auth_obj.search(cr, uid, [('name','=',type),('shop_id','=',shop_id), ('printer_id','=',printer_id),])
        auth_id = None
        if line_auth_ids:
            for line in line_auth_ids:
                auth = line_auth_obj.browse(cr, uid, line, context).sri_authorization_id
                if date_document >= auth.start_date and date_document <= auth.expiration_date: 
                    if not manual:
                        if auth.auto_printer == True:
                            auth_id = auth.id
                    else:
                        if auth.auto_printer == False:
                            auth_id = auth.id        
        if auth_id:
            if company_id == auth_obj.browse(cr, uid, auth_id, context).company_id.id:
                return{'authorization': auth_id}
        return {'authorization': None}     


    def get_auth(self, cr, uid, type, company_id=None, shop_id=None, secuence=None, printer_id=None, context=None):

        # El SRI permite usar Notas de Credito que sean de diferente punto de venta que la factura
        # por ese motivo se modifica el codigo para buscar una autorizacion en base al numero ingresado
        # Esta funcion es utilizada por otras instancias de la parte del SRI
        
        try:

            number = secuence.split('-')
            line_auth_obj = self.pool.get('sri.type.document')

            if context and 'use_secuence' in context and context['use_secuence']:
                # en base a la secuencia verifico si hay autorizacion
                # el company_id si debe ser usado
                shop_id = self.pool.get('sale.shop').search(cr, uid,[('company_id','=',company_id),
                                                                     ('number','=',number[0])])[0]
                printer_id = self.pool.get('sri.printer.point').search(cr, uid, [('shop_id','=',shop_id)])[0]
                
            else:
            
                if shop_id==None:
                        shop_id = self.pool.get('sale.shop').search(cr, uid,[])[0]
                
                if company_id==None:
                        company_id = self.pool.get('res.company').search(cr, uid,[])[0]
                
                if printer_id==None:
                    printer_id = self.pool.get('sri.printer.point').search(cr, uid, [('shop_id','=',shop_id)])[0]
                
                if not self.pool.get('sale.shop').browse(cr, uid, shop_id,context).number == number[0]:
                    return {'authorization': None}
                
                if not self.pool.get('sri.printer.point').browse(cr, uid, printer_id,context).number == number[1]:
                    return {'authorization': None}
            
            
            line_auth_ids = line_auth_obj.search(cr, uid, [('name','=',type),('shop_id','=',shop_id), ('printer_id','=',printer_id)])
            auth_id = None
            
            for line_id in line_auth_ids:
            
                document = self.pool.get('sri.type.document').browse(cr, uid, [line_id,], context)[0]
                
                if not document.sri_authorization_id.auto_printer:
                
                    if (int(number[2])>= document.first_secuence and int(number[2])<= document.last_secuence) and (document.sri_authorization_id.company_id.id == company_id):
                        auth_id = document.sri_authorization_id.id
            
            return{'authorization': auth_id}
            
        except:
            
            return {'authorization': None}
    
    
    def get_auth_secuence(self, cr, uid, type, company_id=None, shop_id=None , printer_id=None, context=None):
        try:
            line_auth_obj = self.pool.get('sri.type.document')
            if shop_id==None:
                shop_id = self.pool.get('sale.shop').search(cr, uid,[])[0]
            if company_id==None:
                company_id = self.pool.get('res.company').search(cr, uid,[])[0]
            if printer_id==None:
                printer_id = self.pool.get('sri.printer.point').search(cr, uid, [('shop_id.id','=',shop_id)])
            line_auth_ids = line_auth_obj.search(cr, uid, [('name','=',type),('state','=',True),('shop_id','=',shop_id),('printer_id','=',printer_id)])
            auth_id = None
            seq_id = None
            for line_id in line_auth_ids:
                auth = self.pool.get('sri.type.document').browse(cr, uid, line_id, context)['sri_authorization_id']
                if (auth.state and auth.company_id.id == company_id):
                    seq_id = line_auth_obj.browse(cr, uid, [line_id,], context)[0]['sequence_id']['id']
                    auth_id = auth.id
            return{'authorization': auth_id, 'sequence':seq_id}
        except:
            return {'authorization': None, 'sequence':None}
        
    def get_auth_range(self, cr, uid, auth_id, type, context=None):
        res = {}
        auth_line_id = self.pool.get('sri.type.document').search(cr, uid, [('sri_authorization_id','=',auth_id),('state','=',True),('name','=',type)])
        auth_line = self.pool.get('sri.type.document').browse(cr, uid, [auth_line_id[0],], context)
        if auth_line:
            res['first_number']=auth_line[0].first_secuence
            res['last_number']=auth_line[0].last_secuence
        return res
    
    def verify_expiration_date(self, cr, uid, context):
        auth_obj = self.pool.get('sri.authorization')
        seq_obj = self.pool.get('ir.sequence')
        ids = []
        for auth_id in auth_obj.search(cr, uid, [('auto_printer','=',True),('state','=',True)]):
            auth= auth_obj.browse(cr, uid, auth_id, context)
            if auth.expiration_date < time.strftime('%Y-%m-%d'):
                for line in auth.type_document_ids:
                    line_next_ids=self.pool.get('sri.type.document').search(cr, uid, [('expired','=',True),('name','=',line.name), ('shop_id','=',line.shop_id.id), ('printer_id','=',line.printer_id.id)])
                    for line_next in self.pool.get('sri.type.document').browse(cr, uid, line_next_ids, context):
                        if line_next.sri_authorization_id.start_date > auth.expiration_date and line_next.sri_authorization_id.auto_printer:
                            self.pool.get('sri.type.document').write(cr, uid, [line_next.id,], {'expired':False, 'first_secuence':line.last_secuence+1, 'last_secuence':line.last_secuence+1}, context)
                            self.pool.get('ir.sequence').write(cr, uid, [line_next.sequence_id.id, ], {'number_next':line.last_secuence+1}, context)
                            ids.append(line_next.sri_authorization_id.id)
                    self.pool.get('sri.type.document').write(cr, uid, [line.id,], {'expired':True}, context)
                    ids.append(line.sri_authorization_id.id)
        auth_obj.write(cr, uid, ids, {}, context)
        return True
    
    _rec_name='number'

sri_authorization()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: