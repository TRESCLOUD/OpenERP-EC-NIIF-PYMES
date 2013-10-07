# -*- coding: UTF-8 -*- #
#########################################################################
# Copyright (C) 2010  Christopher Ormaza, Ecuadorenlinea.net	        #
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
from osv import osv,fields
from tools.translate import _

class res_partner(osv.osv):
    
    def verifica_ruc_spri(self,ruc):
        try:
            if (int(ruc[0]+ruc[1]))<23:
                 prueba1=True
            else:
                 prueba1=False
            
            if (int(ruc[2])==9):
                 prueba2=True
            else:
                 prueba2=False    
        
            val0=int(ruc[0])*4
            val1=int(ruc[1])*3
            val2=int(ruc[2])*2
            val3=int(ruc[3])*7
            val4=int(ruc[4])*6
            val5=int(ruc[5])*5
            val6=int(ruc[6])*4
            val7=int(ruc[7])*3
            val8=int(ruc[8])*2
         
            tot=val0+val1+val2+val3+val4+val5+val6+val7+val8
            veri=tot-((tot/11))*11
         
            if(veri==0):
                if((int(ruc[9]))== 0):
                    prueba3=True
                else:
                    prueba3=False
            else:
                if((int(ruc[9]))==(11-veri)):
                    prueba3=True
                else:
                    prueba3=False
        
            if((int(ruc[10]))+(int(ruc[11]))+(int(ruc[12]))>0):
                prueba4=True
            else:
                prueba4=False
        
            if(prueba1 and prueba2 and prueba3 and prueba4):
                return True
            else: 
                return False
        except:
            return False
        

    def verifica_ruc_spub(self,ruc):
        try: 
            if (int(ruc[0]+ruc[1]))<23:
                prueba1=True
            else:
                prueba1=False
            
            if (int(ruc[2])==6):
                prueba2=True
            else:
                prueba2=False    
        
            val0=int(ruc[0])*3
            val1=int(ruc[1])*2
            val2=int(ruc[2])*7
            val3=int(ruc[3])*6
            val4=int(ruc[4])*5
            val5=int(ruc[5])*4
            val6=int(ruc[6])*3
            val7=int(ruc[7])*2
         
            tot=val0+val1+val2+val3+val4+val5+val6+val7
            veri=tot-((tot/11))*11
         
            if(veri==0):
                if((int(ruc[8]))== 0):
                    prueba3=True
                else:
                    prueba3=False
            else:
                if((int(ruc[8]))==(11-veri)):
                    prueba3=True
                else:
                    prueba3=False
        
            if((int(ruc[9]))+(int(ruc[10]))+(int(ruc[11]))+(int(ruc[12]))>0):
                prueba4=True
            else:
                prueba4=False
        
            if(prueba1 and prueba2 and prueba3 and prueba4):
                 return True
            else: 
                return False
        except:
            return False


    def verifica_ruc_pnat(self,ruc):
        try:
            if (int(ruc[0]+ruc[1]))<23:
                prueba1=True
            else:
                prueba1=False
            
            if (int(ruc[2])<6):
                prueba2=True
            else:
                prueba2=False    
        
            valores = [ int(ruc[x]) * (2 - x % 2) for x in range(9) ]
            suma = sum(map(lambda x: x > 9 and x - 9 or x, valores))
            veri = 10 - (suma - (10*(suma/10)))
            if int(ruc[9]) == int(str(veri)[-1:]):
                prueba3= True
            else:
                prueba3= False
                
            if((int(ruc[10]))+(int(ruc[11]))+(int(ruc[12]))>0):
                prueba4=True
            else:
                prueba4=False
        
            if(prueba1 and prueba2 and prueba3 and prueba4):
                return True
            else: 
                return False
        except:
            return False
        
    def verifica_cedula(self,ced):
        try:
            valores = [ int(ced[x]) * (2 - x % 2) for x in range(9) ]
            suma = sum(map(lambda x: x > 9 and x - 9 or x, valores))
            veri = 10 - (suma - (10*(suma/10)))
            if int(ced[9]) == int(str(veri)[-1:]):
                return True
            else:
                return False
        except:
            return False
        
    def verifica_id_cons_final(self,id):
        b=True
        try:
            for n in id:
                if int(n) != 9:
                    b=False
            return b
        except:
            return False

    
    def _defined_type_ref(self, cr, uid, ids, field_name, arg, context=None):
        res={}
        for partner in self.browse(cr, uid, ids, context):
            ref = partner['ref']
            if(len(ref)==13):
                if self.verifica_ruc_pnat(ref) or self.verifica_ruc_spri(ref) or self.verifica_ruc_spub(ref):
                    res[partner.id]= 'ruc'
                elif self.verifica_id_cons_final(ref):
                    res[partner.id]= 'consumidor'
            elif (len(ref)==10):
                if ref!='9999999999' and self.verifica_cedula(ref):
                    res[partner.id]= 'cedula'
 
        return res
    
    def _assign_code(self, cr, uid, ids, field, arg, context=None):
        ''' Función que asigna un código a cada tipo de identificación.'''        
        
        res = {}

        for partner in self.browse(cr, uid, ids, context):
            foreing = partner['foreing']
            ref = partner['ref']
            if ref:
                if foreing==False:
                    if (len(ref)==13):
                        if self.verifica_ruc_pnat(ref) or self.verifica_ruc_spri(ref) or self.verifica_ruc_spub(ref):
                            res[partner.id]= 'R'
                        elif self.verifica_id_cons_final(ref):
                            res[partner.id]= 'F'                   
                    if ref!='9999999999' and len(ref)==10:
                        res[partner.id]= 'C'
                    if ref=='9999999999':
                        res[partner.id]= 'F'
                else:
                    res[partner.id]= 'P'
            else:
                res[partner.id]= 'O'
        return res
    
    _inherit = 'res.partner'
    
    _columns = {
                # Modificado para que sepueda ingresar pasaportes de hasta 32 caracteres
                'ref':fields.char('CEDULA/RUC', size=32),
                'type_ref':fields.char('CEDULA/RUC Type', size=64, ),
                'foreing':fields.boolean('Foreing?'),
                'code': fields.function(_assign_code, string='Code sri', type='string', store=False, method=True, help='Used to generate the ats',),
        }
    _sql_constraints = [('ref_uniq','unique(ref)', 'The value of CEDULA/RUC must be unique, this value already exists')] 
    
    
    def create(self, cr, uid, values, context=None):
        if not context:
            context = {}
        
        # If foreing is True don't have to verify the CI/RUC
        foreing = False

        if 'foreing' in values:
            foreing = values['foreing']
            
        if context.get('skip_ruc_validation') or foreing:
            return super(res_partner, self).create(cr, uid, values, context)
        ref = None

        try:
            ref = values['ref']
            if not ref:
                values['type_ref']=''
                return super(res_partner, self).create(cr, uid, values, context)
            for i in ref:
                int(i)
            if(len(ref)==13):
                dato=ref
                if(int(dato[2])==9):
                    #verify if partner is a private company
                    if self.verifica_ruc_spri(ref):
                        values['type_ref']='ruc'
                        return super(res_partner, self).create(cr, uid, values, context)
                    elif self.verifica_id_cons_final(ref):
                        values['type_ref']='consumidor'
                        return super(res_partner, self).create(cr, uid, values, context)
                    else:
                        raise osv.except_osv(_('Invalid action !'), _('CEDULA/RUC of Partner is incorrect, please verify'))
                elif(int(dato[2])==6):
                    #verify if partner is a statal company
                    if self.verifica_ruc_spub(ref):
                        values['type_ref']='ruc'
                        return super(res_partner, self).create(cr, uid, values, context)
                    else:
                        raise osv.except_osv(_('Invalid action !'), _('CEDULA/RUC of Partner is incorrect, please verify'))
                elif(int(dato[2])<6):
                    #verify if partner is a natural person 
                    if self.verifica_ruc_pnat(ref):
                        values['type_ref']='ruc'
                        return super(res_partner, self).create(cr, uid, values, context)
                    else:
                        raise osv.except_osv(_('Invalid action !'), _('CEDULA/RUC of Partner is incorrect, please verify'))
                else:   
                    raise osv.except_osv(_('Invalid action !'), _('CEDULA/RUC of Partner is incorrect, please verify'))
            elif(len(ref)==10):
                #verify the dni or Cedula of partner 
                if self.verifica_cedula(ref):
                    values['type_ref']='cedula'
                    return super(res_partner, self).create(cr, uid, values, context)
                else:
                    raise osv.except_osv(_('Invalid action !'), _('CEDULA/RUC of Partner is incorrect, please verify'))
            else:
                raise osv.except_osv(_('Invalid action !'), _('CEDULA/RUC of Partner is incorrect, please verify'))
        except ValueError:
            raise osv.except_osv(_('Invalid action !'), _('CEDULA/RUC of Partner is incorrect, please verify'))      
        except TypeError:
            raise osv.except_osv(_('Invalid action !'), _('CEDULA/RUC of Partner is incorrect, please verify'))
        except KeyError:
            return super(res_partner, self).create(cr, uid, values, context)


    def write(self, cr, uid, ids, values,context=None):
        if not context:
            context = {}

        # If foreing is True don't have to verify the CI/RUC
        # First, check if change the value of foreing, else use the stored value
        foreing = False
        
        if 'foreing' in values:
            foreing = values['foreing']
        else:
            foreing = self.pool.get('res.partner').browse(cr, uid, ids[0]).foreing
            
        if context.get('skip_ruc_validation') or foreing:
            return super(res_partner, self).write(cr, uid, ids, values, context)
        ref = None
        try:
            ref = values['ref']
            if not ref:
                values['type_ref']=''
                return super(res_partner, self).write(cr, uid, ids, values, context)
            for i in ref:
                int(i)
            if(len(ref)==13):
                dato=ref
                if(int(dato[2])==9):
                    #verify if partner is a private company
                    if self.verifica_ruc_spri(ref):
                        values['type_ref']='ruc'
                        return super(res_partner, self).write(cr, uid, ids, values, context)
                    elif self.verifica_id_cons_final(ref):
                        values['type_ref']='consumidor'
                        return super(res_partner, self).write(cr, uid, ids, values, context)
                    else:
                        raise osv.except_osv(_('Invalid action !'), _('CEDULA/RUC of Partner is incorrect, please verify'))
                elif(int(dato[2])==6):
                    #verify if partner is a statal company
                    if self.verifica_ruc_spub(ref):
                        values['type_ref']='ruc'
                        return super(res_partner, self).write(cr, uid, ids, values, context)
                    else:
                        raise osv.except_osv(_('Invalid action !'), _('CEDULA/RUC of Partner is incorrect, please verify'))
                elif(int(dato[2])<6):
                    #verify if partner is a natural person 
                    if self.verifica_ruc_pnat(ref):
                        values['type_ref']='ruc'
                        return super(res_partner, self).write(cr, uid, ids, values, context)
                    else:
                        raise osv.except_osv(_('Invalid action !'), _('CEDULA/RUC of Partner is incorrect, please verify'))
                else:   
                    raise osv.except_osv(_('Invalid action !'), _('CEDULA/RUC of Partner is incorrect, please verify'))
            elif(len(ref)==10):
                #verify the dni or Cedula of partner 
                if self.verifica_cedula(ref):
                    values['type_ref']='cedula'
                    return super(res_partner, self).write(cr, uid, ids, values, context)
                else:
                    raise osv.except_osv(_('Invalid action !'), _('CEDULA/RUC of Partner is incorrect, please verify'))
            else:
                raise osv.except_osv(_('Invalid action !'), _('CEDULA/RUC of Partner is incorrect, please verify'))
        except ValueError:
            raise osv.except_osv(_('Invalid action !'), _('CEDULA/RUC of Partner is incorrect, please verify'))      
        except TypeError:
            raise osv.except_osv(_('Invalid action !'), _('CEDULA/RUC of Partner is incorrect, please verify'))
        except KeyError:
            return super(res_partner, self).write(cr, uid, ids, values, context)

res_partner()
