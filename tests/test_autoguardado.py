from copy import deepcopy
import unittest
from servicios.autoguardado import preparar,editar,guardar,deshacer
from utils.validaciones import validar_campo,rut_valido


class Repo:
    def __init__(self):
        self.row=dict(id='ficticio',version=1,estado='Solicitud',cliente='Fundación Horizonte',contacto='Camila Rojas',email='camila@example.test')
        self.writes=0;self.offline=False;self.lose_ack=False
    def owner_only(self):pass
    def get_case(self,_):
        if self.offline:raise ConnectionError()
        return deepcopy(self.row)
    def update_case(self,case,changes):
        if self.offline:raise ConnectionError()
        if case['version']!=self.row['version']:raise ValueError('Conflicto')
        self.row.update(changes);self.row['version']+=1;self.writes+=1
        if self.lose_ack:
            self.lose_ack=False;raise ConnectionError()
        return deepcopy(self.row)


class AutoguardadoTests(unittest.TestCase):
    def setUp(self):
        self.repo=Repo();self.draft=preparar({},self.repo.row)
    def test_independent_validation(self):
        editar(self.draft,'email','sin-arroba');editar(self.draft,'contacto','Daniela Soto')
        guardar(self.repo,self.draft,ahora=100)
        self.assertEqual(self.repo.row['contacto'],'Daniela Soto')
        self.assertIn('email',self.draft['errores'])
        self.assertEqual(self.draft['pendientes']['email']['valor'],'sin-arroba')
    def test_network_retry_keeps_draft_and_does_not_duplicate_lost_ack(self):
        editar(self.draft,'contacto','Daniela Soto');self.repo.offline=True
        guardar(self.repo,self.draft,ahora=100)
        self.assertIn('contacto',self.draft['pendientes'])
        self.repo.offline=False;self.repo.lose_ack=True
        guardar(self.repo,self.draft,ahora=110)
        guardar(self.repo,self.draft,ahora=120)
        self.assertEqual(self.repo.writes,1)
        self.assertFalse(self.draft['pendientes'])
    def test_external_change_never_gets_overwritten(self):
        editar(self.draft,'contacto','Daniela Soto')
        self.repo.row.update(contacto='Francisca Muñoz',version=2)
        guardar(self.repo,self.draft,ahora=100)
        self.assertEqual(self.repo.row['contacto'],'Francisca Muñoz')
        self.assertIn('contacto',self.draft['conflictos'])
    def test_undo_version_and_deadline(self):
        editar(self.draft,'estado','En revisión');guardar(self.repo,self.draft,ahora=100)
        deshacer(self.repo,self.draft,ahora=109)
        self.assertEqual(self.repo.row['estado'],'Solicitud')
        editar(self.draft,'estado','En revisión');guardar(self.repo,self.draft,ahora=120)
        with self.assertRaises(ValueError):deshacer(self.repo,self.draft,ahora=130)
    def test_undo_cannot_overwrite_a_later_change(self):
        editar(self.draft,'estado','En revisión');guardar(self.repo,self.draft,ahora=100)
        self.repo.row['version']+=1
        with self.assertRaises(ValueError):deshacer(self.repo,self.draft,ahora=105)
    def test_annul_requires_confirmation(self):
        editar(self.draft,'estado','Cancelado');guardar(self.repo,self.draft,ahora=100)
        self.assertEqual(self.repo.writes,0)
        guardar(self.repo,self.draft,ahora=100,confirmar_anulacion=True)
        self.assertEqual(self.repo.row['estado'],'Cancelado')
        self.assertIsNone(self.draft['deshacer'])
    def test_validation_rut_phone_numbers(self):
        self.assertTrue(rut_valido('12.345.678-5'))
        self.assertFalse(rut_valido('12.345.678-9'))
        for field,value in [('telefono','abc'),('participantes',2.5),('horas',float('nan'))]:
            self.assertIsNotNone(validar_campo(field,value))
        self.assertIsNone(validar_campo('telefono','+56 9 1234 5678'))
