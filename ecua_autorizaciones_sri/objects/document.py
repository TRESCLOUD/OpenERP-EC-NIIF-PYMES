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
from osv import osv, fields
import time
from tools.translate import _
class sri_type_document(osv.osv):
    
    def _verify_state(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for document in self.browse(cr, uid, ids, context=context):
            if document.sri_authorization_id.auto_printer:
                res[document.id] = (not document.expired)
            else:
                if document.counter <= document.range:
                    res[document.id]=True
                else:
                    res[document.id]=False
        return res

    
    _name = 'sri.type.document'
    _inherit = 'sri.type.document'
    _columns = {
                'sri_authorization_id':fields.many2one('sri.authorization', 'Authorization', required=True),
                'sequence_id':fields.many2one('ir.sequence', 'Sequence', required=True),
                'state': fields.function(_verify_state, method=True, type='boolean', string='Active',
                                         store={
                                                 'sri.type.document': (lambda self, cr, uid, ids, c={}: ids, ['counter', 'expired'], 8)}),
                'shop_id':fields.many2one('sale.shop', 'Agency', required=True),
                'printer_id':fields.many2one('sri.printer.point', 'Printer Point', required=True),
                'expired':fields.boolean('Expired?',),
                'automatic':fields.boolean('automatic?', required=False),
                }

    def validate_unique_value_document(self, cr, uid, number=None, company_id=None, model=None, field=None, name='Factura', context=None):
        doc_obj = self.pool.get('sri.type.document')
        seq_obj = self.pool.get('ir.sequence')
        company_obj = self.pool.get('res.company')
        obj = self.pool.get(model)
        if not context:
            context = {}
        if not number or not company_id or not field or not name or not model:
            raise osv.except_osv(_('Error!'), _("There's not valid arguments to validate number of document"))
        company = company_obj.browse(cr, uid, company_id, context)
        ids = obj.search(cr, uid, [(field,'=',number),('company_id','=',company_id)])
        if not ids:
            return True
        else:
            raise osv.except_osv(_('Error!'), _("There is another document type %s with number '%s' for the company %s") % (name, number,company.name))

    def get_next_value_secuence(self, cr, uid, type, date, company_id=None, shop_id=None, printer_id=None, model=None, field=None, context=None):
        doc_obj = self.pool.get('sri.type.document')
        seq_obj = self.pool.get('ir.sequence')
        obj = self.pool.get(model)
        if not context:
            context = {}
        if not date:
            date = time.strftime('%Y-%m-%d')
        if not type or not company_id or not shop_id or not printer_id:
            return False
        doc_ids = doc_obj.search(cr, uid, [('name','=',type),('printer_id','=',printer_id),('shop_id','=',shop_id),('state','=',True)])
        docs = doc_obj.browse(cr, uid, doc_ids, context)
        doc_finded = None
        for doc in docs:
            if date >= doc.sri_authorization_id.start_date and date <= doc.sri_authorization_id.expiration_date:
                doc_finded = doc
                break
        if not doc_finded:
            return False
        next_seq = seq_obj.get_next_id(cr, uid, doc_finded.sequence_id.id,0)
        #TODO: Hay que devolver la siguiente secuencia disponible en caso de encontrar documentos en estado de borrador
        flag = True
        count = 0
        while flag:
            ids = obj.search(cr, uid, [(field,'=',next_seq),('company_id','=',company_id)])
            if not ids:
                flag = False
            else:
                count +=1
                next_seq = seq_obj.get_next_id(cr, uid, doc_finded.sequence_id.id, count)            
        return next_seq
    
    def create_secuence(self, pad, number):
        i = 0
        cadena = ''
        pad=pad-len(str(number))
        while i < pad:
            cadena=cadena+'0'
            i+=1
        return cadena+str(number)
    
    #TODO: verificacion por compania
    def write(self, cr, uid, ids, values, context=None):
        td_obj = self.pool.get('sri.type.document')
        try:
            lines_ids = td_obj.search(cr, uid, [('name','=',values['name']),('sri_authorization_id','=',values['sri_authorization_id']),])
            #verifica que existe otra linea de autorizacion con el mismo tipo de documento en la misma autorizacion
            if lines_ids:
                raise osv.except_osv('Error!', _('There is another line with the same type of ducument in authorization'))
            #verifica que las secuencias no sean inversas
            if (values['last_secuence']  - values['first_secuence'] < 0):
                raise osv.except_osv('Error!', _('Your last sequence must be bigger first sequence'))
            return super(sri_type_document, self).write(cr, uid, ids, values, context)
        except:
            return super(sri_type_document, self).write(cr, uid, ids, values, context)

    #TODO: verificacion por compania
    def create(self, cr, uid, values, context=None):
        td_obj = self.pool.get('sri.type.document')
        auth_obj= self.pool.get('sri.authorization')
        lines_ids = td_obj.search(cr, uid, [('name','=',values['name']),
                                            ('sri_authorization_id','=',values['sri_authorization_id']),
                                            ('shop_id','=',values['shop_id']), 
                                            ('printer_id','=',values['printer_id'])])
        
        #verifica que existe otra linea de autorizacion con el mismo tipo de documento en la misma tienda y en el mismo punto de impresion
        if lines_ids:
            raise osv.except_osv('Error!', _('There is another line with the same type of document for printer point in agency %s') % values['shop_id']['name'])
        lines_ids = td_obj.search(cr, uid, [('name','=',values['name']),('shop_id','=',values['shop_id']),('printer_id','=',values['printer_id']), ('automatic','=',values['automatic'])])
        for line in td_obj.browse(cr, uid, lines_ids,context):
            auth_actual = auth_obj.browse(cr, uid, values['sri_authorization_id'], context)
        #verifica que las secuencias no sean inversas
        if (values['last_secuence']  - values['first_secuence'] < 0): 
            raise osv.except_osv('Error!', _('Your last sequence must be bigger than first sequence'))
        if not values['automatic']:
            lines_ids = td_obj.search(cr, uid, [('name','=',values['name']),('shop_id','=',values['shop_id']),('printer_id','=',values['printer_id']), ('automatic','=',False)])
            #Debe haber una unica linea de autorización activa por agencia y punto de impresion
            lines_ids = td_obj.search(cr, uid, [('name','=',values['name']),('shop_id','=',values['shop_id']),('printer_id','=',values['printer_id']), ('state','=',True), ('automatic','=',False)])
            for line in td_obj.browse(cr, uid, lines_ids , context=context):
                values_doc={'counter':line.range + 1}
                td_obj.write(cr, uid, [line.id,], values_doc, context)
        return super(sri_type_document, self).create(cr, uid, values, context)

sri_type_document()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: