
# -*- encoding: utf-8 -*-
########################################################################
#                                                                       
# @authors: Pablo Vizhnay, Patricio Rangles                                                                           
# Copyright (C) 2012  Geoinformatica, TRESCLOUD Cia Ltda.                                 
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
import time
import datetime
from datetime import date
import pooler
from tools.translate import _
import decimal_precision as dp

class institucion_credito(osv.osv):
    
    _name = 'institucion.credito'
    
    _columns = {
        'name': fields.char('Nombre de la Institucion', size=64, required=True),
                }
    
institucion_credito()

class account_voucher(osv.osv):
    
    _inherit = 'account.voucher'
    _name = 'account.voucher'
    
    _n1 = ( "un","dos","tres","cuatro","cinco","seis","siete","ocho",
                "nueve","diez","once","doce","trece","catorce","quince",
                "dieciséis","diecisiete","dieciocho","diecinueve","veinte")
    _n11 =( "un","dós","trés","cuatro","cinco","séis","siete","ocho","nueve")
        
    _n2 = ( "dieci","veinti","treinta","cuarenta","cincuenta","sesenta",
                "setenta","ochenta","noventa")
        
    _n3 = ( "ciento","dosc","tresc","cuatroc","quin","seisc",
                "setec","ochoc","novec")

    def NumeroTextoCompleto(self,num):

        try:
            tmp = '%.2f' % float(num)
            ent = tmp.split(".")[0]
            fra = tmp.split(".")[1]

            enteros = self.numerals(int(ent))
            decimas = self.numerals(int(fra))

            # print "enteros: ", enteros, "decimas :", decimas

            if enteros == 'cero' and decimas != 'cero' :
                letras = " son centavillos, no merece un pagaré "
            else:
                if decimas == 'cero':
                    letras = enteros.upper() + " "
                else:
                    letras = enteros.upper() + " CON " + decimas.upper() + " /100" 
        except:
            letras = "acá hay algo que no me gusta..."

        self.numero = str(num)
        self.largo  = len(letras)
        self.escribir = letras
        return letras

    def numerals(self, nNumero):
        """
        numerals(nNumero) --> cLiteral

        Convierte el número a una cadena literal de caracteres
        P.e.:       201     -->   "doscientos uno"
                   1111     -->   "mil ciento once"

        """
        # función recursiva auxiliar esta es "la" rutina ;)
        def _numerals(n):

            # Localizar los billones
            prim,resto = divmod(n,10L**12)
            if prim!=0:
                if prim==1:
                    cRes = "un billón"
                else:
                    cRes = _numerals(prim)+" billones" # Billones es masculino
                if resto!=0:
                    cRes += " "+_numerals(resto)
            else:
            # Localizar millones
                prim,resto = divmod(n,10**6)
                if prim!=0:
                    if prim==1:
                        cRes = "un millón"
                    else:
                        cRes = _numerals(prim)+" millones" # Millones es masculino
                    if resto!=0:
                        cRes += " " + _numerals(resto)
                else:
            # Localizar los miles
                    prim,resto = divmod(n,10**3)
                    if prim!=0:
                        if prim==1:
                            cRes="mil"
                        else:
                            cRes=_numerals(prim)+" mil"
                        if resto!=0:
                            cRes += " " + _numerals(resto)
                    else:
            # Localizar los cientos
                        prim,resto=divmod(n,100)
                        if prim!=0:
                            if prim==1:
                                if resto==0:
                                    cRes="cien"
                                else:
                                    cRes="ciento"
                            else:
                                cRes=self._n3[prim-1]
                                cRes+="ientos"
                            if resto!=0:
                                cRes+=" "+_numerals(resto)
                        else:
            # Localizar las decenas
                            if n<=20:
                                cRes=self._n1[n-1]
                            else:
                                prim,resto=divmod(n,10)
                                cRes=self._n2[prim-1]
                                if resto!=0:
                                    if prim==2:
                                        cRes+=self._n11[resto-1]
                                    else:
                                        cRes+=" y "+self._n1[resto-1]
            return cRes

        # Nos aseguramos del tipo de <nNumero>
        # se podría adaptar para usar otros tipos (pe: float)
        nNumero = long(nNumero)
        if nNumero < 0:
            # negativos
            cRes = "menos "+_numerals(-nNumero)
        elif nNumero == 0:
            # cero
            cRes = "cero"
        else:
            # positivo
            cRes = _numerals(nNumero)

        # Excepciones a considerar
        if nNumero % 10 == 1 and nNumero % 100 != 11:
            cRes += "o"
        return cRes

# Funciones que convierten a texto un valor numerico FIN
    
    def _valor_en_texto(self, cr, uid, ids, field_name, arg, context):
        
        records = self.browse(cr, uid, ids)
        result = {}
        for r in records:       
            
            result[r.id] = self.NumeroTextoCompleto(r.valor_cheque),
                        
        return result
#        
#        
#    def onchange_otro_nombre(self, cr, uid, otro_nombre, context=None):
#        
#        return True
    def print_report(self, cr, uid, ids, context=None):
   
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'impresion_cheque',    # the 'Service Name' impresion.cheque                                 the report
            'datas' : {
                    'model' : 'account.voucher',    # Report Model
                    'res_ids' : ids
                    }
                }
 
    _columns = {
        #'voucher_bool':fields.boolean('Tarjeta de Credito?'),
        'numero_cheque': fields.char('Numero de Cheque', size=64),
        'cuenta_cheque': fields.char('Numero de Cuenta', size=64),
        'banco_cheque':fields.char('Nombre del Banco', size=64),
        'otro_nombre': fields.boolean('Seleccionar otro nombre para el cheque'),
        'nombre_cheque': fields.char('Nombre para el cheque', size=64),
        'valor_cheque': fields.float('Valor', digits=(5,2)),
        'valor_texto_cheque': fields.function(_valor_en_texto, method=True, type='text', string='Valor', store=False),
        'fecha_cheque': fields.date('Fecha'),
        'ciudad_cheque': fields.char('Ciudad', size=64),
        
        #Voucher
        'lote_voucher':fields.char('Numero de Lote de Voucher', size=64),
        'institucion_id':fields.many2one('institucion.credito', 'Institucion de credito'),                
                }
    
    _defaults = {  
        'otro_nombre': False,
        #'voucher_bool': False,
        }
    
    
account_voucher()


class account_journal(osv.osv):
    
    _inherit = 'account.journal'
    _name = 'account.journal'
    
    _columns = {
        'imprimir_cheque': fields.boolean('Habilitar para generar la impresion de cheques desde egresos (Pagos)'),
        'ingresar_voucher': fields.boolean('Habilitar para ingresar la informacion de vouchers desde ingresos (Cobros)'),
                }
    
    _defaults = {  
        'imprimir_cheque': False,
        'ingresar_voucher': False,
        }
    
account_journal()

 
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: