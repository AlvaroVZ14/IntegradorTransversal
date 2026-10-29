"""Contrato del menú nativo; datos ficticios y sin conexión a Supabase."""
from unittest import TestCase
from unittest.mock import patch
from pathlib import Path
import streamlit as st
from streamlit.testing.v1 import AppTest
from utils.navegacion import PAGINAS


class NavegacionSuperiorTests(TestCase):
    def setUp(self):
        # AppTest.from_string vive en un directorio temporal: resolver las
        # páginas reales contra la raíz del repositorio, como hace app.py.
        raiz=Path(__file__).resolve().parent.parent
        paginas={t:(str(raiz/a),r,i,g) for t,(a,r,i,g) in PAGINAS.items()}
        cambio=patch.dict(PAGINAS,paginas)
        cambio.start();self.addCleanup(cambio.stop)

    def test_registro_estable_y_enlaces_por_rol(self):
        for rol,esperadas in [('admin',['Hoy','Nueva solicitud','Casos y cotizaciones','Compartir','Dashboard']),
                              ('cliente',['Nueva solicitud']),(None,[])]:
            codigo="""
import streamlit as st
from utils.navegacion import crear_paginas
registro,paginas=crear_paginas(PERFIL)
st.session_state['visibles']=[p.title for p in registro if p._visibility=='visible']
st.session_state['rutas']=list(paginas)
st.navigation(registro,position='hidden')
""".replace('PERFIL',repr({'rol':rol}) if rol else 'None')
            app=AppTest.from_string(codigo).run()
            self.assertFalse(app.exception)
            self.assertEqual(app.session_state['visibles'],esperadas)
            self.assertEqual(len(app.session_state['rutas']),7)

    def test_menu_superior_nativo_y_grupo_mas(self):
        # Simular crecimiento del menú sin agregar ninguna página a producción.
        codigo="""
import streamlit as st
from utils.navegacion import registrar_navegacion
registrar_navegacion({'rol':'admin'})
"""
        original=st.navigation
        for titulos,agrupada in [(['Hoy','Nueva solicitud','Casos y cotizaciones','Compartir','Dashboard'],False),
                                (['Hoy','Nueva solicitud','Casos y cotizaciones','Compartir','Dashboard','Estado'],True)]:
            with patch('utils.navegacion.allowed_pages',return_value=titulos),patch('streamlit.navigation',wraps=original) as nav:
                app=AppTest.from_string(codigo).run()
                self.assertFalse(app.exception)
                self.assertEqual(nav.call_args.kwargs['position'],'top')
                registro=nav.call_args.args[0]
                self.assertEqual(isinstance(registro,dict),agrupada)
                if agrupada:
                    self.assertIn('Más',registro)
                    self.assertEqual(len([p for p in registro[''] if p._visibility=='visible']),4)
