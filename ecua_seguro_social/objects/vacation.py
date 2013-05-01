
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
     
    
    def get_year_start_end(self, cr, uid, last_vacation_id, employee_id, year_vacation, date_start_vacation, date_end_vacation, context=None):
        """
        Calcula y devuelve desde que año hasta que ano se va a tomar vacaciones
        Ejm. del 2 al 4 ano se va a tomar vacaciones 
        """
#        el algoritmo es:
#        obtener la fecha de inicio del primer contrato y en base a eso saber desde que año hasta que año le corresponden las vacaciones
#        si hay registros de vacaciones para ese empleado se utiliza la fecha fin del ultimo registro para calcular el año de inicio
#        y la fecha de inicio de la vacacion actual para calcular el año fin
#        si no hay registros el año inicio sera 0
#        y la fecha de inicio de la vacacion actual se utiliza para calcular el año fin
        if not context: context={}
        company_obj= self.pool.get('res.company')
        year_start=0
        year_end=0
        date_start_period=self.pool.get('hr.employee').get_date_last_contract_continuo(cr,uid, employee_id, self.days_holgura ,context)
        date_start=datetime.strptime(date_start_period,"%Y-%m-%d")
        if last_vacation_id:
#            Ejemplo: si la fecha de inicio del contrato es 01/01/2010, la fecha fin de la ultima vacacion es 01/02/2012 y la fecha de inicio de la vacacion que va a tomar es 01/02/2013
#            el año de inicio seria 2(2012-2010); el año fin seria 3(2013-2010)
            date_end=datetime.strptime(self.read(cr,uid,[last_vacation_id],['date_end'])[0]['date_end'],"%Y-%m-%d") # or this.date_end probar
            year_start_aux= date_end - date_start
            year_start=year_start_aux.days / self.dias_ano
            year_end_aux=  datetime.strptime(date_end_vacation,"%Y-%m-%d") - date_start
            year_end= year_end_aux.days / self.dias_ano
        else:
            #primera vez que se va a dar vacaciones acumuladas
            year_start = 0
            #calcular el año de inicio de las vacaciones en base al año configurado en la compañia
            company_id= company_obj._company_default_get(cr, uid, 'hr.vacation', context=context)
            company= company_obj.browse(cr, uid, company_id, context)
            if not company.year_vacation_accumulated_id:
                raise osv.except_osv(_(u'Advertencia'),_(u'Debe configurar el año del que se va a calcular las vacaciones acumuladas, en Compañia'))
            #comparar si el año  al que pertenece la vacacion es menor al año configurado en la compañia 
            if year_vacation < company.year_vacation_accumulated_id.date_start[0:4]:
                raise osv.except_osv(_(u'Advertencia'),_(u'A partir del año %s se pagan vacaciones acumuladas no antes') % (company.year_vacation_accumulated_id.date_start))
            date_end=datetime.strptime(company.year_vacation_accumulated_id.date_stop,"%Y-%m-%d") # or this.date_end probar
            year_start_aux= date_end - date_start
            year_start=year_start_aux.days / self.dias_ano
            #pasar la fecha a fin de año para que se puedan calcular aquellos contratos que no inician al inicio del año
            #ejm: el contrato inicia el 01/06/2010 y la fecha de la vacacion que se va a registrar es 01/05/2012
            #esto devolveria 0,1 cuando en realidad deberia ser 0,2
            #no se incluiria como un año mas por eso se pasa la fecha de la vacacion a fin de año 31/12/2012 
            date_aux=year_vacation + date_start_vacation[4:10]
            now = datetime.strptime(date_aux,"%Y-%m-%d")
            year_adjusted= now + relativedelta.relativedelta(month=12, day=31)
            year_end_aux = year_adjusted - date_start
            year_end = year_end_aux.days / self.dias_ano
        return {'year_start':year_start,'year_end':year_end}
    
    def get_date_next_vacation(self, cr, uid, last_vacation_id, employee_id, year_vacation, date_start, date_end, context={} ):
        """
        Calcula la fecha en que se puede tomar las siguientes vacaciones
        Devuelve un diccionario (key= año de la vacacion, value= fecha de la vacacion) para los años que se dese tener una aproximacion
        si years=4 y la fecha de la proxima vacacion es 01/01/2010, se calculara la fecha de las proximas vacaciones para los 4 años siguientes, hasta el 2014
        """
        def get_years_aproximated(date_base, num_years=1):
            date_dict={}
            for i in range(1,num_years+1):
                date_aux= (date_base + relativedelta.relativedelta(years=+i)).strftime(self.DATE_FORMAT)
                date_dict[date_aux[0:4]]=date_aux
            return date_dict
        
        obj_contract = self.pool.get('hr.contract')
        next_vacation=datetime.now()
        year_date_start= datetime.strptime(date_start[0:4] + "-01-01",self.DATE_FORMAT).strftime(self.DATE_FORMAT)
        if last_vacation_id:
            vacation= self.browse(cr,uid,last_vacation_id,context)
            if vacation.days_vacation_remaining<=0:
                next_vacation= datetime.strptime(vacation.date_end , self.DATE_FORMAT) + relativedelta.relativedelta(years=+1)
            else:
                next_vacation= datetime.strptime(vacation.date_end , self.DATE_FORMAT) + relativedelta.relativedelta(days=+1)
        else:
            #obtener la ultima vacacion del año actual sin considerar la que se esta procesando y a esa fecha sumarle un año si ya tomo todos dias de vacaciones del año actual
            criterios_busqueda=[('employee_id','=',employee_id),
                                ('date_end','<',date_start),
                                ('state','=','confirm')]

            #obtener vacaciones anteriores al registro actual
            vacation_ids=self.search(cr,uid,criterios_busqueda,order="date_start")
            if vacation_ids:
                vacation= self.browse(cr,uid,vacation_ids[-1],context)
                if vacation.days_vacation_remaining<=0:
                    next_vacation= datetime.strptime(vacation.date_end , self.DATE_FORMAT) + relativedelta.relativedelta(years=+1)
                else:
                    next_vacation= datetime.strptime(vacation.date_end , self.DATE_FORMAT) + relativedelta.relativedelta(days=+1)
            else:
                #si todavia no tiene vacaciones registradas
                #calcular la fecha de vacacion en base a la fecha del primer contrato
                #obtener la fecha de inicio del ultimo periodo continuo
                periodo_date_start=self.pool.get('hr.employee').get_date_last_contract_continuo(cr,uid, employee_id, self.days_holgura ,context)
                #porque de otra manera no se tomaria el primer contrato sino el primero del ultimo periodo continuo
                contract_ids = obj_contract.search(cr, uid, [('employee_id','=',employee_id),('date_start','>=',periodo_date_start)], order='date_start', context=context)
                if contract_ids:
                    first_contract =obj_contract.browse(cr,uid,contract_ids[0])
                    next_vacation= datetime.strptime(first_contract.date_start, self.DATE_FORMAT) + relativedelta.relativedelta(years=+1)
        years_calculate= int(year_vacation) - int(next_vacation.strftime(self.DATE_FORMAT)[0:4]) 
        if years_calculate>0:
            date_vacation= get_years_aproximated(next_vacation, num_years=years_calculate)
            return date_vacation[year_vacation]
        else:
            return next_vacation.strftime(self.DATE_FORMAT)
    
    def _calculate_next_vacation(self, cr, uid, ids, field_name, arg , context=None):
        """
        Calcula y devuelve la fecha en que el empleado debe tomar las proximas vacaciones segun el año que correspondan las vacaciones
        """
        if not context: context={}
        #pasar bandera de que a las funciones se las llama de la propia clase
        context.update({'extern':False})
        res={}
        obj_contract = self.pool.get('hr.contract')
        for this in self.browse(cr,uid,ids):
            last_vacation_id= this.last_vacation_id and this.last_vacation_id.id or None
            next_vacation= self.get_date_next_vacation(cr, uid, last_vacation_id, this.employee_id.id, this.year_id.date_start[0:4], this.date_start, this.date_end, context)
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
    
    def _calculate_days_vacation_remaining(self,cr,uid,ids,field_name,arg,context=None):
        """
        Calcula y devuelve los dias que le quedan de vacaciones al empleado
        Considerando que ya ha podido tomar parte de las vacaciones que le corresponden en el periodo
        """
        if not context: context={}
        #pasar bandera de que a las funciones se las llama de la propia clase
        context.update({'extern':False})
        res={}
        for this in self.browse(cr,uid,ids,context):
            res[this.id]=  this.days_max - this.duration 
        return res
    
    def _calculate_days_current(self,cr,uid,ids, field_name,  args ,context=None):
        """
        Busca y calcula los dias de vacaciones que haya tomado en el periodo actual excluyendo las que son superiores en fecha a la actual
        @param vacation_id: objeto hr.vacation
        """
        if not context: context={}
        res={}
        for this in self.browse(cr,uid,ids,context):
            total_current=0
            last_vacation_id= this.last_vacation_id and this.last_vacation_id.id or None
            if last_vacation_id and this.id!= last_vacation_id :  
                year_id_last_vacation= self.read(cr, uid, [last_vacation_id], ['year_id'])[0]['year_id'] 
                if this.year_id.id == year_id_last_vacation[0]:
                    total_current=this.last_vacation_id.duration
            else:
                #porque puede que las vacaciones las tome el 2013 pero pertenecen al año 2012 buscar en el año correcto, excluyendo los registros superiores a la vacacion actual
                vacation_current_ids=self.search(cr,uid,[('state','=','confirm'),
                                                           ('employee_id','=',this.employee_id.id),
                                                           ('year_id','=',this.year_id.id),
                                                           ('date_end','<',this.date_start),
                                                           ('id','!=',this.id)])
                for vacacion in self.browse(cr,uid,vacation_current_ids,context):
                    total_current+=vacacion.duration
            res[this.id]= total_current
        return res
    
    
    def get_days_acumulated(self,cr,uid,last_vacation_id, employee_id, current_year, date_end  ,year_start=0, year_end=4,context=None):
        """
        Busca y calcula los dias de vacaciones que tenga acumulados en los años especificados
        @param last_vacation_id: id del registro de hr.vacation
        @param employee_id: id del registro de hr.employee
        @param current_year: año actual desde el que empezar a buscar dias acumulados
        @param date_end: fecha hasta la que buscar registros guardados
        @param year_start: el numero de años anteriores hasta los que buscar vacaciones acumuladas
        @param year_end: el numero de años anteriores hasta los que buscar vacaciones acumuladas
        Ejm. si la fecha que se esta haciendo las vacaciones es 01/01/2013 y year_end=4,
        Se verificara hasta el 01/01/2009 si hay vacaciones acumuladas.
        se busca desde el periodo actual hacia atras 2012, 2011, 2010 , 2009, ......
        """
        if not context: context={}
        dias_acumulados=0
        year_acumulados=0
        year_date_start= datetime.strptime(current_year + "-01-01",self.DATE_FORMAT).strftime(self.DATE_FORMAT)
        year_date_end= datetime.strptime(current_year + "-12-31",self.DATE_FORMAT).strftime(self.DATE_FORMAT)
        if last_vacation_id:
            dias_restantes= self.browse(cr, uid, last_vacation_id).days_vacation_remaining
            if dias_restantes>0:
                return dias_restantes
        aux_year=1
        for year in range(year_start,year_end):
            date_start_after=datetime.strptime(year_date_start , self.DATE_FORMAT) + relativedelta.relativedelta(years=-aux_year)
            date_end_after=datetime.strptime(year_date_end , self.DATE_FORMAT) + relativedelta.relativedelta(years=-aux_year)
            aux_year+=1
            vacation_after_ids=self.search(cr,uid,[('state','=','confirm'),
                                                   ('employee_id','=', employee_id),
                                                   ('date_start','>=', date_start_after),
                                                   ('date_end','<=', date_end_after)], order="date_start")
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
    
    
    def _calculate_days_vacation_acumulated(self,cr,uid,ids,field_name,arg,context=None):
        """
        Calcula y devuelve los dias que le quedan por tomar de vacaciones sin incluir el registro actual
        solo las acumuladas y las tomadas en el periodo actual
        """
        if not context: context={}
        #pasar bandera de que a las funciones se las llama de la propia clase
        context.update({'extern':False})
        res={}
        for this in self.browse(cr,uid,ids,context):
            anos_trabajo = this.employee_id.working_time / self.dias_ano
            #si es el primer año de trabajo no va a tener vacaciones acumuladas
            if anos_trabajo<=1:
                res[this.id] = 0
                continue
            #recuperar el ultimo registro ingresado para en base a la fecha de ese calcular cuantos años no ha tomado vacaciones
            last_vacation_id= this.last_vacation_id and this.last_vacation_id.id or None
            years=self.get_year_start_end(cr, uid, last_vacation_id, this.employee_id.id, this.year_id.date_start[0:4], this.date_start, this.date_end ,context)
            res[this.id] = self.get_days_acumulated(cr, uid, last_vacation_id, this.employee_id.id, this.date_start[0:4], this.date_end, years.get('year_start'), years.get('year_end'), context)
        return res
    
    def get_days_max(self, days_current_year, days_vacation_acumulated, days_now, last_vacation_id =None,context={}):
        """
        @param days_current_year:  dias tomados el año actual
        @param days_vacation_acumulated:  dias acumulados
        @param days_now: dias que debe tomar el año actual
        @param last_vacation_id: objeto vacation de la ultima vacacion tomada en caso de haber
        @return: float con el numero de dias maximos que puede tomar de vacaciones
        """
        #si ya tomo los dias de vacaciones en el año actual solo permitir tomar los dias restantes.
        #pero en caso de tomar vacaciones del año anterior en fechas del año actual, se debe permitir tomar las que le corresponde el año actual si es que ya puede tomarlas
        if days_current_year>0:
            if last_vacation_id:
                #solo permitir las restantes y las del año actual si ya puede tomarlas
                return last_vacation_id.days_vacation_remaining + days_now
            else:
                return 0
        else:
            if days_vacation_acumulated==0:
                return days_now
            else:
                return days_vacation_acumulated + days_now
            
    def _calculate_days_max(self, cr,uid, ids, field_name, args , context=None):
        """
        Calcula maximo de dias que se le puede permitir tomar de vacaciones
        @param vacation_id:  objeto hr.vacation 
        """
        if not context: context={}
        #pasar bandera de que a las funciones se las llama de la propia clase
        context.update({'extern':False})
        res={}
        for this in self.browse(cr,uid, ids, context): 
            res[this.id]= self.get_days_max(this.days_current_year, this.days_vacation_acumulated, this.days_now, this.last_vacation_id)
        return res
    
    def get_days_now(self, cr,uid, days_current_year, employee_id, year, date_start, date_end, last_vacation=None, context={} ):
        """
        @param days_current_year: el numero de dias tomados el año actual
        @param employee_id: Id del empleado
        @param year: fecha de inicio del año
        @param date_start: fecha de inicio de la vacacion
        @param date_end: fecha fin de la vacacion
        @param last_vacation_id: objeto vacation que representa la ultima vacacion tomada por el empleado
        @return: float con el numero dias que le corresponden tomar el año actual
        """
        last_vacation_id= last_vacation and last_vacation.id or None
        date_next_vacation=self.get_date_next_vacation(cr, uid,last_vacation_id, employee_id, year, date_start, date_end, context)
        #validar si ya puede tomar las vacaciones del año seleccionado
        #modificando la fecha de las proximas vacaciones.
        next_vacation_adjusted= year + date_next_vacation[4:10]
        if date_start >= next_vacation_adjusted:
            year_date_start= datetime.strptime(date_start[0:4] + "-01-01",self.DATE_FORMAT).strftime(self.DATE_FORMAT)
            #posibilidad de que en las vacaciones anteriores no se hayan tomado los dias que le corresponden al año actual, solo los dias acumuladas
            #por eso es necesario calcularlos si es el caso
            if days_current_year>0 :
                if last_vacation and last_vacation.days_now==0:
                    years=self.get_year_start_end(cr, uid, last_vacation_id, employee_id, year, date_start, date_end ,context)
                    return self.get_days_vacation(years.get('year_end'), context)
                else:
                    return 0
            else:
                years=self.get_year_start_end(cr, uid, last_vacation_id, employee_id, year, date_start, date_end ,context)
                return self.get_days_vacation(years.get('year_end'), context)
        else:
            return 0
        
    def _calculate_days_now(self,cr,uid,ids,field_name,arg,context=None):
        """
        Calcula y devuelve los dias que tiene que tomar el presente año
        Considerando que ya ha podido tomar esos dias
        """
        if not context: context={}
        #pasar bandera de que a las funciones se las llama de la propia clase
        context.update({'extern':False})
        res={}
        for this in self.browse(cr,uid,ids,context):
            res[this.id]= self.get_days_now(cr, uid, this.days_current_year, this.employee_id.id, this.year_id.date_start[0:4], this.date_start, this.date_end, this.last_vacation_id, context)
        return res
    
    
    STATES={'draft': [('readonly', False)]}
    '''
    Open ERP Model
    '''
    _name = 'hr.vacation'
    _description = 'hr.vacation'

    _columns = {
            'employee_id':fields.many2one('hr.employee', 'Empleado', required=True),
            'department_id': fields.related('employee_id','department_id', type='many2one', relation='hr.department', string='Departamento'), 
            'year_id':fields.many2one('account.fiscalyear', 'Pertenecen al Año', required=True),    
            #TODO : import time required to get currect date
            'date': fields.date('Fecha'), 
            #TODO : import time required to get currect date
            'date_start': fields.date('Fecha Inicio',required=True), 
            #TODO : import time required to get currect date
            'date_end': fields.date('Fecha Fin',required=True), 
            'duration': fields.function(_calculate_duration, method=True, type='float', digits_compute=dp.get_precision('Vacation precision'), string='Duracion',
                        store={
                              'hr.vacation': (lambda self,cr,uid,ids,c={}:ids,['date_start','date_end'],10 ),
                              }),
            'days_vacation_remaining': fields.function(_calculate_days_vacation_remaining, method=True, type='float', digits_compute=dp.get_precision('Vacation precision'), string='Dias Restantes',
                        store={
                              'hr.vacation': (lambda self,cr,uid,ids,c={}:ids,['employee_id','year_id','date_start','date_end','state'],20 ),
                              }),
            'days_vacation_acumulated': fields.function(_calculate_days_vacation_acumulated, method=True, type='float', digits_compute=dp.get_precision('Vacation precision'), string='Dias Acumulados',
                      store={
                              'hr.vacation': (lambda self,cr,uid,ids,c={}:ids,['employee_id','year_id','date_start','date_end','state'],22 ),
                              }),
            'days_current_year': fields.function(_calculate_days_current, method=True, type='float', digits_compute=dp.get_precision('Vacation precision'), string='Dias tomados en el años actual',
                      store={
                              'hr.vacation': (lambda self,cr,uid,ids,c={}:ids,['employee_id','year_id','date_start','date_end','state'],11 ),
                              }),
            'days_max': fields.function(_calculate_days_max, method=True, type='float', digits_compute=dp.get_precision('Vacation precision'), string='Dias Maximos Permitidos',
                          store={
                              'hr.vacation': (lambda self,cr,uid,ids,c={}:ids,['employee_id','year_id','date_start','date_end','state'],23 ),
                              }),
            'date_next_vacation': fields.function(_calculate_next_vacation, method=True, type='date', string='Fecha en que puede tomar Vacaciones',
                          store={
                              'hr.vacation': (lambda self,cr,uid,ids,c={}:ids,['employee_id','year_id','date_start','date_end','state'],13 ),
                              }), 
            'days_now': fields.function(_calculate_days_now, method=True, type='float', digits_compute=dp.get_precision('Vacation precision'), string='Dias a tomar en el año actual',
                         store={
                              'hr.vacation': (lambda self,cr,uid,ids,c={}:ids,['employee_id','year_id','date_start','date_end','state'],12 ),
                              }),
            
            'last_vacation_id':fields.many2one('hr.vacation', 'Vacacion Anterior', required=False),  
             
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
    _rec_name = 'date_start' 
    
    def get_last_vacation(self, cr, uid, vacation_id, employee_id, date_start, context):
        vacation_ids=self.search(cr,uid,[('state','=','confirm'),
                                             ('employee_id','=',employee_id),
                                             ('date_end','<',date_start),
                                             ('id','!=',vacation_id)],order="date_start")
        return vacation_ids and vacation_ids[-1] or None
    
    def action_cancel(self,cr,uid,ids,context=None):
        self.write(cr, uid, ids, {'state':'cancel'})
        return True
    def copy(self, cr, uid, id, default=None, context=None): 
        if not context:
            context={}
        if not default: default={}
        default.update({'last_vacation_id':None})
        res_id = super(vacation, self).copy(cr, uid, id, default, context)
        return res_id 
    
#    def write(self, cr, uid, ids, vals, context=None):
#        if not context:
#            context={}
#        #TODO: process before updating resource
#        if 'employee_id' in vals:
#            self.pool.get('hr.employee').write(cr, uid, [vals.get('employee_id')],
#                                               {'last_vacation_id': vals.get('last_vacation_id',None)})
#        elif 'last_vacation_id' in vals:
#            this=self.browse(cr,uid, ids[0], context)
#            self.pool.get('hr.employee').write(cr, uid, [this.employee_id.id],
#                                               {'last_vacation_id': vals.get('last_vacation_id',None)})
#        else:
#            this=self.browse(cr,uid, ids[0], context)
#            self.pool.get('hr.employee').write(cr, uid, [this.employee_id.id],
#                                               {'last_vacation_id': this.last_vacation_id and this.last_vacation_id.id or None})
#        res = super(vacation, self).write(cr, uid, ids, vals, context)
#        return res 
    def action_cancel_to_draft(self,cr,uid,ids,context=None):
        self.write(cr, uid, ids, {'state':'draft'})
        return True
    
    def action_confirm(self,cr,uid,ids,context=None):
        self.validate_date(cr, uid, ids, context)
        self.validate_vacation(cr, uid, ids, context)
        this=self.browse(cr, uid, ids[0])
        self.write(cr, uid, ids, {'state':'confirm',
                                  'date':time.strftime('%Y-%m-%d'),
                                  'last_vacation_id': self.get_last_vacation(cr, uid, this.id, this.employee_id.id, this.date_start, context)})
        return True
    def action_validate(self,cr,uid,ids,context=None):
        this=self.browse(cr, uid, ids[0])
        self.write(cr, uid, ids, {'last_vacation_id': self.get_last_vacation(cr, uid, this.id, this.employee_id.id, this.date_start, context)})
        self.validate_date(cr, uid, ids, context)
        self.validate_vacation(cr, uid, ids, context)
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
            if datetime.strptime(this.date_next_vacation,"%Y-%m-%d") > datetime.strptime(this.date_start,"%Y-%m-%d") and this.days_vacation_acumulated<=0:
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
    
    
    def onchange_employee_id(self, cr, uid, ids, employee_id, date_start, context=None):
        if not context:
            context={}
        value = {}
        domain = {}
        if employee_id:
            employee=self.pool.get('hr.employee').browse(cr,uid,employee_id) or None
            value['department_id']=employee.department_id and employee.department_id.id or None
            vacation_id= ids and ids[0] or None
            value['last_vacation_id']= self.get_last_vacation(cr, uid, vacation_id, employee_id,date_start, context)
            
#            date_start=employee.next_vacation.strftime("%Y-%m-%d")
#            date_end=employee.next_vacation + relativedelta.relativedelta(day=employee.days_vacation)
#            value['date_start']=date_start
#            value['date_end']=date_end.strftime("%Y-%m-%d")
        return {'value': value, 'domain': domain }
vacation()