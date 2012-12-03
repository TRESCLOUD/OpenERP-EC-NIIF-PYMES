# -*- encoding: utf-8 -*-
########################################################################
#                                                                       
# @authors: Christopher Ormaza                                                                           
# Copyright (C) 2012  Ecuadorenlinea.net                                  
#                                                                       
#This program is free software: you can redistribute it and/or modify   
#it under the terms of the GNU General Public License as published by   
#the Free Software Foundation, either version 3 of the License, or      
#(at your option) any later version.                                    
#
# This module is GPLv3 or newer and incompatible
# with OpenERP SA "AGPL + Private Use License"!
#                                                                       
#This program is distributed in the hope that it will be useful,        
#but WITHOUT ANY WARRANTY; without even the implied warranty of         
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the          
#GNU General Public License for more details.                           
#                                                                       
#You should have received a copy of the GNU General Public License      
#along with this program.  If not, see http://www.gnu.org/licenses.
########################################################################

from osv import osv
from osv import fields
import decimal_precision as dp
from tools.translate import _

class ir_sequence_line(osv.osv):
    
    _name = 'ir.sequence.line'
    
    _description = 'Lineas de Secuencia'
    
    _columns = {
                'code':fields.char('Code', size=255, required=True),
                'sequence_id':fields.many2one('ir.sequence', 'Sequence', required=False), 
        }

    _rec_name = 'code'
    
ir_sequence_line()

class ir_sequence(osv.osv):
    _inherit = 'ir.sequence'
    

    def get_next_id(self, cr, uid, sequence_id, aditional_value=0, test='id', context=None):
        assert test in ('code','id')
        company_ids = self.pool.get('res.company').search(cr, uid, [], context=context)
        cr.execute('''SELECT id, number_next, prefix, suffix, padding
                      FROM ir_sequence
                      WHERE %s=%%s
                       AND active=true
                       AND (company_id in %%s or company_id is NULL)
                      ORDER BY company_id, id
                      FOR UPDATE NOWAIT''' % test,
                      (sequence_id, tuple(company_ids)))
        res = cr.dictfetchone()
        if res:
            if res['number_next']:
                return self._process(res['prefix']) + '%%0%sd' % res['padding'] % (res['number_next']+aditional_value) + self._process(res['suffix'])
            else:
                return self._process(res['prefix']) + self._process(res['suffix'])
        return False

    def get_next_value_sequence(self, cr, uid, sequence_id=None, company_id=None, model=None, field=None, context=None):
        doc_obj = self.pool.get('sri.type.document')
        seq_obj = self.pool.get('ir.sequence')
        obj = self.pool.get(model)
        if not context:
            context = {}
        if not date:
            date = time.strftime('%Y-%m-%d')
        if not company_id or not sequence_id or not model or not field:
            return False
        next_seq = seq_obj.get_next_id(cr, uid, sequence_id,0)
        #TODO: Hay que devolver la siguiente secuencia disponible en caso de encontrar documentos en estado de borrador
        flag = True
        count = 0
        while flag:
            ids = obj.search(cr, uid, [(field,'=',next_seq)])
            if not ids:
                flag = False
            else:
                count +=1
                next_seq = seq_obj.get_next_id(cr, uid, sequence_id, count)            
        return next_seq
ir_sequence()