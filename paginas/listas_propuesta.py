"""Listas editables de objetivos y momentos, con orden y borrador persistente."""
from uuid import uuid4
import streamlit as st


def editar_lista(repo,caso_id,draft,nombre,guardar):
    campos=('texto',) if nombre=='objetivos_especificos' else ('etiqueta','descripcion')
    titulo='objetivo específico' if nombre=='objetivos_especificos' else 'momento'
    def persistir():
        draft.update(pendiente=True,reintento=0);guardar(repo,caso_id,draft)
    def cambiar(item_id,campo):
        item=next(x for x in draft['datos'][nombre] if x['id']==item_id)
        item[campo]=st.session_state[f'cotedit_{caso_id}_{nombre}_{item_id}_{campo}'];persistir()
    def mover(item_id,paso):
        items=draft['datos'][nombre];i=next(i for i,x in enumerate(items) if x['id']==item_id)
        j=i+paso
        if 0<=j<len(items):items[i],items[j]=items[j],items[i];persistir()
    def quitar(item_id):
        draft['datos'][nombre]=[x for x in draft['datos'][nombre] if x['id']!=item_id];persistir()
    def agregar():
        draft['datos'][nombre].append({'id':str(uuid4()),**{k:'' for k in campos}});persistir()
    items=draft['datos'][nombre]
    for i,item in enumerate(items):
        with st.container(border=True):
            for campo in campos:
                key=f'cotedit_{caso_id}_{nombre}_{item["id"]}_{campo}'
                if key not in st.session_state:st.session_state[key]=item.get(campo,'')
                label=f'Objetivo específico {i+1}' if campo=='texto' else f'{"Etiqueta" if campo=="etiqueta" else "Descripción del momento"} {i+1}'
                widget=st.text_input if campo=='etiqueta' else st.text_area
                widget(label,key=key,on_change=cambiar,args=(item['id'],campo),max_chars=5000)
            a,b,c=st.columns(3)
            a.button('↑ Subir',key=f'up_{caso_id}_{nombre}_{item["id"]}',disabled=i==0,on_click=mover,args=(item['id'],-1),width='stretch')
            b.button('↓ Bajar',key=f'down_{caso_id}_{nombre}_{item["id"]}',disabled=i==len(items)-1,on_click=mover,args=(item['id'],1),width='stretch')
            c.button('Quitar',key=f'del_{caso_id}_{nombre}_{item["id"]}',on_click=quitar,args=(item['id'],),width='stretch')
    st.button('Agregar '+titulo,key=f'add_{caso_id}_{nombre}',on_click=agregar)
