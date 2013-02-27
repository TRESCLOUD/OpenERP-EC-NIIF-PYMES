
# -*- encoding: utf-8 -*-
########################################################################
#                                                                       
# @authors: Carlos Lopez Mite(celm1990@outlook.com)                                                                           
# Copyright (C) 2012  Ecuadorenlinea                                 
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
import time
from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta

class hr_newholidays_calendar(osv.osv):
    '''
    Open ERP Model
    '''
    _name = 'hr.newholidays.calendar'
    _description = 'hr.newholidays.calendar'

    _columns = {
            'year_id':fields.many2one('account.fiscalyear', 'Año', readonly=True,states={'draft': [('readonly', False)]}),
            'line_ids':fields.one2many('hr.newholidays.calendar.lines', 'parent_id', 'Dias no Laborables',required=True,readonly=True,states={'draft': [('readonly', False)]}),
            'state':fields.selection([
                ('draft','Borrador'),
                ('confirm','Confirmado'),
                ('cancel','Cancelado'),
                 ],    'Estado', select=True, readonly=True), 
        }
    _defaults = {  
        'state':'draft',  
        }
    _rec_name = 'year_id' 
    _sql_constraints = [     ('year_unique', 'unique (year_id)', _('Ya esta registrado un calendario para el año seleccionado!')),      ]
    
    def _change_year(self,cr,uid,ids,context):
        if not context: context={}
        this=self.browse(cr,uid,ids[0])
        if not this.year_id:
            return False
        ano=self.pool.get('account.fiscalyear').read(cr,uid,[this.year_id.id],['date_start'])[0]['date_start'][0:4]
        lines=[]
        for line in this.line_ids:
            data={}
            aux_date_end=line.date_end[4:]
            data['date_end']=ano+aux_date_end
            aux_date_start=line.date_start[4:]
            data['date_start']=ano+aux_date_start
            lines.append((1,line.id,data))
        self.write(cr, uid, ids, {'line_ids':lines,'year_id':this.year_id.id})
        return True
    def action_change_year(self,cr,uid,ids,context=None):
        if not context: context={}
        if not self._change_year(cr, uid, ids, context):
            return False
        self._validate_date(cr, uid, ids, context)
        return True
    
    
    def action_cancel(self,cr,uid,ids,context=None):
        self.write(cr, uid, ids, {'state':'cancel'})
        return True
    
    
    def action_cancel_to_draft(self,cr,uid,ids,context=None):
        self.write(cr, uid, ids, {'state':'draft'})
        return True
    
    
    def action_confirm(self,cr,uid,ids,context=None):
        #validar fechas
        if not self._change_year(cr, uid, ids, context):
            return False
        self._validate_date(cr, uid, ids, context)
        self.write(cr, uid, ids, {'state':'confirm'})
        return True
   
    
    def _validate_date(self,cr,uid,ids,context=None):
        if not context: context={}
        this=self.browse(cr,uid,ids[0])
        if not this.line_ids:
            raise osv.except_osv('Error!',('No hay fechas ingresadas'))
        lines_list=[]
        for line in this.line_ids:
            #validar que esten en el año elegido y que la fecha fin sea mayor a fecha inicio
            if (line.date_start < this.year_id.date_start) or (line.date_end > this.year_id.date_stop):
                raise osv.except_osv('Error!',(u'La fechas deben estar dentro del año seleccionado: Inicio: %s Fin: %s' % (line.date_end,line.date_start )))
            if line.date_end < line.date_start:
                raise osv.except_osv('Error!',('La fecha fin %s debe ser mayor a la fecha inicio %s' % (line.date_end,line.date_start )))
            lines_list.append((line))
        longitud=len(lines_list)
        for index in range(0,longitud-1):
            if lines_list[index].date_end<lines_list[index].date_start:
                raise osv.except_osv('Error!',('Fechas mal ingresadas: inicial(%s), final(%s) ') %(lines_list[index].date_start,lines_list[index].date_end))
            for aux in range(index+1,longitud):
                if lines_list[index].date_start<lines_list[aux].date_start:
                    if lines_list[index].date_end>=lines_list[aux].date_start:
                        raise osv.except_osv('Error!',('Fechas mal ingresadas: inicial(%s), final(%s) ') %(lines_list[aux].date_start,lines_list[aux].date_end))
                else:
                    if lines_list[aux].date_end>=lines_list[index].date_start:
                        raise osv.except_osv('Error!',('Fechas mal ingresadas: inicial(%s), final(%s) ') %(lines_list[aux].date_start,lines_list[aux].date_end))
   
    
    def copy(self, cr, uid, id, default=None, context=None): 
        if not context:
            context={}
        default['state']='draft'
        default['year_id']=None
        res_id = super(hr_newholidays_calendar, self).copy(cr, uid, id, default, context)
        return res_id 
    
    
hr_newholidays_calendar()



class hr_newholidays_calendar_lines(osv.osv):
    '''
    Open ERP Model
    '''
    _name = 'hr.newholidays.calendar.lines'
    _description = 'hr.newholidays.calendar.lines'

    _columns = {
            'parent_id':fields.many2one('hr.newholidays.calendar', 'Año'),
            #TODO : import time required to get currect date
            'date_start': fields.date('Fecha Inicio',required=True),
            #TODO : import time required to get currect date
            'date_end': fields.date('Fecha Fin',required=True), 
            'name':fields.char('Descripción del Feriado', size=64, required=True),   
        }
#    _defaults = {  
#        'date_start': lambda *a: time.strftime('%Y-%m-%d'),  
#        'date_end': lambda *a: str(datetime.now() + relativedelta.relativedelta(days=1))[:10],   
#        }

hr_newholidays_calendar_lines()

#########################
#######AUSENCIAS#########
#########################
class hr_newholidays_type(osv.osv):
    '''
    Open ERP Model
    '''
    _name = 'hr.newholidays.type'
    _description = 'hr.newholidays.type'

    _columns = {
            'name':fields.char('Tipo de Ausencia', size=64, required=True),  
            'code':fields.char('Codigo', size=64, required=True, readonly=False), 
            'is_paid':fields.boolean('Ausencia Pagada?', help="Si se debe pagar al empleado por la ausencia marque la casilla \n Ejemplos: En las Visitas al Seguro Social, se debera reconocer al empleado un porcentaje a pesar de no haber asistido a trabajar"),
            'percent': fields.float('Porcentaje a Pagar', digits=(2,2) , help="El porcentaje a pagar al empleado por la ausencia(calculado en base a lo que gana por el dia de trabajo)"),   
        }
    _defaults = {  
        'is_paid': False,  
        'percent':0.0
        }
    def _verifique_percent(self, cr, uid, ids, context=None): 
        if not context:
            context={}
        for this in self.browse(cr,uid,ids):
            if this.percent <0 or this.percent >100:
                return False 
        #TODO : check condition and return boolean accordingly
        return True
    _constraints = [(_verifique_percent, _('Error: Porcentaje entre 0 y 100 %'), ['percent']), ] 
    
    
hr_newholidays_type()


class hr_newholidays(osv.osv):
    STATES={'draft': [('readonly', False)]}
    def _calculate_number_of_days(self,cr,uid,ids,field_name,arg,context):
        """Returns a float equals to the timedelta between two dates given as string."""
        DATETIME_FORMAT = '%Y-%m-%d'
        res = {}
        for this in self.browse(cr, uid, ids):            
            if this.date_start  and this.date_end :
                number_days = datetime.strptime(this.date_end,DATETIME_FORMAT) - datetime.strptime(this.date_start,DATETIME_FORMAT)
            res[this.id] = number_days.days + float(number_days.seconds) / 86400
        return res

    '''
    Open ERP Model
    '''
    _name = 'hr.newholidays'
    _description = 'hr.newholidays'

    _columns = {
            'name':fields.char('Descripcion', size=64, required=True, readonly=True ,states=STATES ), 
            #TODO : import time required to get currect date
            'date': fields.date('Fecha de Registro'), 
            'employee_id':fields.many2one('hr.employee', 'Empleado', required=True, readonly=True ,states=STATES), 
            'type_id':fields.many2one('hr.newholidays.type', 'Tipo de Ausencia', required=True, readonly=True ,states=STATES),
            #TODO : import time required to get currect date
            'date_start': fields.date('Fecha Inicio',required=True ,readonly=True ,states=STATES),
            #TODO : import time required to get currect date
            'date_end': fields.date('Fecha Fin',required=True,readonly=True ,states=STATES),   
            'number_days': fields.function(_calculate_number_of_days, method=True, type='float', string='Numero de Dias'), 
            'state':fields.selection([
                ('draft','Borrador'),
                ('aproved','Aprobado'),
                ('cancel','Cancelado'),
                 ],    'Estado', select=True, readonly=True), 
            
        }
    _defaults = {  
        'date': lambda *a: time.strftime('%Y-%m-%d'),  
        'state':'draft',
        'date_start': lambda *a: time.strftime('%Y-%m-%d'),  
        'date_end': lambda *a: str(datetime.now() + relativedelta.relativedelta(days=1))[:10],
        }
    
    def action_cancel(self,cr,uid,ids,context=None):
        self.write(cr, uid, ids, {'state':'cancel'})
        return True
    
    
    def action_cancel_to_draft(self,cr,uid,ids,context=None):
        self.write(cr, uid, ids, {'state':'draft'})
        return True
    
    
    def action_confirm(self,cr,uid,ids,context=None):
        self._validate_date(cr, uid, ids, context)
        self.write(cr, uid, ids, {'state':'aproved'})
        return True
    
    def _validate_date(self,cr,uid,ids,context=None):
        if not context: context={}
        for this in self.browse(cr,uid,ids):
            #validar  que la fecha fin sea mayor a fecha inicio
            employee_name=self.pool.get('hr.employee').name_get(cr,uid,[this.employee_id.id])[0][1] or ''
            if this.date_end <= this.date_start:
                raise osv.except_osv('Error!',('La fecha fin %s debe ser mayor a la fecha inicio %s \n Empleado: %s' % (this.date_end,this.date_start,employee_name )))
            employee_ids=[]
            #Validar que no tenga registros ese empleado en fechas anteriores ya guardadas y aprobadas
            #        |--------|
            #        :
            #    |--------|
            employee_ids+=self.pool.get('hr.newholidays').search(cr,uid,[('employee_id','=',this.employee_id.id),
                                                                             ('state','=','aproved'),
                                                                             ('date_start','>',this.date_start),
                                                                             ('date_start','<',this.date_end)])
            #        |--------|
            #                 :
            #            |--------|
            employee_ids+=self.pool.get('hr.newholidays').search(cr,uid,[('employee_id','=',this.employee_id.id),
                                                                             ('state','=','aproved'),
                                                                             ('date_end','>',this.date_start),
                                                                             ('date_end','<',this.date_end)])
            #        |--------|
            #    |----------------|
            employee_ids+=self.pool.get('hr.newholidays').search(cr,uid,[('employee_id','=',this.employee_id.id),
                                                                             ('state','=','aproved'),
                                                                             ('date_start','>=',this.date_start),
                                                                             ('date_end','<=',this.date_end)])
            #        |--------|
            #          |---|
            employee_ids+=self.pool.get('hr.newholidays').search(cr,uid,[('employee_id','=',this.employee_id.id),
                                                                             ('state','=','aproved'),
                                                                             ('date_start','<=',this.date_start),
                                                                             ('date_end','>=',this.date_end)])
            if employee_ids:
                raise osv.except_osv('Error!',('El Empleado: %s , ya tiene registrada Ausencia dentro de las fechas: inicial(%s), final(%s)') %(employee_name,this.date_start,this.date_end))

hr_newholidays()


