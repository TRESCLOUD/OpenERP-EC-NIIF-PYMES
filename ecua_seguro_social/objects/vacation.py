
# -*- encoding: utf-8 -*-
########################################################################
#                                                                       
# @authors: Carlos Lopez Mite(celm1990@outlook.com)                                                                           
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
from datetime import datetime
from dateutil import relativedelta
import time
class vacation(osv.osv):
    days_holgura=7
    dias_ano=365
    DATE_FORMAT="%Y-%m-%d"
    def get_year_start_end(self,cr,uid,this,context=None):
        """
        Calcula y devuelve desde que ano hasta que ano se va a tomar vacaciones
        Ejm. del 2 al 4 ano se va a tomar vacaciones 
        """
        if not context: context={}
        year_start=0
        year_end=0
        date_start_period=self.pool.get('hr.employee').get_date_last_contract_continuo(cr,uid, this.employee_id.id, self.days_holgura ,context)
        date_start=datetime.strptime(date_start_period,"%Y-%m-%d")
        vacation_ids=self.search(cr,uid,[('state','=','confirm'),
                                         ('employee_id','=',this.employee_id.id),
                                         ('date_start','>=',date_start),
                                         ('date_end','<',this.date_start),
                                         ('id','!=',this.id)],order="date_start")
        if vacation_ids:
            date_end=datetime.strptime(self.read(cr,uid,[vacation_ids[-1]],['date_end'])[0]['date_end'],"%Y-%m-%d") # or this.date_end probar
            year_start_aux= date_end - date_start
            year_start=year_start_aux.days / self.dias_ano
            year_end_aux=  datetime.strptime(this.date_end,"%Y-%m-%d") - date_start
            year_end= year_end_aux.days / self.dias_ano
        else:
            year_start = 0
            now = datetime.strptime(this.date_start,"%Y-%m-%d")
            year_end_aux = now - date_start
            year_end = year_end_aux.days / self.dias_ano
        return {'year_start':year_start,'year_end':year_end}
    
    def get_days_acumulated(self,cr,uid,vacation_id,year_start=0, year_end=4,context=None):
        """
        Busca y calcula los dias de vacaciones que tenga acumulados en los años especificados
        @param year_end: el numero de años anteriores hasta los que buscar vacaciones acumuladas
        Ejm. si la fecha que se esta haciendo las vacaciones es 01/01/2013 y year_end=4,
        Se verificara hasta el 01/01/2009 si hay vacaciones acumuladas.
        se busca desde el periodo actual hacia atras 2012, 2011, 2010 , 2009, ......
        """
        if not context: context={}
        this =self.browse(cr,uid,vacation_id,context)
        dias_acumulados=0
        year_acumulados=0
        year_date_start= datetime.strptime(this.date_start[0:4] + "-01-01",self.DATE_FORMAT).strftime(self.DATE_FORMAT)
        year_date_end= datetime.strptime(this.date_start[0:4] + "-12-31",self.DATE_FORMAT).strftime(self.DATE_FORMAT)
        #no acumular las del año actual
        vacation_ids=self.search(cr,uid,[('state','=','confirm'),
                                                   ('employee_id','=',this.employee_id.id),
                                                   ('date_start','>=',year_date_start),
                                                   ('date_end','<',this.date_end),
                                                   ('id','!=',this.id)])
        if vacation_ids:
            return 0
        aux_year=1
        for year in range(year_start,year_end):
            date_start_after=datetime.strptime(year_date_start , self.DATE_FORMAT) + relativedelta.relativedelta(years=-aux_year)
            date_end_after=datetime.strptime(year_date_end , self.DATE_FORMAT) + relativedelta.relativedelta(years=-aux_year)
            aux_year+=1
            vacation_after_ids=self.search(cr,uid,[('state','=','confirm'),
                                                   ('employee_id','=',this.employee_id.id),
                                                   ('date_start','>=',date_start_after),
                                                   ('date_end','<=',date_end_after)], order="date_start")
            # si ha tomado vacaciones el año anterior obtengo las vacaciones restantes
            if vacation_after_ids:
                last_vacation=self.browse(cr,uid,vacation_after_ids[-1])
                return last_vacation.days_vacation_remaining 
            #obtener el año de las vacaciones del año anterior
            #si los años acumulado es mayor a lo permitido, pierde el primer año de vacaciones
            #en ese caso simplemente no sumamos los dias que le correspondian en ese año
            #ya que este seria el primer año de vacaciones porque se busca desde el periodo actual hacia atras
            dias_acumulados+=self.get_days_vacation(year, context)
            if (year_end -  year_start) >=4:
                dias_acumulados-=self.get_days_vacation(year_start, context)
        return dias_acumulados
    
    
    def _calculate_days_current(self,cr,uid,ids, field_name,  args ,context=None):
        """
        Busca y calcula los dias de vacaciones que haya tomado en el periodo actual excluyendo las que son superiores en fecha a la actual
        @param vacation_id: objeto hr.vacation
        """
        if not context: context={}
        res={}
        for this in self.browse(cr,uid,ids,context):
            year_date_start= datetime.strptime(this.date_start[0:4] + "-01-01",self.DATE_FORMAT).strftime(self.DATE_FORMAT)
            vacation_current_ids=self.search(cr,uid,[('state','=','confirm'),
                                                       ('employee_id','=',this.employee_id.id),
                                                       ('date_start','>=',year_date_start),
                                                       ('date_end','<',this.date_start),
                                                       ('id','!=',this.id)])
            total_current=0
            for vacacion in self.browse(cr,uid,vacation_current_ids,context):
                total_current+=vacacion.duration
            res[this.id]=total_current
        return res
    
    
    
    def get_days_vacation(self, year=1, context=None):
        """
        Calcula el tiempo en dias que se debe tomar como vacaciones por año
        Considerando que si tiene mas de 5 años de trabajo se debe añadir un dia mas por cada año excedido
        @param year: numero del año a calcular ejemplo 1,2,3,4,5,6
        @return: int que equivale a los dias de vacaciones que se debe tomar en el año
        """
        if not context: context={}
        dias_vacaciones=15
        #Si tiene mas de 5 años de trabajo se añade un dia mas por cada año excedente
        if year > 5:
            dias_vacaciones+= (year - 5)
        return dias_vacaciones

    def _calculate_days_max(self, cr,uid, ids, field_name, args , context=None):
        """
        Calcula maximo de dias que se le puede permitir tomar de vacaciones
        @param vacation_id:  objeto hr.vacation 
        """
        if not context: context={}
        res={}
        for this in self.browse(cr,uid, ids, context):
            #si ya tomo los dias de vacaciones en el año actual solo permitir tomar los dias restantes
            if this.days_current_year>0:
                year_date_start= datetime.strptime(this.date_start[0:4] + "-01-01",self.DATE_FORMAT).strftime(self.DATE_FORMAT)
                vacation_current_ids=self.search(cr,uid,[('state','=','confirm'),
                                                           ('employee_id','=',this.employee_id.id),
                                                           ('date_start','>=',year_date_start),
                                                           ('date_end','<',this.date_start),
                                                           ('id','!=',this.id)])
                if vacation_current_ids:
                    res[this.id]= self.browse(cr,uid, vacation_current_ids[-1],context).days_vacation_remaining
            else:
                if this.days_vacation_acumulated==0:
                    years=self.get_year_start_end(cr, uid, this, context)
                    res[this.id]= self.get_days_vacation(years.get('year_end'), context)
                else:
                    res[this.id]= this.days_vacation_acumulated
        return res
    
    def _calculate_days_vacation_remaining(self,cr,uid,ids,field_name,arg,context=None):
        """
        Calcula y devuelve los dias que le quedan de vacaciones al empleado
        Considerando que ya ha podido tomar parte de las vacaciones que le corresponden en el periodo
        """
        if not context: context={}
        res={}
        for this in self.browse(cr,uid,ids,context):
            res[this.id]=  this.days_max - this.duration 
        return res
    
    def _calculate_days_vacation_acumulated(self,cr,uid,ids,field_name,arg,context=None):
        """
        Calcula y devuelve los dias que le quedan por tomar de vacaciones sin incluir el registro actual
        solo las acumuladas y las tomadas en el periodo actual
        """
        if not context: context={}
        res={}
        for this in self.browse(cr,uid,ids,context):
            anos_trabajo = this.employee_id.working_time / self.dias_ano
            #si es el primer año de trabajo no va a tener vacaciones acumuladas
            if anos_trabajo<=1:
                res[this.id] = 0
                continue
            #recuperar el ultimo registro ingresado para en base a la fecha de ese calcular cuantos años no ha tomado vacaciones
            #PENDIENTE: modificar funcion y pasar desde que año hasta que año calcular dias acumulados
            #ejm desde el 4 al 7 año. para ser precisos en el calculo
            years=self.get_year_start_end(cr, uid, this,context)
            res[this.id] = self.get_days_acumulated(cr, uid, this.id,years.get('year_start'), years.get('year_end'), context)
        return res
    
    def _calculate_next_vacation(self, cr, uid, ids, field_name, arg , context=None):
        """
        Calcula y devuelve la fecha en que el empleado debe tomar las proximas vacaciones
        """
        if not context: context={}
        res={}
        obj_contract = self.pool.get('hr.contract')
        for this in self.browse(cr,uid,ids):
            next_vacation=datetime.now()
            year_date_start= datetime.strptime(this.date_start[0:4] + "-01-01",self.DATE_FORMAT).strftime(self.DATE_FORMAT)
            #obtener la ultima vacacion del año actual y a esa fecha sumarle un año si ya tomo todos dias de vacaciones del año actual
            vacation_ids=self.search(cr,uid,[('state','=','confirm'),
                                             ('employee_id','=',this.employee_id.id),
                                             ('date_start','>=',year_date_start),
                                             ('date_end','<',this.date_start),
                                             ('id','!=',this.id)],order="date_start")
            if vacation_ids:
                last_vacation_id= vacation_ids and vacation_ids[-1]
                vacation= self.browse(cr,uid,last_vacation_id,context)
                if vacation.days_vacation_remaining<=0:
                    next_vacation= datetime.strptime(vacation.date_end , '%Y-%m-%d') + relativedelta.relativedelta(years=+1)
                else:
                    next_vacation= datetime.strptime(vacation.date_end , '%Y-%m-%d')
            else:
                #obtener vacaciones anteriores al año actual
                vacation_ids=self.search(cr,uid,[('state','=','confirm'),
                                                 ('employee_id','=',this.employee_id.id),
                                                 ('date_start','<',this.date_start)],order="date_start")
                if vacation_ids:
                    last_vacation_id= vacation_ids and vacation_ids[-1]
                    vacation= self.browse(cr,uid,last_vacation_id,context)
                    if vacation.days_vacation_remaining<=0:
                        next_vacation= datetime.strptime(vacation.date_end , '%Y-%m-%d') + relativedelta.relativedelta(years=+1)
                    else:
                        next_vacation= datetime.strptime(vacation.date_end , '%Y-%m-%d')
                else:
                    #si todavia no tiene vacaciones registradas
                    #calcular la fecha de vacacion en base a la fecha del primer contrato
                    #obtener la fecha de inicio del ultimo periodo continuo
                    periodo_date_start=self.pool.get('hr.employee').get_date_last_contract_continuo(cr,uid, this.employee_id.id, self.days_holgura ,context)
                    #porque de otra manera no se tomaria el primer contrato sino el primero del ultimo periodo continuo
                    contract_ids = obj_contract.search(cr, uid, [('employee_id','=',this.employee_id.id),('date_start','>=',periodo_date_start)], order='date_start', context=context)
                    if contract_ids:
                        first_contract =obj_contract.browse(cr,uid,contract_ids[0])
                        next_vacation= datetime.strptime(first_contract.date_start, '%Y-%m-%d') + relativedelta.relativedelta(years=+1)
            res[this.id]=next_vacation
        return res
    
    
    def _calculate_duration(self,cr,uid,ids,field_name,arg,context=None):
        """
        Calcula y devuelve en dias la diferencia entre dos fechas
        """
        if not context: context={}
        res={}
        for vacation in self.browse(cr,uid,ids,context):
            if vacation.date_start and vacation.date_end:
                date_start=datetime.strptime(vacation.date_start, '%Y-%m-%d')
                date_end=datetime.strptime(vacation.date_end, '%Y-%m-%d')
                duration=date_end -date_start
                res[vacation.id]=duration.days +1
        return res
    
    STATES={'draft': [('readonly', False)]}
    '''
    Open ERP Model
    '''
    _name = 'hr.vacation'
    _description = 'hr.vacation'

    _columns = {
            'employee_id':fields.many2one('hr.employee', 'Empleados', required=True,readonly=True,states=STATES),
            'department_id':fields.many2one('hr.department', 'Departamento', required=False),
            'year_id':fields.many2one('account.fiscalyear', 'Periodo Actual', required=True,readonly=True,states=STATES),    
            #TODO : import time required to get currect date
            'date': fields.date('Fecha'), 
            #TODO : import time required to get currect date
            'date_start': fields.date('Fecha Inicio',required=True,readonly=True,states=STATES), 
            #TODO : import time required to get currect date
            'date_end': fields.date('Fecha Fin',required=True,readonly=True,states=STATES), 
            'duration': fields.function(_calculate_duration, method=True, type='float', string='Dias Vacaciones'), 
            'days_vacation_remaining': fields.function(_calculate_days_vacation_remaining, method=True, type='float', string='Dias Restantes de Vacaciones'),
            'days_vacation_acumulated': fields.function(_calculate_days_vacation_acumulated, method=True, type='float', string='Total dias Acumulados'),
            'days_current_year': fields.function(_calculate_days_current, method=True, type='float', string='Dias tomados en el años actual'),
            'days_max': fields.function(_calculate_days_max, method=True, type='float', string='Dias Maximos Permitidos'),
            'date_next_vacation': fields.function(_calculate_next_vacation, method=True, type='date', string='Fecha de Proximas Vacaciones'),
            'state':fields.selection([
                ('draft','Borrador'),
                ('confirm','Confirmado'),
                ('cancel','Cancelado'),
                 ],    'Estado', select=True, readonly=True), 
            
        }
    _defaults = {  
        'date': lambda *a: time.strftime('%Y-%m-%d'),
        'date_start': lambda *a: time.strftime('%Y-%m-%d'),  
        'date_end': lambda *a: time.strftime('%Y-%m-%d'),    
        'state':'draft'
        }
    
    def action_cancel(self,cr,uid,ids,context=None):
        self.write(cr, uid, ids, {'state':'cancel'})
        return True
    
    
    def action_cancel_to_draft(self,cr,uid,ids,context=None):
        self.write(cr, uid, ids, {'state':'draft'})
        return True
    
    
    def action_confirm(self,cr,uid,ids,context=None):
        self.validate_date(cr, uid, ids, context)
        self.validate_vacation(cr, uid, ids, context)
        self.write(cr, uid, ids, {'state':'confirm'})
        return True
    
    def validate_vacation(self,cr,uid,ids,context=None):
        """
        Verifica que el empleado seleccionado cumple los requisitos para tomar vacaciones
        """
        if not context: context={}
        for this in self.browse(cr,uid,ids,context):  
            #año de trabajo a la fecha
            anos_trabajo = this.employee_id.working_time / self.dias_ano 
            context.update({'year': anos_trabajo})
            #no tiene el año para tomar vacaciones
            if anos_trabajo<=0:
                raise osv.except_osv('Error!',(u'El empleado no puede tomar Vacaciones, tiene %s dias trabajando para la empresa. Debe completar el año para tomar vacaciones' % (int(this.employee_id.working_time))))
            #Validar que las vacaciones las tome despues de la fecha en que cumple el año no antes
            if this.date_next_vacation > datetime.strptime(this.date_start,"%Y-%m-%d"):
                raise osv.except_osv('Error!',(u'El empleado puede tomar las vacaciones despues del: %s. Antes no....!!!' % (this.date_next_vacation)))
            #trata de tomar mas de lo permitido
            if this.duration > this.days_max:
                raise osv.except_osv('Error!',(u'El empleado solo puede tomar %s dias como maximo. No puede tomar mas dias de vacaciones en el año actual.' % (this.days_max)))
        return True

        
    
    def validate_date(self,cr,uid,ids,context=None):
        """
        Valida que las fecha sean correctas
        """
        for this in self.browse(cr,uid,ids):
            employee_name=self.pool.get('hr.employee').name_get(cr,uid,[this.employee_id.id])[0][1] or ''
            
            if this.date_start> this.date_end:
                raise osv.except_osv('Error!',('La fecha de inicio debe ser mayor a la fecha fin'))
            if (this.year_id.date_start > this.date_start):
                raise osv.except_osv('Error!',('El año seleccionado no puede ser mayor a las fechas de inicio y fin'))
            vacation_ids=[]
            #Validar que no tenga registros ese empleado en fechas anteriores ya guardadas y aprobadas
            #        |--------|
            #        :
            #    |--------|
            vacation_ids+=self.pool.get('hr.vacation').search(cr,uid,[('employee_id','=',this.employee_id.id),
                                                                             ('state','=','confirm'),
                                                                             ('date_start','>=',this.date_start),
                                                                             ('date_start','<=',this.date_end)])
            #        |--------|
            #                 :
            #            |--------|
            vacation_ids+=self.pool.get('hr.vacation').search(cr,uid,[('employee_id','=',this.employee_id.id),
                                                                             ('state','=','confirm'),
                                                                             ('date_end','>=',this.date_start),
                                                                             ('date_end','<=',this.date_end)])
            #        |--------|
            #    |----------------|
            vacation_ids+=self.pool.get('hr.vacation').search(cr,uid,[('employee_id','=',this.employee_id.id),
                                                                             ('state','=','confirm'),
                                                                             ('date_start','>=',this.date_start),
                                                                             ('date_end','<=',this.date_end)])
            #        |--------|
            #          |---|
            vacation_ids+=self.pool.get('hr.vacation').search(cr,uid,[('employee_id','=',this.employee_id.id),
                                                                             ('state','=','confirm'),
                                                                             ('date_start','<=',this.date_start),
                                                                             ('date_end','>=',this.date_end)])
            if vacation_ids:
                raise osv.except_osv('Error!',('El Empleado: %s , ya tiene registrada Vacaciones dentro de las fechas: inicial(%s), final(%s)') %(employee_name,this.date_start,this.date_end))
        return True
    
    
    def onchange_employee_id(self, cr, uid, ids, employee_id, context=None):
        if not context:
            context={}
        value = {}
        domain = {}
        employee=self.pool.get('hr.employee').browse(cr,uid,employee_id) or None
        if employee:
            value['department_id']=employee.department_id and employee.department_id.id or None
#            date_start=employee.next_vacation.strftime("%Y-%m-%d")
#            date_end=employee.next_vacation + relativedelta.relativedelta(day=employee.days_vacation)
#            value['date_start']=date_start
#            value['date_end']=date_end.strftime("%Y-%m-%d")
        return {'value': value, 'domain': domain }
vacation()