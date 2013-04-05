# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011 NovaPoint Group LLC (<http://www.novapointgroup.com>)
#    Copyright (C) 2004-2010 OpenERP SA (<http://www.openerp.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################

# can be used for numbers as large as 999 vigintillion
# (vigintillion --> 10 to the power 60)
# tested with Python24      vegaseat      07dec2006

# Modificado por Andres Calle - TRESCLOUD Cía Ltda andres.calle@trescloud.com 
# Basado en el trabajo realizado por Gabriel Umaña gabriumaa@gmail.com

""" 
Este archivo fue realizado por Gabriel Umana  gabriumaa@gmail.com
Es para poner los valores de los cheques en castellano
"""
import math

UNIDADES = ( '', 'Un ', 'Dos ', 'Tres ', 'Cuatro ', 'Cinco ', 'Seis ', 'Siete ', 'Ocho ', 'Nueve ', 'Diez ', 'Once ', 'Doce ', 'Trece ', 'Catorce ', 'Quince ', 'Dieciseis ', 'Diecisiete ', 'Dieciocho ', 'Diecinueve ', 'Veinte ')
DECENAS = ('Venti', 'Treinta ', 'Cuarenta ', 'Cincuenta ', 'Sesenta ', 'Setenta ', 'Ochenta ', 'Noventa ', 'Cien ')
CENTENAS = ('Ciento ', 'Doscientos ', 'Trecientos ', 'Cuatrocientos ', 'Quinientos ', 'Seiscientos ', 'Setecientos ', 'ochocientos ', 'novecientos '  )      

def Numero_a_Texto(number_in):
    convertido = ''
    number_str = str(number_in) if (type(number_in) != 'str') else number_in
    number_str =  number_str.zfill(9)
    millones, miles, cientos = number_str[:3], number_str[3:6], number_str[6:]
    if(millones):
        if(millones == '001'):
            convertido += 'Un Millon '
        elif(int(millones) > 0):
            convertido += '%sMillones ' % __convertNumber(millones)
    if(miles):
        if(miles == '001'):
            convertido += 'Mil '
        elif(int(miles) > 0):
            convertido += '%sMil ' % __convertNumber(miles)
    if(cientos):
        if(cientos == '001'):
            convertido += 'Un '
        elif(int(cientos) > 0):
            convertido += '%s ' % __convertNumber(cientos)
    return convertido

def __convertNumber(n):
    output = ''
    if(n == '100'):
        output = "Cien "
    elif(n[0] != '0'):
        output = CENTENAS[int(n[0])-1]
    k = int(n[1:])
    if(k <= 20):
        output += UNIDADES[k]
    else:
        if((k > 30) & (n[2] != '0')):
            output += '%sy %s' % (DECENAS[int(n[1])-2], UNIDADES[int(n[2])])
        else:
            output += '%s%s' % (DECENAS[int(n[1])-2], UNIDADES[int(n[2])])
    return output


def amount_to_words_es(j):
    try:   
        Arreglo1 = str(j).split(',')
        Arreglo2 = str(j).split('.')
        if (len(Arreglo1) > len(Arreglo2) or len(Arreglo1) == len(Arreglo2)):
             Arreglo = Arreglo1
        else:
            Arreglo = Arreglo2
            
        if (len(Arreglo) == 2):  
            whole = math.floor(j)  
            frac = j - whole
            num = str("{0:.2f}".format(frac))[2:]            
            return Numero_a_Texto(Arreglo[0]) + 'con ' + num + "/100"
        elif (len(Arreglo) == 1):
           return Numero_a_Texto(Arreglo[0]) + 'con ' + '00/100'
    except ValueError:
        return "Cero"